# Created by matveyev at 26.01.2021

import os
import xml.etree.cElementTree as ET
import PyTango
import HasyUtils as hu

from distutils.util import strtobool
from PyQt5 import QtWidgets, QtCore

from onlinexml_editor.gui.new_device_ui import Ui_AddDevice
from onlinexml_editor.property_widget import PropertyWidget
from onlinexml_editor.devices_class import SerialDeviceNode, GroupNode
from onlinexml_editor.lookandfill import EMPTY_INPUT

ALWAYS_PERSONAL = ['active', 'comment', 'name', 'tags']


class ConfigureDevice(QtWidgets.QDialog):

    # ----------------------------------------------------------------------
    def __init__(self, parent, options):
        super(ConfigureDevice, self).__init__(parent)

        self._ui = Ui_AddDevice()
        self._ui.setupUi(self)

        self._common_properties_grid = QtWidgets.QGridLayout(self._ui.common_properties)
        self._common_property_widgets = {}

        self._personal_properties_grid = QtWidgets.QGridLayout(self._ui.personal_properties)
        self._personal_property_widgets = {}

        self._last_ind = 0

        self.new_device = {}
        self._arbitrary = True
        self._possible_devices = []
        self._class = []

        self._ui.fr_common_properties.setVisible(False)
        self._ui.fr_personal_properties.setVisible(False)

        self._default_color = self._ui.le_name.styleSheet()

        self.templates = {}
        but_menu = QtWidgets.QMenu(self)
        self._parce_menu_group(ET.parse(os.path.join(os.path.dirname(__file__), 'default_templates.xml')).getroot(),
                               but_menu)
        self._ui.but_template.setMenu(but_menu)

        if options['new']:
            self.tango_host = PyTango.Database().get_db_host().split('.')[0] + ":10000"

            self._type = options['type']
            self.new_device = True

            if self._type in ['group', 'configuration']:
                self._ui.fr_template.setVisible(False)

            elif self._type == 'serial_device':
                self._ui.fr_common_properties.setVisible(True)
                self._ui.fr_personal_properties.setVisible(True)

            else:
                if type(options['parent']) == SerialDeviceNode:
                    self._ui.fr_template.setVisible(False)
                    self._ui.fr_common_properties.setVisible(True)
                    personal, common = self._parse_serial_device(options['parent'])
                    for key in personal:
                        self._add_property('personal', key, '', doRefresh=False)
                    for key, value in common.items():
                        self._add_property('common', key, value, editable=False, doRefresh=False)
                        if key == 'hostname':
                            self.tango_host = value
                    if len(options['parent'].children):
                        for key, value in options['parent'].child(0).info.items():
                            if key == 'device':
                                try:
                                    self._class = [hu.getClassNameByDevice(value, self.tango_host)]
                                except:
                                    host = self.tango_host.split(':')
                                    self._class = [PyTango.Database(host[0], host[1]).get_device_info(value).class_name]

                    self._unlock_device(False)

                self._ui.fr_personal_properties.setVisible(True)

            self._ui.le_name.setStyleSheet(EMPTY_INPUT)
        else:
            self._ui.fr_template.setVisible(False)

            self.new_device = False
            self.edited_device = options['device']
            self._sub_device = options['sub_device']

            self._ui.chk_unlock.setChecked(True)

            self.tango_host = PyTango.Database().get_db_host().split('.')[0] + ":10000"

            if type(self.edited_device) == SerialDeviceNode:
                self._type = 'serial'

                personal, common = self._parse_serial_device(self.edited_device)
                self._ui.fr_common_properties.setVisible(True)
                for key, value in common.items():
                    self._add_property('common', key, value, doRefresh=False)
                    if key == 'hostname':
                        self.tango_host = value

                device = self.edited_device.children[self._sub_device]
                self._ui.fr_personal_properties.setVisible(True)
                self._ui.le_name.setText(device.info['name'])
                self._ui.le_comment.setText(device.info['comment'])
                if 'tags' in device.info:
                    self._ui.le_tags.setText(device.info['tags'])

                for key, value in device.info.items():
                    if key not in ALWAYS_PERSONAL:
                        self._add_property('personal', key, value, doRefresh=False)
                    if key == 'hostname':
                        self.tango_host = value

            else:
                self._type = 'device'
                self._ui.fr_personal_properties.setVisible(True)
                self._ui.le_name.setText(self.edited_device.info['name'])
                if 'tags' in self.edited_device.info:
                    self._ui.le_tags.setText(self.edited_device.info['tags'])
                self._ui.le_comment.setText(self.edited_device.info['comment'])
                for key, value in self.edited_device.info.items():
                    if key not in ALWAYS_PERSONAL:
                        self._add_property('personal', key, value, doRefresh=False)
                    if key == 'hostname':
                        self.tango_host = value

        self._ui.le_tango_host.setText(self.tango_host)
        self._rescan_database()

        self._ui.chk_unlock.clicked.connect(self._unlock_device)

        self._ui.cmd_rescan_database.clicked.connect(self._rescan_database)

        self._ui.cmd_add_common_property.clicked.connect(lambda: self._add_property('common'))
        self._ui.cmd_add_personal_property.clicked.connect(lambda: self._add_property('personal'))

        self._ui.le_name.textEdited.connect(self._colorize_ui)

        self._bild_view()

    # ----------------------------------------------------------------------
    def _parce_action(self, element, menu):
        action = QtWidgets.QAction(element.get('name'), self)
        action.triggered.connect(lambda state, name=element.get('name'): self._apply_template(name))
        menu.addAction(action)
        self.templates[element.get('name')] = element

    # ----------------------------------------------------------------------
    def _parce_menu_group(self, element, menu):
        for child in list(element):
            if child.tag == 'group':
                new_menu = QtWidgets.QMenu(child.get('name'), self)
                menu.addMenu(new_menu)
                self._parce_menu_group(child, new_menu)
            elif child.tag == 'action':
                self._parce_action(child, menu)

    @staticmethod
    # ----------------------------------------------------------------------
    def _parse_serial_device(device):

        common = dict(device.info)
        for key in ALWAYS_PERSONAL:
            if key in common:
                del common[key]

        all_keys = []
        for child in device.children:
            all_keys += list(child.info.keys())

        all_keys = list(set(all_keys))
        for key in ALWAYS_PERSONAL:
            if key in all_keys:
                all_keys.remove(key)

        return all_keys, common

    # ----------------------------------------------------------------------
    def _unlock_device(self, state):
        self._ui.cmd_add_common_property.setVisible(state)
        self._ui.cmd_add_personal_property.setVisible(state)

        for widget in list(self._common_property_widgets.values()) + list(self._personal_property_widgets.values()):
            widget.unlock(state)

    # ----------------------------------------------------------------------
    def _colorize_ui(self):
        if self._ui.le_name.text() == "":
            self._ui.le_name.setStyleSheet(EMPTY_INPUT)
        else:
            self._ui.le_name.setStyleSheet(self._default_color)

    # ----------------------------------------------------------------------
    def accept(self):
        name = self._ui.le_name.text()
        while name == '':
            name, ok_pressed = QtWidgets.QInputDialog.getText(self, "Get device name", "Name:",
                                                             QtWidgets.QLineEdit.Normal, "")
            if not ok_pressed:
                self.reject()
                return

        if self.new_device:
            self._make_new_device(name)
        else:
            self._modify_device()

        super(ConfigureDevice, self).accept()

    @staticmethod
    # ----------------------------------------------------------------------
    def _fill_with_sub_elements(device, container):
        for widget in container.values():
            valid, name, value = widget.get_data()
            if valid:
                property_element = ET.SubElement(device, name)
                property_element.text = value

    # ----------------------------------------------------------------------
    def _make_new_device(self, name):
        self.new_device = ET.Element(self._type, {'name': name, 'active': 'yes', 'comment': self._ui.le_comment.text()})

        if self._type in ['serial_device', 'single_device']:

            if self._type == 'serial_device':
                self._fill_with_sub_elements(self.new_device, self._common_property_widgets)
                device = ET.SubElement(self.new_device, 'single_device', attrib={'name': self._ui.le_name.text(),
                                                                                 'active': 'yes',
                                                                                 'comment': self._ui.le_comment.text()})

                self._fill_with_sub_elements(device, self._personal_property_widgets)

            else:
                self._fill_with_sub_elements(self.new_device, self._personal_property_widgets)

    # ----------------------------------------------------------------------
    def _modify_device(self):
        def fill_info(device_info):
            device_info['comment'] = self._ui.le_comment.text()
            device_info['name'] = name
            if self._ui.le_tags.text() != '':
                device_info['tags'] = self._ui.le_tags.text()
            else:
                if 'tags' in device_info:
                    del device_info['tags']

        name = self._ui.le_name.text()
        while name == '':
            name, okPressed = QtWidgets.QInputDialog.getText(self, "Get device name", "Name:",
                                                             QtWidgets.QLineEdit.Normal, "")
            if not okPressed:
                self.reject()

        if type(self.edited_device) == SerialDeviceNode or type(self.edited_device) == GroupNode:
            if type(self.edited_device) == SerialDeviceNode:
                _refill_device(self.edited_device, self._common_property_widgets)

            if self._sub_device is None:
                fill_info(self.edited_device.info)

            else:
                device = self.edited_device.children[self._sub_device]
                _refill_device(device, self._personal_property_widgets)
                fill_info(device.info)

        else:
            _refill_device(self.edited_device, self._personal_property_widgets)
            fill_info(self.edited_device.info)

        super(ConfigureDevice, self).accept()

    # ----------------------------------------------------------------------
    def _apply_template(self, template_name):
        self._common_property_widgets = {}
        self._personal_property_widgets = {}

        self._ui.chk_unlock.setChecked(False)

        self._arbitrary = False if self.templates[template_name].get('arbitrary') is None else \
            strtobool(self.templates[template_name].get('arbitrary'))
        self._class = [] if self.templates[template_name].get('class') is None else \
            self.templates[template_name].get('class').split(';')
        self._rescan_database()

        for child in list(self.templates[template_name]):
            for key, value in child.attrib.items():
                if key not in ALWAYS_PERSONAL:
                    self._add_property(child.tag if self._type != 'single_device' else 'personal',
                                       key, value, self._arbitrary, False)

        self._ui.cmd_add_common_property.setVisible(template_name == 'Arbitrary device')
        self._ui.cmd_add_personal_property.setVisible(template_name == 'Arbitrary device')

        self._bild_view()

    # ----------------------------------------------------------------------
    def _rescan_database(self):
        self.tango_host = self._ui.le_tango_host.text()

        self._possible_devices = []
        for c_name in self._class:
            self._possible_devices += hu.getDeviceNamesByClass(c_name, self.tango_host)

        for widget in list(self._common_property_widgets.values()) + list(self._personal_property_widgets.values()):
            widget.update_gui()

    # ----------------------------------------------------------------------
    def get_devices_list(self):
        return self._possible_devices

    # ----------------------------------------------------------------------
    def _add_property(self, property_type, name='', value='', editable=True, doRefresh=True):

        new_property = PropertyWidget(self, self._last_ind, name, value, editable)
        new_property.delete_me.connect(self._delete_property)
        if property_type == 'common':
            self._common_property_widgets[self._last_ind] = new_property
        else:
            self._personal_property_widgets[self._last_ind] = new_property

        self._last_ind += 1

        if doRefresh:
            self._bild_view()

    # ----------------------------------------------------------------------
    def _delete_property(self, ind):

        if ind in self._common_property_widgets:
            del self._common_property_widgets[ind]
        else:
            del self._personal_property_widgets[ind]

        self._bild_view()

    # ----------------------------------------------------------------------
    def _bild_view(self):

        for container, widgets in zip([self._ui.common_properties, self._ui.personal_properties],
                                      [self._common_property_widgets, self._personal_property_widgets]):
            layout = container.layout()
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                if item:
                    w = layout.itemAt(i).widget()
                    if w:
                        layout.removeWidget(w)
                        w.setVisible(False)

            QtWidgets.QWidget().setLayout(container.layout())
            layout = QtWidgets.QVBoxLayout(container)

            for widget in widgets.values():
                widget.setVisible(True)
                layout.addWidget(widget, alignment=QtCore.Qt.AlignTop)
            layout.addStretch()


# ----------------------------------------------------------------------
def _refill_device(device, widgets):
    keys = list(device.info.keys())
    for key in ['name', 'comment', 'active']:
        keys.remove(key)
    for key in keys:
        del device.info[key]

    for widget in widgets.values():
        valid, name, value = widget.get_data()
        if valid:
            device.info[name] = value