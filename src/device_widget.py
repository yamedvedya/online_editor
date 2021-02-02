# Created by matveyev at 21.01.2021

from datetime import datetime
import os

from PyQt5 import QtWidgets

from src.gui.device_widget_ui import Ui_DeviceWidget

# ----------------------------------------------------------------------
class DeviceWidget(QtWidgets.QDialog):
    """
    """
    SOURCE_DIR = "src"
    DATETIME = "%Y-%m-%d %H:%M:%S"

    # ----------------------------------------------------------------------
    def __init__(self, parent):
        super(DeviceWidget, self).__init__(parent)

        self._ui = Ui_DeviceWidget()
        self._ui.setupUi(self)

