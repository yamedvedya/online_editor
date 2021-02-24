# Created by matveyev at 26.01.2021

from PyQt5 import QtWidgets, QtCore
from src.gui.property_ui import Ui_Property

# ----------------------------------------------------------------------
class PropertyWidget(QtWidgets.QWidget):
    delete_me = QtCore.pyqtSignal(int)

    # ----------------------------------------------------------------------
    def __init__(self, parent, id, name='', value='', name_editable=True):
        super(PropertyWidget, self).__init__(parent)
        self._id = id

        self._ui = Ui_Property()
        self._ui.setupUi(self)
        self._ui.le_name.setText(name)
        self._ui.le_name.setEnabled(name_editable)
        self._ui.le_value.setText(value)

        self._ui.cmd_delete.clicked.connect(lambda checked, x=self._id: self.delete_me.emit(x))

    # ----------------------------------------------------------------------
    def get_data(self):
        if self._ui.le_name.text() != '' and self._ui.le_value.text() != '':
            return True, self._ui.le_name.text(), self._ui.le_value.text()
        else:
            return False, None, None