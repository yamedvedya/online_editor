# Created by matveyev at 26.01.2021

from PyQt5 import QtWidgets, QtCore
from onlinexml_editor.gui.property_ui import Ui_Property


# ----------------------------------------------------------------------
class PropertyWidget(QtWidgets.QWidget):
    delete_me = QtCore.pyqtSignal(int)

    # ----------------------------------------------------------------------
    def __init__(self, parent, id, name='', value='', editable=True):
        super(PropertyWidget, self).__init__(parent)
        self._id = id

        self._ui = Ui_Property()
        self._ui.setupUi(self)

        self._default_color = self._ui.le_name.styleSheet()

        self._ui.le_name.setText(name)
        self._ui.le_name.setEnabled(editable)

        self._ui.le_value.setText(value)
        self._ui.le_value.setEnabled(editable)
        if value == '':
            self._ui.le_value.setStyleSheet("QLineEdit {background: rgb(255, 102, 74);}")

        self._ui.le_name.textEdited.connect(lambda: self._colorize('le_name'))
        self._ui.le_value.textEdited.connect(lambda: self._colorize('le_value'))

        self._ui.cmd_delete.clicked.connect(lambda checked, x=self._id: self.delete_me.emit(x))

    # ----------------------------------------------------------------------
    def _colorize(self, ui):
        if getattr(self._ui, ui).text() == "":
            getattr(self._ui, ui).setStyleSheet("QLineEdit {background: rgb(255, 102, 74);}")
        else:
            getattr(self._ui, ui).setStyleSheet(self._default_color)

    # ----------------------------------------------------------------------
    def get_data(self):
        if self._ui.le_name.text() != '' and self._ui.le_value.text() != '':
            return True, self._ui.le_name.text(), self._ui.le_value.text()
        else:
            return False, None, None