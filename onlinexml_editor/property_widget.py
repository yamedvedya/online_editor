# Created by matveyev at 26.01.2021

from PyQt5 import QtWidgets, QtCore
from onlinexml_editor.gui.property_ui import Ui_Property
from onlinexml_editor.lookandfill import EMPTY_INPUT

ALWAYS_EDITABLE = ['device']


# ----------------------------------------------------------------------
class PropertyWidget(QtWidgets.QWidget):
    delete_me = QtCore.pyqtSignal(int)

    # ----------------------------------------------------------------------
    def __init__(self, parent, id, name='', value='', editable=True):
        super(PropertyWidget, self).__init__(parent)
        self._id = id

        self._ui = Ui_Property()
        self._ui.setupUi(self)

        self._selectable_device = False

        self._default_color = self._ui.le_name.styleSheet()

        self._editable = editable

        self._name = name
        self._ui.le_name.setText(name)

        self._value = value
        self._ui.le_value.setText(value)

        self.unlock(editable)

        self._parent = parent

        if value == '':
            self._ui.le_value.setStyleSheet(EMPTY_INPUT)

        self.update_gui()

        self._ui.le_name.textEdited.connect(lambda: self._colorize('le_name'))
        self._ui.le_value.textEdited.connect(lambda: self._colorize('le_value'))

        self._ui.cmd_delete.clicked.connect(lambda checked, x=self._id: self.delete_me.emit(x))

    # ----------------------------------------------------------------------
    def update_gui(self):
        if self._value == '___local___':
            self._ui.le_value.setText(self._parent.tango_host)

        self._selectable_device = False
        if self._name == 'device':
            possible_devices = self._parent.get_devices_list()
            if len(possible_devices):
                self._selectable_device = True
                self._ui.cmb_value.clear()
                self._ui.cmb_value.addItems(possible_devices)
                refresh_combo_box(self._ui.cmb_value, self._value)

        self._ui.cmb_value.setVisible(self._selectable_device)
        self._ui.le_value.setVisible(not self._selectable_device)

    # ----------------------------------------------------------------------
    def unlock(self, state):
        new_state = True if state else self._editable
        self._ui.le_name.setEnabled(new_state)

        self._ui.le_value.setEnabled(new_state if self._name not in ALWAYS_EDITABLE else True)
        self._ui.cmb_value.setEnabled(new_state if self._name not in ALWAYS_EDITABLE else True)

        self._ui.cmd_delete.setVisible(new_state)

    # ----------------------------------------------------------------------
    def _colorize(self, ui):
        if getattr(self._ui, ui).text() == "":
            getattr(self._ui, ui).setStyleSheet(EMPTY_INPUT)
        else:
            getattr(self._ui, ui).setStyleSheet(self._default_color)

    # ----------------------------------------------------------------------
    def get_data(self):
        name = self._ui.le_name.text()
        if name == '':
            return False, None, None

        value = self._ui.cmb_value.currentText() if self._selectable_device else self._ui.le_value.text()
        while value == '':
            value, ok_pressed = QtWidgets.QInputDialog.getText(self, f"Get {self._ui.le_name.text()} value",
                                                               f"{self._ui.le_name.text()}:",
                                                               QtWidgets.QLineEdit.Normal, "")
            if not ok_pressed:
                if name in ALWAYS_EDITABLE:
                    raise RuntimeError('Obligatory property not entered')
                return False, None, None

        return True, name, value


# ----------------------------------------------------------------------
def refresh_combo_box(combo, text):
    idx = combo.findText(text)
    if idx != -1:
        combo.setCurrentIndex(idx)
        return True
    else:
        combo.setCurrentIndex(0)
        return False