# Created by matveyev at 26.01.2021

import os
import xml.etree.cElementTree as ET
import PyTango

from PyQt5 import QtWidgets, QtCore

from onlinexml_editor.gui.new_device_ui import Ui_AddDevice
from onlinexml_editor.property_widget import PropertyWidget
from onlinexml_editor.devices_class import SerialDeviceNode, GroupNode

ALWAYS_PERSONAL = ['active', 'comment', 'name']


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

        self._ui.fr_common_properties.setVisible(False)
        self._ui.fr_personal_properties.setVisible(False)

        self._ui.cmd_apply_template.clicked.connect(self._apply_template)
        self._ui.cmb_template.currentIndexChanged.connect(self._apply_template)

        self._ui.cmd_add_common_property.clicked.connect(lambda: self._add_property('common'))
        self._ui.cmd_add_personal_property.clicked.connect(lambda: self._add_property('personal'))

        self._default_color = self._ui.le_name.styleSheet()
        self._ui.le_name.textEdited.connect(self._colorize_ui)

        self.templates = ET.parse(os.path.join(os.path.dirname(__file__), 'default_templates.xml')).getroot()

        for device in self.templates.iter('device'):
            if device.get('name') is not None:
                self._ui.cmb_template.addItem(device.get('name'))

        if options['new']:
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

                self._ui.fr_personal_properties.setVisible(True)

            self._ui.le_name.setStyleSheet("QLineEdit {background: rgb(255, 102, 74);}")
        else:
            self._ui.fr_template.setVisible(False)

            self.new_device = False
            self.edited_device = options['device']
            self._sub_device = options['sub_device']

            if type(self.edited_device) == SerialDeviceNode:
                self._type = 'serial'

                personal, common = self._parse_serial_device(self.edited_device)
                self._ui.fr_common_properties.setVisible(True)
                for key, value in common.items():
                    self._add_property('common', key, value, doRefresh=False)

                device = self.edited_device.children[self._sub_device]
                self._ui.fr_personal_properties.setVisible(True)
                self._ui.le_name.setText(device.info['name'])
                self._ui.le_comment.setText(device.info['comment'])

                for key, value in device.info.items():
                    if key not in ALWAYS_PERSONAL:
                        self._add_property('personal', key, value, doRefresh=False)

            else:
                self._type = 'device'
                self._ui.fr_personal_properties.setVisible(True)
                self._ui.le_name.setText(self.edited_device.info['name'])
                self._ui.le_comment.setText(self.edited_device.info['comment'])
                for key, value in self.edited_device.info.items():
                    if key not in ALWAYS_PERSONAL:
                        self._add_property('personal', key, value, doRefresh=False)

        self._bild_view()

    # ----------------------------------------------------------------------
    def _parse_serial_device(self, device):

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
    def _colorize_ui(self):
        if self._ui.le_name.text() == "":
            self._ui.le_name.setStyleSheet("QLineEdit {background: rgb(255, 102, 74);}")
        else:
            self._ui.le_name.setStyleSheet(self._default_color)

    # ----------------------------------------------------------------------
    def accept(self):
        name = self._ui.le_name.text()
        while name == '':
            name, okPressed = QtWidgets.QInputDialog.getText(self, "Get device name", "Name:",
                                                             QtWidgets.QLineEdit.Normal, "")
            if not okPressed:
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
        self.new_device = ET.Element(self._type, {'name': name, 'active': 'no', 'comment': self._ui.le_comment.text()})

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
        name = self._ui.le_name.text()
        while name == '':
            name, okPressed = QtWidgets.QInputDialog.getText(self, "Get device name", "Name:",
                                                             QtWidgets.QLineEdit.Normal, "")
            if not okPressed:
                self.reject()

        if isinstance(self.edited_device, SerialDeviceNode) or isinstance(self.edited_device, GroupNode):
            if isinstance(self.edited_device, SerialDeviceNode):
                _refill_device(self.edited_device, self._common_property_widgets)

            if self._sub_device is None:
                self.edited_device.info['comment'] = self._ui.le_comment.text()
                self.edited_device.info['name'] = name
            else:
                device = self.edited_device.children[self._sub_device]
                _refill_device(device, self._personal_property_widgets)
                device.info['comment'] = self._ui.le_comment.text()
                device.info['name'] = name

        else:
            _refill_device(self.edited_device, self._personal_property_widgets)
            self.edited_device.info['comment'] = self._ui.le_comment.text()
            self.edited_device.info['name'] = name

        super(ConfigureDevice, self).accept()

    # ----------------------------------------------------------------------
    def _apply_template(self):
        self._common_property_widgets = {}
        self._personal_property_widgets = {}

        template = self._ui.cmb_template.currentText()
        for device in self.templates.iter('device'):
            if device.get('name') == template:
                for child in list(device):
                    for key, value in child.attrib.items():
                        if value == '___local___':
                            value = PyTango.Database().get_db_host().split('.')[0] + ":10000"
                        if self._type == 'single_device':
                            self._add_property('personal', key, value)
                        else:
                            self._add_property(child.tag, key, value)

        self._bild_view()

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