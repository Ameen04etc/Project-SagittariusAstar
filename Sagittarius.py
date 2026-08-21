# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Sagittarius_A.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QHeaderView,
    QLineEdit, QMainWindow, QPlainTextEdit, QSizePolicy,
    QSplitter, QTabWidget, QTreeView, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(581, 394)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(1, 2, 2, 2)
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        font = QFont()
        font.setWeight(QFont.Thin)
        font.setItalic(False)
        font.setKerning(False)
        self.tabWidget.setFont(font)
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.West)
        self.tabWidget.setTabShape(QTabWidget.TabShape.Rounded)
        self.tabWidget.setElideMode(Qt.TextElideMode.ElideNone)
        self.tabWidget.setMovable(False)
        self.Plottables = QWidget()
        self.Plottables.setObjectName(u"Plottables")
        self.tabWidget.addTab(self.Plottables, "")
        self.Executables = QWidget()
        self.Executables.setObjectName(u"Executables")
        self.verticalLayout = QVBoxLayout(self.Executables)
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.Splitter = QSplitter(self.Executables)
        self.Splitter.setObjectName(u"Splitter")
        self.Splitter.setOrientation(Qt.Orientation.Vertical)
        self.Splitter.setOpaqueResize(True)
        self.Splitter.setHandleWidth(2)
        self.Splitter.setChildrenCollapsible(False)
        self.FileSystem = QTreeView(self.Splitter)
        self.FileSystem.setObjectName(u"FileSystem")
        self.FileSystem.setFrameShape(QFrame.Shape.NoFrame)
        self.FileSystem.setFrameShadow(QFrame.Shadow.Plain)
        self.Splitter.addWidget(self.FileSystem)
        self.Terminal = QPlainTextEdit(self.Splitter)
        self.Terminal.setObjectName(u"Terminal")
        self.Terminal.setFrameShape(QFrame.Shape.NoFrame)
        self.Terminal.setFrameShadow(QFrame.Shadow.Plain)
        self.Splitter.addWidget(self.Terminal)
        self.lineEdit = QLineEdit(self.Splitter)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setFrame(False)
        self.lineEdit.setClearButtonEnabled(True)
        self.Splitter.addWidget(self.lineEdit)

        self.verticalLayout.addWidget(self.Splitter)

        self.tabWidget.addTab(self.Executables, "")
        self.Runs = QWidget()
        self.Runs.setObjectName(u"Runs")
        self.tabWidget.addTab(self.Runs, "")
        self.Calculator = QWidget()
        self.Calculator.setObjectName(u"Calculator")
        font1 = QFont()
        font1.setBold(False)
        font1.setItalic(False)
        font1.setKerning(False)
        self.Calculator.setFont(font1)
        self.tabWidget.addTab(self.Calculator, "")

        self.horizontalLayout.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Plottables), QCoreApplication.translate("MainWindow", u"Plottables", None))
        self.lineEdit.setText("")
        self.lineEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Type commands", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Executables), QCoreApplication.translate("MainWindow", u"Executables", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Runs), QCoreApplication.translate("MainWindow", u"  Runs   ", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Calculator), QCoreApplication.translate("MainWindow", u"Calculator", None))
    # retranslateUi

