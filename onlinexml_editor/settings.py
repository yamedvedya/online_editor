# Created by matveyev at 07.04.2021

import os

from PyQt5 import QtWidgets, QtCore

from onlinexml_editor.gui.settings_ui import Ui_AppSettings
from onlinexml_editor.password import PasswordSetup
from onlinexml_editor.general_settings import APP_NAME, DEFAULT_SUPERUSER_PASS

SYSTEM_DEFAULT_ONLINE_XML = '/usr/local/experiment/online_dir/online.xml'
SYSTEM_DEFAULT_ARCHIVE = '/usr/local/experiment/online_dir/archive/'
SYSTEM_DEFAULT_LIBRARY = os.path.expanduser('~/.onlinexml_editor/')

# ----------------------------------------------------------------------
class AppSettings(QtWidgets.QDialog):
    """
    """

    # ----------------------------------------------------------------------
    def __init__(self, parent):
        super(AppSettings, self).__init__(parent)

        self._ui = Ui_AppSettings()
        self._ui.setupUi(self)

        settings = QtCore.QSettings(APP_NAME)

        self.archive_path = ''
        self.online_path = ''
        self.library_path = ''

        self.auto_save = False
        self.auto_archive = True

        try:
            self.restoreGeometry(settings.value("Settings/geometry"))
        except:
            pass

        path = settings.value('OnlinePath')
        if path is not None:
            self._ui.le_online_path.setText(str(path))
        else:
            if os.path.exists(SYSTEM_DEFAULT_ONLINE_XML):
                self._ui.le_online_path.setText(SYSTEM_DEFAULT_ONLINE_XML)

        path = settings.value('ArchivePath')
        if path is not None:
            self._ui.le_archive_path.setText(str(path))
        else:
            if os.path.exists(SYSTEM_DEFAULT_ARCHIVE):
                self._ui.le_archive_path.setText(SYSTEM_DEFAULT_ARCHIVE)
            elif os.path.exists(SYSTEM_DEFAULT_ONLINE_XML):
                path = os.path.join(os.path.dirname(SYSTEM_DEFAULT_ONLINE_XML), 'archive')
                if os.path.exists(path):
                    self._ui.le_archive_path.setText(path)

        path = settings.value('LibraryPath')
        if path is not None:
            self._ui.le_library_path.setText(str(path))
        else:
            if os.path.exists(SYSTEM_DEFAULT_LIBRARY):
                self._ui.le_library_path.setText(SYSTEM_DEFAULT_LIBRARY)

        autosave = settings.value('AutoSave')
        if autosave is not None:
            self._ui.chk_auto_save.setChecked(bool(autosave))
        else:
            self._ui.chk_auto_save.setChecked(True)

        autoarchive = settings.value('AutoArchive')
        if autoarchive is not None:
            self._ui.chk_auto_archive.setChecked(bool(autoarchive))
        else:
            self._ui.chk_auto_archive.setChecked(True)

        try:
            if bool(settings.value("DefaultSuperuser")):
                self._ui.rb_superuser.setChecked(True)
            else:
                self._ui.rb_regular_user.setChecked(True)
        except:
            pass

        self._ui.bg_user_role.buttonClicked.connect(self._change_role)

        for ui in ['archive_path', 'online_path', 'library_path']:
            getattr(self._ui, f'cmd_{ui}').clicked.connect(lambda state, source=ui: self._change_path(source))

        self._ui.cmd_superuser_pass.clicked.connect(self._set_pass)

    # ----------------------------------------------------------------------
    def _block_signals(self, flag):
        self._ui.rb_superuser.blockSignals(flag)
        self._ui.rb_regular_user.blockSignals(flag)

        for ui in ['archive_path', 'online_path', 'library_path']:
            getattr(self._ui, f'le_{ui}').blockSignals(flag)
            getattr(self._ui, f'cmd_{ui}').blockSignals(flag)

        self._ui.chk_auto_save.blockSignals(flag)
        self._ui.chk_auto_archive.blockSignals(flag)

    # ----------------------------------------------------------------------
    def _set_pass(self):
        PasswordSetup(self).exec_()

    # ----------------------------------------------------------------------
    def _change_role(self, button):
        superuser_pass = QtCore.QSettings(APP_NAME).value('SuperuserPassword')
        if superuser_pass is None:
            superuser_pass = DEFAULT_SUPERUSER_PASS
        else:
            superuser_pass = str(superuser_pass)

        self._block_signals(True)
        if button == self._ui.rb_superuser:
            text, okPressed = QtWidgets.QInputDialog.getText(self, "Password", "Superuser password:",
                                                             QtWidgets.QLineEdit.Password, "")
            if okPressed and text != '':
                if text != superuser_pass:
                    self._ui.rb_regular_user.setChecked(True)
                else:
                    self._ui.rb_superuser.setChecked(True)

        self._block_signals(False)

    # ----------------------------------------------------------------------
    def _change_path(self, source):
        if source == 'online_path':
            default_path = self._ui.le_online_path.text()
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Online.xml file', default_path if default_path != ''
                                                                                     else os.getcwd(),
                                                            'online.xml (online.xml)')
        else:
            default_path = getattr(self._ui, f'le_{source}').text()
            path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Archive folder' if source == 'archive_path'
                                                                    else 'Library folder',
                                                              default_path if default_path != '' else os.getcwd())

        if path:
            getattr(self._ui, f'le_{source}').setText(path)

    # ----------------------------------------------------------------------
    def accept(self):
        all_ok = True
        error_text = ''

        for ui in ['archive_path', 'online_path', 'library_path']:
            setattr(self, ui, str(getattr(self._ui, f'le_{ui}').text()))
            if not os.path.exists(getattr(self, ui)):
                all_ok *= False
                error_text += f'The {ui} path does not exist\n'

        if not all_ok:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Cannot save settings due to following errors:")
            msg.setInformativeText(error_text)
            msg.setWindowTitle("Error")
            msg.exec_()
            return

        settings = QtCore.QSettings(APP_NAME)
        settings.setValue('OnlinePath', str(self.online_path))
        settings.setValue('ArchivePath', str(self.archive_path))
        settings.setValue('LibraryPath', str(self.library_path))

        self.auto_save = self._ui.chk_auto_save.isChecked()
        settings.setValue('AutoSave', int(self.auto_save))

        self.auto_archive = self._ui.chk_auto_archive.isChecked()
        settings.setValue('AutoArchive', int(self.auto_archive))

        if self._ui.rb_superuser.isChecked():
            settings.setValue('DefaultSuperuser', True)
        else:
            settings.setValue('DefaultSuperuser', False)

        QtCore.QSettings(APP_NAME).setValue("Settings/geometry", self.saveGeometry())
        super(AppSettings, self).accept()

    # ----------------------------------------------------------------------
    def reject(self):
        QtCore.QSettings(APP_NAME).setValue("Settings/geometry", self.saveGeometry())
        super(AppSettings, self).reject()

