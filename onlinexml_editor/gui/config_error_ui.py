# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'uis/config_error.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(707, 469)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(17)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setTextFormat(QtCore.Qt.RichText)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.plain_text = QtWidgets.QPlainTextEdit(Dialog)
        self.plain_text.setObjectName("plain_text")
        self.verticalLayout.addWidget(self.plain_text)
        self.but_box = QtWidgets.QDialogButtonBox(Dialog)
        self.but_box.setOrientation(QtCore.Qt.Horizontal)
        self.but_box.setStandardButtons(QtWidgets.QDialogButtonBox.Abort|QtWidgets.QDialogButtonBox.Ignore|QtWidgets.QDialogButtonBox.Ok)
        self.but_box.setObjectName("but_box")
        self.verticalLayout.addWidget(self.but_box)

        self.retranslateUi(Dialog)
        self.but_box.accepted.connect(Dialog.accept)
        self.but_box.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Error!"))
        self.label.setText(_translate("Dialog", "No configuration is selected"))

