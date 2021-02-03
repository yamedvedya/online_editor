# ----------------------------------------------------------------------
# Author:        yury.matveev@desy.de
# ----------------------------------------------------------------------

"""
"""

APP_NAME = "OnlieXmlEditor"
SUPER_USER_PASS = 'admin'
online_path = '/usr/local/experiment/online_dir/online.xml'
lib_path = '/gpfs/local/online_libs'

import os
import psutil
import PyTango
import xml.etree.cElementTree as ET
import numpy as np
from copy import deepcopy

from PyQt5 import QtWidgets, QtCore, QtGui

# from src.aboutdialog import AboutDialog
from src.online_table_model import ConfigurationNode, SerialDeviceNode, GroupNode, DeviceNode, \
    OnlineModel, DeviceModel, ProxyDeviceModel
from src.add_device import ConfigureDevice

from src.gui.main_window_ui import Ui_OnLineEditor

# ----------------------------------------------------------------------
class MainWindow(QtWidgets.QMainWindow):
    """
    """
    LOG_PREVIEW = "gvim"
    STATUS_TICK = 2000              # [ms]

    # ----------------------------------------------------------------------
    def __init__(self, options):
        """
        """
        super(MainWindow, self).__init__()
        self._ui = Ui_OnLineEditor()
        self._ui.setupUi(self)
        self._load_ui_settings()

        self.applied = False
        self.superuser_mode = True

        self._init_status_bar()
        self._init_actions()

        self.configs = []
        self.groups = []
        self.devices = []
        self.online_model = OnlineModel()
        self.online_proxy = ProxyDeviceModel()
        self.online_proxy.setSourceModel(self.online_model)
        try:
            self.online_proxy.new_version = True
            self.online_proxy.setRecursiveFilteringEnabled(True)
        except AttributeError:
            self.online_proxy.new_version = False
            # self._ui.le_find.blockSignals(True)
            # self._ui.le_find.setText('Search works only with PyQt5 > 5.10. Ask system admin to update package')
            # self._ui.le_find.setEnabled(False)

        self.view_device = None
        self.viewed_device = None
        self.device_model = DeviceModel()
        self.device_proxy = ProxyDeviceModel()
        self.device_proxy.setSourceModel(self.device_model)

        self.clipboard = None

        self._working_path = None
        self.settings = None
        self._working_file = None
        if options.file is None:
            self._working_path = lib_path
            if not self.open_new_lib():
                raise RuntimeError('No file to display!')
        else:
            self.open_lib(options.file)

        self._status_timer = QtCore.QTimer(self)
        self._status_timer.timeout.connect(self._refresh)
        self._status_timer.start(self.STATUS_TICK)

    # ----------------------------------------------------------------------
    def refresh_tables(self):
        """
        """
        self._ui.tb_device.viewport().update()
        self._ui.tw_online.viewport().update()

    # ----------------------------------------------------------------------
    def open_lib(self, file_name):
        self._working_path = os.path.dirname(os.path.abspath(file_name))
        self._working_file = file_name
        self.settings = ET.parse(file_name)

        self.groups = []
        self.devices = []
        self.online_model.clear()
        self.device_model.clear()

        self.view_device = None

        for ind, configuration in enumerate(self.settings.getroot()):
            group = ConfigurationNode(self.online_model.root, self, np.array([ind]), configuration)
            self.configs.append(group)
            self.devices.append([])
            self._parse_group(group, configuration)

        self._ui.tw_online.setModel(self.online_proxy)
        self._ui.tw_online.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._ui.tw_online.customContextMenuRequested.connect(lambda pos: self._show_context_menu(pos))

        self._ui.tb_device.setModel(self.device_proxy)

        self._ui.tw_online.selectionModel().currentChanged.connect(self.hide_show_table)
        self._ui.tb_device.clicked.connect(self.table_clicked)

        self.refresh_tables()

    # ----------------------------------------------------------------------
    def table_clicked(self):
        self._ui.tb_device.viewport().update()

    # ----------------------------------------------------------------------
    def _parse_group(self, root, data):
        for index, item in enumerate(data):
            self._parse_device(root, item, index)

    # ----------------------------------------------------------------------
    def _parse_device(self, root, item, index):
            sub_path = np.append(root.my_id, [index])
            if item.tag == 'group':
                group = GroupNode(root, self, sub_path, item)
                self.groups.append(group)
                self._parse_group(group, item)

            elif item.tag == 'serial_device':
                group = SerialDeviceNode(root, self, sub_path, item)
                self.groups.append(group)
                for idx, sub_item in enumerate(item.findall('single_device')):
                    self.devices[root.my_id[0]].append(DeviceNode(group, self,
                                                            np.append(sub_path, [idx]), sub_item, group))
            else:
                self.devices[root.my_id[0]].append(DeviceNode(root, self, sub_path, item))

    # ----------------------------------------------------------------------
    def hide_show_table(self, index):
        # pass

        index = self.online_proxy.mapToSource(index)
        self.viewed_device = None
        self.device_model.clear()

        if self.online_model.is_single_device(index):
            device = self.online_model.get_node(index)
            self.device_model.start_adding(1)
            self.viewed_device = device
            self.view_device = DeviceNode(self.device_model.root, self, device.my_id,
                                          device.info, device.serial_device)
            self.device_model.finish_adding()

        elif self.online_model.is_serial_device(index) or self.online_model.is_part_or_serial_device(index):
            device = self.online_model.get_node(index)
            if self.online_model.is_part_or_serial_device(index):
                device = device.parent
            self.viewed_device = device
            self.device_model.start_adding(device.child_count)
            self.view_device = []
            for children in device.children:
                self.view_device.append(DeviceNode(self.device_model.root, self, children.my_id,
                                                   children.info, children.serial_device))

            self.device_model.finish_adding()

        self.device_model.add_columns()
        self.refresh_tables()

    # ----------------------------------------------------------------------
    def _show_context_menu(self, pos):

        if not self.superuser_mode:
            return

        menu = QtWidgets.QMenu()

        add_action = QtWidgets.QAction('Add')
        paste_action = QtWidgets.QAction('Paste')
        copy_action = QtWidgets.QAction('Copy')
        cut_action = QtWidgets.QAction('Cut')
        del_action = QtWidgets.QAction('Delete')
        new_action = QtWidgets.QAction('New configuration...')

        if self._ui.tw_online.indexAt(pos).isValid():
            selected_index = self.online_proxy.mapToSource(self._ui.tw_online.selectionModel().currentIndex())

            selected_device = self.online_model.get_node(selected_index)
            parent_device = selected_device.parent

            selected_element = self.settings.getroot()
            parent_element = self.settings.getroot()
            for key in selected_device.my_id[:-1]:
                selected_element = selected_element[key]
                parent_element = parent_element[key]
            if selected_element.tag == 'serial_device':
                selected_element = selected_element.findall('single_device')[selected_device.my_id[-1]]
            else:
                selected_element = selected_element[selected_device.my_id[-1]]

            menu.addAction(add_action)

            paste_enabled = False
            if self.clipboard is not None:
                # if we have group to paste
                if self.clipboard[1].tag == 'group':
                    # if the destination is device - we can paste group to the parent, if it is not serial_device
                    if selected_element.tag == 'single_device':
                        if parent_element.tag != 'serial_device':
                            paste_enabled = True
                            insert_element = parent_element
                            insert_device = parent_device
                    # if the destination is group or configuration - we can paste group to the device
                    elif selected_element.tag in ['group', 'configuration']:
                        paste_enabled = True
                        insert_element = selected_element
                        insert_device = selected_device

                elif self.clipboard[0].tag == 'serial_device' or self.clipboard[1].tag == 'serial_device':
                    if selected_element.tag == 'single_device':
                        if _check_serial_device(self.clipboard[0], parent_element):
                            paste_enabled = True
                            insert_element = parent_element
                            insert_device = parent_device
                    elif selected_element.tag == 'serial_device':
                        if _check_serial_device(self.clipboard[0], selected_element):
                            paste_enabled = True
                            insert_element = selected_element
                            insert_device = selected_device

                elif selected_element.tag == 'single_device':
                    if parent_element.tag != 'serial_device':
                        paste_enabled = True
                        insert_element = parent_element
                        insert_device = parent_device

                else:
                    paste_enabled = True
                    insert_element = selected_element
                    insert_device = selected_device

            if paste_enabled:
                menu.addAction(paste_action)
            menu.addAction(copy_action)
            menu.addAction(cut_action)
            menu.addAction(del_action)
        else:
            menu.addAction(new_action)

        action = menu.exec_(self.mapToGlobal(pos))

        if action == copy_action:
            self.clipboard = [parent_element, deepcopy(selected_element)]

        elif action == cut_action:
            self.clipboard = [parent_element, deepcopy(selected_element)]
            self._delete_element(parent_element, selected_element, selected_index)

        elif action == del_action:
            self._delete_element(parent_element, selected_element, selected_index)

        elif action == paste_action:
            self._add_element(insert_element, insert_device, self.clipboard[1], selected_index)

        elif action == add_action:
            if parent_element.tag == 'serial_device' or selected_element.tag == 'serial_device':
                parent_is_serial_device = True
                dialog = ConfigureDevice(self, {'new': True, 'types': ['single_device'], 'tail': parent_element[-1].tail})
            else:
                dialog = ConfigureDevice(self, {'new': True, 'types': ['group', 'serial_device', 'single_device'],
                                                'tail': selected_element[-1].tail})
                parent_is_serial_device = False

            if dialog.exec_():
                if parent_is_serial_device:
                    if len(parent_element):
                        parent_element[-1].tail += "\t"
                    parent_element.append(dialog.new_device)
                else:
                    if len(selected_element):
                        selected_element[-1].tail += "\t"
                    selected_element.append(dialog.new_device)

        elif action == new_action:
            dialog = ConfigureDevice(self, {'new': True, 'types': ['configuration']})
            if dialog.exec_():
                self.settings.getroot().append(dialog.new_device)

        self.save_library()

    # ----------------------------------------------------------------------
    def _delete_element(self, parent_element, selected_element, selected_index):

        for ind, el in enumerate(parent_element):
            if selected_element == el:
                last_element = ind == len(parent_element) - 1

        parent_element.remove(selected_element)
        if last_element:
            parent_element[-1].tail = parent_element[-1].tail.replace('    ', '\t')[:-1]
        self.online_model.remove(selected_index)

    # ----------------------------------------------------------------------
    def _add_element(self, insert_element, insert_device, selected_element, selected_index):
        if len(insert_element):
            insert_element[-1].tail += "\t"
        insert_element.append(selected_element)
        self.online_model.start_adding(selected_index)
        self._parse_device(insert_device, selected_element, insert_device.child_count)
        self.online_model.finish_adding()

    # ----------------------------------------------------------------------
    def _get_selected_device(self):
        sub_device = None
        selected_element = None

        if self.viewed_device is not None:
            selected_index = self.device_proxy.mapToSource(self._ui.tb_device.selectionModel().currentIndex())
            selected_device = self.device_model.get_node(selected_index)

            selected_element = self.settings.getroot()
            for key in self.viewed_device.my_id:
                selected_element = selected_element[key]

            if selected_device != self.device_model.root and isinstance(self.viewed_device, SerialDeviceNode):
                sub_device = selected_device.my_id[-1]

        return selected_element, sub_device

    # ----------------------------------------------------------------------
    def edit_device_properties(self):
        device_to_edit, sub_device = self._get_selected_device()
        if ConfigureDevice(self, {'new': False, 'device': device_to_edit, 'sub_device': sub_device}).exec_():
            self.save_library()

    # ----------------------------------------------------------------------
    def new_online_selected(self, new_id):
        for device in self.configs:
            if device.my_id != new_id:
                device.deactivate()

     # ----------------------------------------------------------------------
    def save_library(self, new_file=None):

        self.applied = False
        self.refresh_tables()

        if new_file is None:
            new_file = self._working_file
        else:
            self._working_file = new_file
            self._working_path = os.path.dirname(os.path.abspath(new_file))

        self.settings.write(new_file)

    # ----------------------------------------------------------------------
    def open_new_lib(self):
        new_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open new library file', self._working_path,
                                                         'Library files (*.xml)')
        if new_file:
            self.open_lib(new_file)
            return True
        else:
            return False

    # ----------------------------------------------------------------------
    def save_lib_as(self):
        new_file, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save library as', self._working_path,
                                                            'Library files (*.xml)')
        if new_file:
            self.save_library(new_file)

    # ----------------------------------------------------------------------
    def set_super_user(self, state):
        if state:
            if not self.superuser_mode:
                password, okPressed = QtWidgets.QInputDialog.getText(self, "Type superuser password", "Superuser pass:",
                                                                 QtWidgets.QLineEdit.Normal, "")
                if okPressed:
                    self.superuser_mode = password == SUPER_USER_PASS

        else:
            self.superuser_mode = False

        self.normal_user.setChecked(not self.superuser_mode)
        self.super_user.setChecked(self.superuser_mode)

        self.refresh_tables()

    # ----------------------------------------------------------------------
    def config_error(self, text, informative_text='', detailed_text=''):
        self.msg = QtWidgets.QMessageBox()
        self.msg.setModal(False)
        self.msg.setIcon(QtWidgets.QMessageBox.Critical)
        self.msg.setText(text)
        self.msg.setInformativeText(informative_text)
        if detailed_text != '':
            self.msg.setDetailedText(detailed_text)
        self.msg.setWindowTitle("Error")
        self.msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
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

        config_ind = None
        for ind, config in enumerate(self.configs):
            if config.is_activated():
                config_ind = ind

        if config_ind is None:
            self.config_error("No configuration is selected", 'Activate one configuration')
            return

        data = []
        used_names = {}
        used_addresses = {}

        double_name = {}
        double_addresses = {}
        wrong_addresses = {}
        off_devices = {}
        wrong_attributes = {}
        rest_errors = {}

        has_error = False
        active_mgs = {}
        for device in self.devices[config_ind]:
            if device.is_exported():
                data.append(device.get_data_to_export())
                is_tango = False
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
                        has_error = True
                    elif tango_address is None:
                        rest_errors[my_name] = ['No tango address']
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
                                        wrong_attributes[my_name] = [device.get_my_path()]

                            except PyTango.DevFailed:
                                has_error = True
                                off_devices[my_name] = [device.get_my_path()]

                        except PyTango.DevFailed:
                            has_error = True
                            wrong_addresses[my_name] = [device.get_my_path()]

        for name, devices in active_mgs.items():
            devices = [device.strip().replace('timers=', '').replace('counters=', '') for device in devices.replace(' ', '').split(',')]
            for device in devices:
                if device not in used_names:
                    has_error = True
                    rest_errors[name] = ['MG: {} not in configuration']

        if has_error:
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
            self.config_error('Config has errors!', informative_text=details)
            return False, None
        else:
            if only_check:
                self.info_dialog('Configuration is OK')
            else:
                return True, data

    # ----------------------------------------------------------------------
    def apply_configuration(self):
        status, data = self.check_configuration(False)
        if status:
            root = ET.Element("hw")
            root.text = '\n'

            for element in data:
                root.append(element)

            tree = ET.ElementTree(root)
            tree.write(online_path, xml_declaration=True)

            self.applied = True

    # ----------------------------------------------------------------------
    def modify_filters(self, text):

        self.online_proxy.setFilterRegExp(text)
        self.online_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.online_proxy.setDynamicSortFilter(True)

        if text != '':
            self._ui.tw_online.expandAll()
        else:
            self._ui.tw_online.collapseAll()

    # ----------------------------------------------------------------------
    def check_device(self):
        pass

    # ----------------------------------------------------------------------
    def show_about(self):
        pass
        # AboutDialog(self).exec_()

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
        self._save_ui_settings()

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
    def _init_actions(self):
        """
        """
        open_lib = QtWidgets.QAction('Open library', self)
        # open_lib.setShortcut('Ctrl+O')
        open_lib.toggled.connect(self.open_new_lib)

        save_lib_as = QtWidgets.QAction('Save library as', self)
        # save_lib_as.setShortcut('Ctrl+S')
        save_lib_as.toggled.connect(self.save_lib_as)

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

        self.normal_user.setChecked(not self.superuser_mode)
        self.super_user.setChecked(self.superuser_mode)

        chk_group.triggered.connect(lambda button: self.set_super_user(button == self.super_user))

        about = QtWidgets.QAction('About', self)
        about.toggled.connect(self.show_about)

        self.menuBar().addAction(open_lib)
        self.menuBar().addAction(save_lib_as)
        self.menuBar().addMenu(mode_menu)
        self.menuBar().addAction(about)

        self._ui.but_edit_properties.clicked.connect(self.edit_device_properties)
        self._ui.but_check_device.clicked.connect(self.check_device)

        self._ui.but_check.clicked.connect(lambda: self.check_configuration(True))
        self._ui.but_apply.clicked.connect(self.apply_configuration)

        self._ui.le_find.textEdited.connect(self.modify_filters)

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
        if self.applied:
            lb_status_style = "QLabel {color: rgb(50, 255, 50);}"
            lb_status_text = 'APPLIED'
        else:
            lb_status_style = "QLabel {color: rgb(255, 0, 0);}"
            lb_status_text = 'NOT APPLIED'

        self._ui.lb_applied.setStyleSheet(lb_status_style)
        self._ui.lb_applied.setText(lb_status_text)

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