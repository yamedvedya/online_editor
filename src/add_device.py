# Created by matveyev at 26.01.2021

import xml.etree.cElementTree as ET

from PyQt5 import QtWidgets, QtCore

from src.gui.new_device_ui import Ui_AddDevice
from src.property_widget import PropertyWidget


class ConfigureDevice(QtWidgets.QDialog):
    delete_me = QtCore.pyqtSignal(int)

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

        self._ui.cmb_type.currentTextChanged.connect(self._change_device_type)
        self._ui.cmd_add_common_property.clicked.connect(lambda: self._add_property('common'))
        self._ui.cmd_add_personal_property.clicked.connect(lambda: self._add_property('personal'))

        if options['new']:
            self.new_device = True
            self._ui.cmb_type.addItems(options['types'])
            self.tail = options['tail']
        else:
            self.new_device = False
            self.edited_device = options['device']
            self._sub_device = options['sub_device']

            self._ui.cmb_type.setEnabled(False)

            if self.edited_device.tag == 'serial_device':
                self._ui.fr_common_properties.setVisible(True)
                for property in self.edited_device:
                    if property.tag != 'single_device':
                        self._add_property('common', property.tag, property.text, False)

                if self._sub_device is None:
                    self._ui.le_name.setText(self.edited_device.attrib['name'])
                    self._ui.le_comment.setText(self.edited_device.attrib['comment'])
                else:
                    device = self.edited_device.findall('single_device')[self._sub_device]
                    self._ui.fr_personal_properties.setVisible(True)
                    self._ui.le_name.setText(device.attrib['name'])
                    self._ui.le_comment.setText(device.attrib['comment'])

                    for property in device:
                        self._add_property('personal', property.tag, property.text, False)
            else:
                self._ui.fr_personal_properties.setVisible(True)
                self._ui.le_name.setText(self.edited_device.attrib['name'])
                self._ui.le_comment.setText(self.edited_device.attrib['comment'])
                for property in self.edited_device:
                    self._add_property('personal', property.tag, property.text, False)

            self._bild_view()

    # ----------------------------------------------------------------------
    def accept(self):
        name = self._ui.le_name.text()
        while name == '':
            name, okPressed = QtWidgets.QInputDialog.getText(self, "Get device name", "Name:",
                                                             QtWidgets.QLineEdit.Normal, "")
            if not okPressed:
                self.reject()

        if self.new_device:
            self._make_new_device(name)
        else:
            self._modify_device()

        super(ConfigureDevice, self).accept()

    # ----------------------------------------------------------------------
    def _make_new_device(self, name):
        type = self._ui.cmb_type.currentText()
        self.new_device = ET.Element(type, {'name': name, 'active': 'no', 'comment': self._ui.le_comment.text()})
        self.new_device.text = self.tail + "\t"

        if type in ['serial_device', 'single_device']:

            property_element = None
            if type == 'serial_device':
                container = self._common_property_widgets
            else:
                container = self._personal_property_widgets
            for widget in container.values():
                valid, name, value = widget.get_data()
                if valid:
                    property_element = ET.SubElement(self.new_device, name)
                    property_element.text = value
                    property_element.tail = self.tail + "\t\t"

            if property_element is not None:
                self.new_device.text += '\t'
                property_element.tail = self.tail + '\t'

        self.new_device.tail = self.tail

    # ----------------------------------------------------------------------
    def _modify_device(self):
        name = self._ui.le_name.text()
        while name == '':
            name, okPressed = QtWidgets.QInputDialog.getText(self, "Get device name", "Name:",
                                                             QtWidgets.QLineEdit.Normal, "")
            if not okPressed:
                self.reject()

        if self.edited_device.tag == 'serial_device':
            _refill_device(self.edited_device, self._common_property_widgets)
            if self._sub_device is None:
                self.edited_device.attrib['comment'] = self._ui.le_comment.text()
                self.edited_device.attrib['name'] = name
            else:
                device = self.edited_device.findall('single_device')[self._sub_device]

                device.attrib['comment'] = self._ui.le_comment.text()
                device.attrib['name'] = name
                _refill_device(device, self._personal_property_widgets)
        else:
            self.edited_device.attrib['comment'] = self._ui.le_comment.text()
            self.edited_device.attrib['name'] = name
            _refill_device(self.edited_device, self._personal_property_widgets)

        super(ConfigureDevice, self).accept()

    # ----------------------------------------------------------------------
    def _change_device_type(self, text):
        self._common_property_widgets = {}
        if text in ['group', 'configuration']:
            self._ui.fr_common_properties.setVisible(False)
            self._ui.fr_personal_properties.setVisible(False)
        elif text == 'serial_device':
            self._ui.fr_common_properties.setVisible(True)
            self._ui.fr_personal_properties.setVisible(False)
        else:
            self._ui.fr_common_properties.setVisible(False)
            self._ui.fr_personal_properties.setVisible(True)

        self._bild_view()

    # ----------------------------------------------------------------------
    def _add_property(self, type, name='', value='', doRefresh=True):

        new_property = PropertyWidget(self, self._last_ind, name, value)
        new_property.delete_me.connect(self._delete_property)
        if type == 'common':
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
    single_devices = device.findall('single_device')

    new_tail = device.text.replace('    ', '\t')
    for item in device[::-1]:
        device.remove(item)

    element = None
    for widget in widgets.values():
        valid, name, value = widget.get_data()
        if valid:
            element = ET.SubElement(device, name)
            element.text = value
            element.tail = new_tail

    if len(single_devices):
        for element in single_devices:
            device.append(element)
    else:
        if element is not None:
            element.tail = new_tail[:-1]