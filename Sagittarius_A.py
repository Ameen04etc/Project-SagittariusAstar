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
from PySide6.QtWidgets import (QApplication, QButtonGroup, QFrame, QHBoxLayout,
    QHeaderView, QLayout, QLineEdit, QMainWindow,
    QPlainTextEdit, QSizePolicy, QSplitter, QStackedWidget,
    QTabWidget, QToolButton, QTreeView, QVBoxLayout,
    QWidget)

from pathlineedit import PathLineEdit
from vpushbutton import VPushButton

class Ui_SagittariusA(object):
    def setupUi(self, SagittariusA):
        if not SagittariusA.objectName():
            SagittariusA.setObjectName(u"SagittariusA")
        SagittariusA.resize(436, 336)
        SagittariusA.setMaximumSize(QSize(16777215, 16777215))
        self.centralwidget = QWidget(SagittariusA)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        font = QFont()
        font.setFamilies([u"Calibri"])
        font.setWeight(QFont.Thin)
        font.setItalic(False)
        font.setKerning(False)
        self.tabWidget.setFont(font)
        self.tabWidget.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.West)
        self.tabWidget.setTabShape(QTabWidget.TabShape.Rounded)
        self.tabWidget.setElideMode(Qt.TextElideMode.ElideNone)
        self.tabWidget.setTabsClosable(False)
        self.tabWidget.setMovable(False)
        self.tabWidget.setTabBarAutoHide(True)
        self.Plottables = QWidget()
        self.Plottables.setObjectName(u"Plottables")
        self.verticalLayout_9 = QVBoxLayout(self.Plottables)
        self.verticalLayout_9.setSpacing(0)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.PlotWindows = QTabWidget(self.Plottables)
        self.PlotWindows.setObjectName(u"PlotWindows")
        self.PlotWindows.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.PlotWindows.setTabPosition(QTabWidget.TabPosition.East)
        self.PlotWindows.setTabsClosable(True)
        self.PlotWindows.setTabBarAutoHide(False)
        self.PaneContainer = QWidget()
        self.PaneContainer.setObjectName(u"PaneContainer")
        self.verticalLayout_5 = QVBoxLayout(self.PaneContainer)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.WaveWindow = QWidget(self.PaneContainer)
        self.WaveWindow.setObjectName(u"WaveWindow")

        self.verticalLayout_4.addWidget(self.WaveWindow)


        self.verticalLayout_5.addLayout(self.verticalLayout_4)

        self.PlotWindows.addTab(self.PaneContainer, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.PlotWindows.addTab(self.tab, "")

        self.verticalLayout_9.addWidget(self.PlotWindows)

        self.tabWidget.addTab(self.Plottables, "")
        self.Database = QWidget()
        self.Database.setObjectName(u"Database")
        self.verticalLayout_8 = QVBoxLayout(self.Database)
        self.verticalLayout_8.setSpacing(0)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.spltr_database = QSplitter(self.Database)
        self.spltr_database.setObjectName(u"spltr_database")
        self.spltr_database.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.spltr_database.setFrameShape(QFrame.Shape.Panel)
        self.spltr_database.setFrameShadow(QFrame.Shadow.Sunken)
        self.spltr_database.setLineWidth(0)
        self.spltr_database.setOrientation(Qt.Orientation.Vertical)
        self.spltr_database.setHandleWidth(2)
        self.layoutWidget = QWidget(self.spltr_database)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.hlout_database = QHBoxLayout(self.layoutWidget)
        self.hlout_database.setSpacing(0)
        self.hlout_database.setObjectName(u"hlout_database")
        self.hlout_database.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.hlout_database.setContentsMargins(0, 0, 0, 0)
        self.stackedWidget = QStackedWidget(self.layoutWidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy)
        self.stackedWidget.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.page_exec = QWidget()
        self.page_exec.setObjectName(u"page_exec")
        sizePolicy.setHeightForWidth(self.page_exec.sizePolicy().hasHeightForWidth())
        self.page_exec.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self.page_exec)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.vlout_files_exec = QVBoxLayout()
        self.vlout_files_exec.setSpacing(2)
        self.vlout_files_exec.setObjectName(u"vlout_files_exec")
        self.ToolPanel_exec = QWidget(self.page_exec)
        self.ToolPanel_exec.setObjectName(u"ToolPanel_exec")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.ToolPanel_exec.sizePolicy().hasHeightForWidth())
        self.ToolPanel_exec.setSizePolicy(sizePolicy1)
        self.ToolPanel_exec.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.horizontalLayout_5 = QHBoxLayout(self.ToolPanel_exec)
        self.horizontalLayout_5.setSpacing(4)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.back_exec = QToolButton(self.ToolPanel_exec)
        self.back_exec.setObjectName(u"back_exec")
        self.back_exec.setMinimumSize(QSize(0, 30))
        self.back_exec.setStyleSheet(u"QToolButton {\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    background-color: rgb(45, 45, 45);\n"
"    padding: 3px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: rgb(75, 75, 75);\n"
"}\n"
"\n"
"QToolButton:pressed {\n"
"    background-color: rgb(50, 50, 50);\n"
"}")
        self.back_exec.setArrowType(Qt.ArrowType.LeftArrow)

        self.horizontalLayout_5.addWidget(self.back_exec)

        self.fwd_exec = QToolButton(self.ToolPanel_exec)
        self.fwd_exec.setObjectName(u"fwd_exec")
        self.fwd_exec.setMinimumSize(QSize(0, 30))
        self.fwd_exec.setStyleSheet(u"QToolButton {\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    background-color: rgb(45, 45, 45);\n"
"    padding: 3px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: rgb(75, 75, 75);\n"
"}\n"
"\n"
"QToolButton:pressed {\n"
"    background-color: rgb(50, 50, 50);\n"
"}")
        self.fwd_exec.setArrowType(Qt.ArrowType.RightArrow)

        self.horizontalLayout_5.addWidget(self.fwd_exec)

        self.up_exec = QToolButton(self.ToolPanel_exec)
        self.up_exec.setObjectName(u"up_exec")
        self.up_exec.setMinimumSize(QSize(0, 30))
        self.up_exec.setStyleSheet(u"QToolButton {\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    background-color: rgb(45, 45, 45);\n"
"    padding: 3px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: rgb(75, 75, 75);\n"
"}\n"
"\n"
"QToolButton:pressed {\n"
"    background-color: rgb(50, 50, 50);\n"
"}")
        self.up_exec.setArrowType(Qt.ArrowType.UpArrow)

        self.horizontalLayout_5.addWidget(self.up_exec)

        self.path_exec = PathLineEdit(self.ToolPanel_exec)
        self.path_exec.setObjectName(u"path_exec")
        self.path_exec.setMinimumSize(QSize(0, 30))
        self.path_exec.setMaximumSize(QSize(16777215, 16777215))
        self.path_exec.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.path_exec.setStyleSheet(u"QLineEdit {\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    background-color: rgb(60, 60, 60);\n"
"    padding: 3px;\n"
"}\n"
"\n"
"QLineEdit:hover {\n"
"    background-color: rgb(75, 75, 75);\n"
"}\n"
"\n"
"QLineEdit:pressed {\n"
"    background-color: rgb(50, 50, 50);\n"
"}")
        self.path_exec.setFrame(True)
        self.path_exec.setEchoMode(QLineEdit.EchoMode.Normal)

        self.horizontalLayout_5.addWidget(self.path_exec)

        self.search_exec = QLineEdit(self.ToolPanel_exec)
        self.search_exec.setObjectName(u"search_exec")
        self.search_exec.setMinimumSize(QSize(0, 30))
        self.search_exec.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.search_exec.setStyleSheet(u"QLineEdit {\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    background-color: rgb(60, 60, 60);\n"
"    padding: 3px;\n"
"}\n"
"\n"
"QLineEdit:hover {\n"
"    background-color: rgb(75, 75, 75);\n"
"}\n"
"\n"
"QLineEdit:pressed {\n"
"    background-color: rgb(50, 50, 50);\n"
"}")
        self.search_exec.setFrame(True)

        self.horizontalLayout_5.addWidget(self.search_exec)

        self.horizontalLayout_5.setStretch(0, 1)
        self.horizontalLayout_5.setStretch(1, 1)
        self.horizontalLayout_5.setStretch(2, 1)
        self.horizontalLayout_5.setStretch(3, 4)
        self.horizontalLayout_5.setStretch(4, 1)

        self.vlout_files_exec.addWidget(self.ToolPanel_exec)

        self.FileSystem_exec = QTreeView(self.page_exec)
        self.FileSystem_exec.setObjectName(u"FileSystem_exec")
        self.FileSystem_exec.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.FileSystem_exec.setStyleSheet(u"QTreeView {\n"
"    background-color: rgb(37, 37, 38);\n"
"    border: none;\n"
"}\n"
"\n"
"QTreeView::item {\n"
"    padding: 2px;\n"
"}\n"
"\n"
"QTreeView::item:selected {\n"
"    background-color: rgb(70, 70, 70);\n"
"    color: white;\n"
"}\n"
"\n"
"QTreeView::item:hover {\n"
"    background-color: rgb(50, 50, 50);\n"
"}\n"
"\n"
"QTreeView::item:selected:hover {\n"
"    background-color: rgb(70, 70, 70);\n"
"}\n"
"\n"
"QHeaderView::section {\n"
"    background-color: rgb(37, 37, 38);\n"
"    color: white;\n"
"\n"
"    border: none;\n"
"\n"
"    padding: 4px;\n"
"}\n"
"\n"
"QHeaderView::section {\n"
"    background-color: rgb(45, 45, 45);\n"
"    border: none;\n"
"    border-right: 1px solid rgb(38, 38, 38);\n"
"    padding-left: 6px;\n"
"\n"
"}")
        self.FileSystem_exec.setFrameShape(QFrame.Shape.NoFrame)
        self.FileSystem_exec.setFrameShadow(QFrame.Shadow.Plain)

        self.vlout_files_exec.addWidget(self.FileSystem_exec)


        self.verticalLayout.addLayout(self.vlout_files_exec)

        self.stackedWidget.addWidget(self.page_exec)
        self.page_run = QWidget()
        self.page_run.setObjectName(u"page_run")
        sizePolicy.setHeightForWidth(self.page_run.sizePolicy().hasHeightForWidth())
        self.page_run.setSizePolicy(sizePolicy)
        self.verticalLayout_3 = QVBoxLayout(self.page_run)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.vlout_files_run = QVBoxLayout()
        self.vlout_files_run.setSpacing(2)
        self.vlout_files_run.setObjectName(u"vlout_files_run")
        self.ToolPanel_run = QWidget(self.page_run)
        self.ToolPanel_run.setObjectName(u"ToolPanel_run")
        sizePolicy1.setHeightForWidth(self.ToolPanel_run.sizePolicy().hasHeightForWidth())
        self.ToolPanel_run.setSizePolicy(sizePolicy1)
        self.ToolPanel_run.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.horizontalLayout_7 = QHBoxLayout(self.ToolPanel_run)
        self.horizontalLayout_7.setSpacing(4)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.back_run = QToolButton(self.ToolPanel_run)
        self.back_run.setObjectName(u"back_run")
        self.back_run.setMinimumSize(QSize(0, 30))
        self.back_run.setStyleSheet(u"QToolButton {\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    background-color: rgb(45, 45, 45);\n"
"    padding: 3px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: rgb(75, 75, 75);\n"
"}\n"
"\n"
"QToolButton:pressed {\n"
"    background-color: rgb(50, 50, 50);\n"
"}")
        self.back_run.setArrowType(Qt.ArrowType.LeftArrow)

        self.horizontalLayout_7.addWidget(self.back_run)

        self.fwd_run = QToolButton(self.ToolPanel_run)
        self.fwd_run.setObjectName(u"fwd_run")
        self.fwd_run.setMinimumSize(QSize(0, 30))
        self.fwd_run.setStyleSheet(u"QToolButton {\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    background-color: rgb(45, 45, 45);\n"
"    padding: 3px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: rgb(75, 75, 75);\n"
"}\n"
"\n"
"QToolButton:pressed {\n"
"    background-color: rgb(50, 50, 50);\n"
"}")
        self.fwd_run.setArrowType(Qt.ArrowType.RightArrow)

        self.horizontalLayout_7.addWidget(self.fwd_run)

        self.up_run = QToolButton(self.ToolPanel_run)
        self.up_run.setObjectName(u"up_run")
        self.up_run.setMinimumSize(QSize(0, 30))
        self.up_run.setStyleSheet(u"QToolButton {\n"
"    /* Use forward slashes for the file path */\n"
"    qproperty-icon: url(\"C:/Users/Ameen Aazam/Downloads/up-arrow-svgrepo-com.svg\");\n"
"    \n"
"    /* Adjust this to match the size you want the arrow to render */\n"
"    qproperty-iconSize: 15px 15px; \n"
"}\n"
"QToolButton {\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    background-color: rgb(45, 45, 45);\n"
"    padding: 3px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: rgb(75, 75, 75);\n"
"}\n"
"\n"
"QToolButton:pressed {\n"
"    background-color: rgb(50, 50, 50);\n"
"}")
        self.up_run.setArrowType(Qt.ArrowType.NoArrow)

        self.horizontalLayout_7.addWidget(self.up_run)

        self.path_run = PathLineEdit(self.ToolPanel_run)
        self.path_run.setObjectName(u"path_run")
        self.path_run.setMinimumSize(QSize(0, 30))
        self.path_run.setMaximumSize(QSize(16777215, 16777215))
        self.path_run.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.path_run.setStyleSheet(u"QLineEdit {\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    background-color: rgb(60, 60, 60);\n"
"    padding: 3px;\n"
"}\n"
"\n"
"QLineEdit:hover {\n"
"    background-color: rgb(75, 75, 75);\n"
"}\n"
"\n"
"QLineEdit:pressed {\n"
"    background-color: rgb(50, 50, 50);\n"
"}")
        self.path_run.setFrame(True)
        self.path_run.setEchoMode(QLineEdit.EchoMode.Normal)

        self.horizontalLayout_7.addWidget(self.path_run)

        self.search_run = QLineEdit(self.ToolPanel_run)
        self.search_run.setObjectName(u"search_run")
        self.search_run.setMinimumSize(QSize(0, 30))
        self.search_run.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.search_run.setStyleSheet(u"QLineEdit {\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    background-color: rgb(60, 60, 60);\n"
"    padding: 3px;\n"
"}\n"
"\n"
"QLineEdit:hover {\n"
"    background-color: rgb(75, 75, 75);\n"
"}\n"
"\n"
"QLineEdit:pressed {\n"
"    background-color: rgb(50, 50, 50);\n"
"}")
        self.search_run.setFrame(True)

        self.horizontalLayout_7.addWidget(self.search_run)

        self.horizontalLayout_7.setStretch(0, 1)
        self.horizontalLayout_7.setStretch(1, 1)
        self.horizontalLayout_7.setStretch(2, 1)
        self.horizontalLayout_7.setStretch(3, 4)
        self.horizontalLayout_7.setStretch(4, 1)

        self.vlout_files_run.addWidget(self.ToolPanel_run)

        self.FileSystem_run = QTreeView(self.page_run)
        self.FileSystem_run.setObjectName(u"FileSystem_run")
        self.FileSystem_run.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.FileSystem_run.setStyleSheet(u"QTreeView {\n"
"    background-color: rgb(37, 37, 38);\n"
"    border: none;\n"
"}\n"
"\n"
"QTreeView::item {\n"
"    padding: 2px;\n"
"}\n"
"\n"
"QTreeView::item:selected {\n"
"    background-color: rgb(70, 70, 70);\n"
"    color: white;\n"
"}\n"
"\n"
"QTreeView::item:hover {\n"
"    background-color: rgb(50, 50, 50);\n"
"}\n"
"\n"
"QTreeView::item:selected:hover {\n"
"    background-color: rgb(70, 70, 70);\n"
"}\n"
"\n"
"QHeaderView::section {\n"
"    background-color: rgb(37, 37, 38);\n"
"    color: white;\n"
"\n"
"    border: none;\n"
"\n"
"    padding: 4px;\n"
"}\n"
"\n"
"QHeaderView::section {\n"
"    background-color: rgb(45, 45, 45);\n"
"    border: none;\n"
"    border-right: 1px solid rgb(38, 38, 38);\n"
"    padding-left: 6px;\n"
"\n"
"}")
        self.FileSystem_run.setFrameShape(QFrame.Shape.NoFrame)
        self.FileSystem_run.setFrameShadow(QFrame.Shadow.Plain)

        self.vlout_files_run.addWidget(self.FileSystem_run)


        self.verticalLayout_3.addLayout(self.vlout_files_run)

        self.stackedWidget.addWidget(self.page_run)

        self.hlout_database.addWidget(self.stackedWidget)

        self.side_lout = QVBoxLayout()
        self.side_lout.setSpacing(0)
        self.side_lout.setObjectName(u"side_lout")
        self.side_lout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.vlout_exec_run = QWidget(self.layoutWidget)
        self.vlout_exec_run.setObjectName(u"vlout_exec_run")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.vlout_exec_run.sizePolicy().hasHeightForWidth())
        self.vlout_exec_run.setSizePolicy(sizePolicy2)
        self.vlout_exec_run.setMinimumSize(QSize(30, 0))
        self.vlout_exec_run.setMaximumSize(QSize(30, 16777215))
        self.verticalLayout_6 = QVBoxLayout(self.vlout_exec_run)
        self.verticalLayout_6.setSpacing(4)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.verticalLayout_6.setContentsMargins(4, 0, 0, 0)
        self.Executables_btn = VPushButton(self.vlout_exec_run)
        self.buttonGroup = QButtonGroup(SagittariusA)
        self.buttonGroup.setObjectName(u"buttonGroup")
        self.buttonGroup.addButton(self.Executables_btn)
        self.Executables_btn.setObjectName(u"Executables_btn")
        sizePolicy2.setHeightForWidth(self.Executables_btn.sizePolicy().hasHeightForWidth())
        self.Executables_btn.setSizePolicy(sizePolicy2)
        self.Executables_btn.setMinimumSize(QSize(30, 0))
        self.Executables_btn.setMaximumSize(QSize(30, 16777215))
        self.Executables_btn.setAcceptDrops(False)
        self.Executables_btn.setStyleSheet(u"QPushButton {\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    background-color: rgb(60, 60, 60);\n"
"    padding: 3px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(75, 75, 75);\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(50, 50, 50);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: rgb(80, 120, 200);\n"
"}")
        self.Executables_btn.setCheckable(True)
        self.Executables_btn.setAutoDefault(False)
        self.Executables_btn.setFlat(False)

        self.verticalLayout_6.addWidget(self.Executables_btn)

        self.Runs_btn = VPushButton(self.vlout_exec_run)
        self.buttonGroup.addButton(self.Runs_btn)
        self.Runs_btn.setObjectName(u"Runs_btn")
        sizePolicy2.setHeightForWidth(self.Runs_btn.sizePolicy().hasHeightForWidth())
        self.Runs_btn.setSizePolicy(sizePolicy2)
        self.Runs_btn.setMinimumSize(QSize(30, 0))
        self.Runs_btn.setMaximumSize(QSize(30, 16777215))
        self.Runs_btn.setStyleSheet(u"QPushButton {\n"
"    border: none;\n"
"    border-radius: 6px;\n"
"    background-color: rgb(60, 60, 60);\n"
"    padding: 3px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(75, 75, 75);\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(50, 50, 50);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: rgb(80, 120, 200);\n"
"}")
        self.Runs_btn.setCheckable(True)

        self.verticalLayout_6.addWidget(self.Runs_btn)


        self.side_lout.addWidget(self.vlout_exec_run)

        self.side_lout.setStretch(0, 10)

        self.hlout_database.addLayout(self.side_lout)

        self.hlout_database.setStretch(0, 10)
        self.hlout_database.setStretch(1, 1)
        self.spltr_database.addWidget(self.layoutWidget)

        self.verticalLayout_8.addWidget(self.spltr_database)

        self.tabWidget.addTab(self.Database, "")
        self.Calculator = QWidget()
        self.Calculator.setObjectName(u"Calculator")
        self.tabWidget.addTab(self.Calculator, "")
        self.Editor = QWidget()
        self.Editor.setObjectName(u"Editor")
        self.verticalLayout_7 = QVBoxLayout(self.Editor)
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(self.Editor)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.tabWidget_2 = QTabWidget(self.splitter)
        self.tabWidget_2.setObjectName(u"tabWidget_2")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.horizontalLayout = QHBoxLayout(self.tab_2)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.plainTextEdit = QPlainTextEdit(self.tab_2)
        self.plainTextEdit.setObjectName(u"plainTextEdit")

        self.horizontalLayout.addWidget(self.plainTextEdit)

        self.tabWidget_2.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.tabWidget_2.addTab(self.tab_3, "")
        self.splitter.addWidget(self.tabWidget_2)
        self.terminalout = QWidget(self.splitter)
        self.terminalout.setObjectName(u"terminalout")
        self.splitter.addWidget(self.terminalout)

        self.verticalLayout_7.addWidget(self.splitter)

        self.tabWidget.addTab(self.Editor, "")

        self.verticalLayout_2.addWidget(self.tabWidget)

        SagittariusA.setCentralWidget(self.centralwidget)

        self.retranslateUi(SagittariusA)

        self.tabWidget.setCurrentIndex(3)
        self.PlotWindows.setCurrentIndex(0)
        self.stackedWidget.setCurrentIndex(0)
        self.Executables_btn.setDefault(False)


        QMetaObject.connectSlotsByName(SagittariusA)
    # setupUi

    def retranslateUi(self, SagittariusA):
        SagittariusA.setWindowTitle(QCoreApplication.translate("SagittariusA", u"MainWindow", None))
        self.PlotWindows.setTabText(self.PlotWindows.indexOf(self.PaneContainer), QCoreApplication.translate("SagittariusA", u"Window 1", None))
        self.PlotWindows.setTabText(self.PlotWindows.indexOf(self.tab), QCoreApplication.translate("SagittariusA", u"Page", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Plottables), QCoreApplication.translate("SagittariusA", u"Plottables", None))
        self.back_exec.setText("")
        self.fwd_exec.setText(QCoreApplication.translate("SagittariusA", u"...", None))
        self.up_exec.setText(QCoreApplication.translate("SagittariusA", u"...", None))
        self.path_exec.setText("")
        self.search_exec.setPlaceholderText(QCoreApplication.translate("SagittariusA", u"Search", None))
        self.back_run.setText("")
        self.fwd_run.setText(QCoreApplication.translate("SagittariusA", u"...", None))
        self.up_run.setText(QCoreApplication.translate("SagittariusA", u"...", None))
        self.path_run.setText("")
        self.search_run.setPlaceholderText(QCoreApplication.translate("SagittariusA", u"Search", None))
        self.Executables_btn.setText(QCoreApplication.translate("SagittariusA", u"Executables", None))
        self.Runs_btn.setText(QCoreApplication.translate("SagittariusA", u"Runs", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Database), QCoreApplication.translate("SagittariusA", u"Database", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Calculator), QCoreApplication.translate("SagittariusA", u"Calculator", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_2), QCoreApplication.translate("SagittariusA", u"Tab 1", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_3), QCoreApplication.translate("SagittariusA", u"Tab 2", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Editor), QCoreApplication.translate("SagittariusA", u"Editor", None))
    # retranslateUi

