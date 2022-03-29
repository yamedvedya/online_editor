from PyQt5 import QtWidgets

from onlinexml_editor.gui.config_error_ui import Ui_Dialog


class ConfigError(QtWidgets.QDialog):

    def __init__(self, text, detailed_text, applying):
        super(ConfigError, self).__init__()

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)

        self._ui.label.setStyleSheet("QLabel {color: rgb(255, 0, 0);}")
        self._ui.label.setText(text)

        if detailed_text != '':
            self._ui.plain_text.setPlainText(detailed_text)
        else:
            self._ui.plain_text.setVisible(False)

        if applying:
            self._ui.but_box.removeButton(self._ui.but_box.buttons()[0])
        else:
            self._ui.but_box.removeButton(self._ui.but_box.buttons()[-1])
            self._ui.but_box.removeButton(self._ui.but_box.buttons()[-1])

