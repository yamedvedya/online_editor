# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'uis/new_device.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AddDevice(object):
    def setupUi(self, AddDevice):
        AddDevice.setObjectName("AddDevice")
        AddDevice.resize(603, 583)
        AddDevice.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.verticalLayout = QtWidgets.QVBoxLayout(AddDevice)
        self.verticalLayout.setObjectName("verticalLayout")
        self.fr_tango_host = QtWidgets.QFrame(AddDevice)
        self.fr_tango_host.setObjectName("fr_tango_host")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.fr_tango_host)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_6 = QtWidgets.QLabel(self.fr_tango_host)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_6.addWidget(self.label_6)
        self.le_tango_host = QtWidgets.QLineEdit(self.fr_tango_host)
        self.le_tango_host.setObjectName("le_tango_host")
        self.horizontalLayout_6.addWidget(self.le_tango_host)
        self.cmd_rescan_database = QtWidgets.QPushButton(self.fr_tango_host)
        self.cmd_rescan_database.setObjectName("cmd_rescan_database")
        self.horizontalLayout_6.addWidget(self.cmd_rescan_database)
        self.verticalLayout.addWidget(self.fr_tango_host)
        self.fr_template = QtWidgets.QFrame(AddDevice)
        self.fr_template.setObjectName("fr_template")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.fr_template)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.fr_template)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.but_template = QtWidgets.QPushButton(self.fr_template)
        self.but_template.setObjectName("but_template")
        self.horizontalLayout.addWidget(self.but_template)
        self.chk_unlock = QtWidgets.QCheckBox(self.fr_template)
        self.chk_unlock.setObjectName("chk_unlock")
        self.horizontalLayout.addWidget(self.chk_unlock)
        self.horizontalLayout.setStretch(1, 1)
        self.verticalLayout.addWidget(self.fr_template)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.le_name = QtWidgets.QLineEdit(AddDevice)
        self.le_name.setObjectName("le_name")
        self.gridLayout.addWidget(self.le_name, 0, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(AddDevice)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.le_tags = QtWidgets.QLineEdit(AddDevice)
        self.le_tags.setObjectName("le_tags")
        self.gridLayout.addWidget(self.le_tags, 1, 1, 1, 1)
        self.label_7 = QtWidgets.QLabel(AddDevice)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 1, 0, 1, 1)
        self.label_4 = QtWidgets.QLabel(AddDevice)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 2, 0, 1, 1)
        self.le_comment = QtWidgets.QLineEdit(AddDevice)
        self.le_comment.setObjectName("le_comment")
        self.gridLayout.addWidget(self.le_comment, 2, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.fr_personal_properties = QtWidgets.QFrame(AddDevice)
        self.fr_personal_properties.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.fr_personal_properties.setFrameShadow(QtWidgets.QFrame.Raised)
        self.fr_personal_properties.setObjectName("fr_personal_properties")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.fr_personal_properties)
        self.verticalLayout_2.setContentsMargins(0, -1, 0, -1)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtWidgets.QLabel(self.fr_personal_properties)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.cmd_add_personal_property = QtWidgets.QPushButton(self.fr_personal_properties)
        self.cmd_add_personal_property.setObjectName("cmd_add_personal_property")
        self.horizontalLayout_3.addWidget(self.cmd_add_personal_property)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.personal_properties = QtWidgets.QWidget(self.fr_personal_properties)
        self.personal_properties.setMinimumSize(QtCore.QSize(330, 0))
        self.personal_properties.setObjectName("personal_properties")
        self.verticalLayout_2.addWidget(self.personal_properties)
        self.verticalLayout.addWidget(self.fr_personal_properties)
        self.fr_common_properties = QtWidgets.QFrame(AddDevice)
        self.fr_common_properties.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.fr_common_properties.setFrameShadow(QtWidgets.QFrame.Raised)
        self.fr_common_properties.setObjectName("fr_common_properties")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.fr_common_properties)
        self.verticalLayout_3.setContentsMargins(0, -1, 0, -1)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_5 = QtWidgets.QLabel(self.fr_common_properties)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem1)
        self.cmd_add_common_property = QtWidgets.QPushButton(self.fr_common_properties)
        self.cmd_add_common_property.setObjectName("cmd_add_common_property")
        self.horizontalLayout_5.addWidget(self.cmd_add_common_property)
        self.verticalLayout_3.addLayout(self.horizontalLayout_5)
        self.common_properties = QtWidgets.QWidget(self.fr_common_properties)
        self.common_properties.setMinimumSize(QtCore.QSize(330, 0))
        self.common_properties.setObjectName("common_properties")
        self.verticalLayout_3.addWidget(self.common_properties)
        self.verticalLayout.addWidget(self.fr_common_properties)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)
        self.label_8 = QtWidgets.QLabel(AddDevice)
        self.label_8.setObjectName("label_8")
        self.verticalLayout.addWidget(self.label_8)
        self.but_ok_cancel = QtWidgets.QDialogButtonBox(AddDevice)
        self.but_ok_cancel.setOrientation(QtCore.Qt.Horizontal)
        self.but_ok_cancel.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.but_ok_cancel.setObjectName("but_ok_cancel")
        self.verticalLayout.addWidget(self.but_ok_cancel)

        self.retranslateUi(AddDevice)
        self.but_ok_cancel.accepted.connect(AddDevice.accept)
        self.but_ok_cancel.rejected.connect(AddDevice.reject)
        QtCore.QMetaObject.connectSlotsByName(AddDevice)

    def retranslateUi(self, AddDevice):
        _translate = QtCore.QCoreApplication.translate
        AddDevice.setWindowTitle(_translate("AddDevice", "Dialog"))
        self.label_6.setText(_translate("AddDevice", "Select Tango host:"))
        self.cmd_rescan_database.setText(_translate("AddDevice", "Rescan database"))
        self.label.setText(_translate("AddDevice", "Select template:"))
        self.but_template.setText(_translate("AddDevice", "Select template"))
        self.chk_unlock.setText(_translate("AddDevice", "Unlock fields"))
        self.label_2.setText(_translate("AddDevice", "Name:"))
        self.label_7.setText(_translate("AddDevice", "Tags:"))
        self.label_4.setText(_translate("AddDevice", "Comment:"))
        self.label_3.setText(_translate("AddDevice", "Individual entries"))
        self.cmd_add_personal_property.setText(_translate("AddDevice", "Add entry"))
        self.label_5.setText(_translate("AddDevice", "Common entries"))
        self.cmd_add_common_property.setText(_translate("AddDevice", "Add entry"))
        self.label_8.setText(_translate("AddDevice", "* fields, marked by red frame, are obligatory"))

