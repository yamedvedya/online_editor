# ----------------------------------------------------------------------
# Author:        yury.matveev@desy.de
# ----------------------------------------------------------------------

"""
"""

import os
import time
import tempfile
import shutil
import logging

import psutil
import PyTango
import xml.etree.cElementTree as ET

from pathlib import Path
from datetime import datetime
from PyQt5 import QtWidgets, QtCore

from onlinexml_editor.aboutdialog import AboutDialog
from onlinexml_editor.config_error import ConfigError
from onlinexml_editor.online_table_model import OnlineModel, DeviceModel, ProxyDeviceModel
from onlinexml_editor.devices_class import DeviceNode, GroupNode, SerialDeviceNode, ConfigurationNode, \
    check_column, SupportAdd
from onlinexml_editor.configure_device import ConfigureDevice
from onlinexml_editor.columns_selector import ColumnSelector
from onlinexml_editor.settings import AppSettings

from onlinexml_editor.gui.main_window_ui import Ui_OnLineEditor
from onlinexml_editor.general_settings import APP_NAME, DEFAULT_SUPERUSER_PASS

logger = logging.getLogger(APP_NAME)


# ----------------------------------------------------------------------
class OnlinexmlEditor(QtWidgets.QMainWindow):
    """
    """
    STATUS_TICK = 2000              # [ms]

    # ----------------------------------------------------------------------
    def __init__(self, options):
        """
        """
        super(OnlinexmlEditor, self).__init__()
        self._ui = Ui_OnLineEditor()
        self._ui.setupUi(self)
        self._load_ui_settings()

        self._super_user_pass = None
        self._online_path = None
        self._superuser_mode = False
        self._last_modified = None
        self._last_edit_step = -1

        counter = 0
        self._temp_dir = os.path.join(tempfile.gettempdir(), 'onlinexml_editor_{:s}'.format(str(counter)))
        while os.path.exists(self._temp_dir):
            counter += 1
            self._temp_dir = os.path.join(tempfile.gettempdir(), 'onlinexml_editor_{:s}'.format(str(counter)))
        os.mkdir(self._temp_dir)

        if not self._load_settings():
            raise RuntimeError('Cannot load settings!')

        # this is a proxy for displaying the whole file
        self.online_model = OnlineModel()
        self.online_model.drag_drop_signal.connect(self.drag_drop)
        self.online_model.save_columns_count()
        self.online_proxy = ProxyDeviceModel()
        self.online_proxy.setSourceModel(self.online_model)
        try:
            self.online_proxy.new_version = True
            self.online_proxy.setRecursiveFilteringEnabled(True)
        except AttributeError:
            self.online_proxy.new_version = False
        self.online_proxy.setFilterKeyColumn(-1)

        self._ui.tw_online.setModel(self.online_proxy)
        self._ui.tw_online.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._ui.tw_online.customContextMenuRequested.connect(lambda pos: self._show_context_menu(pos))
        self._ui.tw_online.setWordWrap(True)

        # this is a proxy for displaying only selected file
        self.viewed_devices = []
        self.viewed_devices_map = {}
        self.device_model = DeviceModel()
        self.device_proxy = ProxyDeviceModel()
        self.device_proxy.setSourceModel(self.device_model)

        self._ui.tb_device.setModel(self.device_proxy)
        self._ui.tb_device.clicked.connect(lambda: self._ui.but_edit_properties.setEnabled(True))
        self._ui.tb_device.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self._ui.tb_device.setWordWrap(True)

        self.online_model.dataChanged.connect(self.new_online_selected)

        self.online_model.set_superuser_mode(self._superuser_mode)
        self.device_model.set_superuser_mode(self._superuser_mode)

        self._ui.but_edit_properties.setEnabled(False)

        self._init_status_bar()
        self._init_actions()

        self.clipboard = None
        self.get_default_lib(options)

        self._status_timer = QtCore.QTimer(self)
        self._status_timer.timeout.connect(self._refresh)
        self._status_timer.start(self.STATUS_TICK)

    # ----------------------------------------------------------------------
    def get_default_lib(self, options):

        file_name = str(options.file)
        if not file_name.endswith('.xml'):
            file_name += '.xml'

        if file_name != 'default.xml' and not os.path.exists(os.path.join(self._library_path, file_name)):
            file = QtWidgets.QFileDialog.getOpenFileName(self, 'Cannot find library file, please locate it',
                                                         self._library_path, 'XML settings (*.xml)')
            if file[0]:
                if self._read_lib(file[0]):
                    return
        else:
            if self._read_lib(os.path.join(self._library_path, file_name)):
                return

        if not os.path.exists(self._library_path):
            os.mkdir(self._library_path)

        if not os.path.exists(os.path.join(self._library_path, file_name)):
            QtWidgets.QMessageBox.warning(self, 'Open error',
                                          'Cannot open default library, current online.xml will be imported!')
            if not self.import_lib():
                raise RuntimeError('Cannot import online.xml')

    # ----------------------------------------------------------------------
    def open_new_lib(self):
        new_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open new library file', str(Path.home()),
                                                            'Library files (*.xml)')
        if new_file:
            self.save_history()
            if new_file == self._online_path:
                logger.info('Importing current online.xml from {}'.format(new_file))
                self.import_lib()
            else:
                logger.info('Opening new file {}'.format(new_file))
                self._read_lib(new_file)
            return True
        else:
            return False

    # ----------------------------------------------------------------------
    def save_lib_as(self):
        new_file, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save library as', str(Path.home()),
                                                            'Library files (*.xml)')
        if new_file:
            new_file += '.xml'
            logger.info('Saving library to file {}'.format(new_file))
            self.save_library(new_file)

    # ----------------------------------------------------------------------
    def force_import_lib(self):
        reply = QtWidgets.QMessageBox.critical(self, 'Import Online.xml',
                                               'Attention, this will overwrite your current library! Continue?',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                                               QtWidgets.QMessageBox.Cancel)
        if reply == QtWidgets.QMessageBox.Yes:
            self.import_lib()

    # ----------------------------------------------------------------------
    def import_lib(self):
        try:
            settings = ET.parse(self._online_path)
        except Exception as err:
            logger.error('Cannot import online.xml: {}'.format(repr(err)))
            return False

        self.online_model.clear()
        self.device_model.clear()

        self.online_model.start_adding_row(1)

        group = ConfigurationNode(self.online_model.root,
                                  {'name': 'default', 'active': 'yes', 'comment': 'as imported'})
        for device in settings.getroot():
            info = {'active': 'yes', 'comment': ''}
            for child in device:
                info[child.tag] = child.text
            DeviceNode(group, info)

        self.online_model.finish_row_changes()
        self.save_library()

        self.refresh_tables()

        return True

    # ----------------------------------------------------------------------
    def refresh_tables(self):
        """
        """
        self._ui.tb_device.viewport().update()
        for ind in range(self._ui.tb_device.horizontalHeader().count()):
            self._ui.tb_device.horizontalHeader().setSectionResizeMode(ind, QtWidgets.QHeaderView.ResizeToContents)

        self._ui.tw_online.viewport().update()
        for ind in range(self._ui.tw_online.header().count()):
            self._ui.tw_online.header().setSectionResizeMode(ind, QtWidgets.QHeaderView.ResizeToContents)

    # --------------------------------------------------------------------
    def _read_lib(self, file_name):
        try:
            configs = ET.parse(file_name).getroot()
        except Exception as err:
            logger.error('Cannot read {}: {}'.format(file_name, repr(err)))
            return False

        self.online_model.clear()
        self.device_model.clear()

        self.online_model.start_adding_row(len(configs))
        for configuration in configs:
            group = ConfigurationNode(self.online_model.root, configuration)
            self._parse_group(group, configuration)

        self.online_model.finish_row_changes()

        self.refresh_tables()

        return True

    # ----------------------------------------------------------------------
    def _data_modified(self):
        self._last_modified = time.time()
        logger.debug('Data modified at {}'.format(self._last_modified))

        self.refresh_tables()

    # ----------------------------------------------------------------------
    def undo(self):
        f_name = os.path.join(self._temp_dir, '{:s}.xml'.format(str(self._last_edit_step)))
        logger.debug('Undo: last edit step {}, load history file {}'.format(self._last_edit_step, f_name))
        self._read_lib(f_name)
        self._last_edit_step -= 1
        self.undo_action.setEnabled(self._last_edit_step >= 0)
        self.refresh_tables()

    # ----------------------------------------------------------------------
    def save_history(self):
        self._last_edit_step += 1
        f_name = os.path.join(self._temp_dir, '{:s}.xml'.format(str(self._last_edit_step)))
        logger.debug('Save history file: last edit step {}, file {}'.format(self._last_edit_step, f_name))
        self._drop_library(f_name)
        self.undo_action.setEnabled(True)
        self.refresh_tables()

    # ----------------------------------------------------------------------
    def save_library(self, file_name=None):
        self.refresh_tables()

        if file_name is not None:
            logger.info('Saving in {}'.format(file_name))
            self._drop_library(file_name)

        file_name = os.path.join(self._library_path, 'default.xml')
        logger.info('Saving in {}'.format(file_name))
        self._drop_library(file_name)

        QtCore.QSettings(APP_NAME).setValue("last_saved", time.time())

    # ----------------------------------------------------------------------
    def _drop_library(self, new_file):
        library = ET.Element('library')
        library.text = '\n\t'
        data = None
        for config in self.online_model.root.children:
            data = config.get_data_to_save(library, '\t')

        if data is not None:
            data.tail = '\n'

        tree = ET.ElementTree(library)
        if new_file == os.path.join(self._library_path, 'default.xml'):
            self.archive(new_file)

        tree.write(new_file)

    # ----------------------------------------------------------------------
    def table_clicked(self):
        self._ui.tb_device.viewport().update()
        for ind in range(self._ui.tb_device.horizontalHeader().count()):
            pass

    # ----------------------------------------------------------------------
    def _parse_group(self, root, data):
        for item in data:
            self._parse_device(root, item)

    # ----------------------------------------------------------------------
    def _parse_device(self, root, item, row_to_insert=-1):
        if item.tag == 'group':
            self._parse_group(GroupNode(root, item, row=row_to_insert), item)

        elif item.tag == 'serial_device':
            group = SerialDeviceNode(root, item, row=row_to_insert)
            for sub_item in item.findall('single_device'):
                DeviceNode(group, sub_item)
        else:
            DeviceNode(root, item, row=row_to_insert)

    # ----------------------------------------------------------------------
    def index_to_viewed_device(self, index):

        index = self.online_proxy.mapToSource(index)

        if self.online_model.is_single_device(index) or self.online_model.is_group(index):
            return self.online_model.get_node(index), index

        elif self.online_model.is_serial_device(index) or self.online_model.is_part_or_serial_device(index):
            device = self.online_model.get_node(index)
            if self.online_model.is_part_or_serial_device(index):
                device = device.parent
                index = index.parent()
            return device, index

        return None, None

    # ----------------------------------------------------------------------
    def get_row_path(self, index, path=''):

        if index.parent().isValid():
            path = self.get_row_path(index.parent(), path)

        path += str(index.row())

        return path

    # ----------------------------------------------------------------------
    def new_device_to_table(self, added_selection, released_selection):

        for index in released_selection.indexes()[::self.online_proxy.columnCount()]:
            removed_device, index = self.index_to_viewed_device(index)
            if removed_device is not None:
                for device, path in self.viewed_devices:
                    if removed_device == device:
                        self.viewed_devices.remove((device, path))

        for index in added_selection.indexes()[::self.online_proxy.columnCount()]:
            new_device, index = self.index_to_viewed_device(index)
            if new_device is not None:
                device_not_found = True
                for device, _ in self.viewed_devices:
                    device_not_found *= new_device != device
                if device_not_found:
                    self.viewed_devices.append((new_device, self.get_row_path(index)))

        self.viewed_devices.sort(key=lambda x: x[1])

        logger.debug('Displaying {}'.format(';'.join([device.info['name'] for device, _ in self.viewed_devices])))

        self.refresh_table()

    # ----------------------------------------------------------------------
    def refresh_table(self):

        self.device_model.clear()
        self.viewed_devices_map = {}
        self._ui.but_edit_properties.setEnabled(False)

        for device, _ in self.viewed_devices:
            current_row = self.device_model.rowCount()
            if isinstance(device, SerialDeviceNode):
                self.device_model.start_adding_row(device.child_count, current_row)
                for idx, children in enumerate(device.children):
                    node = DeviceNode(self.device_model.root, children.info, device.info)
                    self.viewed_devices_map[node] = (device, idx)
                self.device_model.finish_row_changes()

            elif isinstance(device, DeviceNode):
                self.device_model.start_adding_row(1, current_row)
                DeviceNode(self.device_model.root, device.info)
                self.device_model.finish_row_changes()

            elif isinstance(device, GroupNode):
                num_devices = 0
                for children in device.children:
                    if isinstance(children, DeviceNode):
                        num_devices += 1
                self.device_model.start_adding_row(num_devices, current_row)
                num_devices = 0
                for idx, children in enumerate(device.children):
                    if isinstance(children, DeviceNode):
                        DeviceNode(self.device_model.root, children.info)
                        num_devices += 1
                self.device_model.finish_row_changes()

            self.device_model.add_columns()
            if isinstance(device, SerialDeviceNode):
                for column in range(3, self._ui.tb_device.horizontalHeader().count()-1):
                    if self.device_model.headerData(column, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole) not in ['sardananame', 'comment']:
                        self._ui.tb_device.setSpan(current_row, column, device.child_count, 1)

        self.refresh_tables()

    # ----------------------------------------------------------------------
    def _show_context_menu(self, pos):

        if not self._superuser_mode:
            return

        menu = QtWidgets.QMenu()

        add_menu = QtWidgets.QMenu('Add...')

        add_group = QtWidgets.QAction('Group')
        add_serial = QtWidgets.QAction('Serial devices')
        add_device = QtWidgets.QAction('Device')

        paste_action = QtWidgets.QAction('Paste')
        copy_config = QtWidgets.QAction('Paste')
        copy_action = QtWidgets.QAction('Copy')
        cut_action = QtWidgets.QAction('Cut')
        del_action = QtWidgets.QAction('Delete')
        new_action = QtWidgets.QAction('New configuration')
        convert_action = QtWidgets.QAction()

        clip_devices = None

        selected_indexes = [self.online_proxy.mapToSource(index) for index in
                            self._ui.tw_online.selectionModel().selectedIndexes()][::self.online_proxy.columnCount()]
        selected_devices = [self.online_model.get_node(index) for index in selected_indexes]

        clicked_index = self._ui.tw_online.indexAt(pos)

        if clicked_index.isValid():
            clicked_index = self.online_proxy.mapToSource(clicked_index)
            clicked_device = self.online_model.get_node(clicked_index)

            if len(selected_indexes) == 1:
                add_support = clicked_device.accept_add()
                if add_support in [SupportAdd.ONLY_DEVICE, SupportAdd.ANY]:
                    if add_support == SupportAdd.ANY:
                        add_menu.addAction(add_group)
                        add_menu.addAction(add_serial)
                    add_menu.addAction(add_device)
                    menu.addMenu(add_menu)

                if self.clipboard is not None:
                    paste_enabled, clip_devices = clicked_device.accept_paste(self.clipboard)
                    if paste_enabled:
                        menu.addAction(paste_action)

                convert_enable, caption = clicked_device.can_be_converted()
                if convert_enable:
                    convert_action.setText(caption)
                    menu.addAction(convert_action)

            menu.addAction(cut_action)
            menu.addAction(copy_action)
            menu.addAction(del_action)

        else:
            clicked_device = None
            menu.addAction(new_action)
            if self.clipboard is not None and len(self.clipboard) == 1 and self.clipboard[0].tag == 'configuration':
                clip_devices = self.clipboard[0]
                menu.addAction(copy_config)

        action = menu.exec_(self.mapToGlobal(pos))

        if action is not None:
            try:
                self._last_modified = time.time()
                self.save_history()

                log_msg = 'Context menu: action: {}, '.format(action.text().lower())

                if clicked_device is not None:
                    log_msg += ', clicked_device: {}'.format(clicked_device.info['name'])

                for device in selected_devices:
                    log_msg += ', selected_device: {}'.format(device.info['name'])

                if clip_devices is not None:
                    for device in clip_devices:
                        log_msg += ', clip_device: {}'.format(device.attrib['name'])

                logger.debug(log_msg)

                if action == copy_action:
                    self.clipboard = [device.get_data_to_copy() for device in selected_devices]

                elif action == cut_action:
                    self.clipboard = [device.get_data_to_copy() for device in selected_devices]
                    for index in selected_indexes:
                        self.online_model.remove(index)

                elif action == del_action:
                    for index in selected_indexes:
                        self.online_model.remove(index)

                elif action == paste_action:
                    for device in clip_devices:
                        self.add_element(clicked_index, device, index=clicked_index)

                elif action == copy_config:
                    self.add_config(clip_devices)

                elif action == convert_action:
                    new_device = clicked_device.get_converted()
                    self.add_element(clicked_index.parent(), new_device, index=clicked_index)
                    self.online_model.remove(clicked_index)

                elif action in [add_group, add_serial, add_device]:
                    if action == add_group:
                        type = 'group'
                    elif action == add_serial:
                        type = 'serial_device'
                    else:
                        type = 'single_device'

                    dialog = ConfigureDevice(self, {'new': True, 'type': type, 'parent': clicked_device})

                    if dialog.exec_():
                        self.add_element(clicked_index, dialog.new_device, index=clicked_index)

                elif action == new_action:
                    dialog = ConfigureDevice(self, {'new': True, 'type': 'configuration'})
                    if dialog.exec_():
                        self.add_element(QtCore.QModelIndex(), dialog.new_device,
                                         row=self.online_model.get_node(self.online_model.root_index).child_count)

                self.refresh_tables()
            except Exception as err:
                logger.error(f'Could not execute command: {err}')

    # ----------------------------------------------------------------------
    def drag_drop(self, mode, dropped_index, dropped_row, dragged_indexes):

        dragged_devices = [self.online_model.get_node(index).get_data_to_copy() for index in dragged_indexes]
        dropped_device = self.online_model.get_node(dropped_index)

        msg = 'Drag&drop: dragged '
        for device in dragged_devices:
            msg += f'{device.attrib["name"]};'

        logger.debug(f"{msg} dropped to {dropped_device.info['name']} at row {dropped_row}")

        paste_enabled, clip_devices = dropped_device.accept_paste(dragged_devices)
        if paste_enabled:
            self._last_modified = time.time()
            self.save_history()

            logger.debug('Drag&drop: paste_enabled')
            for device, index in zip(clip_devices, dragged_indexes):
                self.add_element(dropped_index, device, row=dropped_row)
                if mode == 'move':
                    self.online_model.remove(index)

            self.refresh_table()

    # ----------------------------------------------------------------------
    def add_config(self, config):
        logger.debug('Adding config')
        self.online_model.start_adding_row(1, self.online_model.get_node(self.online_model.root_index).child_count)
        group = ConfigurationNode(self.online_model.root, config)
        group.deactivate()
        self._parse_group(group, config)
        self.online_model.finish_row_changes()

    # ----------------------------------------------------------------------
    def add_element(self, insert_index, insert_device, index=None, row=0):
        if index is not None:
            device_to_insert, row_to_insert = self.online_model.start_insert_row(insert_index, index=index)
        else:
            device_to_insert, row_to_insert = self.online_model.start_insert_row(insert_index, row=row)

        self._parse_device(device_to_insert, insert_device, row_to_insert)
        self.online_model.finish_row_changes()

    # ----------------------------------------------------------------------
    def edit_device_properties(self):
        if len(self.viewed_devices):

            selected_index = self.device_proxy.mapToSource(self._ui.tb_device.selectionModel().currentIndex())
            selected_device = self.device_model.get_node(selected_index)

            logger.debug('Edit properties for {}'.format(selected_device.info['name']))

            params = {'new':  False}

            if selected_device in self.viewed_devices_map:
                params['device'] = self.viewed_devices_map[selected_device][0]
                params['sub_device'] = self.viewed_devices_map[selected_device][1]
            else:
                params['device'] = selected_device
                params['sub_device'] = None

            self.save_history()
            if ConfigureDevice(self, params).exec_():
                self._last_modified = time.time()
                self.refresh_table()
            else:
                self._last_edit_step -= 1
                self.undo_action.setEnabled(self._last_edit_step >= 0)

    # ----------------------------------------------------------------------
    def new_online_selected(self, index):

        new_device = self.online_model.get_node(index)
        logger.info('New configuration selected: {}'.format(new_device.info['name']))
        if isinstance(new_device, ConfigurationNode) and index.column() == check_column:
            for device in self.online_model.root.children:
                if device != new_device:
                    device.deactivate()

    # ----------------------------------------------------------------------
    def set_super_user(self, button):

        if button == self.super_user:
            if not self._superuser_mode:
                password, okPressed = QtWidgets.QInputDialog.getText(self, "Type superuser password", "Superuser pass:",
                                                                 QtWidgets.QLineEdit.Password, "")
                if okPressed:
                    self._superuser_mode = password == self._super_user_pass
        else:
            self._superuser_mode = False

        if self._superuser_mode:
            logger.info('Set superuser')
        else:
            logger.info('Set regular user')

        self.normal_user.setChecked(not self._superuser_mode)
        self.super_user.setChecked(self._superuser_mode)

        self.online_model.set_superuser_mode(self._superuser_mode)
        self.device_model.set_superuser_mode(self._superuser_mode)

        self.refresh_tables()

    # ----------------------------------------------------------------------
    def config_error(self, text='', detailed_text='', applying=False):

        self.msg = ConfigError(text, detailed_text, applying)
        self.msg.setModal(False)

        if applying:
            return self.msg.exec_()
        else:
            self.msg.show()

    # ----------------------------------------------------------------------
    def info_dialog(self, text):

        self.msg = QtWidgets.QMessageBox()
        self.msg.setModal(False)
        self.msg.setIcon(QtWidgets.QMessageBox.Information)
        self.msg.setText(text)
        self.msg.setWindowTitle("Info")
        self.msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        self.msg.show()

    # ----------------------------------------------------------------------
    def check_configuration(self, only_check=True):

        def _parse_error(dict):
            msg = ''
            for key, values in dict.items():
                msg += '\t' + key + ':\n'
                for value in values:
                    msg += '\t\t' + value + '\n'
            return msg

        config_to_export = None
        for config in self.online_model.root.children:
            if config.is_activated():
                config_to_export = config
                break

        if config_to_export is None:
            self.config_error(text="No configuration is selected")
            return

        logger.info('Checking configuration {}'.format(config_to_export.info['name']))
        data = []
        used_names = {}
        used_addresses = {}

        double_name = {}
        double_addresses = {}
        wrong_addresses = {}
        off_devices = {}
        wrong_attributes = {}
        rest_errors = {}

        cofig_has_error = False
        active_mgs = {}
        for device in config_to_export.get_all_activated_devices():
            data.append(device.get_data_to_export())
            is_tango = False
            has_error = False
            my_name = ''
            tango_address = None
            parameter = None
            hostname = None
            is_mg = False
            is_diffract = False
            for child in data[-1]:
                if child.tag == 'type':
                    is_diffract = child.text == 'diffractometercontroller'

            for child in data[-1]:
                if child.tag in ['name', 'sardananame'] and my_name != child.text:
                    if child.text in used_names.keys():
                        logger.warning(
                            'Checking configuration: {}: repeating name {}'.format(device.get_my_path(), child.text))
                        has_error = True
                        if child.text not in double_name.keys():
                            double_name[child.text] = [used_names[child.text], device.get_my_path()]
                        else:
                            double_name[child.text].append(device.get_my_path())
                    else:
                        my_name = child.text
                        used_names[child.text] = device.get_my_path()

                elif child.tag == 'device' and not is_diffract:
                    if child.text in used_addresses.keys():
                        logger.warning(
                            'Checking configuration: {}: repeating address {}'.format(device.get_my_path(), child.text))
                        has_error = True
                        if child.text not in double_addresses.keys():
                            double_addresses[child.text] = [used_addresses[child.text], device.get_my_path()]
                        else:
                            double_addresses[child.text].append(device.get_my_path())
                    else:
                        used_addresses[child.text] = device.get_my_path()

                    tokens = child.text.split('/')
                    if len(tokens) > 2:
                        tango_address = '/'.join(tokens[:3])
                    else:
                        tango_address = None
                    if len(tokens) > 3:
                        parameter = tokens[3]
                    else:
                        parameter = None

                elif child.tag == 'hostname':
                    hostname = child.text

                elif child.tag == 'control':
                    is_tango = child.text == 'tango'

                elif child.text == 'measurement_group':
                    is_mg = True

                elif child.tag == 'mgs':
                    active_mgs[my_name] = child.text

            if is_tango and not is_mg and not is_diffract:
                if hostname is None:
                    rest_errors[my_name] = ['No hostname']
                    logger.warning(
                        'Checking configuration: {}: no hostname'.format(device.get_my_path()))
                    has_error = True
                elif tango_address is None:
                    rest_errors[my_name] = ['No tango address']
                    logger.warning(
                        'Checking configuration: {}: no tango address'.format(device.get_my_path()))
                    has_error = True
                else:
                    try:
                        dev = PyTango.DeviceProxy(hostname + '/' + tango_address)
                        try:
                            dev.state()
                            if parameter is not None:
                                try:
                                    getattr(dev, parameter)
                                except:
                                    has_error = True
                                    logger.warning(
                                        'Checking configuration: {}: wrong attribute {}'.format(device.get_my_path(),
                                                                                                parameter))
                                    wrong_attributes[my_name] = [device.get_my_path()]

                        except PyTango.DevFailed:
                            has_error = True
                            logger.warning(
                                'Checking configuration: {}: device OFF'.format(device.get_my_path(),
                                                                                hostname + '/' + tango_address))
                            off_devices[my_name] = [device.get_my_path()]

                    except PyTango.DevFailed:
                        has_error = True
                        logger.warning(
                            'Checking configuration: {}: wrong address'.format(device.get_my_path(),
                                                                               hostname + '/' + tango_address))
                        wrong_addresses[my_name] = [device.get_my_path()]

            if has_error:
                cofig_has_error = True
            else:
                logger.info('Checking configuration: {} is OK'.format(device.get_my_path()))

        for name, devices in active_mgs.items():
            has_error = False
            devices = [device.strip().replace('timers=', '').replace('counters=', '')
                       for device in devices.replace(' ', '').split(',')]
            for device in devices:
                if device not in used_names:
                    has_error = True
                    logger.warning(
                        f'Checking configuration: {device} listed in mg {name} is  ot included in configuration')
                    rest_errors[name] = [f'MG {name}: {device} not in configuration']

            if has_error:
                cofig_has_error = True
            else:
                logger.info('Checking configuration: mg {} is OK'.format(name))

        if cofig_has_error:
            logger.info('Checking configuration done. Errors found')
            details = ''
            if len(double_name):
                details += 'DUPLICATE NAMES:\n'
                details += _parse_error(double_name)
            if len(double_addresses):
                details += 'DUPLICATE ADDRESSES:\n'
                details += _parse_error(double_addresses)
            if len(wrong_addresses):
                details += 'WRONG ADDRESSES:\n'
                details += _parse_error(wrong_addresses)
            if len(off_devices):
                details += 'OFF DEVICES:\n'
                details += _parse_error(off_devices)
            if len(wrong_attributes):
                details += 'WRONG ATTRIBUTES:\n'
                details += _parse_error(wrong_attributes)
            if len(rest_errors):
                details += 'REST ERRORS:\n'
                details += _parse_error(rest_errors)
            if only_check:
                self.config_error(text='Config has errors!', detailed_text=details)
            else:
                if self.config_error(text='Config has errors!', detailed_text=details, applying=True):
                    return data
                else:
                    return None
        else:
            logger.info('Checking configuration done. All is OK')
            if only_check:
                self.info_dialog('Configuration is OK')
            else:
                return data

    # ----------------------------------------------------------------------
    def archive(self, file_name):
        dir_name = os.path.join(os.path.dirname(file_name), 'archive')
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)

        base_name = os.path.join(dir_name, datetime.today().strftime('%Y_%m_%d_%H_%M_%S'))
        new_name = base_name + '.xml'
        counter = 0
        while os.path.exists(new_name):
            counter += 1
            new_name = base_name + f'{counter}' + '.xml'

        shutil.move(file_name, new_name)
        logger.info('Archive {} to {}'.format(file_name, new_name))

    # ----------------------------------------------------------------------
    def apply_configuration(self):
        self.save_library()
        data = self.check_configuration(False)

        if data is not None:

            if self._auto_archive:
                self.archive(self._online_path)

            logger.info('Applying configuration: saving to {}'.format(self._online_path))

            root = ET.Element("hw")
            root.text = '\n'

            for element in data:
                root.append(element)

            tree = ET.ElementTree(root)
            tree.write(self._online_path, xml_declaration=True)

            settings = QtCore.QSettings(APP_NAME)
            settings.setValue("MainWindow/geometry", self.saveGeometry())

            QtCore.QSettings(APP_NAME).setValue("last_applied", os.path.getmtime(self._online_path))

            self._last_modified = time.time()
            QtCore.QSettings(APP_NAME).setValue("last_modified", self._last_modified)

            QtCore.QSettings(APP_NAME).setValue("last_saved", time.time())

    # ----------------------------------------------------------------------
    def modify_filters(self, text):

        logger.info('Filtering {}'.format(text))

        self.online_proxy.setFilterRegExp(text)
        self.online_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.online_proxy.setDynamicSortFilter(True)

        if text != '':
            self._ui.tw_online.expandAll()
        else:
            self._ui.tw_online.collapseAll()

    # ----------------------------------------------------------------------
    def configure_columns(self):
        if ColumnSelector().exec_():
            self.online_model.add_columns()

    # ----------------------------------------------------------------------
    def show_about(self):
        AboutDialog(self).exec_()

    # ----------------------------------------------------------------------
    def show_settings(self):
        dialog = AppSettings(self)
        if dialog.exec_():
            self._load_settings()

    # ----------------------------------------------------------------------
    def closeEvent(self, event):
        """
        """
        if self.clean_close():
            event.accept()
        else:
            event.ignore()

    # ----------------------------------------------------------------------
    def clean_close(self):
        """
        """
        logger.info('Close: removing tmp files from {}'.format(self._temp_dir))

        self._save_ui_settings()
        if self._auto_save:
            self.save_library()

        shutil.rmtree(self._temp_dir, ignore_errors=True)

        QtWidgets.qApp.clipboard().clear()

        return True

    # ----------------------------------------------------------------------
    def _quit_program(self):
        """
        """
        if self.clean_close():
            QtWidgets.qApp.quit()
            # pass

    # ----------------------------------------------------------------------
    def _save_ui_settings(self):
        """Save basic GUI settings.
        """
        settings = QtCore.QSettings(APP_NAME)

        settings.setValue("MainWindow/geometry", self.saveGeometry())
        settings.setValue("MainWindow/state", self.saveState())

    # ----------------------------------------------------------------------
    def _load_ui_settings(self):
        """Load basic GUI settings.
        """
        settings = QtCore.QSettings(APP_NAME)

        try:
            self.restoreGeometry(settings.value("MainWindow/geometry"))
        except:
            pass

        try:
            self.restoreState(settings.value("MainWindow/state"))
        except:
            pass

    # ----------------------------------------------------------------------
    def _load_settings(self):
        settings = QtCore.QSettings(APP_NAME)

        all_ok = True

        path = settings.value('OnlinePath')
        if path is None:
            all_ok *= False
        else:
            self._online_path = str(path)
            logger.info('Load settings: online.xml path {}'.format(self._online_path))

        path = settings.value('LibraryPath')
        if path is None:
            all_ok *= False
        else:
            self._library_path = str(path)
            logger.info('Load settings: library path {}'.format(self._library_path))

        autosave = settings.value('AutoSave')
        if path is None:
            all_ok *= False
        else:
            self._auto_save = bool(autosave)
            logger.info(f'Load settings: autosave {"True" if self._auto_save else "False"}')

        autoarchive = settings.value('AutoArchive')
        if path is None:
            all_ok *= False
        else:
            self._auto_archive = bool(autoarchive)
            logger.info(f'Load settings: autoarchive {"True" if self._auto_archive else "False"}')

        password = settings.value('SuperuserPassword')
        if password is None:
            self._super_user_pass = DEFAULT_SUPERUSER_PASS
        else:
            self._super_user_pass = str(password)

        try:
            self._superuser_mode = bool(settings.value('DefaultSuperuser'))
            logger.info('Load settings: DEFAULT SUPERUSER!!!')
        except:
            self._superuser_mode = False

        if not all_ok:
            dialog = AppSettings(self)
            if dialog.exec_():
                self._online_path = dialog.online_path
                self._library_path = dialog.library_path

                self._auto_save = dialog.auto_save
                self._auto_archive = dialog.auto_archive

                return True
            return False

        try:
           self._last_modified = float(QtCore.QSettings(APP_NAME).value("last_modified"))
        except:
           self._last_modified = 0

        return True

    # ----------------------------------------------------------------------
    def _init_actions(self):
        """
        """
        self.undo_action = QtWidgets.QAction('Undo', self)
        self.undo_action.setShortcut('Ctrl+Z')
        self.undo_action.triggered.connect(self.undo)
        self.undo_action.setEnabled(False)

        open_lib_action = QtWidgets.QAction('Open library', self)
        open_lib_action.setShortcut('Ctrl+O')
        open_lib_action.triggered.connect(self.open_new_lib)

        save_lib_action = QtWidgets.QAction('Save library', self)
        # save_lib_as.setShortcut('Ctrl+S')
        save_lib_action.triggered.connect(lambda: self.save_library())

        saveas_lib_action = QtWidgets.QAction('Save library as', self)
        # save_lib_as.setShortcut('Ctrl+S')
        saveas_lib_action.triggered.connect(self.save_lib_as)

        columns_action = QtWidgets.QAction('Select columns', self)
        # save_lib_as.setShortcut('Ctrl+S')
        columns_action.triggered.connect(self.configure_columns)

        settings_action = QtWidgets.QAction('Settings', self)
        settings_action.triggered.connect(self.show_settings)

        mode_menu = QtWidgets.QMenu('Switch user', self)

        self.normal_user = QtWidgets.QAction('Standart user', self)
        self.normal_user.setCheckable(True)
        self.super_user = QtWidgets.QAction('Superuser', self)
        self.super_user.setCheckable(True)
        mode_menu.addAction(self.normal_user)
        mode_menu.addAction(self.super_user)

        chk_group = QtWidgets.QActionGroup(self)
        chk_group.addAction(self.normal_user)
        chk_group.addAction(self.super_user)

        import_lib_action = QtWidgets.QAction('Import current online.xml', self)
        # save_lib_as.setShortcut('Ctrl+S')
        import_lib_action.triggered.connect(self.force_import_lib)

        self.normal_user.setChecked(not self._superuser_mode)
        self.super_user.setChecked(self._superuser_mode)

        chk_group.triggered.connect(self.set_super_user)

        about_action = QtWidgets.QAction('About', self)
        about_action.triggered.connect(self.show_about)

        self.menuBar().addAction(self.undo_action)
        self.menuBar().addAction(open_lib_action)
        self.menuBar().addAction(save_lib_action)
        self.menuBar().addAction(saveas_lib_action)
        self.menuBar().addAction(columns_action)
        self.menuBar().addMenu(mode_menu)
        self.menuBar().addAction(settings_action)
        self.menuBar().addAction(import_lib_action)
        self.menuBar().addAction(about_action)

        self._ui.but_edit_properties.clicked.connect(self.edit_device_properties)

        self._ui.but_check.clicked.connect(lambda: self.check_configuration(True))
        self._ui.but_apply.clicked.connect(self.apply_configuration)

        self._ui.le_find.textEdited.connect(self.modify_filters)

        self.online_model.dataChanged.connect(self._data_modified)
        self.device_model.dataChanged.connect(self._data_modified)

        self._ui.tw_online.selectionModel().selectionChanged.connect(self.new_device_to_table)
        self._ui.tb_device.clicked.connect(self.table_clicked)

    # ----------------------------------------------------------------------
    def _init_status_bar(self):
        """
        """
        processID = os.getpid()
        currentDir = os.getcwd()

        lbProcessID = QtWidgets.QLabel("PID {}".format(processID))
        lbProcessID.setStyleSheet("QLabel {color: #000066;}")
        lbCurrentDir = QtWidgets.QLabel("{}".format(currentDir))

            # resource usage
        process = psutil.Process(processID)
        mem = float(process.memory_info().rss) / (1024. * 1024.)
        cpu = process.cpu_percent()

        self._lb_resources_status = QtWidgets.QLabel("| {:.2f}MB | CPU {} % |".format(mem, cpu))

        self.statusBar().addPermanentWidget(lbProcessID)
        self.statusBar().addPermanentWidget(lbCurrentDir)
        self.statusBar().addPermanentWidget(self._lb_resources_status)

    # ----------------------------------------------------------------------
    def _refresh(self):
        """
        """
        try:
           _last_applied = float(QtCore.QSettings(APP_NAME).value("last_applied"))
        except:
           _last_applied = 0

        try:
           _last_modified = float(QtCore.QSettings(APP_NAME).value("last_modified"))
        except:
           _last_modified = 0

        try:
           _last_saved = float(QtCore.QSettings(APP_NAME).value("last_saved"))
        except:
           _last_saved = 0

        if os.path.getmtime(self._online_path) == _last_applied and self._last_modified == _last_modified:
            lb_status_style = "QLabel {color: rgb(50, 255, 50);}"
            lb_status_text = 'APPLIED'
        else:
            lb_status_style = "QLabel {color: rgb(255, 0, 0);}"
            lb_status_text = 'NOT APPLIED'

        self._ui.lb_applied.setStyleSheet(lb_status_style)
        self._ui.lb_applied.setText(lb_status_text)

        if self._last_modified <= _last_saved:
            lb_status_style = "QLabel {color: rgb(50, 255, 50);}"
            lb_status_text = 'SAVED'
        else:
            lb_status_style = "QLabel {color: rgb(255, 0, 0);}"
            lb_status_text = 'NOT SAVED'

        self._ui.lb_saved.setStyleSheet(lb_status_style)
        self._ui.lb_saved.setText(lb_status_text)

        process = psutil.Process(os.getpid())
        mem = float(process.memory_info().rss) / (1024. * 1024.)
        cpu = psutil.cpu_percent()

        self._lb_resources_status.setText("| {:.2f}MB | CPU {} % |".format(mem,
                                                                           cpu))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------


def _check_serial_device(device1, device2):
    result = True
    for child1 in device1:
        key_found = False
        for child2 in device2:
            if child1.tag == child2.tag:
                key_found = True
                result *= child1.text == child2.text
                break
        result *= key_found
    return result
