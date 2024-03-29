# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'uis/settings.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AppSettings(object):
    def setupUi(self, AppSettings):
        AppSettings.setObjectName("AppSettings")
        AppSettings.resize(660, 403)
        AppSettings.setMinimumSize(QtCore.QSize(650, 0))
        AppSettings.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.verticalLayout = QtWidgets.QVBoxLayout(AppSettings)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox_3 = QtWidgets.QGroupBox(AppSettings)
        self.groupBox_3.setObjectName("groupBox_3")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.groupBox_3)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.chk_auto_archive = QtWidgets.QCheckBox(self.groupBox_3)
        self.chk_auto_archive.setObjectName("chk_auto_archive")
        self.gridLayout_3.addWidget(self.chk_auto_archive, 0, 1, 1, 1)
        self.chk_auto_save = QtWidgets.QCheckBox(self.groupBox_3)
        self.chk_auto_save.setEnabled(True)
        self.chk_auto_save.setObjectName("chk_auto_save")
        self.gridLayout_3.addWidget(self.chk_auto_save, 0, 2, 1, 1)
        self.verticalLayout.addWidget(self.groupBox_3)
        self.groupBox = QtWidgets.QGroupBox(AppSettings)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.le_online_path = QtWidgets.QLineEdit(self.groupBox)
        self.le_online_path.setObjectName("le_online_path")
        self.gridLayout.addWidget(self.le_online_path, 0, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 1, 0, 1, 1)
        self.cmd_library_path = QtWidgets.QPushButton(self.groupBox)
        self.cmd_library_path.setObjectName("cmd_library_path")
        self.gridLayout.addWidget(self.cmd_library_path, 1, 2, 1, 1)
        self.le_library_path = QtWidgets.QLineEdit(self.groupBox)
        self.le_library_path.setObjectName("le_library_path")
        self.gridLayout.addWidget(self.le_library_path, 1, 1, 1, 1)
        self.cmd_online_path = QtWidgets.QPushButton(self.groupBox)
        self.cmd_online_path.setObjectName("cmd_online_path")
        self.gridLayout.addWidget(self.cmd_online_path, 0, 2, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(AppSettings)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        spacerItem = QtWidgets.QSpacerItem(91, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 1, 2, 1, 1)
        self.rb_superuser = QtWidgets.QRadioButton(self.groupBox_2)
        self.rb_superuser.setObjectName("rb_superuser")
        self.bg_user_role = QtWidgets.QButtonGroup(AppSettings)
        self.bg_user_role.setObjectName("bg_user_role")
        self.bg_user_role.addButton(self.rb_superuser)
        self.gridLayout_2.addWidget(self.rb_superuser, 1, 1, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.groupBox_2)
        self.label_4.setObjectName("label_4")
        self.gridLayout_2.addWidget(self.label_4, 0, 0, 2, 1)
        self.rb_regular_user = QtWidgets.QRadioButton(self.groupBox_2)
        self.rb_regular_user.setChecked(True)
        self.rb_regular_user.setObjectName("rb_regular_user")
        self.bg_user_role.addButton(self.rb_regular_user)
        self.gridLayout_2.addWidget(self.rb_regular_user, 0, 1, 1, 1)
        self.cmd_superuser_pass = QtWidgets.QPushButton(self.groupBox_2)
        self.cmd_superuser_pass.setObjectName("cmd_superuser_pass")
        self.gridLayout_2.addWidget(self.cmd_superuser_pass, 2, 0, 1, 3)
        self.verticalLayout.addWidget(self.groupBox_2)
        spacerItem1 = QtWidgets.QSpacerItem(20, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.buttonBox = QtWidgets.QDialogButtonBox(AppSettings)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(AppSettings)
        self.buttonBox.accepted.connect(AppSettings.accept)
        self.buttonBox.rejected.connect(AppSettings.reject)
        QtCore.QMetaObject.connectSlotsByName(AppSettings)

    def retranslateUi(self, AppSettings):
        _translate = QtCore.QCoreApplication.translate
        AppSettings.setWindowTitle(_translate("AppSettings", "Settings"))
        self.groupBox_3.setTitle(_translate("AppSettings", "Save and archiv behaviour"))
        self.chk_auto_archive.setText(_translate("AppSettings", "Automatic archive every apply"))
        self.chk_auto_save.setText(_translate("AppSettings", "Automatic save on exit"))
        self.groupBox.setTitle(_translate("AppSettings", "Paths"))
        self.label_2.setText(_translate("AppSettings", "Online.xml path"))
        self.label_5.setText(_translate("AppSettings", "Library path"))
        self.cmd_library_path.setText(_translate("AppSettings", "Set folder"))
        self.cmd_online_path.setText(_translate("AppSettings", "Set folder"))
        self.groupBox_2.setTitle(_translate("AppSettings", "Superuser"))
        self.rb_superuser.setText(_translate("AppSettings", "Superuser"))
        self.label_4.setText(_translate("AppSettings", "Startup user role"))
        self.rb_regular_user.setText(_translate("AppSettings", "Regular user"))
        self.cmd_superuser_pass.setText(_translate("AppSettings", "Change superuser password"))

