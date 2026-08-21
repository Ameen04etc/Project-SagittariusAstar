import os
os.add_dll_directory(r"C:\opencv\build\x64\vc16\bin")
os.add_dll_directory(r"C:\Qt\6.11.1\msvc2022_64\bin")
from importlib.resources import path
from Sagittarius_A import Ui_SagittariusA
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QSplitter, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QScrollBar, QSizePolicy,
                               QPushButton, QToolButton, QToolTip,
                               QFrame, QLabel, QTreeView)
from PySide6.QtCore import    (QProcess, Qt, QObject,
                               Signal, QRectF, QPointF,
                               Slot, QRect, QEvent,
                               QSize, QPoint, QSignalBlocker,
                               QTimer)
from PySide6.QtGui import     (QPainter, QColor, QPen,
                               QPixmap, QFont, QMouseEvent,
                               QImage, QCursor, QPainterPath,
                               QStandardItemModel, QStandardItem)
import renderCore
from numba import njit
import numpy as np
import cv2
import math
import time
import shiboken6
import traceback

Debug         = False
padding       = 5
max_val       = 9
DigitalCircle = {
    1   :[[0, 0]],
    2   :[[0, 1], [1, 0], [0, -1], [-1, 0]],
    3   :[[0, 2], [1, 1], [2, 0], [1, -1], [0, -2], [-1, -1], [-2, 0], [-1, 1]],
    4   :[[1, 2], [2, 1], [2, -1], [1, -2], [-1, -2], [-2, -1], [-2, 1], [-1, 2]],
    5   :[[0, 3], [1, 3], [2, 2], [3, 1], [3, 0], [3, -1], [2, -2], [1, -3], [0, -3], [-1, -3], [-2, -2], [-3, -1], [-3, 0], [-3, 1], [-2, 2], [-1, 3]],
    6   :[[0, 4], [1, 4], [2, 3], [3, 2], [4, 1], [4, 0], [4, -1], [3, -2], [2, -3], [1, -4], [0, -4], [-1, -4], [-2, -3], [-3, -2], [-4, -1], [-4, 0], [-4, 1], [-3, 2], [-2, 3], [-1, 4]]
}


class WaveWindow(QObject):
    # Highest in the Wave hierarchy ... holds the following architecture (roughly)
    """
            WaveWindow
            │
            ├── GlobalWaveModel                     (Checked)
            │
            ├── GlobalViewport                      (checked)
            │
            ├── Preview                             (checked)
            │
            ├── PaneManager                         (checked)
            │   │
            │   ├── Pane                            (checked)
            │   │   ├── Model                       (checked)
            │   │   ├── Viewport                    (checked)
            │   │   ├── Controller                  (checked)
            │   │   ├── Renderer                    (checked)
            │   │   ├── HitTest                     (checked)
            │   │   └── Widgets                     (checked)
            │   │
            │   ├── Pane
            │   └── Pane
            │
            ├── Signal Browser                      (Yet to think upon)
            │
            ├── Measurement Engine                  (Yet to think upon)
            │
            ├── Cursor Engine                       (Yet to think upon)
            │
            ├── Marker Engine                       (Yet to think upon)
            │
            ├── Search Engine                       (Yet to think upon)
            │
            └── Export Engine                       (Yet to think upon)
    """

    def __init__(self, GlobalWidget : QWidget):
        super().__init__(GlobalWidget)
        self.Widget          = GlobalWidget
        self.GlobalViewModel = GlobalViewModel()
        self.GlobalViewPort  = GlobalViewPort()

        self.ToolBar         = QWidget(self.Widget)
        self.RightWidget     = QWidget(self.Widget)
        self.LeftWidget      = QWidget(self.Widget)
        self.LeftHeader      = QWidget(self.Widget)
        self.WaveWidget      = GlobalWaveWidget(self.Widget, self.GlobalViewModel)
        self.Splitter        = QSplitter(Qt.Orientation.Horizontal)

        self.PaneManager     = PaneManager(self.WaveWidget, self.LeftWidget, self.GlobalViewModel, self.Splitter)
        self.AxisWidget      = GlobalAxisWidget(self.Widget)
        self.PreView         = GlobalPreView(self.Widget, self.PaneManager)
        self.CursorManager   = GlobalCursorManager(self.WaveWidget, self.GlobalViewPort, self.PaneManager)
        self.LayoutConfig ()
        self.ToolBarConfig()
        self.SignalManager()
    
    def LayoutConfig(self):

        self.GlobalLout = QVBoxLayout(self.Widget)
        self.GlobalLout.setContentsMargins(0, 0, 0, 0)
        self.GlobalLout.setSpacing(0)

        leftMasterWidget = QWidget()
        leftMasterWidget.setMaximumWidth(200)

        leftDummyWidget = QWidget(leftMasterWidget)
        leftDummyWidget.setFixedHeight(30)
        leftDummyWidget.setStyleSheet("background: rgb(30, 30, 30);")

        self.LeftHeader.setFixedHeight(18)
        self.LeftHeader.setStyleSheet("background: rgb(30, 30, 30);")

        # self.LeftWidget .setMaximumWidth(200)
        self.RightWidget.setStyleSheet("background: rgb(30, 30, 30);")

        self.RightLaout  = QVBoxLayout(self.RightWidget)
        self.RightLaout.setContentsMargins(0, 0, 0, 0)
        self.RightLaout.setSpacing(0)

        self.LeftLayout  = QVBoxLayout(leftMasterWidget)
        self.LeftLayout.setContentsMargins(0, 0, 0, 0)
        self.LeftLayout.setSpacing(0)

        self.PreView   .setParent(self.RightWidget)
        self.WaveWidget.setParent(self.RightWidget)
        self.AxisWidget.setParent(self.RightWidget)

        self.PrViewLout = QHBoxLayout()
        self.PrViewLout.setContentsMargins(0, 0, 0, 0)
        self.PrViewLout.setSpacing(0)

        self.AxisLayout = QHBoxLayout()
        self.AxisLayout.setContentsMargins(0, 0, 0, 0)
        self.AxisLayout.setSpacing(0)

        self.ToolBar.setFixedHeight(60)
        self.ToolBar.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        # self.ToolBar.setStyleSheet(u"QWidget {\n"
        #                             "border: none;\n"
        #                             "background-color: rgb(30, 30, 30);\n"
        #                             "padding: 3px;\n"
        #                             "}")

        self.PreViewOffsetL = QWidget(self.RightWidget)
        self.PreViewOffsetL.setFixedSize(QSize(35, 18))
        self.PreViewOffsetL.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))

        self.PreViewOffsetR = QWidget(self.RightWidget)
        self.PreViewOffsetR.setFixedSize(QSize(8, 18))
        self.PreViewOffsetR.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))

        self.PreView.setFixedHeight(18)
        self.PreView.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        self.PreView.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.PreView.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.PrViewLout.addWidget(self.PreViewOffsetL)
        self.PrViewLout.addWidget(self.PreView)
        self.PrViewLout.addWidget(self.PreViewOffsetR)

        self.WaveWidget.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        self.WaveWidget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.AxsOffsetL = QWidget(self.RightWidget)
        self.AxsOffsetL.setFixedSize(QSize(35, 30))
        self.AxsOffsetL.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))

        self.AxsOffsetR = QWidget(self.RightWidget)
        self.AxsOffsetR.setFixedSize(QSize(8, 30))
        self.AxsOffsetR.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))

        self.AxisWidget.setFixedHeight(30)
        self.AxisWidget.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        self.AxisLayout.addWidget(self.AxsOffsetL)
        self.AxisLayout.addWidget(self.AxisWidget)
        self.AxisLayout.addWidget(self.AxsOffsetR)

        self.RightLaout.addLayout(self.PrViewLout)
        self.RightLaout.addWidget(self.WaveWidget)
        self.RightLaout.addLayout(self.AxisLayout)

        self.LeftLayout.addWidget(self.LeftHeader)
        self.LeftLayout.addWidget(self.LeftWidget)
        self.LeftLayout.addWidget(leftDummyWidget)

        self.Splitter.addWidget(leftMasterWidget)
        self.Splitter.addWidget(self.RightWidget)

        self.GlobalLout.addWidget(self.ToolBar )
        self.GlobalLout.addWidget(self.Splitter)

    #     style = """
    #     /* Style the outer border of the entire splitter */
    #     QSplitter {
    #         border: 3px solid #2C3E50; 
    #         background-color: #ECF0F1; 
    #     }

    #     /* Style the default handle */
    #     QSplitter::handle {
    #         background-color: #E74C3C; /* A nice red color */
    #         border: 1px solid #C0392B;
    #         border-radius: 2px;
    #     }

    #     /* Set specific thickness for horizontal orientation */
    #     QSplitter::handle:horizontal {
    #         width: 2px; 
    #         margin: 2px 0px; /* Gives a little gap at the top and bottom */
    #     }

    #     /* Set specific thickness for vertical orientation */
    #     QSplitter::handle:vertical {
    #         height: 2px;
    #         margin: 0px 2px;
    #     }

    #     /* Add a hover effect so the user knows it's draggable */
    #     QSplitter::handle:hover {
    #         background-color: #F1C40F; /* Turns yellow on hover */
    #     }
        
    #     /* Optional: Style the child widgets so they look nice inside the border */
    #     QTextEdit {
    #         border: none;
    #         background-color: #FFFFFF;
    #     }
    # """

    #     self.Splitter.setStyleSheet(style)
    
    def ToolBarConfig(self):
        tb_layout = QHBoxLayout(self.ToolBar)
        tb_layout.setContentsMargins(5, 2, 5, 2)
        
        self.Split   = QToolButton(self.ToolBar)
        self.Combine = QToolButton(self.ToolBar)
        self.VCursor = QToolButton(self.ToolBar)
        self.HCursor = QToolButton(self.ToolBar)

        self.Split  .setText("Split")
        self.Combine.setText("Combine")
        self.VCursor.setText("Vertical Cursor")
        self.HCursor.setText("Horizontal Cursor")

        tb_layout.addWidget(self.Split)
        tb_layout.addWidget(self.Combine)
        tb_layout.addWidget(self.VCursor)
        tb_layout.addWidget(self.HCursor)
        tb_layout.addStretch() # Push buttons left

        self.Split.clicked.connect(self.PaneManager.SplitPanes)
        self.Combine.clicked.connect(self.PaneManager.CombPanes)
    
    def SetAxis(self, axis):
        self.GlobalViewModel.SetGlobalAxis(axis)
    
    def AddSignal(self, signal, SignalName):
        self.GlobalViewModel.AddGlobalSignal(signal, SignalName)
    
    def SignalManager(self):
        self.GlobalViewModel.GlobalSignalAdded.connect(lambda signal: self.PaneManager.GlobalSignalAdded.emit(signal))
        self.AxisWidget     .GlobalAxsResize  .connect(lambda w: setattr(self.GlobalViewPort, 'AxisWidth', w))

        self.GlobalViewModel.SetAxis          .connect(self.GlobalViewPort.ResetGlobalXPort)
        self.GlobalViewPort .GlobalPortChanged.connect(self.AxisWidget    .ViewPortSocket  )
        self.GlobalViewPort .GlobalPortChanged.connect(self.CursorManager .ViewPortSocket  )

        self.PaneManager    .SelectBroadCast  .connect(lambda: self.PreView.update())
        self.PaneManager    .Split            .connect(lambda: self.CursorManager.inspect.emit(self.CursorManager.HeldCurs), type = Qt.QueuedConnection)
        self.PaneManager    .Combine          .connect(lambda: self.CursorManager.inspect.emit(self.CursorManager.HeldCurs), type = Qt.QueuedConnection)

        self.PaneManager    .XPortBroadCast   .connect(self.GlobalViewPort.SyncGlobalXPort)
        self.PaneManager    .PreViewUpdate    .connect(self.PreView.update)
        self.PaneManager    .AddGlobalCursor  .connect(self.CursorManager.AddCursor)
        self.PaneManager    .CursorRelease    .connect(self.CursorManager.ReleaseCursor)

        self.PreView        .PreViewResize    .connect(lambda h, w: self.PaneManager.PreViewResize.emit(h, w))
        self.PreView        .XPortCommand     .connect(lambda xmin, xmax: self.PaneManager.XPortBroadCast.emit(xmin, xmax, None, None, None, False))

        self.PreView        .XPortCommand     .connect(self.GlobalViewPort.SyncGlobalXPort)
        self.PreView        .PreViewResize    .emit   (self.PreView.height(), self.PreView.width())

        # self.CursorManager  .inspect          .connect(lambda held: print("HeldCurs :", held))
        self.CursorManager  .fitCommand       .connect(lambda: self.PaneManager.XPortBroadCast.emit(0, 0, 0, 0, 0, True))


class GlobalViewModel(QObject):
    ##==================================================
    # stores Axis data and all signals data and metadata
    ##==================================================
    SetAxis             = Signal(object)
    GlobalSignalAdded   = Signal(object)

    def __init__(self):
        super().__init__()
        self.GlobalSignals = {}
        self.GlobalIndex   = 0
        self.Axis          = None
        self.AxisStart     = 0
        self.AxisStop      = 0
        self.AxisRange     = 0

        self.colors = [
            QColor(205,  49,  49),  # Red
            QColor( 13, 188, 121),  # Green
            QColor( 36, 114, 200),  # Blue
            QColor(229, 229,  16),  # Yellow
            QColor(188,  63, 188),  # Magenta
            QColor( 17, 168, 205),  # Cyan
            QColor(255, 128, 000),  # Orange
            QColor(255, 160, 220),  # Pink
            QColor(128, 255, 128),  # Light Green
            QColor(128, 128, 255)   # Light Blue
        ]

    def SetGlobalAxis(self, axis):
        self.Axis = axis
        self.AxisStart = np.min(axis)
        self.AxisStop  = np.max(axis)
        self.AxisRange = self.AxisStop - self.AxisStart
        self.SetAxis.emit(self.Axis)

    def AddGlobalSignal(self, data, name):
        Newsignal = GlobalSignalModel()
        self.SignalMetaData(Newsignal, data, name)
        self.GlobalSignals.update({self.GlobalIndex : Newsignal})
        self.GlobalIndex += 1
        self.GlobalSignalAdded.emit(Newsignal)
    
    def RemoveGlobalSignal(self, GlobalIDs):
        self.GlobalSignals = [
            sig for sig in self.GlobalSignals
            if sig.Global_ID not in GlobalIDs
        ]

        for i, sig in enumerate(self.GlobalSignals):
            sig.Global_ID = i

    def SignalMetaData(self, NewSignal : GlobalSignalModel, data, name):
        NewSignal.Global_ID = self.GlobalIndex
        NewSignal.name      = name
        NewSignal.color     = self.colors[NewSignal.Global_ID % len(self.colors)]
        NewSignal.data      = data


class GlobalSignalModel:
    ##=================================================
    # A signle signal object with its data and metadata
    ##=================================================
    def __init__(self):
        self.Global_ID = 0
        self.name      = None
        self.color     = None
        self.data      = None


class GlobalViewPort(QObject):
    ##==============================================================================================
    # Stores the minimum, maximum visible values, tick value and tick start value of the Global axis
    ##==============================================================================================
    GlobalPortChanged = Signal(float, float, float, float)

    def __init__(self):
        super().__init__()
        self.Axis       = None
        self.Abs_XMin   = None
        self.Abs_XMax   = None
        self.View_XMin  = None
        self.View_XMax  = None
        self.View_XRng  = None
        self.Nx         = 10
        self.XTick      = None
        self.XTickStart = None
        self.AxisWidth  = 1180 - 2 * padding

    def ResetGlobalXPort(self, axis):
        self.Axis       = axis
        self.Abs_XMin   = np.min(axis)
        self.Abs_XMax   = np.max(axis)
        self.View_XMin  = self.Abs_XMin
        self.View_XMax  = self.Abs_XMax
        self.View_XRng  = self.View_XMax  - self.View_XMin
        self.XTick      = self.TickCalculator()
        self.XTickStart = int(self.View_XMin/self.XTick) * self.XTick

        self.GlobalPortChanged.emit(self.View_XMin, self.View_XMax, self.XTick, self.XTickStart)

    def FitGlobalXPort(self):
        self.View_XMin  = self.Abs_XMin
        self.View_XMax  = self.Abs_XMax
        self.View_XRng  = self.View_XMax - self.View_XMin
        self.XTick      = self.TickCalculator()
        self.XTickStart = int(self.View_XMin/self.XTick) * self.XTick

        self.GlobalPortChanged.emit(self.View_XMin, self.View_XMax, self.XTick, self.XTickStart)

    def SyncGlobalXPort(self, min, max, rng = None, tick =  None, tickstart = None, fit =  None):
        if fit:
            self.FitGlobalXPort()
            return
        
        self.View_XMin  = min
        self.View_XMax  = max
        if rng is None: self.View_XRng = max - min
        else: self.View_XRng  = rng
        if tick is None: self.XTick = self.TickCalculator()
        else: self.XTick      = tick
        if tickstart is None: self.XTickStart = int(self.View_XMin/self.XTick) * self.XTick
        else: self.XTickStart = tickstart

        self.GlobalPortChanged.emit(self.View_XMin, self.View_XMax, self.XTick, self.XTickStart)
    
    def TickCalculator(self):
        self.Nx = max(np.ceil(40 * self.AxisWidth / 1180), 1)
        if self.View_XRng == 0:
            self.Abs_XMin  = 0
            self.Abs_XMax  = 1
            self.View_XMin = 0
            self.View_XMax = 1
            self.View_XRng = 1

        raw_spacing  = abs(self.View_XRng)/self.Nx
        dec          = 10 ** np.floor(np.log10(raw_spacing))
        norm_spacing = raw_spacing / dec
        ref          = [1, 2, 5, 10, 25]
        i            = np.argmin(np.abs(np.ones(len(ref)) * norm_spacing - ref))
        tick         = ref[np.argmin(np.abs(np.ones(len(ref)) * norm_spacing - ref))] * dec * (self.View_XRng/abs(self.View_XRng))
        while True:
            if self.View_XRng / tick <= self.Nx + 1: break
            elif i >= len(ref): break
            else:
                i += 1
                tick = ref[i] * dec * (self.View_XRng/abs(self.View_XRng))
        return tick


class GlobalWaveWidget(QWidget):
    SetCurrentPane = Signal(int)
    InsertSignals  = Signal(object)
    RemoveSignals  = Signal(object, int)
    AddPane        = Signal(int)

    def __init__(self, parent, GlobalViewModel : GlobalViewModel):
        super().__init__(parent)
        self.SplitterConfig()
        self.ViewModel  = GlobalViewModel
        self.HoverTrace = HoverTrace(self)
        self.EdgeWidet  = BorderWidget(self)
        self.PaneID     = 0
        self.EdgeActive = False
        self.EdgePx     = None
        self.EdgeUp     = False
        self.EdgeDn     = False
        self.EdgeMid    = False
        self.setMouseTracking(True)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(30, 30, 30))
        painter.drawRect(
            0, 0,
            self.width(), self.height()
        )
        painter.end()

    def SplitterConfig(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.Splitter = QSplitter(Qt.Orientation.Vertical)
        self.Splitter.setChildrenCollapsible(False)
        layout.addWidget(self.Splitter)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        localPosition = event.position().toPoint()
        self.Configure(localPosition)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        localPosition = event.position().toPoint()
        self.Configure(localPosition)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.EdgeWidet.resize(QSize(self.width(), 2)) # <------ Commented out!

    def Configure(self, position):
        canvasPosition = None
        canvasHeight   = 0
        for i in range(self.Splitter.count()):
            pane = self.Splitter.widget(i)
            if pane.geometry().contains(position):
                self.PaneID = i
                canvasPosition = pane.mapFromGlobal(self.mapToGlobal(position)).y()
                canvasHeight   = pane.height()

        if position.y() > self.height() or position.y() < 0: self.PaneID = None

        if (self.PaneID is not None) and (canvasPosition is not None) and self.EdgeActive:
            if (0 < canvasPosition < padding):
                self.EdgeUp  = True
                self.EdgeDn  = False
                self.EdgeMid = False
                if self.PaneID == 0: self.EdgePx = 1
                else:
                    handle = self.Splitter.handle(self.PaneID)
                    self.EdgePx = handle.pos().y()

                self.EdgeWidet.move(0, self.EdgePx)
                self.EdgeWidet.show()

            elif (canvasHeight - padding < canvasPosition < canvasHeight):
                self.EdgeUp  = False
                self.EdgeDn  = True
                self.EdgeMid = False
                if self.PaneID == self.Splitter.count() - 1: self.EdgePx = self.height() - 1
                else:
                    handle = self.Splitter.handle(self.PaneID + 1)
                    self.EdgePx = handle.pos().y()

                self.EdgeWidet.move(0, self.EdgePx)
                self.EdgeWidet.show()
            
            else:
                self.EdgeUp  = False
                self.EdgeDn  = False
                self.EdgeMid = True
                self.EdgeWidet.hide()

        elif (self.PaneID is None) or (not self.EdgeActive): self.EdgeWidet.hide()

    def TraceTransfer(self):
        index = None
        if self.EdgeUp: index = self.PaneID
        elif self.EdgeDn: index = self.PaneID + 1

        if index is not None:
            if index < self.HoverTrace.PaneID: sourceID = self.HoverTrace.PaneID + 1
            elif index > self.HoverTrace.PaneID: sourceID = self.HoverTrace.PaneID
            elif index == self.HoverTrace.PaneID:
                if self.EdgeUp: sourceID = self.HoverTrace.PaneID + 1
                elif self.EdgeDn: sourceID = self.HoverTrace.PaneID

        signals = []
        for value in self.HoverTrace.TraceMaps.values():
            signals.append(self.ViewModel.GlobalSignals[value])
        
        if self.EdgeMid:
            self.SetCurrentPane.emit(self.PaneID)
            if (self.PaneID != self.HoverTrace.PaneID) and len(signals) != 0:
                self.InsertSignals.emit(signals)
                self.RemoveSignals.emit(signals, self.HoverTrace.PaneID)
            self.EdgeMid = False

        elif self.EdgeUp:
            self.AddPane.emit(index)
            self.InsertSignals.emit(signals)
            self.RemoveSignals.emit(signals, sourceID)
            self.EdgeUp = False

        elif self.EdgeDn:
            self.AddPane.emit(index)
            self.InsertSignals.emit(signals)
            self.RemoveSignals.emit(signals, sourceID)
            self.EdgeDn = False
        
        self.HoverTrace.TraceMaps.clear()


class BorderWidget(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.resize(QSize(parent.width(), 2))
        self.hide()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 255, 0), 1, Qt.DashLine))
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.drawLine(
            0, 0,
            self.width(), 0
            )

        painter.end()


class GlobalAxisWidget(QWidget):
    ##=======================================
    # Creates widget and draws the Axis on it
    ##=======================================
    GlobalAxsResize = Signal(float)

    def __init__(self, Parent):
        super().__init__()
        self.setParent(Parent)
        self.View_AxMin   = None
        self.View_AxMax   = None
        self.View_AxRange = None
        self.AxTick       = None
        self.AxTickStart  = None
        self.AxTickStop   = None
        self.exponent     = 0
    
    def ViewPortSocket(self, xmin, xmax, tick, tickstart):
        self.View_AxMin   = xmin
        self.View_AxMax   = xmax
        self.View_AxRange = xmax - xmin
        self.AxTick       = tick
        self.AxTickStart  = tickstart
        self.AxTickStop   = self.AxTickStart + np.floor((self.View_AxMax - self.AxTickStart) / self.AxTick) * self.AxTick
        self.engFormat(start = self.AxTickStart, stop = self.AxTickStop)
        self.update()

    def paintEvent(self, event):
        if self.AxTick is None or self.View_AxRange is None or self.View_AxRange == 0:
            return
        super().paintEvent(event)

        axpainter = QPainter(self)

        axpainter.fillRect(self.rect(), QColor(30, 30, 30))
        axpainter.setPen(QPen(QColor(200, 200, 200), 2))
        axpainter.setRenderHint(QPainter.Antialiasing, True)

        Current_AxTick_Value = self.AxTickStart - self.AxTick
        XPxTick = self.AxTick * (self.width() - 2 * padding) / self.View_AxRange
        XPxTickStart = (self.AxTickStart - self.View_AxMin) * (self.width() - 2 * padding) / self.View_AxRange + padding

        axpainter.drawLine(
                padding, 0,
                self.width() - padding, 0
            )
        axpainter.setPen(QPen(QColor(200, 200, 200), 0.5))
        
        Current_AxTick_Px = XPxTickStart - XPxTick
        # count = 0
        while True:
            if Current_AxTick_Px > self.width() :
                break
            axpainter.drawLine(
                Current_AxTick_Px, 0,
                Current_AxTick_Px, self.height()//3
            )
            font = QFont("Arial", 7)
            axpainter.setFont(font)
            axpainter.drawText(
                QRect(
                    Current_AxTick_Px - 40,
                    self.height()//3 + 2,
                    80,
                    20
                ),
                Qt.AlignHCenter,
                self.engFormat(value = Current_AxTick_Value)
            )

            for count in range (9):
                subTick = float(Current_AxTick_Px + (count + 1) * XPxTick / 10)
                axpainter.drawLine(
                    subTick, 0,
                    subTick, self.height() // 7
                )

            Current_AxTick_Px += XPxTick
            Current_AxTick_Value += self.AxTick
            if abs(Current_AxTick_Value/self.AxTick) <= 1e-6 : Current_AxTick_Value = 0

    def engFormat(self, value = None, start = None, stop = None):
        prefixes = {
            -15: 'f',
            -12: 'p',
            -9 : 'n',
            -6 : 'u',
            -3 : 'm',
            0  :  '',
            3  : 'k',
            6  : 'M',
            9  : 'G',
            12 : 'T'
        }

        if value == 0:
            return "0"

        if start == 0:
            self.exponent = 0
            if stop != 0:
                stopex = (int(np.floor(np.log10(abs(stop )))) // 3) * 3
                if stopex > 0: self.exponent = stopex
        
        if (start is not None) and (stop is not None):
            if start == 0: self.exponent = 0
            elif start != 0: self.exponent = (int(np.floor(np.log10(abs(start)))) // 3) * 3

            if stop  == 0: stopex = 0
            elif stop  != 0: stopex        = (int(np.floor(np.log10(abs(stop )))) // 3) * 3

            if (stop == 0): pass
            elif (start ==  0): self.exponent = stopex
            elif (stopex > self.exponent): self.exponent = stopex
            
            self.exponent = max(min(self.exponent, 12), -15)

        if value is not None:
            scaled = value / (10 ** self.exponent)
            return f"{scaled:g}{prefixes[self.exponent]}"

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.GlobalAxsResize.emit(self.width() - 2 * padding) # <--------- Commented out!


class GlobalPreView(QWidget):
    PreViewResize = Signal(float, float)
    XPortCommand  = Signal(float, float)

    def __init__(self, Parent, PaneManager : PaneManager):
        super().__init__()
        self.setParent(Parent)
        self.PaneManager = PaneManager
        self.xpos        = 0
        self.LeftEdge    = 0
        self.RightEdge   = self.width()
        self.LeftEdit    = False
        self.RightEdit   = False
        self.Hold        = False
        self.Click       = False
        self.setMouseTracking(True)
    
    def paintEvent(self, event):
        print("PREVIEW WIDTH", self.width())
        super().paintEvent(event)
        
        PrevPainter = QPainter(self)
        PrevPainter.setRenderHint(QPainter.Antialiasing)
        PrevPainter.fillRect(self.rect(), QColor(35, 35, 35))
        
        rectangle = QRect(padding, 0,
                          (self.width() - 2 * padding), self.height()
                        )
        
        for Trace in self.PaneManager.Panes[self.PaneManager.CurrentPane].Canvas.PreViewTraceMap:
            print("TRACEWIDTH =", Trace.width())
            PrevPainter.drawPixmap(rectangle, Trace)
        
        Vxmin          = self.PaneManager.Panes[0].ViewPort.View_XMin
        Axmin          = self.PaneManager.Panes[0].ViewPort.Abs_XMin
        Vxmax          = self.PaneManager.Panes[0].ViewPort.View_XMax
        Axrng          = self.PaneManager.Panes[0].ViewPort.Abs_XRng
        self.LeftEdge  = (self.width() - 2 * padding) * (Vxmin - Axmin) / Axrng + padding
        self.RightEdge = (self.width() - 2 * padding) * (Vxmax - Axmin) / Axrng + padding
        w              = max(self.RightEdge - self.LeftEdge, 10)
        h              = self.height()

        PrevPainter.setPen(QPen(QColor(255, 255, 255, 60), 1))
        PrevPainter.setBrush(QColor(50, 50, 50, 160))
        PrevPainter.drawRect(self.LeftEdge, 0, w, h)
        PrevPainter.end()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()
        self.PreViewResize.emit(self.height(), self.width()) # <------ Commented out!

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        Mouse_Pos = event.position()
        prevPos   = self.xpos
        self.xpos = Mouse_Pos.x()

        if ((self.xpos > self.LeftEdge - 3) and (self.xpos < self.LeftEdge + 3)) or ((self.xpos > self.RightEdge - 3) and (self.xpos < self.RightEdge + 3)):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        
        elif ((self.xpos > self.LeftEdge + 3) and (self.xpos < self.RightEdge - 3)):
            if (not self.LeftEdit) and (not self.RightEdit):
                if not self.Hold: self.setCursor(Qt.CursorShape.OpenHandCursor)
                else: self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            if not self.Click: self.setCursor(Qt.CursorShape.ArrowCursor)

        if self.LeftEdit:
            Axrng          = self.PaneManager.Panes[0].ViewPort.Abs_XRng
            Axmin          = self.PaneManager.Panes[0].ViewPort.Abs_XMin
            xmax           = self.PaneManager.Panes[0].ViewPort.View_XMax
            self.LeftEdge  = max(min(self.xpos, (self.width() - padding - 10)), padding)
            self.RightEdge = (self.width() - 2 * padding) * (xmax - Axmin) / Axrng + padding
            xmin           = (self.LeftEdge - padding) * Axrng / (self.width() - 2 * padding) + Axmin
            if self.LeftEdge >= self.RightEdge - 10:
                self.RightEdge = self.LeftEdge + 10
                xmax           = (self.RightEdge - padding) * Axrng / (self.width() - 2 * padding) + Axmin
            
            self.XPortCommand.emit(xmin, xmax)
            self.update()
        
        if self.RightEdit:
            Axrng          = self.PaneManager.Panes[0].ViewPort.Abs_XRng
            Axmin          = self.PaneManager.Panes[0].ViewPort.Abs_XMin
            xmin           = self.PaneManager.Panes[0].ViewPort.View_XMin
            self.RightEdge = min(max(self.xpos, 10 + padding), (self.width() - padding))
            self.LeftEdge  = (self.width() - 2 * padding) * (xmin - Axmin) / Axrng + padding
            xmax           = (self.RightEdge - padding) * Axrng / (self.width() - 2 * padding) + Axmin
            if self.RightEdge <= self.LeftEdge + 10:
                self.LeftEdge = self.RightEdge - 10
                xmin          = (self.LeftEdge - padding) * Axrng / (self.width() - 2 * padding) + Axmin
            
            self.XPortCommand.emit(xmin, xmax)
            self.update()
        
        if self.Hold:
            dx = self.xpos - prevPos
            if (dx > 0):
                shiftx          = min(dx, (self.width() - padding) - self.RightEdge)
                self.RightEdge += shiftx
                self.LeftEdge  += shiftx
            else:
                shiftx          = min(-dx, self.LeftEdge - padding)
                self.RightEdge -= shiftx
                self.LeftEdge  -= shiftx

            Axrng = self.PaneManager.Panes[0].ViewPort.Abs_XRng
            Axmin = self.PaneManager.Panes[0].ViewPort.Abs_XMin
            xmin  = (self.LeftEdge - padding) * Axrng / (self.width() - 2 * padding) + Axmin
            xmax  = (self.RightEdge - padding) * Axrng / (self.width() - 2 * padding) + Axmin
            self.XPortCommand.emit(xmin, xmax)
            self.update()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        Mouse_Pos  = event.position()
        self.xpos  = Mouse_Pos.x()
        self.Click = True
        if ((self.xpos > self.LeftEdge - 3) and (self.xpos < self.LeftEdge + 3)): self.LeftEdit = True
        else: self.LeftEdit = False
        if ((self.xpos > self.RightEdge - 3) and (self.xpos < self.RightEdge + 3)): self.RightEdit = True
        else: self.RightEdit = False
        if ((self.xpos > self.LeftEdge + 3) and (self.xpos < self.RightEdge - 3)):
            self.Hold = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else: self.Hold = False
    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.Hold:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.LeftEdit  = False
        self.RightEdit = False
        self.Hold      = False
        self.Click     = False


class GlobalCursorManager(QObject):
    inspect    = Signal(object)
    delete     = Signal()
    fitCommand = Signal()

    def __init__(self, ParentWidget : QWidget, ViewPort : GlobalViewPort, PaneManager : PaneManager):
        super().__init__()
        self.ParentWidget  = ParentWidget
        self.ViewPort      = ViewPort
        self.PaneManager   = PaneManager
        self.Cursors       = {}
        self.CursorCount   = 0
        self.CurrentId     = 0
        self.HeldCurs      = {}
        self.CurrentCursor = None
        self.AppendMode    = False
        self.ParentWidget.installEventFilter(self)
    
    def eventFilter(self, watched, event):
        if watched == self.ParentWidget and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key_Shift:
                self.AppendMode = True
            if event.key() == Qt.Key_Delete:
                self.delete.emit()
                Nheld = len(self.HeldCurs)
                self.CursorCount -= Nheld
                for key in self.HeldCurs.keys():
                    self.Cursors.pop(key)
                self.HeldCurs = {}
                self.inspect.emit(self.HeldCurs)
        
        if watched == self.ParentWidget and event.type() == QEvent.Type.KeyRelease:
            if event.key() == Qt.Key_Shift:
                self.AppendMode = False
        
        return super().eventFilter(watched, event)

    def AddCursor(self, global_pos):
        cursor    = GlobalCursor(self.ParentWidget, self.ViewPort, self.PaneManager)
        cursor.id = self.CursorCount
        cursor.UpdatePosition(global_pos - QPoint(cursor.width() // 2, 0))
        self.SignalManager(cursor)

        for c in self.Cursors.values():
            c.Release()

        self.Cursors[self.CursorCount] = cursor
        self.CursorCount += 1

        cursor.show()

        self.HeldCurs = {cursor.id : global_pos}
        self.inspect.emit(self.HeldCurs)
    
    def HoldCursor(self, cursId, hover = False):
        GlobalPosition = self.Cursors[cursId].mapToGlobal(QPointF(self.Cursors[cursId].width() // 2, 0))
        canvx_position = self.PaneManager.Panes[0].Canvas.mapFromGlobal(GlobalPosition).x()

        if hover:
            self.Cursors[cursId].Hold(hover)
            if cursId not in self.HeldCurs.keys():
                if (padding < canvx_position < self.PaneManager.Panes[0].Canvas.width() - padding):
                    self.HeldCurs.update(
                        {cursId : GlobalPosition}
                    )
                self.inspect.emit(self.HeldCurs)
        
        elif self.AppendMode:
            self.Cursors[cursId].Hold(hover)
            if cursId not in self.HeldCurs.keys():
                if (padding < canvx_position < self.PaneManager.Panes[0].Canvas.width() - padding):
                    self.HeldCurs.update(
                        {cursId : GlobalPosition}
                    )
                self.inspect.emit(self.HeldCurs)
        
        else:
            for cursor in self.Cursors.values():
                cursor.Release(hover)
            
            self.Cursors[cursId].Hold(hover)
            if (padding < canvx_position < self.PaneManager.Panes[0].Canvas.width() - padding):
                self.HeldCurs = {cursId : self.Cursors[cursId].mapToGlobal(QPoint(self.Cursors[cursId].width() // 2, 0))}

            self.inspect.emit(self.HeldCurs)
    
    def ReleaseCursor(self, cursId = None, hover = False):
        if hover:
            self.Cursors[cursId].Release(hover)
            self.HeldCurs.pop(cursId, None)
        else:
            for cursor in self.Cursors.values():
                cursor.Release(hover)
            self.HeldCurs = {}
        self.inspect.emit(self.HeldCurs)

    def DragCursor(self, global_pos, cursID):
        canvx_position = self.PaneManager.Panes[0].Canvas.mapFromGlobal(global_pos).x()
        if (1 < canvx_position < self.PaneManager.Panes[0].Canvas.width() - 1):
            self.Cursors[cursID].UpdatePosition(QPointF(global_pos.x() - self.Cursors[cursID].width() // 2, global_pos.y()))
        
        if (padding < canvx_position < self.PaneManager.Panes[0].Canvas.width() - padding): self.HeldCurs[cursID] = global_pos
        elif cursID in self.HeldCurs.keys(): self.HeldCurs.pop(cursID)
        self.inspect.emit(self.HeldCurs)

    def ViewPortSocket(self):
        for id, cursor in self.Cursors.items():
            cursor.ViewPortSocket()
            global_position = cursor.mapToGlobal(QPointF(cursor.width() // 2, 0))
            canvx_position  = self.PaneManager.Panes[0].Canvas.mapFromGlobal(global_position).x()

            if id in self.HeldCurs.keys():
                if (padding < canvx_position < self.PaneManager.Panes[0].Canvas.width() - padding):
                    self.HeldCurs[id] = global_position
                else: self.HeldCurs.pop(id)
            
            elif cursor.Select and (padding < canvx_position < self.PaneManager.Panes[0].Canvas.width() - padding):
                self.HeldCurs.update({id : global_position})
        
        self.inspect.emit(self.HeldCurs)
    
    def SignalManager(self, cursor : GlobalCursor):
        cursor.selected  .connect(self.HoldCursor   )
        cursor.CursDrag  .connect(self.DragCursor   )
        cursor.released  .connect(self.ReleaseCursor)
        cursor.fitCommand.connect(lambda: self.fitCommand.emit())
        self  .delete    .connect(cursor.Cleanup    )
        self  .inspect   .connect(lambda held: self.PaneManager.GlobalCursorData.emit(held))
        self  .PaneManager.CursorUpddate.connect(cursor.HELPERSelectedEmit)


class GlobalCursor(QWidget):
    selected   = Signal(int, bool)
    released   = Signal(int, bool)
    CursDrag   = Signal(object, int)
    fitCommand = Signal()

    def __init__(self, parent : QWidget, ViewPort : GlobalViewPort, PaneManager : PaneManager):
        super().__init__(parent)
        self.ParentWidget = parent
        self.ViewPort     = ViewPort
        self.PaneManager  = PaneManager
        self.id           = 0
        self.Select       = True
        self.HoverSelect  = False
        self.Drag         = False
        self.setFixedWidth(8)
        self.setFixedHeight(parent.height())
        self.setMouseTracking(True)
        self.setFocus()
        parent.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched == self.parent() and event.type() == QEvent.Type.Resize:
            self.setFixedHeight(watched.height())
            # self.selected.emit(self.id, self.HoverSelect)
        return super().eventFilter(watched, event)

    def paintEvent(self, event):
        Cpainter = QPainter(self)
        Cpainter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pixelRatio = self.devicePixelRatioF()

        Cpen1 = QPen(QColor(200, 200, 200), 2, Qt.DashLine)
        Cpen2 = QPen(QColor(200, 200, 200), 1, Qt.DashLine)

        Cpen1.setCosmetic(True)
        Cpen2.setCosmetic(True)

        if self.Select: Cpainter.setPen(Cpen1)
        elif self.HoverSelect: Cpainter.setPen(Cpen1)
        else: Cpainter.setPen(Cpen2)

        physical_mid_x = round((self.width() / 2.0) * pixelRatio)
        logical_mid_x = physical_mid_x / pixelRatio

        Cpainter.drawLine(
            QPointF(logical_mid_x, 6),
            QPointF(logical_mid_x, float(self.height() - padding + 1))
        )
        Cpainter.end()

    def Hold(self, hover = False):
        if hover: self.HoverSelect = True
        else: self.Select = True
        self.update()

    def Release(self, hover = False):
        if hover: self.HoverSelect = False
        else: self.Select = False
        self.update()

    def UpdatePosition(self, GlobalPosition):
        self.LocalPosition  = self.ParentWidget.mapFromGlobal(GlobalPosition).x()
        self.CanvasPosition = self.PaneManager.Panes[0].Canvas.mapFromGlobal(GlobalPosition).x() + self.width() // 2
        self.AxisPosition   = self.ViewPort.View_XMin + (self.CanvasPosition - padding) * self.ViewPort.View_XRng / (self.PaneManager.Panes[0].Canvas.width() - 2 * padding)

        self.move(self.LocalPosition, 0)

    def ViewPortSocket(self):
        self.CanvasPosition = (self.AxisPosition - self.ViewPort.View_XMin) * (self.PaneManager.Panes[0].Canvas.width() - 2 * padding) / self.ViewPort.View_XRng + padding
        GlobalPosition      = self.PaneManager.Panes[0].Canvas.mapToGlobal(QPointF(self.CanvasPosition, 0))
        self.LocalPosition  = self.ParentWidget.mapFromGlobal(GlobalPosition).x() - self.width() // 2

        self.move(self.LocalPosition, 0)

    def Cleanup(self):
        if self.Select:
            parent_widget = self.parent()
            if parent_widget is not None:
                parent_widget.removeEventFilter(self)
            self.deleteLater()

    def enterEvent(self, event):
        super().enterEvent(event)
        self.setFocus()
        self.HoverSelect = True
        self.selected.emit(self.id, True)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.clearFocus()
        self.HoverSelect = False
        if not self.Select:
            self.released.emit(self.id, True)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.Select = True
        self.Drag = True
        self.selected.emit(self.id, False)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.Drag = False

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.setCursor(Qt.CursorShape.SizeHorCursor)
        if self.Drag:
            global_pos = QCursor.pos()
            self.CursDrag.emit(global_pos, self.id)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            if self.Select: self.Cleanup()
            print("Delete")
        if event.key() == Qt.Key_F:
            self.fitCommand.emit()

    def HELPERSelectedEmit(self):
        self.selected.emit(self.id, self.HoverSelect)


class PaneManager(QObject):
    GlobalSignalAdded = Signal(object)
    Split             = Signal()
    Combine           = Signal()
    PreViewResize     = Signal(float, float)
    SelectBroadCast   = Signal(int)
    XPortBroadCast    = Signal(object, object, object, object, object, bool)
    PreViewUpdate     = Signal()
    AddGlobalCursor   = Signal(object)
    CursorRelease     = Signal()
    GlobalCursorData  = Signal(object)
    CursorUpddate     = Signal()
    RlsHltBroadCast   = Signal()
    XZoomEnable       = Signal(bool)
    YZoomEnable       = Signal(bool)
    XZoomBroadCast    = Signal(object, object)
    XZoomStartBDC     = Signal(bool)
    listScrollBDC     = Signal(object)

    def __init__(self, WaveWidget : GlobalWaveWidget, ListWidget : QWidget, GlobalViewModel : GlobalViewModel, Splitter : QSplitter):
        super().__init__()
        self.GlobalViewModel = GlobalViewModel
        self.WaveWidget      = WaveWidget
        self.ListWidget      = ListWidget
        self.GlobalSplitter  = Splitter
        self.ListSplitter    = QSplitter(Qt.Orientation.Vertical)
        self.Panes           = []
        self.Lists           = []
        self.NPanes          = 0
        self.CurrentPane     = 0
        self.SignalManager()
        self.ListSplitterConfig()
        self.AddPane(self.CurrentPane)
    
    def InsertSignal(self, Signals, PaneId = None):
        print("Signal Insert")
        id = PaneId if PaneId is not None else self.CurrentPane
        self.Panes[id].ViewModel.AddPaneSignal(*Signals)
        self.PreViewUpdate.emit()

    def RemoveSignal(self, Signals, PaneId = None):
        ToRemIDs = []
        id = PaneId if PaneId is not None else self.CurrentPane
        for signal in Signals:
            GlobalID = signal.Global_ID
            for trace in self.Panes[id].ViewModel.PaneSignals:
                if trace.Global_ID == GlobalID: ToRemIDs.append(trace.Local_ID)

        self.Panes[id].ViewModel.RemovePaneSignal(ByIDs = True, IDs = ToRemIDs)
        self.ListSplitter.splitterMoved.connect(lambda pos, index: self.WaveWidget.Splitter.setSizes(self.ListSplitter.sizes()))
        self.WaveWidget.Splitter.splitterMoved.connect(lambda pos, index: self.ListSplitter.setSizes(self.WaveWidget.Splitter.sizes()))

    def AddPane(self, index, ViewModel = None, ViewPort = None):
        Pane = WavePane(index, self.GlobalViewModel, ViewModel = ViewModel, ViewPort = ViewPort, WaveWidget = self.WaveWidget)
        if ViewPort is None:
            Pane.ViewPort.SetAxisSocket(self.GlobalViewModel.Axis)
        Pane.Widget.setParent(self.WaveWidget)
        self.Panes.insert(index, Pane)
        self.NPanes += 1

        for idx, pane in enumerate(self.Panes):
            pane.PaneID = idx
        
        self.CurrentPane = index
        self.WaveWidget.Splitter.insertWidget(index, Pane.Widget)
        self.PaneSignalManager(Pane)
        self.AddSignalListPane(index, Pane.ViewModel)
        Pane.Canvas.ViewPortUpdate.emit(Pane.Canvas.width() - 2 * padding, Pane.Canvas.height() - 2 * padding)

    def AddSignalListPane(self, index, ViewModel = None):
        ListPane = SignalListPane(index, ViewModel)
        self.ListSplitter.insertWidget(index, ListPane.Widget)
        self.Lists.insert(index, ListPane)

        for idx, List in enumerate(self.Lists):
            List.ListID = idx

        if index == self.NPanes - 1:
            ListPane.MasterEnable()
            if self.NPanes >= 2:
                self.Lists[index - 1].MasterDisable()

        self.ListSignalManager(ListPane)

    def RemovePane(self, PaneID):
        if len(self.Panes) <= 1:
            return
        
        self.Panes[PaneID].Cleanup()
        self.Panes.pop(PaneID)
        self.RemoveSignalListPane(PaneID)
        for i, Pane in enumerate(self.Panes):
            Pane.PaneID            = i
            Pane.Canvas.PaneID     = i
            Pane.Axis.PaneID       = i
            Pane.Widget.PaneID     = i
            Pane.HitTest.PaneID    = i
            Pane.Controller.PaneID = i
        self.NPanes -= 1
        if self.CurrentPane >= self.NPanes: self.CurrentPane -= 1

    def RemoveSignalListPane(self, PaneID):
        if len(self.Lists) <= 1:
            return
        
        if PaneID == self.NPanes - 1:
            self.Lists[PaneID - 1].MasterEnable()

        self.Lists[PaneID].MasterDisable()
        self.Lists[PaneID].Cleanup()
        self.Lists.pop(PaneID)
        for i, list in enumerate(self.Lists):
            list.PaneID = i

    def SplitPanes(self):
        if len(self.GlobalViewModel.GlobalSignals) <= 1:
            return

        CanvasWidth = self.Panes[0].Canvas.width()
        xmin = self.Panes[0].ViewPort.View_XMin
        xmax = self.Panes[0].ViewPort.View_XMax
        RemPanes = []
        RemLists = []
        for Pane in self.Panes:
            Pane.Canvas.ReSizeEnable = False
        
        for pane in self.Panes:
            RemPanes.append(pane)
            # pane.Cleanup()
            pane.Widget.hide()

        self.Lists[-1].MasterDisable()
        for listPane in self.Lists:
            RemLists.append(listPane)
            # listPane.Cleanup()
            listPane.Widget.hide()

        self.Lists.clear()
        self.Panes.clear()
        self.NPanes = 0
        i = 0
        for Signal in self.GlobalViewModel.GlobalSignals.values():
            ViewModel = PaneViewModel(i)
            ViewModel.AddPaneSignal(Signal)

            ViewPort = PaneViewPort()
            ViewPort.SetAxisSocket(self.GlobalViewModel.Axis)
            ViewPort.PaneViewModelSocket(ViewModel.Abs_YAvg, ViewModel.Abs_YRng)
            ViewPort.View_XMin = xmin
            ViewPort.View_XMax = xmax
            ViewPort.update()

            Pane = WavePane(i, self.GlobalViewModel, ViewModel, ViewPort, self.WaveWidget, width = CanvasWidth)
            ListPane = SignalListPane(i, ViewModel)
            Pane.Canvas.ReSizeEnable = False
            self.WaveWidget.Splitter.addWidget(Pane.Widget)
            self.ListSplitter.addWidget(ListPane.Widget)
            self.Panes.append(Pane)
            self.Lists.append(ListPane)
            self.PaneSignalManager(Pane)
            self.ListSignalManager(ListPane)
            self.NPanes += 1
            i += 1
        
        for Pane in self.Panes:
            Pane.Canvas.ReSizeEnable = True
            Pane.Canvas.ViewPortUpdate.emit((Pane.Canvas.width() - 2 * padding), (Pane.Canvas.height() - 2 * padding))
            Pane.Canvas.ReBuildGridMap()
            Pane.Canvas.ReBuildTraceMap()
            Pane.Canvas.ReBuildPreViewMap()

        self.Lists[-1].MasterEnable()
        self.CurrentPane = 0
        self.PreViewUpdate.emit()
        self.Split.emit()

        QTimer.singleShot(0, lambda: self.QueuedCleanup(RemPanes))
        QTimer.singleShot(0, lambda: self.QueuedCleanup(RemLists))

    def CombPanes(self):
        t = time.perf_counter()
        if self.NPanes <= 1:
            return
        xmin = self.Panes[0].ViewPort.View_XMin
        xmax = self.Panes[0].ViewPort.View_XMax
        
        ViewModel = PaneViewModel(0)
        signals = []
        for sig in self.GlobalViewModel.GlobalSignals.values():
            signals.append(sig)
        ViewModel.AddPaneSignal(*signals)
        
        ViewPort = PaneViewPort()
        ViewPort.SetAxisSocket(self.GlobalViewModel.Axis)
        ViewPort.PaneViewModelSocket(ViewModel.Abs_YAvg, ViewModel.Abs_YRng)
        ViewPort.View_XMin = xmin
        ViewPort.View_XMax = xmax
        ViewPort.update()

        self.WaveWidget.Splitter.setUpdatesEnabled(False)
        self.ListSplitter.setUpdatesEnabled(False)

        RemPanes = []
        for Pane in self.Panes:
            Pane.Canvas.ReSizeEnable = False
            Pane.Widget.hide()
            RemPanes.append(Pane)
        self.Panes.clear()
        self.NPanes = 0

        RemLists = []
        self.Lists[-1].MasterDisable()
        for ListPane in self.Lists:
            ListPane.Widget.hide()
            RemLists.append(ListPane)
        self.Lists.clear()

        self.AddPane(0, ViewModel, ViewPort)

        self.WaveWidget.Splitter.setUpdatesEnabled(True)
        self.ListSplitter.setUpdatesEnabled(True)
        self.Combine.emit()

        QTimer.singleShot(0, lambda: self.QueuedCleanup(RemPanes))
        QTimer.singleShot(0, lambda: self.QueuedCleanup(RemLists))

    def ListSplitterConfig(self):
        ListLayout = QVBoxLayout(self.ListWidget)
        ListLayout.setContentsMargins(0, 0, 0, 0)
        ListLayout.setSpacing(0)
        ListLayout.addWidget(self.ListSplitter)
        self.ListSplitter.setChildrenCollapsible(False)

    def UpdateList(self, ListID):
        self.Lists[ListID].ReconfigureView()

    def PaneSignalManager(self, Pane : WavePane):
        Pane.PaneSelected                  .connect(lambda              : setattr(self, 'CurrentPane', Pane.PaneID  ))
        Pane.PaneSelected                  .connect(lambda              : self.SelectBroadCast.emit(self.CurrentPane))
        self.SelectBroadCast               .connect(lambda CurrentPaneID: setattr(Pane, 'CurrentPane', CurrentPaneID))
        self.SelectBroadCast               .connect(Pane.Canvas.HELPERSetActive)
        self.SelectBroadCast               .connect(Pane.Axis  .HELPERSetActive)

        Pane.ViewPort  .XPortCommand       .connect(lambda min, max, rng, tick, tickstart, fit: self.XPortBroadCast.emit(min, max, rng, tick, tickstart, fit))

        self.XPortBroadCast                .connect(Pane.ViewPort.XPortRespond)

        # Pane.ViewModel .GlobalSignalRemoved.connect(self.GlobalViewModel.RemoveGlobalSignal)
        Pane.ViewModel .UpdateList         .connect(self.UpdateList)
        Pane.ViewModel .Empty              .connect(lambda     : self.RemovePane(Pane.PaneID)  )
        Pane.ViewPort  .PreViewUpdate      .connect(lambda     : self.PreViewUpdate.emit()     )
        Pane.Canvas    .PreViewUpdate      .connect(lambda     : self.PreViewUpdate.emit()     )
        Pane.Canvas    .CurserUpdate       .connect(lambda     : self.CursorUpddate.emit()     )
        Pane.Controller.AddGlobalCursor    .connect(lambda    x: self.AddGlobalCursor.emit(x)  )
        Pane.Controller.CursorRelease      .connect(lambda     : self.CursorRelease.emit()     )
        Pane.Controller.ReleaseHighlight   .connect(lambda     : self.RlsHltBroadCast.emit()   )
        Pane.Controller.XZoomEnable        .connect(lambda    l: self.XZoomEnable.emit(l)      )
        Pane.Controller.YZoomEnable        .connect(lambda    l: self.YZoomEnable.emit(l)      )
        Pane.Controller.XZoomCommand       .connect(lambda x, y: self.XZoomBroadCast.emit(x, y))
        Pane.Controller.XZoomStart         .connect(lambda    l: self.XZoomStartBDC.emit(l)    )

        self.PreViewResize                 .connect(lambda h, w: setattr(Pane.Canvas, 'PreViewHeight', h))
        self.PreViewResize                 .connect(lambda h, w: setattr(Pane.Canvas, 'PreViewWidth' , w))
        self.XZoomEnable                   .connect(lambda    l: setattr(Pane.Canvas, 'XZoom'        , l))
        self.YZoomEnable                   .connect(lambda    l: setattr(Pane.Canvas, 'YZoom'        , l))

        # self.PreViewResize                 .connect(Pane.Canvas   .ReBuildPreViewMap  )
        self.GlobalSignalAdded             .connect(Pane.ViewModel.AddPaneSignal      )
        self.GlobalCursorData              .connect(Pane.VCursorEngine.Configure      )
        self.RlsHltBroadCast               .connect(Pane.Canvas.HELPERClearHitResults )
        self.RlsHltBroadCast               .connect(Pane.Canvas.update                )
        self.XZoomBroadCast                .connect(Pane.Controller.HELPERXZoomRespond)
        self.XZoomStartBDC                 .connect(Pane.Controller.HELPERXZoomStart  )

    def ListSignalManager(self, ListPane : SignalListPane):
        ListPane.Widget.horizontalScrollBar().valueChanged.connect(lambda v:self.listScrollBDC.emit(v))
        self.listScrollBDC.connect(ListPane.ScrollConfig)
        self.ListSplitter.splitterMoved.connect(lambda pos, index: self.WaveWidget.Splitter.setSizes(self.ListSplitter.sizes()))
        self.WaveWidget.Splitter.splitterMoved.connect(lambda pos, index: self.ListSplitter.setSizes(self.WaveWidget.Splitter.sizes()))

    def SignalManager(self):
        self.WaveWidget.SetCurrentPane.connect(lambda idx: setattr(self, 'CurrentPane', idx))
        self.WaveWidget.InsertSignals .connect(self.InsertSignal)
        self.WaveWidget.RemoveSignals .connect(self.RemoveSignal)
        self.WaveWidget.AddPane       .connect(self.AddPane     )

    def QueuedCleanup(self, toRemove):
        for pane in toRemove:
            pane.Cleanup()


class WavePane(QObject):
    ##====================================================================
    # Parent class for all informations and objects related to a wave pane
    ##====================================================================
    PaneSelected = Signal()
    
    def __init__(self, PaneID, GlobalViewModel : GlobalViewModel, ViewModel = None, ViewPort = None, WaveWidget = None, width = None):
        super().__init__()
        if Debug: print("WavePane init")
        self.PaneID        = PaneID
        self.CurrentPane   = 0
        self.WaveWidget    = WaveWidget
        self.GlobViewModel = GlobalViewModel
        if ViewModel is None:
            self.ViewModel = PaneViewModel(self.PaneID)
        else:
            self.ViewModel = ViewModel
        if ViewPort is None:
            self.ViewPort  = PaneViewPort()
        else:
            self.ViewPort  = ViewPort
        self.Canvas        = PaneCanvas(self.PaneID, self.GlobViewModel, self.ViewModel.PaneSignals, self.ViewPort, width)
        self.Axis          = PaneAxis(self.PaneID, self.ViewPort)
        self.Widget        = PaneWidget(self.PaneID, self.Canvas, self.Axis, self.ViewPort)
        self.HitTest       = HitTest(self.PaneID, self.ViewModel.PaneSignals, self.ViewPort, self.Canvas)
        self.Controller    = PaneController(self.PaneID, self.ViewModel, self.ViewPort, self.Canvas, self.HitTest, self.WaveWidget)
        self.VCursorEngine = VCursorEngine(self.ViewPort, self.Canvas, self.HitTest)

        self.SignalManager()

    def SignalManager(self):
        self.GlobViewModel   .SetAxis           .connect(self.ViewPort.SetAxisSocket)
        
        self.ViewModel       .LocalSignalRemoved.connect(lambda: setattr(self.Canvas, 'PointerFlag', False))
        self.ViewModel       .LocalSignalRemoved.connect(lambda:     self.Controller.HoverWidget.hide()    )

        self.ViewModel       .LocalSignalRemoved.connect(self.Canvas.HitResult.HELPERReset )
        self.ViewModel       .LocalSignalRemoved.connect(self.HitTest.HitResult.HELPERReset)
        self.ViewModel       .LocalSignalAdded  .connect(self.ViewPort.PaneViewModelSocket )
        self.ViewModel       .LocalSignalRemoved.connect(self.ViewPort.PaneViewModelSocket )

        self.HitTest         .HitBroadCast      .connect(lambda hresult: setattr(self.ViewModel , 'HitResult'    , hresult))
        self.HitTest         .HitBroadCast      .connect(lambda hresult: setattr(self.Canvas    , 'HitResult'    , hresult))
        self.ViewPort        .PanePortSignal    .connect(lambda        : setattr(self.Axis      , 'RefreshAxis'  , True   ))
        
        self.ViewPort        .PanePortSignal    .connect(self.Canvas          .Configure )
        self.ViewPort        .PanePortSignal    .connect(self.Axis            .update    )
        self.ViewPort        .YPortCommand      .connect(self.Widget.ScrollBar.PortSocket)

        self.Canvas          .HitRebuild        .connect(self.HitTest   .Rebuild)
        self.Canvas          .HitRebuildAdd     .connect(self.HitTest   .AddTrace)
        self.Canvas          .ViewPortUpdate    .connect(lambda w, h: setattr(self.ViewPort, 'CanvWidth' , w))
        self.Canvas          .ViewPortUpdate    .connect(lambda w, h: setattr(self.ViewPort, 'CanvHeight', h))
        self.Canvas          .ViewPortUpdate    .connect(lambda     : self.ViewPort.update())


        self.Canvas          .ControlEvent      .connect(self.Controller.EventHandle)
        self.Widget.ScrollBar.ScrollCommand     .connect(self.ViewPort.ScrollRespond)

        self.Controller      .PaneSelected      .connect(lambda: self.PaneSelected.emit())
        self.HitTest         .FieldEmit         .connect(lambda field: setattr(self.Canvas, 'FieldMatrix', field))
        self.ViewPort        .PanePortSignal    .connect(lambda: self.VCursorEngine.Configure(CursorData = {}, Reconfigure = True))
    
    def Cleanup(self):
        self.ViewModel .deleteLater()
        self.ViewPort  .deleteLater()
        self.HitTest   .deleteLater()
        self.Controller.deleteLater()

        self.VCursorEngine._is_cleaned_up = True
        for BList in self.VCursorEngine.Bubbles.values():
            for b in BList:
                b.deleteLater()
            BList.clear()
        self.VCursorEngine.PrevData = None

        self.VCursorEngine.deleteLater()
        self.Widget       .deleteLater()


class SignalListPane(QObject):
    ListScroll = Signal(object)

    def __init__(self, ListID, ViewModel : PaneViewModel):
        super().__init__()
        self.ViewModel = ViewModel
        self.ListID    = ListID
        self.Widget    = QTreeView()
        self.model     = QStandardItemModel()
        self.rootNode  = self.model.invisibleRootItem()
        self.Master    = False
        self.Widget.setModel(self.model)
        self.StyleConfig()
        self.ReconfigureView()
        self.Widget.setFrameShape(QFrame.Shape.NoFrame)
        self.Widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.Widget.setHeaderHidden(True)

    def ReconfigureView(self):
        self.model.removeRows(0, self.model.rowCount())
        for signal in self.ViewModel.PaneSignals:
            row = [QStandardItem(str(signal.Name)), QStandardItem(str(signal.Visible))]
            self.rootNode.appendRow(row)

    def StyleConfig(self):
        style = """
            /* Style the main TreeView background and text */
            QTreeView {
                background-color: rgb(30, 30, 30);
                color: #e0e0e0;
                border: none;
                alternate-background-color: #323232;
            }

            /* Style the items when you hover over them */
            QTreeView::item:hover {
                background-color: #3d4f5c;
            }

            /* Style the items when they are clicked/selected */
            QTreeView::item:selected {
                background-color: #007acc;
                color: white;
            }
            
            /* Style header */
            QHeaderView::section {
                background-color: rgb(80, 80, 80);
                color: #ffffff;
                padding: 1px;
                border: 0px solid #444444;
            }
        """
        self.Widget.setStyleSheet(style)

        policy = self.Widget.sizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Policy.Ignored)
        self.Widget.setSizePolicy(policy)
        self.Widget.setMinimumHeight(4 * padding)

    def MasterEnable(self):
        self.Master = True
        self.Widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.Widget.horizontalScrollBar().blockSignals(False)

    def MasterDisable(self):
        self.Master = False
        self.Widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.Widget.horizontalScrollBar().blockSignals(True)

    def ScrollConfig(self, value):
        if not self.Master: self.Widget.horizontalScrollBar().setValue(value)

    def Cleanup(self):
        if self.Widget: self.Widget.deleteLater()
        self.deleteLater()


class VCursorEngine(QObject):

    @property
    def Trace(self): return np.array(self.HitTest.TraceMatrix)
    @property
    def ColorData(self): return self.HitTest.TraceData

    def __init__(self, ViewPort : PaneViewPort, CanvWidget : QWidget, HitTest : HitTest):
        super().__init__()
        self.ViewPort = ViewPort
        self.Canvas   = CanvWidget
        self.HitTest  = HitTest
        self.PrevData = None
        self.Bubbles  = {}

        self._is_cleaned_up = False
    
    def Configure(self, CursorData : dict, Reconfigure = False):
        if self._is_cleaned_up:
            return
        
        # print("CursData :", CursorData)
        if self.PrevData is None:
            for key, value in CursorData.items():
                localX = int(self.Canvas.mapFromGlobal(value).x())

                if (localX < padding or localX > self.Canvas.width() - padding): continue

                bubbleList = []
                snapList   = []
                for idx, y in enumerate(self.Trace[:, localX - padding]):
                    point = QPointF(localX, y)
                    Ysnap = 16 * ((y + padding) // 16) + 16 / 2
                    color = self.ColorData[idx]["color"]

                    if Ysnap in snapList:
                        orientation = 1
                    else:
                        snapList.append(Ysnap)
                        orientation = 0
                    bubble = ValueBubble(self.Canvas, point, Ysnap, color, self.ViewPort, V = True, Orientation = orientation)
                    bubbleList.append(bubble)
                    bubble.show()
                self.Bubbles.update({key : bubbleList})
            self.PrevData = CursorData.copy()

        elif Reconfigure:
            for BList in self.Bubbles.values():
                for b in BList:
                    b.Cleanup()
            self.Bubbles.clear()
            for key, value in self.PrevData.items():
                localX = int(self.Canvas.mapFromGlobal(value).x())

                if (localX < padding or localX > self.Canvas.width() - padding):
                    if key in self.Bubbles.keys():
                        for bubble in self.Bubbles[key]:
                            bubble.Cleanup()
                        self.Bubbles[key].clear()
                    continue

                bubbleList = []
                snapList   = []
                for idx, y in enumerate(self.Trace[:, localX - padding]):
                    point = QPointF(localX, y)
                    Ysnap = 16 * ((y + padding) // 16) + 16 / 2
                    color = self.ColorData[idx]["color"]

                    if Ysnap in snapList:
                        orientation = 1
                    else:
                        snapList.append(Ysnap)
                        orientation = 0
                    bubble = ValueBubble(self.Canvas, point, Ysnap, color, self.ViewPort, V = True, Orientation = orientation)
                    bubbleList.append(bubble)
                    bubble.show()
                self.Bubbles.update({key : bubbleList})
        
        else:
            toAdd = set(CursorData.keys()) - set(self.PrevData.keys())
            toRem = set(self.PrevData.keys()) - set(CursorData.keys())

            for id in toAdd:
                value = CursorData[id]
                localX = int(self.Canvas.mapFromGlobal(value).x())

                if (localX < padding or localX > self.Canvas.width() - padding): continue

                bubbleList = []
                snapList   = []
                for idx, y in enumerate(self.Trace[:, localX - padding]):
                    point = QPointF(localX, y)
                    Ysnap = 16 * ((y + padding) // 16) + 16 / 2
                    color = self.ColorData[idx]["color"]

                    if Ysnap in snapList:
                        orientation = 1
                    else:
                        snapList.append(Ysnap)
                        orientation = 0
                    bubble = ValueBubble(self.Canvas, point, Ysnap, color, self.ViewPort, V = True, Orientation = orientation)
                    bubbleList.append(bubble)
                    bubble.show()
                self.Bubbles.update({id : bubbleList})

            for id in toRem:
                for bubble in self.Bubbles[id]:
                    bubble.Cleanup()
                self.Bubbles.pop(id)
            
            for key, value in CursorData.items():
                localX = int(self.Canvas.mapFromGlobal(value).x())

                if (localX < padding or localX > self.Canvas.width() - padding):
                    if key in self.Bubbles.keys():
                        for bubble in self.Bubbles[key]:
                            bubble.Cleanup()
                        self.Bubbles[key].clear()
                    continue

                if value.x() != self.Bubbles[key][0].pos().x():
                    snapList = []
                    for idx, bubble in enumerate(self.Bubbles[key]):
                        localY = self.Trace[idx][localX - padding]
                        Ysnap  = 16 * ((localY + padding) // 16) + 16 / 2     # 16 is the width of the bubble widget
                        point  = QPointF(localX, localY)
                        
                        if Ysnap in snapList:
                            orientation = 1
                        else:
                            snapList.append(Ysnap)
                            orientation = 0
                        bubble.position    = point
                        bubble.Ysnap       = Ysnap
                        bubble.Orientation = orientation
                        bubble.UpdatePosition()
            
            self.PrevData = CursorData.copy()


class PaneViewModel(QObject):
    LocalSignalAdded    = Signal(float, float, bool, object)
    LocalSignalRemoved  = Signal(float, float, bool, object)
    GlobalSignalRemoved = Signal(list)
    Empty               = Signal()
    UpdateList          = Signal(int)

    def __init__(self, PaneID):
        super().__init__()
        self.PaneID       = PaneID
        self.PaneSignals  = []
        self.Pane_ID      = 0
        self.Abs_YMin     = 0
        self.Abs_YMax     = 0
        self.Abs_YRng     = 0
        self.Abs_YAvg     = 0
        self.Prev_Min     = 0
        self.Prev_Max     = 0
        self.LocalIdx     = 0
        self.HitResult    = HitResult()

    def AddPaneSignal(self, *Signals):
        for sig in Signals:
            self.AddInternal(sig)
        self.LocalSignalAdded.emit(self.Abs_YAvg, self.Abs_YRng, True, None)
        self.UpdateList.emit(self.PaneID)

        # print("Adding Pane Signal at pane =", self.PaneID)
        # for sig in self.PaneSignals:
        #     print("Signal Local  ID =", sig.Local_ID)
        #     print("Signal Global ID =", sig.Global_ID)
        #     print("---")
    
    def AddInternal(self, Signal : GlobalSignalModel):
        NewSignal           = PaneSignalModel()
        NewSignal.Global_ID = Signal.Global_ID
        NewSignal.Local_ID  = self.LocalIdx
        NewSignal.Name      = Signal.name
        NewSignal.YMin      = np.min(Signal.data)
        NewSignal.YMax      = np.max(Signal.data)
        self.PaneSignals.append(NewSignal)
        self.LocalIdx += 1
        self.UpdateBounds()

    def RemovePaneSignal(self, ByIDs = False, IDs = None):
        if (not ByIDs) and len(self.HitResult.ClickedIDs) == 0:
            return

        if ByIDs: LocalIDs = IDs
        else: LocalIDs = self.HitResult.ClickedIDs

        self.PaneSignals[:] = [
            sig for sig in self.PaneSignals
            if sig.Local_ID not in LocalIDs
        ]

        if not ByIDs:
            self.HitResult.ClickedIDs.clear()
            self.HitResult.CurrentID = None
        
        for idx in range(len(self.PaneSignals)):
            self.PaneSignals[idx].Local_ID = idx
        
        self.LocalIdx -= len(LocalIDs)
        self.RecalculateBounds()
        
        self.LocalSignalRemoved.emit(self.Abs_YAvg, self.Abs_YRng, False, LocalIDs)
        # self.GlobalSignalRemoved.emit(GlobalIDs)
        if len(self.PaneSignals) == 0: self.Empty.emit()
        self.UpdateList.emit(self.PaneID)
    
    def UpdateBounds(self):
        if self.LocalIdx == 0:
            self.Abs_YMin = self.PaneSignals[-1].YMin
            self.Abs_YMax = self.PaneSignals[-1].YMax
        else:
            if self.PaneSignals[-1].YMin < self.Abs_YMin :
                self.Prev_Min = self.Abs_YMin
                self.Abs_YMin = self.PaneSignals[-1].YMin
            if self.PaneSignals[-1].YMax > self.Abs_YMax :
                self.Prev_Max = self.Abs_YMax
                self.Abs_YMax = self.PaneSignals[-1].YMax
        
        self.Abs_YAvg = (self.Abs_YMin + self.Abs_YMax) / 2
        self.Abs_YRng = (self.Abs_YMax - self.Abs_YMin)
    
    def RecalculateBounds(self):
        """Complete recalculation of bounds needed after a removal."""
        if not self.PaneSignals:
            self.Abs_YMin = 0
            self.Abs_YMax = 0
            self.Abs_YRng = 0
            self.Abs_YAvg = 0
            return
        
        self.Prev_Min = self.Abs_YMin
        self.Prev_Max = self.Abs_YMax
        self.Abs_YMin = min(sig.YMin for sig in self.PaneSignals)
        self.Abs_YMax = max(sig.YMax for sig in self.PaneSignals)
        self.Abs_YAvg = (self.Abs_YMin + self.Abs_YMax) / 2
        self.Abs_YRng = (self.Abs_YMax - self.Abs_YMin)
    
    def HighLight(self):
        for signal in self.PaneSignals:
            if signal.Local_ID in self.HitResult.ClickedIDs: signal.Highlight = True
            else: signal.Highlight = False


class PaneSignalModel:
    ##=================================================================================================================
    # Does not store the data directly, only stores a reference through the global ID and stores pane viewspecific info
    ##=================================================================================================================
    def __init__(self):
        self.Global_ID = 0
        self.Local_ID  = 0
        self.Name      = ""
        self.Visible   = True
        self.Highlight = False
        self.YMin      = 0
        self.YMax      = 0
        self.Width     = 0.8


class PaneViewPort(QObject):
    PanePortSignal  = Signal(bool, bool)
    XPortCommand    = Signal(float, float, float, float, float, bool)
    YPortCommand    = Signal()
    PreViewUpdate   = Signal()

    def __init__(self):
        super().__init__()
        self.CanvWidth  = 1180
        self.CanvHeight = 1180

        self.Axis      = None
        self.Abs_XMin  = 0.0
        self.Abs_XMax  = 1.0
        self.Abs_XRng  = 1.0
        self.Abs_YMin  = 0.0
        self.Abs_YMax  = 1.0
        self.Abs_YRng  = 1.0

        self.View_XMin = 0.0
        self.View_XMax = 1.0
        self.View_XRng = 1.0
        self.Nx        = max(np.ceil(40 * self.CanvWidth / 1180), 1)
        self.XTick     = 0.1
        self.XTickStart= 0.0

        self.View_YMin = 0.0
        self.View_YMax = 1.0
        self.View_YRng = 1.0
        self.View_YAvg = 0.5
        self.Ny        = max(np.ceil(40 * self.CanvHeight / 1180), 1)
        self.YTick     = 0.1
        self.YTickStart= 0.0

        self.XFitFlag  = True
        self.YFitFlag  = True

    def SetAxisSocket(self, axis):
        if axis is None:
            return
        self.Abs_XMin    = np.min(axis)
        self.Abs_XMax    = np.max(axis)
        self.Abs_XRng    = self.Abs_XMax - self.Abs_XMin

        self.View_XMin   = self.Abs_XMin
        self.View_XMax   = self.Abs_XMax
        self.View_XRng   = self.View_XMax - self.View_XMin

        self.Nx          = max(np.ceil(40 * self.CanvWidth / 1180), 1)
        self.XTick       = self.TickCalculator(self.View_XRng, self.Nx)
        if self.XTick   == 0:
            self.Abs_XMin  = 0.0
            self.Abs_XMax  = 10
            self.Abs_XRng  = 10
            self.View_XMin = 0.0
            self.View_XMax = 10
            self.View_XRng = 10
            self.XTick     = 1
        self.XTickStart  = int(self.View_XMin/self.XTick) * self.XTick
        self.XFitFlag    = True

    def PaneViewModelSocket(self, abs_avg, abs_range, Add = False, RemIDs = None):
        self.Abs_YMin = abs_avg - abs_range * 1.2 / 2
        self.Abs_YMax = abs_avg + abs_range * 1.2 / 2
        self.Abs_YRng = abs_range * 1.2
        
        if self.YFitFlag:
            Prev_YMin        = self.View_YMin
            Prev_YMax        = self.View_YMax
            self.View_YMin   = self.Abs_YMin
            self.View_YMax   = self.Abs_YMax
            self.View_YRng   = self.View_YMax - self.View_YMin
            self.View_YAvg   = (self.View_YMax + self.View_YMin) / 2

            self.Ny          = max(np.ceil(40 * self.CanvHeight / 1180), 1)
            self.YTick       = self.TickCalculator(self.View_YRng, self.Ny)
            if self.YTick   == 0:
                self.Abs_YMin  = 0.0
                self.Abs_YMax  = 1.0
                self.Abs_YRng  = 1.0
                self.View_YMin = 0.0
                self.View_YMax = 1.0
                self.View_YRng = 1.0
                self.View_YAvg = 0.5
                self.YTick     = 0.1
            self.YTickStart  = int(self.View_YMin/self.YTick) * self.YTick

            if (np.abs(Prev_YMin - self.View_YMin) > 0.01 * self.View_YRng or np.abs(Prev_YMax - self.View_YMax) > 0.01 * self.View_YRng):
                PortChange = True
                self.YPortCommand.emit()
            else: PortChange = False
        else: PortChange = False
        self.PanePortSignal.emit(PortChange, False)

    def RectZoomPort(self, Start, Stop):
        XMin_Prev        = self.View_XMin
        XMax_Prev        = self.View_XMax
        self.View_XMax   = self.View_XMin + max(Start.x(), Stop.x())
        self.View_XMin  += min(Start.x(), Stop.x())
        self.View_XRng   = self.View_XMax - self.View_XMin

        self.Nx          = max(np.ceil(40 * self.CanvWidth / 1180), 1)
        self.XTick       = self.TickCalculator(self.View_XRng, self.Nx)
        self.XTickStart  = int(self.View_XMin/self.XTick) * self.XTick

        YMin_Prev        = self.View_YMin
        YMax_Prev        = self.View_YMax
        self.View_YMax   = self.View_YMin + max(Start.y(), Stop.y())
        self.View_YMin  += min(Start.y(), Stop.y())
        self.View_YRng   = self.View_YMax - self.View_YMin
        self.View_YAvg   = (self.View_YMax + self.View_YMin) / 2

        self.Ny          = max(np.ceil(40 * self.CanvHeight / 1180), 1)
        self.YTick       = self.TickCalculator(self.View_YRng, self.Ny)
        self.YTickStart  = int(self.View_YMin/self.YTick) * self.YTick

        if self.View_XRng < self.Abs_XRng : self.XFitFlag = False
        if self.View_YRng < self.Abs_YRng : self.YFitFlag = False

        if ((self.View_XMin != XMin_Prev) or (self.View_XMax != XMax_Prev)):
            self.XPortCommand.emit(self.View_XMin, self.View_XMax, self.View_XRng, self.XTick, self.XTickStart, False)
            XPortChange = True
        else:
            XPortChange = False
        if ((self.View_YMin != YMin_Prev) or (self.View_YMax != YMax_Prev)):
            self.YPortCommand.emit()
        
        self.PanePortSignal.emit(True, XPortChange)
        self.PreViewUpdate.emit()

    def NavUp(self):
        # print("NavUp Called")
        if (self.View_YMax < self.Abs_YMax):
            shifty = min(self.View_YRng/10, self.Abs_YMax - self.View_YMax)
            self.View_YMax += shifty
            self.View_YMin += shifty
            self.View_YAvg  = (self.View_YMax + self.View_YMin)/2
            self.YTickStart = int(self.View_YMin/self.YTick) * self.YTick

            self.YPortCommand.emit()
            self.PanePortSignal.emit(True, False)

    def NavDn(self):
        # print("NavDn Called")
        if (self.View_YMin > self.Abs_YMin):
            shifty = min(self.View_YRng/10, self.View_YMin - self.Abs_YMin)
            self.View_YMax -= shifty
            self.View_YMin -= shifty
            self.View_YAvg  = (self.View_YMax + self.View_YMin)/2
            self.YTickStart = int(self.View_YMin/self.YTick) * self.YTick

            self.YPortCommand.emit()
            self.PanePortSignal.emit(True, False)

    def NavRt(self):
        # print("NavRt Called")
        if (self.View_XMax < self.Abs_XMax):
            shiftx = min(self.View_XRng/5, self.Abs_XMax - self.View_XMax)
            self.View_XMax += shiftx
            self.View_XMin += shiftx
            self.XTickStart = int(self.View_XMin/self.XTick) * self.XTick

            self.XPortCommand.emit(self.View_XMin, self.View_XMax, self.View_XRng, self.XTick, self.XTickStart, False)
            self.PanePortSignal.emit(True, True)
            self.PreViewUpdate.emit()

    def NavLt(self):
        # print("NavLt Called")
        if (self.View_XMin > self.Abs_XMin):
            shiftx = min(self.View_XRng/5, self.View_XMin - self.Abs_XMin)
            self.View_XMax -= shiftx
            self.View_XMin -= shiftx
            self.XTickStart = int(self.View_XMin/self.XTick) * self.XTick
            
            self.XPortCommand.emit(self.View_XMin, self.View_XMax, self.View_XRng, self.XTick, self.XTickStart, False)
            self.PanePortSignal.emit(True, True)
            self.PreViewUpdate.emit()

    def FitPort(self):
        XMin_Prev       = self.View_XMin
        XMax_Prev       = self.View_XMax
        self.View_XMin  = self.Abs_XMin
        self.View_XMax  = self.Abs_XMax
        self.View_XRng  = self.View_XMax - self.View_XMin

        self.Nx         = max(np.ceil(40 * self.CanvWidth / 1180), 1)
        self.XTick      = self.TickCalculator(self.View_XRng, self.Nx)
        self.XTickStart = int(self.View_XMin/self.XTick) * self.XTick

        YMin_Prev        = self.View_YMin
        YMax_Prev        = self.View_YMax
        self.View_YMin   = self.Abs_YMin
        self.View_YMax   = self.Abs_YMax
        self.View_YRng   = self.View_YMax - self.View_YMin
        self.View_YAvg   = (self.View_YMax + self.View_YMin) / 2

        self.Ny          = max(np.ceil(40 * self.CanvHeight / 1180), 1)
        self.YTick       = self.TickCalculator(self.View_YRng, self.Ny)
        self.YTickStart  = int(self.View_YMin/self.YTick) * self.YTick

        self.XFitFlag    = True
        self.YFitFlag    = True

        if ((self.View_XMin != XMin_Prev) or (self.View_XMax != XMax_Prev)):
            self.XPortCommand.emit(self.View_XMin, self.View_XMax, self.View_XRng, self.XTick, self.XTickStart, True)
            print("XPortCommand")
            XPortChange = True
        else:
            XPortChange = False

        if ((self.View_YMin != YMin_Prev) or (self.View_YMax != YMax_Prev)):
            self.YPortCommand.emit()

        self.PanePortSignal.emit(True, XPortChange)
        self.PreViewUpdate.emit()

    def XPortRespond(self, xmin = 0, xmax = 10, xrng = 10, xtick = 1, xtickstart = None, Fit = False):
        if Fit:
            self.FitPort()
            return
        elif (self.View_XMin == xmin) and (self.View_XMax == xmax):
            return
        self.View_XMin  = xmin
        self.View_XMax  = xmax
        if xrng is None:
            self.View_XRng = xmax - xmin
        else: self.View_XRng = xrng

        self.Nx = max(np.ceil(40 * self.CanvWidth / 1180), 1)
        if xtick is None: self.XTick = self.TickCalculator(self.View_XRng, self.Nx)
        else: self.XTick = xtick
        if xtickstart is None: self.XTickStart = int(self.View_XMin/self.XTick) * self.XTick
        else: self.XTickStart = xtickstart

        self.PanePortSignal.emit(True, True)

    def ScrollRespond(self, dy):
        if dy >= 0:
            if (self.View_YMax < self.Abs_YMax):
                shifty = min(dy, self.Abs_YMax - self.View_YMax)
                self.View_YMax += shifty
                self.View_YMin += shifty
                self.View_YAvg  = (self.View_YMax + self.View_YMin)/2
                self.YTickStart = int(self.View_YMin/self.YTick) * self.YTick
        
        else:
            if (self.View_YMin > self.Abs_YMin):
                shifty = min(-dy, self.View_YMin - self.Abs_YMin)
                self.View_YMax -= shifty
                self.View_YMin -= shifty
                self.View_YAvg  = (self.View_YMax + self.View_YMin)/2
                self.YTickStart = int(self.View_YMin/self.YTick) * self.YTick

        self.PanePortSignal.emit(True, False)

    def TickCalculator(self, range, N):
        if range == 0: return 0
        else:
            raw_spacing = abs(range)/N
            dec = 10 ** np.floor(np.log10(raw_spacing))
            norm_spacing = raw_spacing / dec
            ref  = [1, 2, 5, 10, 25]
            i    = np.argmin(np.abs(np.ones(len(ref)) * norm_spacing - ref))
            tick = ref[np.argmin(np.abs(np.ones(len(ref)) * norm_spacing - ref))] * dec * (range/abs(range))
            while True:
                if range / tick <= N + 1: break
                elif i >= len(ref): break
                else:
                    i += 1
                    tick = ref[i] * dec * (range/abs(range))

            return tick

    def update(self):
        self.View_XRng  = self.View_XMax - self.View_XMin
        self.Nx         = max(np.ceil(40 * self.CanvWidth / 1180), 1)
        self.XTick      = self.TickCalculator(self.View_XRng, self.Nx)
        if self.XTick   == 0:
            self.Abs_XMin  = 0.0
            self.Abs_XMax  = 1.0
            self.Abs_XRng  = 1.0
            self.View_XMin = 0.0
            self.View_XMax = 1.0
            self.View_XRng = 1.0
            self.XTick     = 0.1
        self.XTickStart = int(self.View_XMin/self.XTick) * self.XTick

        self.View_YRng  = self.View_YMax - self.View_YMin
        self.Ny         = max(np.ceil(40 * self.CanvHeight / 1180), 1)
        self.YTick      = self.TickCalculator(self.View_YRng, self.Ny)
        if self.YTick   == 0:
            self.Abs_YMin  = 0.0
            self.Abs_YMax  = 1.0
            self.Abs_YRng  = 1.0
            self.View_YMin = 0.0
            self.View_YMax = 1.0
            self.View_YRng = 1.0
            self.View_YAvg = 0.5
            self.YTick     = 0.1
        self.YTickStart  = int(self.View_YMin/self.YTick) * self.YTick

        self.XPortCommand.emit(self.View_XMin, self.View_XMax, self.View_XRng, self.XTick, self.XTickStart, False)


class PaneWidget(QWidget):

    def __init__(self, PaneID, Canvas : PaneCanvas, Axis : ScrollBar, ViewPort : PaneViewPort):
        # print("PaneWidget init")
        super().__init__()
        self.RefreshPane  = True
        self.PaneID       = PaneID
        self.CanvasWidget = Canvas
        self.AxsWidget    = Axis
        self.ViewPort     = ViewPort
        self.ScrollBar    = ScrollBar(self.ViewPort)
        self.LayoutSetup()
        
    def LayoutSetup(self):
        self.CanvasWidget.setParent(self)
        self.AxsWidget   .setParent(self)

        self.CanvasWidget.setMinimumHeight(4 * padding)
        self.AxsWidget   .setMinimumHeight(4 * padding)
        self.ScrollBar   .setMinimumHeight(4 * padding)
        self             .setMinimumHeight(4 * padding)

        self.Layout = QHBoxLayout(self)
        self.Layout.setContentsMargins(0, 0, 0, 0)
        self.Layout.setSpacing(0)

        self.AxsWidget.setStyleSheet("background: black;")

        self.Layout.addWidget(self.AxsWidget)
        self.Layout.addWidget(self.CanvasWidget)
        self.Layout.addWidget(self.ScrollBar)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # self.CanvasWidget.update()
        # self.AxsWidget.update()
        self.ScrollBar.update() # <------ Commented out!
        self.update() #<------ Commented out!


class PaneCanvas(QWidget):
    ControlEvent   = Signal(object)
    HitRebuild     = Signal()
    HitRebuildAdd  = Signal()
    PreViewUpdate  = Signal()
    CurserUpdate   = Signal()
    ViewPortUpdate = Signal(float, float)
    
    @property
    def PixelRatio(self)      : return self.devicePixelRatioF()
    @property
    def Axis(self)            : return self.GlobView.Axis
    @property
    def AxisStart(self)       : return self.GlobView.AxisStart
    @property
    def AxisStop(self)        : return self.GlobView.AxisStop
    @property
    def AxisRange(self)       : return self.GlobView.AxisRange
    @property
    def xMin(self)            : return self.ViewPort.View_XMin
    @property
    def xMax(self)            : return self.ViewPort.View_XMax
    @property
    def AxisCoveredPerPx(self): return self.ViewPort.View_XRng/ (self.width() - 2 * padding)
    @property
    def yRange(self)          : return self.ViewPort.View_YRng
    @property
    def yAvg(self)            : return self.ViewPort.View_YAvg
    
    def __init__(self, PaneID, GlobalViewModel, LocalSignals, ViewPort : PaneViewPort, width = None):
        super().__init__()
        # print("WaveCanvas init")
        if width is not None: self.resize(width, self.height())
        self.PaneID        = PaneID
        self.GlobView      = GlobalViewModel
        self.GlobSignals   = self.GlobView.GlobalSignals
        self.LocSignals    = LocalSignals
        self.ViewPort      = ViewPort
        self.GridMap       = QPixmap(int(self.width() * self.PixelRatio), int(self.height() * self.PixelRatio))
        self.prevIdx       = 0
        self.postIdx       = 0
        self.FieldMatrix   = None
        self.RectZoom      = False
        self.XZoom         = False
        self.YZoom         = False
        self.ZoomStartPx   = None
        self.ZoomStopPx    = None
        self.PointX        = None
        self.PointY        = None
        self.PointID       = None

        self.RefreshCanvas = True
        self.AddTraceFlag  = False
        self.RemTraceFlag  = False
        self.PointerFlag   = False
        self.Active        = False
        self.MousePoint    = None

        self.PreViewTraceMap = []
        self.ViewTraceMap    = []
        self.TraceData       = []
        self.RemTraces       = []
        self.InCanvGlobIDs   = []
        self.ToAddGlobIDs    = []
        self.ToRemGlobIDs    = []
        self.AbsSampleIdxs   = np.array([], dtype = int)
        self.AbsActivePx     = np.array([], dtype = int)
        self.SampleIdxs      = np.array([], dtype = int)
        self.ActivePx        = np.array([], dtype = int)

        self.PaintCounter    = 0
        self.ReBuildCounter  = 0

        self.PreViewHeight = 18
        self.PreViewWidth  = self.width()
        self.HitResult     = HitResult()

        self.ResizeCounter = 0
        self.ReSizeEnable  = True
        self.Resizing      = False

        self.debugonce     = True

        self.ViewAxisMetaData()
        self.AbsAxisMetaData()

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        policy = self.sizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Policy.Ignored)
        self.setSizePolicy(policy)

    def paintEvent(self, event):
        if self.ViewPort.View_XRng is None or self.ViewPort.View_YRng is None:
            return
        
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(30, 30, 30))

        rectangle = QRect(padding, padding,
                          self.width() - 2 * padding, self.height() - 2 * padding
                          )
        if self.Active: 
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(QPen(QColor(255, 255, 255, 50), 1, Qt.DashLine))
            painter.drawRect(-1, 1,
                            self.width() - 1, self.height() - 2)
            painter.setPen(Qt.NoPen)
            painter.setRenderHint(QPainter.Antialiasing, False)

        if self.Resizing: painter.drawPixmap(rectangle, self.GridMap)
        else: painter.drawPixmap(padding, padding, self.GridMap)

        if self.Resizing:
            for TraceMap in self.ViewTraceMap:
                print("TRACEMAP WIDTH =", TraceMap.width())
                painter.drawPixmap(rectangle, TraceMap)
        else:
            for TraceMap in self.ViewTraceMap:
                painter.drawPixmap(padding, padding, TraceMap)

        # if self.FieldMatrix is not None:
        #     rgb_data = self.FieldMatrix
        #     h, w, ch = rgb_data.shape
        #     bytes_per_line = ch * w
        #     q_img = QImage(
        #         rgb_data.data,
        #         w, h,
        #         bytes_per_line,
        #         QImage.Format.Format_RGB888
        #     ).copy()
        #     rect = QRect(
        #         padding, padding,
        #         self.width() - 2 * padding, self.height() - 2 * padding
        #         )
        #     painter.drawImage(rect, q_img)
        # painter.drawPixmap(padding, padding, self.GridMap)
        
        # if self.MousePoint is not None:
        #     for CoordPoints in DigitalCircle.values():
        #         for Coord in CoordPoints:
        #             painter.drawPoint(
        #                 int(self.MousePoint.x() + Coord[0]), int(self.MousePoint.y() + Coord[1])
        #             )

        if len(self.HitResult.ClickedIDs) != 0:
            painter.fillRect(QRect(padding, padding, self.width() - 2 * padding, self.height() - 2 * padding), QColor(10, 10, 10, 150))
            for idx in self.HitResult.ClickedIDs:
                painter.drawPixmap(padding, padding, self.ViewTraceMap[idx])
                painter.drawPixmap(padding, padding, self.ViewTraceMap[idx])
                painter.drawPixmap(padding, padding, self.ViewTraceMap[idx])
                painter.drawPixmap(padding, padding, self.ViewTraceMap[idx])
                painter.drawPixmap(padding, padding, self.ViewTraceMap[idx])
                painter.drawPixmap(padding, padding, self.ViewTraceMap[idx])
                painter.drawPixmap(padding, padding, self.ViewTraceMap[idx])
                painter.drawPixmap(padding, padding, self.ViewTraceMap[idx])
                painter.drawPixmap(padding, padding, self.ViewTraceMap[idx])
                painter.drawPixmap(padding, padding, self.ViewTraceMap[idx])

        painter.setRenderHint(QPainter.Antialiasing, True)

        if self.RectZoom and (self.ZoomStartPx is not None) and (self.ZoomStopPx is not None):
            painter.setPen(QPen(QColor(150, 150, 150), 0.5, Qt.DashLine))
            painter.setBrush(QColor(100, 100, 100, 40))
            zoomrect = QRectF(
                self.ZoomStartPx,
                self.ZoomStopPx
            ).normalized()
            painter.drawRect(zoomrect)

        if self.PointerFlag:
            # self.PointXPx = (self.PointX - self.ViewPort.View_XMin) * (self.width() - 2 * padding) / self.ViewPort.View_XRng + padding
            # self.PointYPx = (self.height() - 2 * padding) - (self.PointY - self.ViewPort.View_YMin) * (self.height() - 2 * padding) / self.ViewPort.View_YRng + padding
            if len(self.HitResult.ClickedIDs) != 0 and self.PointID in self.HitResult.ClickedIDs:  
                GlobalID = self.LocSignals[self.PointID].Global_ID
                color    = self.GlobSignals[GlobalID].color
                pen = QPen(color)
                pen.setWidth(5)
                pen.setCapStyle(Qt.RoundCap)

                painter.setPen(pen)
                painter.drawPoint(round(self.PointXPx), round(self.PointYPx))
            
            elif len(self.HitResult.ClickedIDs) == 0:
                GlobalID = self.LocSignals[self.PointID].Global_ID
                color    = self.GlobSignals[GlobalID].color
                pen = QPen(color)
                pen.setWidth(5)
                pen.setCapStyle(Qt.RoundCap)

                painter.setPen(pen)
                painter.drawPoint(int(self.PointXPx), int(self.PointYPx))

            # print("Is --->", "(", self.PointXPx, ",", self.PointYPx, ")")
        
        painter.end()
        self.PaintCounter += 1
        
    def Configure(self, PortChanged: bool, XPortChanged : bool):
        TargetIDs         = {sig.Global_ID for sig in self.LocSignals}
        current           = set(self.InCanvGlobIDs)
        self.ToAddGlobIDs = list(TargetIDs - current)
        self.ToRemGlobIDs = list(current - TargetIDs)

        if len(self.ToAddGlobIDs) != 0: self.AddPreViewMap()

        if len(self.ToRemGlobIDs) != 0: self.RemPreViewMap()

        if PortChanged:
            t = time.perf_counter()
            if XPortChanged:
                self.ViewAxisMetaData()
            self.ReBuildTraceMap()
            self.ReBuildGridMap()
            self.update()
            # print("Time to Render =", (time.perf_counter() - t) * 1000, "mS")
            # print("=======================")

        elif len(self.ToAddGlobIDs) != 0:
            self.AddTraceMap()
            self.update()

        elif len(self.ToRemGlobIDs) != 0:
            self.RemTraceMap()
            self.update()

    def ReBuildTraceMap(self):
        if self.Axis is None or len(self.Axis) == 0:
            return
        if self.width() <= 1 or self.height() <= 1:
            return
        # print("Map Rebuild")
        
        # C++ Helper Function to speed up
        self.ViewTraceMap.clear()

        mapPtr = []
        for signal in self.LocSignals:
            map = QPixmap(
                (self.width() - 2 * padding) * self.PixelRatio,
                (self.height() - 2 * padding) * self.PixelRatio
                )
            map.fill(Qt.transparent)
            map.setDevicePixelRatio(self.PixelRatio)

            self.ViewTraceMap.append(map)

            ptr = shiboken6.getCppPointer(map)[0]
            mapPtr.append(ptr)
        
        renderCore.rebuildTraceMap(
            self.TraceData,
            mapPtr,
            self.InCanvGlobIDs,
            self.ToAddGlobIDs,
            self.ToRemGlobIDs,
            self.LocSignals,
            self.GlobSignals,
            self.Axis,
            self.ActivePx,
            self.SampleIdxs,
            self.PixelRatio,
            (self.width() - 2 * padding),
            (self.height() - 2 * padding),
            self.xMin,
            self.xMax,
            self.AxisStart,
            self.AxisStop,
            self.AxisCoveredPerPx,
            self.yAvg,
            self.yRange,
            self.prevIdx,
            self.postIdx
        )

        self.HitRebuild.emit()
        self.ReBuildCounter += 1

    def AddTraceMap(self):
        print("AddTraceMap in canvas =", self.PaneID)
        print("To add global ID =", self.ToAddGlobIDs)

        for Globalid in self.ToAddGlobIDs:
            for sig in self.LocSignals:
                if sig.Global_ID == Globalid:
                    LocalID = sig.Local_ID
            
            trace = self.GlobSignals[Globalid].data
            color = self.GlobSignals[Globalid].color
            width = self.LocSignals[LocalID].Width

            Map = QPixmap(
                int(self.width() * self.PixelRatio),
                int(self.height() * self.PixelRatio)
                )
            Map.fill(Qt.transparent)
            Map.setDevicePixelRatio(self.PixelRatio)
            Pxpainter = QPainter(Map)
            Pxpainter.setRenderHint(QPainter.Antialiasing, False)

            center    = []
            min       = []
            max       = []

            if(self.xMin > self.AxisStart):
                prevXPx = (self.Axis[self.prevIdx] - self.xMin) / self.AxisCoveredPerPx
                prevYpx = (self.yAvg + self.yRange / 2 - trace[self.prevIdx]) * self.height() / self.yRange
                center.append((prevXPx, prevYpx))
                min   .append((prevXPx, prevYpx))
                max   .append((prevXPx, prevYpx))

            for px in self.ActivePx:
                leftIndex  = self.SampleIdxs[px]
                rightIndex = self.SampleIdxs[px + 1]
                incSamples = trace[leftIndex : rightIndex]
                pxYmax = (self.yAvg + self.yRange / 2 - np.min(incSamples)) * self.height() / self.yRange
                pxYmin = (self.yAvg + self.yRange / 2 - np.max(incSamples)) * self.height() / self.yRange
                pxYctr = (pxYmax + pxYmin) / 2
                if (pxYmax - pxYmin) / self.height() <= 0.02:
                    pxYmin = pxYctr
                    pxYmax = pxYctr
                else:
                    Pxpainter.drawLine(
                        px, pxYmin,
                        px, pxYmax
                    )
                center.append((px, pxYctr))
                min   .append((px, pxYmin))
                max   .append((px, pxYmax))

            if(self.xMax < self.AxisStop):
                postXPx = (self.Axis[self.postIdx] - self.xMin) / self.AxisCoveredPerPx
                postYpx = (self.yAvg + self.yRange / 2 - trace[self.postIdx]) * self.height() / self.yRange
                center.append((postXPx, postYpx))
                min   .append((postXPx, postYpx))
                max   .append((postXPx, postYpx))

            Pxpainter.setRenderHint(QPainter.Antialiasing, True)
            Pxpainter.setPen(QPen(color, width))
            points = [QPointF(x, y) for x, y in center]
            Pxpainter.drawPolyline(points)
            Pxpainter.setRenderHint(QPainter.Antialiasing, False)
            Pxpainter.end()
        
            self.TraceData.insert(LocalID,
                                  {
                "Global_ID" : Globalid,
                "Local_ID"  : LocalID,
                "CentrX"    : [pt[0] for pt in center],
                "CentrY"    : [pt[1] for pt in center],
                "MinY"      : [pt[1] for pt in min],
                "MaxY"      : [pt[1] for pt in max],
                "color"     : color
            })

            self.ViewTraceMap.insert(LocalID, Map)
            self.InCanvGlobIDs.insert(LocalID, Globalid)
            if Debug: print("Add TraceMap added ID =", Globalid)
        if Debug: print("In canvas After Adding =", self.InCanvGlobIDs)
        self.ToAddGlobIDs.clear()
        self.HitRebuild.emit()
        # self.HitRebuildAdd.emit()

    def RemTraceMap(self):
        if Debug:
            print("Remove Trace Map")
            print("Length before removing =", len(self.ViewTraceMap))
            print("Contents before remove :", self.ViewTraceMap)
            print("To remove in before method =", self.ToRemGlobIDs)
            print("In canvas Ids in before method =", self.InCanvGlobIDs)
        for Gid in self.ToRemGlobIDs:
            if Debug: print("To rem in for loop = ", Gid)
            self.InCanvGlobIDs.remove(Gid)
        self.ViewTraceMap[:] = [
            Map for i, Map in enumerate(self.ViewTraceMap)
            if self.TraceData[i]["Global_ID"] not in self.ToRemGlobIDs
        ]
        
        self.TraceData[:] = [
            trace for trace in self.TraceData
            if trace["Global_ID"] not in self.ToRemGlobIDs
        ]
        
        for i, trace in enumerate(self.TraceData):
            trace["Local_ID"] = i

        if Debug:
            print("TraceMap Length in Rem method =", len(self.ViewTraceMap))
            print("Contents after removing :", self.ViewTraceMap)
        
        self.ToRemGlobIDs.clear()
        self.HitRebuild.emit()

    def ReBuildPreViewMap(self):
        print("ReBuild PreView Map")
        if self.Axis is None or len(self.Axis) == 0:
            return
        if self.width() <= 1 or self.height() <= 1:
            return
        
        self.PreViewTraceMap.clear()

        self.PreViewHeight = 18
        self.PreViewWidth  = (self.width() - 2 * padding)

        yAvg   = (self.ViewPort.Abs_YMin + self.ViewPort.Abs_YMax) / 2
        yRange = self.ViewPort.Abs_YRng

        for item in self.LocSignals:
            GlobalID = item.Global_ID
            # self.InCanvGlobIDs.append(GlobalID)
            Map = QPixmap(
                int(self.PreViewWidth * self.PixelRatio),
                int(self.PreViewHeight * self.PixelRatio)
                )
            Map.fill(Qt.transparent)
            Map.setDevicePixelRatio(self.PixelRatio)
            Pxpainter = QPainter(Map)
            Pxpainter.setRenderHint(QPainter.Antialiasing, False)

            trace    = self.GlobSignals[GlobalID].data
            color    = self.GlobSignals[GlobalID].color
            width    = item.Width
            Pxpainter.setPen(QPen(color, width/2))
            
            center    = []
            min       = []
            max       = []

            for px in self.AbsActivePx:
                leftIndex  = self.AbsSampleIdxs[px]
                rightIndex = self.AbsSampleIdxs[px + 1]
                incSamples = trace[leftIndex : rightIndex]
                pxYmax = (yAvg + yRange / 2 - np.min(incSamples)) * self.PreViewHeight / yRange
                pxYmin = (yAvg + yRange / 2 - np.max(incSamples)) * self.PreViewHeight / yRange
                pxYctr = (pxYmax + pxYmin) / 2
                if (pxYmax - pxYmin) / self.height() <= 0.01:
                    pxYmin = pxYctr
                    pxYmax = pxYctr
                else:
                    Pxpainter.drawLine(
                        px, pxYmin,
                        px, pxYmax
                    )
                center.append((px, pxYctr))
                min   .append((px, pxYmin))
                max   .append((px, pxYmax))

            Pxpainter.setRenderHint(QPainter.Antialiasing, True)
            Pxpainter.setPen(QPen(color, width))
            points = [QPointF(x, y) for x, y in center]
            Pxpainter.drawPolyline(points)
            Pxpainter.setRenderHint(QPainter.Antialiasing, False)
            Pxpainter.end()

            self.PreViewTraceMap.append(Map)

        self.PreViewUpdate.emit()

    def AddPreViewMap(self):
        if Debug: print("Add PreView Map")
        self.PreViewHeight = 18
        self.PreViewWidth  = (self.width() - 2 * padding)

        yAvg   = (self.ViewPort.Abs_YMin + self.ViewPort.Abs_YMax) / 2
        yRange = self.ViewPort.Abs_YRng

        for GlobalID in self.ToAddGlobIDs:
            LocalID = None
            for sig in self.LocSignals:
                if sig.Global_ID == GlobalID:
                    LocalID = sig.Local_ID
                    break

            if LocalID is None:
                print(f"Warning: GlobalID {GlobalID} is not in LocSignals yet. Skipping.")
                continue
            
            trace = self.GlobSignals[GlobalID].data
            color = self.GlobSignals[GlobalID].color
            width = self.LocSignals[LocalID].Width

            Map = QPixmap(
                int(self.PreViewWidth * self.PixelRatio),
                int(self.PreViewHeight * self.PixelRatio)
                )
            Map.fill(Qt.transparent)
            Map.setDevicePixelRatio(self.PixelRatio)
            Pxpainter = QPainter(Map)
            Pxpainter.setRenderHint(QPainter.Antialiasing, False)

            center    = []
            min       = []
            max       = []

            for px in self.AbsActivePx:
                leftIndex  = self.AbsSampleIdxs[px]
                rightIndex = self.AbsSampleIdxs[px + 1]
                incSamples = trace[leftIndex : rightIndex]
                pxYmax = (yAvg + yRange / 2 - np.min(incSamples)) * self.PreViewHeight / yRange
                pxYmin = (yAvg + yRange / 2 - np.max(incSamples)) * self.PreViewHeight / yRange
                pxYctr = (pxYmax + pxYmin) / 2
                if (pxYmax - pxYmin) / self.height() <= 0.01:
                    pxYmin = pxYctr
                    pxYmax = pxYctr
                else:
                    Pxpainter.drawLine(
                        px, pxYmin,
                        px, pxYmax
                    )
                center.append((px, pxYctr))
                min   .append((px, pxYmin))
                max   .append((px, pxYmax))

            Pxpainter.setRenderHint(QPainter.Antialiasing, True)
            Pxpainter.setPen(QPen(color, width))
            points = [QPointF(x, y) for x, y in center]
            Pxpainter.drawPolyline(points)
            Pxpainter.setRenderHint(QPainter.Antialiasing, False)
            Pxpainter.end()
        
            self.PreViewTraceMap.insert(LocalID, Map)
        
        self.PreViewUpdate.emit()

    def RemPreViewMap(self):
        if Debug: print("Remove PreView Map")
        self.PreViewTraceMap[:] = [
            Map for i, Map in enumerate(self.PreViewTraceMap)
            if self.TraceData[i]["Global_ID"] not in self.ToRemGlobIDs
        ]

        self.PreViewUpdate.emit()

    def ReBuildGridMap(self):
        if self.ViewPort.View_XRng == 0:
            return
        
        if self.ViewPort.View_YRng == 0:
            return

        if self.width() <= 1 or self.height() <= 1:
            return

        thickPen = QPen(QColor(100,100,100), 0.25, Qt.DashLine)
        thinPen  = QPen(QColor(100,100,100, 100), 0.25, Qt.DashLine)

        self.GridMap = QPixmap(
            int((self.width() - 2 * padding) * self.PixelRatio),
            int((self.height() - 2 * padding) * self.PixelRatio)
        )
        
        self.GridMap.setDevicePixelRatio(self.PixelRatio)
        self.GridMap.fill(Qt.transparent)

        Gridpainter = QPainter(self.GridMap)
        Gridpainter.setRenderHint(QPainter.Antialiasing, False)

        XPxTick = self.ViewPort.XTick * (self.width() - 2 * padding) / self.ViewPort.View_XRng
        XPxTickStart = (self.ViewPort.XTickStart - self.ViewPort.View_XMin) * (self.width() - 2 * padding) / self.ViewPort.View_XRng
        YPxTick = self.ViewPort.YTick * (self.height() - 2 * padding) / self.ViewPort.View_YRng
        YPxTickStart = (self.height() - 2 * padding) - (self.ViewPort.YTickStart - self.ViewPort.View_YMin) * (self.height() - 2 * padding) / self.ViewPort.View_YRng

        Gridpainter.setPen(thickPen)

        CurrentYtickPx = YPxTickStart + YPxTick
        while True:
            if CurrentYtickPx < 0 :
                break
            Gridpainter.drawLine(
                0, CurrentYtickPx,
                (self.width() - 2 * padding), CurrentYtickPx
            )

            Gridpainter.setPen(thinPen)
            for count in range(4):
                subTick = CurrentYtickPx - (count + 1) * YPxTick / 5
                Gridpainter.drawLine(
                    0, subTick,
                    (self.width() - 2 * padding), subTick
                )
            Gridpainter.setPen(thickPen)

            CurrentYtickPx -= YPxTick

        CurrentXtickPx = XPxTickStart - XPxTick
        while True:
            if CurrentXtickPx > self.width():
                break
            Gridpainter.drawLine(
                CurrentXtickPx, 0,
                CurrentXtickPx, (self.height() - 2 * padding)
            )

            Gridpainter.setPen(thinPen)
            for count in range(4):
                subTick = CurrentXtickPx + (count + 1) * XPxTick / 5
                Gridpainter.drawLine(
                    subTick, 0,
                    subTick, (self.height() - 2 * padding)
                )
            Gridpainter.setPen(thickPen)

            CurrentXtickPx += XPxTick

        Gridpainter.end()

    def ViewAxisMetaData(self):
        if self.Axis is None or len(self.Axis) == 0:
            return
        
        AxisEdges      = self.xMin + self.AxisCoveredPerPx * np.arange(self.width() + 2)
        SampleIdxs     = np.searchsorted(self.Axis, AxisEdges, side='left')
        SampleIdxShift = SampleIdxs[1:]

        self.SampleIdxs = SampleIdxs
        self.prevIdx    = np.min(SampleIdxs) - 1
        self.postIdx    = np.max(SampleIdxs) + 1
        self.ActivePx   = np.where((SampleIdxShift - SampleIdxs[:-1]) != 0)[0]

    def AbsAxisMetaData(self):
        if self.Axis is None or len(self.Axis) == 0:
            return
        
        xMin = self.ViewPort.Abs_XMin
        AxisCoveredPerPx = self.ViewPort.Abs_XRng/(self.width() - 2 * padding)
        AxisEdges = xMin + AxisCoveredPerPx * np.arange((self.width() - 2 * padding) + 2)
        SampleIdxs = np.searchsorted(self.Axis, AxisEdges, side='left')
        SampleIdxShift = SampleIdxs[1:]

        self.AbsSampleIdxs = SampleIdxs
        self.AbsActivePx   = np.where((SampleIdxShift - SampleIdxs[:-1]) != 0)[0]

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.ControlEvent.emit(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.ControlEvent.emit(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.ControlEvent.emit(event)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.ControlEvent.emit(event)

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self.ControlEvent.emit(event)

    def resizeEvent(self, event):
        def countUP():
            prevCount = self.ResizeCounter
            self.ResizeCounter += 1
            if prevCount <= 0 and self.ResizeCounter > 0:
                self.Resizing = True

        def countDN():
            prevCount = self.ResizeCounter
            self.ResizeCounter -= 1
            if prevCount > 0 and self.ResizeCounter <= 0:
                self.Resizing = False
                self.ViewPortUpdate.emit((self.width() - 2 * padding), (self.height() - 2 * padding))     # <------ Commented out!
                self.ViewAxisMetaData()                                                                   # <------ Commented out!
                self.AbsAxisMetaData()                                                                    # <------ Commented out!
                self.ReBuildTraceMap()                                                                    # <------ Commented out!
                self.ReBuildPreViewMap()                                                                  # <------ Commented out!
                self.CurserUpdate.emit()                                                                  # <------ Commented out!
                self.update()

        if self.width() <= 1 or self.height() <= 1:
            return
        if not self.ReSizeEnable:
            return

        countUP()
        QTimer.singleShot(50, countDN)

        self.ReBuildGridMap()                                                                     # <------ Commented out!
        
        event.accept()

    def enterEvent(self, event):
        super().enterEvent(event)
        self.setFocus()
        self.ControlEvent.emit(event)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.clearFocus()
        self.ControlEvent.emit(event)

    def HELPERClearHitResults(self):
        self.HitResult.ClickedIDs.clear()

    def HELPERSetActive(self, currentPane):
        if self.PaneID == currentPane: self.Active = True
        else: self.Active = False

        self.update()


class PaneAxis(QWidget):
    @property
    def PixelRatio(self): return self.devicePixelRatioF()
    
    @property
    def YPxTick(self): return self.ViewPort.YTick * (self.height() - 2 * padding) / self.ViewPort.View_YRng
    
    @property
    def YPxTickStart(self):
        if self.ViewPort.View_YRng == 0:
            return None
        return (self.height() - 2 * padding) - (self.ViewPort.YTickStart - self.ViewPort.View_YMin) * (self.height() - 2 * padding) / self.ViewPort.View_YRng

    def __init__(self, PaneID, PaneViewPort : PaneViewPort):
        super().__init__()
        self.PaneID      = PaneID
        self.ViewPort    = PaneViewPort
        self.exponent    = 0
        self.RefreshAxis = True
        self.Active      = False
        self.setFixedWidth(35)

        policy = self.sizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Policy.Ignored)
        self.setSizePolicy(policy)
    
    def paintEvent(self, event):
        if self.ViewPort.YTick is None or self.ViewPort.View_YRng is None:
            return

        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.RefreshAxis:
            self.UpdateAxis()
            self.RefreshAxis = False
        painter.drawPixmap(0, padding, self.pixmap)

        if self.Active:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(QPen(QColor(255, 255, 255, 50), 1, Qt.DashLine))
            painter.drawRect(1, 1,
                            self.width() + 1, self.height() - 2)
            painter.setPen(Qt.NoPen)
            painter.setRenderHint(QPainter.Antialiasing, False)
    
    def UpdateAxis(self):
        if self.YPxTickStart == None:
            return

        yTickStop = self.ViewPort.YTickStart + np.floor((self.ViewPort.View_YMax - self.ViewPort.YTickStart) / self.ViewPort.YTick) * self.ViewPort.YTick
        self.engFormat(start = self.ViewPort.YTickStart, stop = yTickStop)

        self.pixmap = QPixmap(
            int(self.width() * self.PixelRatio),
            int((self.height() - 2 * padding) * self.PixelRatio)
        )

        self.pixmap.setDevicePixelRatio(self.PixelRatio)
        self.pixmap.fill(Qt.transparent)
        Pxpainter = QPainter(self.pixmap)
        Pxpainter.fillRect(self.rect(), QColor(30,30,30))

        Pxpainter.setRenderHint(QPainter.Antialiasing, False)
    
        Pxpainter.setPen(QPen(QColor(200, 200, 200), 0.5))
        Pxpainter.drawLine(
                self.width() - 1, 0,
                self.width() - 1, self.height()
            )
        
        Current_AxTick_Px = self.YPxTickStart + self.YPxTick
        Current_AxTick_Value = self.ViewPort.YTickStart - self.ViewPort.YTick
        # count = 0
        while True:
            if Current_AxTick_Px < padding :
                break
            Pxpainter.drawLine(
                self.width() - 1 , Current_AxTick_Px,
                self.width() - 1 - self.width()//3, Current_AxTick_Px
            )
            font = QFont("Arial", 7)
            Pxpainter.setFont(font)
            Pxpainter.drawText(
                QRect(
                    -5, round(Current_AxTick_Px) - 10,
                    self.width() - 6 + 2, 20
                ),
                Qt.AlignRight | Qt.AlignVCenter,
                self.engFormat(value = Current_AxTick_Value)
            )

            for count in range (9):
                subTick = float(Current_AxTick_Px - (count + 1) * self.YPxTick / 10)
                Pxpainter.drawLine(
                    self.width(), subTick,
                    6 * self.width() // 7, subTick
                )

            Current_AxTick_Px -= self.YPxTick
            Current_AxTick_Value += self.ViewPort.YTick
            if abs(Current_AxTick_Value/self.ViewPort.YTick) <= 1e-6 : Current_AxTick_Value = 0

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.setFocus()

    def engFormat(self, value = None, start = None, stop = None):
            prefixes = {
                -15: 'f',
                -12: 'p',
                -9 : 'n',
                -6 : 'u',
                -3 : 'm',
                0  :  '',
                3  : 'k',
                6  : 'M',
                9  : 'G',
                12 : 'T'
            }

            if value == 0:
                return "0"
    
            if start == 0:
                self.exponent = 0
                if stop != 0:
                    stopex = (int(np.floor(np.log10(abs(stop )))) // 3) * 3
                    if stopex > 0: self.exponent = stopex
            
            if (start is not None) and (stop is not None):
                if start == 0: self.exponent = 0
                elif start != 0: self.exponent = (int(np.floor(np.log10(abs(start)))) // 3) * 3
    
                if stop  == 0: stopex = 0
                elif stop  != 0: stopex        = (int(np.floor(np.log10(abs(stop )))) // 3) * 3

                if (stop == 0): pass
                elif (start ==  0): self.exponent = stopex
                elif (stopex > self.exponent): self.exponent = stopex

                self.exponent = max(min(self.exponent, 12), -15)
    
            if value is not None:
                scaled = value / (10 ** self.exponent)
                return f"{scaled:g}{prefixes[self.exponent]}"

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.RefreshAxis = True
        self.update() # <------ Commented out!

    def HELPERSetActive(self, currentPane):
        if self.PaneID == currentPane: self.Active = True
        else: self.Active = False

        self.update()


class ScrollBar(QScrollBar):
    ScrollCommand = Signal(float)

    @property
    def page(self): return self.pageStep()

    @property
    def total(self): return self.maximum() - self.minimum() + self.pageStep()

    @property
    def ratio(self): return self.page / self.total

    def __init__(self, ViewPort : PaneViewPort):
        super().__init__()
        self.SCALE    = 1000
        self.ViewPort = ViewPort

        self.setFixedWidth(8)
        self.setMinimum(0)
        self.setMaximum(((self.ViewPort.Abs_YMax - self.ViewPort.Abs_YMin) - (self.ViewPort.View_YMax - self.ViewPort.View_YMin)) * self.SCALE)
        self.setValue((self.ViewPort.Abs_YMax - self.ViewPort.View_YMax) * self.SCALE)

        self.setOrientation(Qt.Orientation.Vertical)
        self.setTracking(True)
        self.StyleConfig()
        
        policy = self.sizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Policy.Ignored)
        self.setSizePolicy(policy)
        
        self.valueChanged.connect(self.PortCommand)

    def PortSocket(self):
        self.blockSignals(True)
        self.setPageStep((self.ViewPort.View_YMax - self.ViewPort.View_YMin) * self.SCALE)
        self.setMinimum(0)
        self.setMaximum(((self.ViewPort.Abs_YMax - self.ViewPort.Abs_YMin) - (self.ViewPort.View_YMax - self.ViewPort.View_YMin)) * self.SCALE)
        self.setValue((self.ViewPort.Abs_YMax - self.ViewPort.View_YMax) * self.SCALE)

        self.StyleConfig()
        self.update()
        self.blockSignals(False)
    
    def PortCommand(self):
        dy = (self.ViewPort.Abs_YMax - self.ViewPort.View_YMax) - self.value() / self.SCALE
        self.ScrollCommand.emit(dy)

    def StyleConfig(self):
        self.setStyleSheet("""
            QScrollBar:vertical {
                background: rgb(30,30,30);
                width: 8px;
                margin: 0px;
                border: none;
            }

            QScrollBar::handle:vertical {
                background: rgb(100,100,100);
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background: rgb(130,130,130);
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: rgb(30,30,30);
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
                border: none;
            }
            """)
        
        if self.ratio > 0.99:
            self.setStyleSheet("""
                QScrollBar:vertical {
                    background: rgb(30,30,30);
                    width: 8px;
                    border: none;
                }

                QScrollBar::handle:vertical {
                    background: transparent;
                    min-height: 0px;
                    max-height: 0px;
                }

                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {
                    background: rgb(30,30,30);
                }

                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    height: 0px;
                    background: none;
                    border: none;
                }
                """)


class HoverWidget(QFrame):

    def __init__(self, Parent = None):
        super().__init__(Parent)
        self.SignalLabel = QLabel()
        self.XLabel      = QLabel()
        self.YLabel      = QLabel()
        self.CurrrentID  = -1
        self.CurrentX    = 0
        self.CurrentY    = 0
        self.OffsetX     = QPoint(10, 0)
        self.OffsetY     = QPoint(0, 0)

        self.setWindowFlags(Qt.SubWindow | Qt.FramelessWindowHint | Qt.WindowTransparentForInput)
        self.setFocusPolicy(Qt.NoFocus)
        self.LayoutConfig()
        self.StyleConfig()
        self.hide()
    
    def paintEvent(self, event):
        super().paintEvent(event)

    def LayoutConfig(self):
        Layout = QGridLayout()
        Layout.setContentsMargins(2, 2, 4, 2)
        Layout.setHorizontalSpacing(6)
        Layout.setVerticalSpacing(0)

        self.SignalPrefix = QLabel("Signal :")
        self.XPrefix      = QLabel("XAxis :")
        self.YPrefix      = QLabel("YAxis :")

        self.SignalPrefix.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.XPrefix     .setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.YPrefix     .setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.SignalLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.XLabel     .setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.YLabel     .setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        Layout.addWidget(self.SignalPrefix, 0, 0)
        Layout.addWidget(self.SignalLabel , 0, 1)

        Layout.addWidget(self.XPrefix,      1, 0)
        Layout.addWidget(self.XLabel ,      1, 1)

        Layout.addWidget(self.YPrefix,      2, 0)
        Layout.addWidget(self.YLabel ,      2, 1)
        
        self.setLayout(Layout)
    
    def StyleConfig(self):
        self.setStyleSheet("""
            HoverWidget {
                background-color: rgba(50, 50, 50, 200);
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 6px;
            }
                           
            HoverWidget QLabel {
                background: transparent;
                border: none;
                color: black;
                font-family: Arial;
                font-size: 8px;
            }
            
            QLabel[text$=":"] {
                font-weight: bold;
            }
        """)
    
    def UpdateInfo(self, SigID, x, y, XPix, YPix, w, h):
        if (SigID == self.CurrrentID) and (np.abs((x - self.CurrentX) / self.CurrentX) <= 1e-4) and (np.abs((y - self.CurrentY) / self.CurrentY) <= 1e-4):
            return
        
        xval = self.engFormat(x)
        yval = self.engFormat(y)

        self.SignalLabel.setText(f"{SigID}")
        self.XLabel.setText(xval)
        self.YLabel.setText(yval)
        self.adjustSize()

        self.ShowAt(XPix, YPix, w, h)
    
    def ShowAt(self, XPix, YPix, w, h):
        if (XPix - padding <= w / 4):
            self.OffsetX = QPoint(10, 0)
        if (YPix - padding <= h / 4):
            self.OffsetY = QPoint(0, 0)
        if (XPix - padding >= 3 * w / 4):
            self.OffsetX = QPoint(-(self.width() + 10), 0)
        if (YPix - padding >= 3 * h / 4):
            self.OffsetY = QPoint(0, -self.height())
        
        self.move(QPoint(XPix, YPix) + self.OffsetX + self.OffsetY)
        self.show()
    
    def engFormat(self, value):
        prefixes = {
                -15: 'f',
                -12: 'p',
                -9 : 'n',
                -6 : 'u',
                -3 : 'm',
                0  :  '',
                3  : 'k',
                6  : 'M',
                9  : 'G',
                12 : 'T'
            }

        if value == 0:
            return f"{0:0.4f}"
        
        exponent = (int(np.floor(np.log10(abs(value)))) // 3) * 3
        exponent = max(min(exponent, 12), -15)
        scaled   = value / (10 ** exponent)

        return f"{scaled:0.4f}{prefixes[exponent]}"

    def enterEvent(self, event):
        super().enterEvent(event)
        self.hide()


class HoverTrace(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.TraceMaps = {}
        self.PaneID    = None
        self.setFixedSize(QSize(60, 30))
        self.hide()

    def paintEvent(self, event):
        super().paintEvent(event)

        pixelRatio = self.devicePixelRatio()

        painter = QPainter(self)
        for map in self.TraceMaps:
            # Scale the pixmap down
            scaled_map = map.scaled(
                self.width() * pixelRatio,
                self.height() * pixelRatio,
                Qt.IgnoreAspectRatio,      # Options: IgnoreAspectRatio, KeepAspectRatio, KeepAspectRatioByExpanding
                Qt.SmoothTransformation
            )
            
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)
            painter.drawPixmap(0, 0, scaled_map)

        # painter.setPen(QPen(QColor(200, 200, 200)))
        # painter.drawRect(
        #     0, 0,
        #     self.width(), self.height()
        # )
        
        painter.end()


class ValueBubble(QWidget):

    @property
    def xmin(self): return self.ViewPort.View_XMin
    @property
    def xrng(self): return self.ViewPort.View_XRng
    @property
    def ymin(self): return self.ViewPort.View_YMin
    @property
    def yrng(self): return self.ViewPort.View_YRng

    def __init__(self, parent : QWidget, position : QPointF, snap, color : QColor, ViewPort : PaneViewPort, V : bool = False, H : bool = False, Orientation = 0):
        super().__init__(parent)
        self.position    = position
        self.Ysnap       = snap
        self.Color       = color
        self.ViewPort    = ViewPort
        self.text        = ""
        self.V           = V
        self.H           = H
        self.Orientation = Orientation

        font = self.font()
        font.setPixelSize(10)
        self.setFont(font)

        self.UpdatePosition()
    
    def paintEvent(self, event):
        x_offset = 10
        tail_w = 8 + x_offset
        right_padding = 10.0

        h = float(self.height())
        w = float(self.width())

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        body_path = QPainterPath()
        if self.Orientation == 0:
            body_rect = QRectF(tail_w, 1.0, w - tail_w - 1.0, h - 2.0)
        elif self.Orientation == 1:
            body_rect = QRectF(1.0, 1.0, w - tail_w - 1.0, h - 2.0)
        
        body_path.addRoundedRect(body_rect, 5, 5)

        delta = 3
        tail_path = QPainterPath()

        if self.Orientation == 0:
            tail_path.moveTo(0, self.position.y() - self.Ysnap + h / 2 + padding)
            tail_path.lineTo(tail_w + 3, h/2 - delta)
            tail_path.lineTo(tail_w + 3, h/2 + delta)
        elif self.Orientation == 1:
            tail_path.moveTo(self.width(), self.position.y() - self.Ysnap + h / 2 + padding)
            tail_path.lineTo(self.width() - (tail_w + 3), h/2 - delta)
            tail_path.lineTo(self.width() - (tail_w + 3), h/2 + delta)
        tail_path.closeSubpath()

        combined_path = body_path.united(tail_path)
        
        pen = QPen(QColor(255, 255, 255, 60), 1)
        pen.setCosmetic(True)
        painter.setBrush(QColor(50, 50, 50, 200))
        painter.setPen(pen)
        painter.drawPath(combined_path)

        if isinstance(self.Color, QColor):
            brushColor = self.Color
        else:
            brushColor = QColor(*self.Color)
        
        painter.setBrush(brushColor)
        painter.setPen(Qt.NoPen)
        dot_x = int(tail_w + 4) if self.Orientation == 0 else 6
        painter.drawEllipse(
            dot_x, int(self.height() // 2 - 4), 8, 8
        )

        if self.Orientation == 0:
            text_rect = QRectF(
                tail_w + 16.0, 0.0, w - (tail_w + 16.0 + right_padding), h
            )
        elif self.Orientation == 1:
            text_rect = QRectF(
                16.0, 0.0, w - (tail_w + 16.0 + right_padding), h
            )
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self.text,
        )

        painter.end()
    
    def UpdatePosition(self):
        if self.V and self.parent():
            self.value = (
                self.ymin + (((self.parent().height() - 2 * padding) - self.position.y()) * self.yrng) / (self.parent().height() - 2 * padding)
            )
        elif self.H and self.parent():
            self.value = (
                self.xmin + (self.position.x() * self.xrng) / (self.parent().width() - 2 * padding)
            )

        self.text = f"{self.value:0.4f}"

        fm = self.fontMetrics()
        text_width = fm.horizontalAdvance(self.text)

        x_offset = 10
        tail_w = 8 + x_offset
        dot_and_padding = 16.0
        right_padding = 10.0

        needed_w = int(tail_w + dot_and_padding + text_width + right_padding)
        if self.width() != needed_w:
            self.resize(needed_w, 16)
        
        h = float(self.height())
        if self.Orientation == 0:
            self.move(int(self.position.x()), int(self.Ysnap - h // 2))
        elif self.Orientation == 1:
            self.move(
                int(self.position.x()) - self.width(), int(self.Ysnap - h // 2)
            )
        self.update()

    def Cleanup(self):
        self.deleteLater()


class HitTest(QObject):
    HitBroadCast = Signal(object)
    FieldEmit    = Signal(object)
    HitReady     = Signal()

    def __init__(self, PaneID, PaneSignals, PaneViewPort, Canvas : PaneCanvas):
        super().__init__()
        self.PaneID         = PaneID
        self.Signals        = PaneSignals
        self.ViewPort       = PaneViewPort
        self.Canvas         = Canvas
        self.TraceData      = self.Canvas.TraceData
        self.HitResult      = HitResult()
        self.FieldMatrix    = np.full((self.Canvas.height() - 2 * padding, self.Canvas.width() - 2 * padding), -1, dtype = np.int32)
        self.PointMatrix    = np.full((self.Canvas.height() - 2 * padding, self.Canvas.width() - 2 * padding), -1, dtype = np.int32)
        self.TraceMatrix    = []
        self.highlightwidth = 1
        
        self.debugonce      = True
    
    def Rebuild(self):
        if self.Canvas.width() <= 1 or self.Canvas.height() <= 1:
            return

        self.FieldMatrix, self.TraceMatrix, self.PointMatrix = renderCore.hitRebuild(
            self.FieldMatrix,
            self.TraceMatrix,
            self.PointMatrix,
            self.TraceData,
            self.Canvas.height() - 2 * padding,
            self.Canvas.width() - 2 * padding,
            self.highlightwidth
        )


        # if self.FieldMatrix.shape != (self.Canvas.height(), self.Canvas.width()):
        #     self.FieldMatrix = np.full((self.Canvas.height(), self.Canvas.width()), -1, dtype = np.int32)
        #     self.PointMatrix = np.full((self.Canvas.height(), self.Canvas.width()), -1, dtype = float)
        # else:
        #     self.FieldMatrix.fill(-1)
        #     self.PointMatrix.fill(-1)
        
        # self.highlightwidth = 5
        # h = self.Canvas.height()
        # w = self.Canvas.width()
        # r = self.highlightwidth // 2
        
        # self.TraceMatrix = [[] for _ in range(w)]

        # for trace in self.TraceData:
        #     LocalID   = trace["Local_ID"]
        #     trcCentrX = trace["CentrX"]
        #     trcCentrY = trace["CentrY"]
        #     trcMin    = trace["MinY"]
        #     trcMax    = trace["MaxY"]
        
        #     pts = np.array(
        #         list(zip(trcCentrX, trcCentrY)),
        #         dtype=np.int32
        #         )
        #     cv2.polylines(
        #         self.FieldMatrix,
        #         [pts],
        #         False,
        #         LocalID,
        #         thickness=self.highlightwidth,
        #         lineType=cv2.LINE_8
        #     )
    
        #     for i, center in enumerate(trcCentrX):
        #         cx = int(center)
        #         if (i + 1 < len(trcCentrX)):
        #             nextCenter = int(trcCentrX[i + 1])
        #             if nextCenter == center:            # These are pixels which contains indices (so if the same pixel contains > 1 indices, then continue)
        #                 continue

        #             for x in range(int(center), int(nextCenter)):
        #                 y = (x - center) * (trcCentrY[i + 1] - trcCentrY[i]) / (nextCenter - center) + trcCentrY[i]
        #                 py = int(y)
        #                 self.TraceMatrix[x].append(y)
        #                 if x < w:
        #                     rows = np.where(self.FieldMatrix[:, x] == LocalID)[0]
        #                     splits = np.where(np.diff(rows) > 1)[0] + 1
        #                     chunks = np.split(rows, splits)
        #                     for chunk in chunks:
        #                         self.PointMatrix[chunk, x] = y
                
        #         cv2.line(
        #             self.FieldMatrix,
        #             (cx, int(trcMin[i])),
        #             (cx, int(trcMax[i])),
        #             LocalID,
        #             thickness = self.highlightwidth
        #         )

        #     view1 = self.FieldMatrix[145-20:166+20, 95-20:106+20]
        #     view2 = self.TraceMatrix[145-20:166+20, 95-20:106+20]
        #     for row in view1:
        #         print(" ".join(f"{' ':>2}" if v == -1 else f"{int(v):>2}" for v in row))
        #     for row in view2:
        #         print(" ".join(f"{' ':>2}" if v == -1 else f"{int(v):>2}" for v in row))
            
        self.HitReady.emit()
        self.get_renderable_image()
        # print("Hit Rebuild Time =", (time.perf_counter() - t0) * 1000, "mS")

    # Need to update <def AddTrace(self)> ---> Include TraceMatrix and Update PointMatrix
    def AddTrace(self):
        if Debug: print("HitTest -> AddTrace") # <----------------------------------------------------------------
        self.highlightwidth = 5
        h = self.Canvas.height()
        w = self.Canvas.width()
        r = self.highlightwidth // 2

        LocalID   = self.TraceData[-1]["Local_ID"]
        trcCentrX = self.TraceData[-1]["CentrX"]
        trcCentrY = self.TraceData[-1]["CentrY"]
        trcMin    = self.TraceData[-1]["MinY"]
        trcMax    = self.TraceData[-1]["MaxY"]
        pts = np.array(
            list(zip(trcCentrX, trcCentrY)),
            dtype=np.int32
            )

        cv2.polylines(
            self.FieldMatrix,
            [pts],
            False,
            LocalID,
            thickness=self.highlightwidth,
            lineType=cv2.LINE_8
        )
        NewTracePoints = np.array([])
        for i, center in enumerate(trcCentrX):
            if (i + 1 < len(trcCentrX)):
                nextCenter = int(trcCentrX[i + 1])
                if nextCenter == center:
                    continue

                for x in range(int(center), int(nextCenter + 1)):
                    y = (x - center) * (trcCentrY[i + 1] - trcCentrY[i]) / (nextCenter - center) + trcCentrY[i]
                    py = int(y)
                    np.append(NewTracePoints, y, axis = 1)
                    if x < w:
                        rows = np.where(self.FieldMatrix[:, x] == LocalID)[0]
                        splits = np.where(np.diff(rows) > 1)[0] + 1
                        chunks = np.split(rows, splits)
                        for chunk in chunks:
                            self.PointMatrix[chunk, x] = y

            cv2.line(
                self.FieldMatrix,
                (int(center), int(trcMin[i])),
                (int(center), int(trcMax[i])),
                LocalID,
                thickness = self.highlightwidth
            )

        self.TraceMatrix = np.vstack((self.TraceMatrix, NewTracePoints))
        
        self.HitReady.emit()

    def Query(self, xPix, yPix, appendMode = False, click = True):
        xPix -= padding
        yPix -= padding

        self.HitResult.Valid     = False
        self.HitResult.CurrentID = None
        self.HitResult.AxisX     = None
        self.HitResult.AxisY     = None

        # if ((xPix >= 0) and (xPix < self.Canvas.width() - 2 * padding) and (yPix >= 0) and (yPix < self.Canvas.height() - 2 * padding)):
        #     hit_id = self.FieldMatrix[round(yPix), round(xPix)]

        # circle_coords = set()
        # for coords in DigitalCircle.values():
        #     for coord in coords:
        #         circle_coords.add(tuple(coord))

        # print("--- FieldMatrix Local View (Circle overlay in RED) ---")
        
        # for dy in range(max_val, -max_val - 1, -1):
        #     row_string = ""
            
        #     # Loop through columns (X-axis, left to right)
        #     for dx in range(-max_val, max_val + 1):
        #         # 1. Calculate actual matrix coordinates
        #         matrix_x = xPix + dx
        #         matrix_y = yPix + dy
                
        #         # 2. Check if within canvas bounds
        #         if (0 <= matrix_x < self.Canvas.width() - 2 * padding) and \
        #            (0 <= matrix_y < self.Canvas.height() - 2 * padding):
        #             val = self.FieldMatrix[matrix_y, matrix_x]
        #         else:
        #             val = -1 # Treat out-of-bounds as empty space
                
        #         # 3. Format the base text
        #         if val == -1:
        #             char_to_print = ". "
        #         else:
        #             char_to_print = f"{val} "
                    
        #         # 4. If the current offset is inside the DigitalCircle, turn it RED
        #         if (dx, dy) in circle_coords:
        #             # \033[91m turns text red, \033[0m resets it back to normal
        #             char_to_print = f"\033[91m{char_to_print}\033[0m"
                    
        #         row_string += char_to_print
                
        #     print(row_string)
        # print("------------------------------------------------------")

        for CoordPoints in DigitalCircle.values():
            BreakFlag = False
            for Coord in CoordPoints:
                x = xPix + Coord[0]
                y = yPix + Coord[1]
                if (0 <= x < self.Canvas.width() - 2 * padding) and (0 <= y < self.Canvas.height() - 2 * padding):
                    hit_id = self.FieldMatrix[int(y), int(x)]
                    if hit_id != -1:
                        # print("--------------------------")
                        # print("Should be -->","(", x + padding, ",", y + padding, ")")
                        self.Found_x = x
                        self.Found_y = y
                        BreakFlag = True
                        break
                else: hit_id = -1
            
            if hit_id != -1:
                if self.Signals[hit_id].Visible:
                    self.HitResult.Valid = True
                    self.HitResult.CurrentID = hit_id
                    if click:
                        if not appendMode:
                            self.HitResult.ClickedIDs.clear()
                        if hit_id not in self.HitResult.ClickedIDs:
                            self.HitResult.ClickedIDs.append(hit_id)
                    
                    self.HitResult.AxisX = self.ViewPort.View_XMin + x * self.ViewPort.View_XRng / (self.Canvas.width() - 2 * padding)
                    self.HitResult.AxisY = self.ViewPort.View_YMin + ((self.Canvas.height() - 2 * padding) - self.TraceMatrix[hit_id, int(x)]) * self.ViewPort.View_YRng / (self.Canvas.height() - 2 * padding)
                    
            else:
                self.HitResult.Valid = False
                if click and (not appendMode): self.HitResult.ClickedIDs.clear()
                self.CurrentID = None
                self.HitResult.AxisX = None
                self.HitResult.AxisY = None
            
            if click: self.HitBroadCast.emit(self.HitResult)

            if BreakFlag: break

    def get_renderable_image(self):
        # print("Renderable Image")
        h, w = self.FieldMatrix.shape
        rgb_img = np.zeros((h, w, 3), dtype=np.uint8)
        unique_ids = np.unique(self.FieldMatrix)
        for lid in unique_ids:
            if lid == -1:
                continue
            color = [int((lid * 50) % 255), int((lid * 80) % 255), 255]
            rgb_img[self.FieldMatrix == lid] = color
        
        
        self.FieldEmit.emit(rgb_img)


class HitResult:
    def __init__(self):
        self.Valid      = False
        self.ClickedIDs = []
        self.CurrentID  = None
        self.AxisX      = None
        self.AxisY      = None
    
    def HELPERReset(self):
        self.ClickedIDs.clear()
        self.Valid     = False
        self.CurrentID = None
        self.AxisX     = None
        self.AxisY     = None


class PaneController(QObject):
    PaneSelected     = Signal()
    AddGlobalCursor  = Signal(object)
    CursorRelease    = Signal()
    ReleaseHighlight = Signal()
    XZoomEnable      = Signal(bool)
    YZoomEnable      = Signal(bool)
    XZoomCommand     = Signal(object, object)
    XZoomStart       = Signal(bool)

    def __init__(self, PaneID, PaneViewModel : PaneViewModel, PaneViewPort : PaneViewPort, Canvas : PaneCanvas, HitTest : HitTest, WaveWidget : GlobalWaveWidget):
        super().__init__()
        self.PaneID         = PaneID
        self.WaveWidget     = WaveWidget
        self.ViewModel      = PaneViewModel
        self.ViewPort       = PaneViewPort
        self.Canvas         = Canvas
        self.HitTest        = HitTest
        self.HoverWidget    = HoverWidget(self.Canvas)
        self.HoverMissCount = 0
        self.MaxHoverMisses = 3
        self.XPix           = None
        self.YPix           = None
        self.LastXPix       = None
        self.LastYPix       = None
        self.Hover          = True
        self.EdgeUp         = False
        self.EdgeDn         = False
        self.AppendMode     = False
        self.LeftButton     = False
        self.RightButton    = False
        self.Command        = False
        self.Listen         = False
    
    def EventHandle(self, event = None):

        if event.type() == QEvent.Type.MouseButtonPress:
            self.XPix    = int(event.position().x())
            self.YPix    = int(event.position().y())
            self.Hover   = False
            self.Command = True
            self.Listen  = False

            self.Canvas.MousePoint = event.position()
            self.Canvas.update()
            
            if ((self.XPix <= self.Canvas.width()) and (self.YPix <= self.Canvas.height()) and (self.XPix >= 0) and (self.YPix >= 0)):
                self.PaneSelected.emit()
            
            if event.button() == Qt.LeftButton:
                self.LeftButton = True

                self.HitTest.Query(self.XPix, self.YPix, self.AppendMode)
                self.ViewModel.HighLight()
                self.Canvas.update()
                if not self.HitTest.HitResult.Valid:
                    self.ReleaseHighlight.emit()
                
                self.WaveWidget.HoverTrace.PaneID = self.PaneID
                self.WaveWidget.HoverTrace.TraceMaps.clear()
                for id in self.HitTest.HitResult.ClickedIDs:
                    self.WaveWidget.HoverTrace.TraceMaps.update({self.Canvas.ViewTraceMap[id] : self.ViewModel.PaneSignals[id].Global_ID})

            self.CursorRelease.emit()
            
            if event.button() == Qt.RightButton:
                self.RightButton = True
                self.Canvas.RectZoom    = True
                self.Canvas.ZoomStartPx = event.position()
                self.Canvas.ZoomStopPx  = event.position()

                if self.Canvas.XZoom:
                    self.Canvas.ZoomStartPx.setY(-1)
                    self.Canvas.ZoomStopPx.setY(self.Canvas.height() + 1)
                    self.XZoomStart.emit(True)
                    self.XZoomCommand.emit(self.Canvas.mapToGlobal(self.Canvas.ZoomStartPx), self.Canvas.mapToGlobal(self.Canvas.ZoomStopPx))
                
                elif self.Canvas.YZoom:
                    self.Canvas.ZoomStartPx.setX(-1)
                    self.Canvas.ZoomStopPx.setX(self.Canvas.width() + 1)
                
                self.ZoomStart = QPointF(
                    max(padding + 0.5, min(self.Canvas.ZoomStartPx.x() - padding, self.Canvas.width() - padding - 0.5)) * self.ViewPort.View_XRng/(self.Canvas.width() - 2 * padding),
                    ((self.Canvas.height() - 2 * padding) - max(padding + 0.5, min(self.Canvas.ZoomStartPx.y() - padding, self.Canvas.height() - padding - 0.5))) * self.ViewPort.View_YRng/(self.Canvas.height() - 2 * padding)
                )

                self.ZoomStop  = QPointF(
                    max(padding + 0.5, min(self.Canvas.ZoomStopPx.x() - padding, self.Canvas.width() - padding)) * self.ViewPort.View_XRng/self.Canvas.width(),
                    ((self.Canvas.height() - 2 * padding) - max(padding + 0.5, min(self.Canvas.ZoomStopPx.y() - padding, self.Canvas.height() - padding - 0.5))) * self.ViewPort.View_YRng/(self.Canvas.height() - 2 * padding)
                )

                self.Canvas.update()
        
        if event.type() == QEvent.Type.MouseMove:
            self.LastXPix = self.XPix
            self.LastYPix = self.YPix
            self.XPix = event.position().x()
            self.YPix = event.position().y()

            self.Canvas.MousePoint = event.position()
            self.Canvas.update()

            if ((not self.LeftButton) and (not self.RightButton)):
                self.Hover  = True
                self.EdgeUp = False
                self.EdgeDn = False

                if (self.LastXPix is not None) and (self.LastYPix is not None):

                    if(((self.XPix - self.LastXPix) != 0) or ((self.YPix - self.LastYPix) != 0)):
                        self.HitTest.Query(self.XPix, self.YPix, self.AppendMode, click = False)

                        if self.HitTest.HitResult.Valid:
                            XVal = self.HitTest.HitResult.AxisX
                            YVal = self.HitTest.HitResult.AxisY
                            
                            if len(self.HitTest.HitResult.ClickedIDs) != 0 and self.HitTest.HitResult.CurrentID in self.HitTest.HitResult.ClickedIDs:
                                self.HoverWidget.UpdateInfo(self.HitTest.HitResult.CurrentID, XVal, YVal, self.XPix, self.HitTest.Found_y, (self.Canvas.width() - 2 * padding), (self.Canvas.height() - 2 * padding))

                            elif len(self.HitTest.HitResult.ClickedIDs) == 0:
                                self.HoverWidget.UpdateInfo(self.HitTest.HitResult.CurrentID, XVal, YVal, self.XPix, self.HitTest.Found_y, (self.Canvas.width() - 2 * padding), (self.Canvas.height() - 2 * padding))
                            
                            self.Canvas.PointerFlag = True
                            self.Canvas.PointID     = self.HitTest.HitResult.CurrentID
                            self.Canvas.PointXPx    = self.HitTest.Found_x + padding
                            self.Canvas.PointYPx    = self.HitTest.Found_y + padding
                            self.Canvas.update()
                        
                        else:
                            self.HoverMissCount += 1

                            if self.HoverMissCount >= self.MaxHoverMisses:
                                self.HoverWidget.hide()
                                prevFlag = self.Canvas.PointerFlag
                                self.Canvas.PointerFlag = False

                                if (prevFlag != self.Canvas.PointerFlag):
                                    self.Canvas.update()

            elif self.LeftButton and self.HitTest.HitResult.Valid:
                self.Hover = False
                self.WaveWidget.EdgeActive = True
                self.Canvas.PointerFlag = False

                globalPos = QCursor.pos()
                localPos  = self.WaveWidget.mapFromGlobal(globalPos)
                self.WaveWidget.HoverTrace.move((localPos.x() - self.WaveWidget.HoverTrace.width() / 2), (localPos.y() - self.WaveWidget.HoverTrace.height() / 2))

                self.HoverWidget.hide()
                self.Canvas.update()
                self.WaveWidget.update()
                self.WaveWidget.HoverTrace.show()

            if self.Canvas.RectZoom:
                self.Canvas.ZoomStopPx = event.position()
                self.Canvas.ZoomStopPx = QPointF(
                    max(0.5, min(self.Canvas.ZoomStopPx.x(), self.Canvas.width() - 0.5)),
                    max(0.5, min(self.Canvas.ZoomStopPx.y(), self.Canvas.height() - 0.5))
                )

                if   self.Canvas.XZoom:
                    self.Canvas.ZoomStopPx.setY(self.Canvas.height() + 1)
                    self.XZoomCommand.emit(self.Canvas.mapToGlobal(self.Canvas.ZoomStartPx), self.Canvas.mapToGlobal(self.Canvas.ZoomStopPx))

                elif self.Canvas.YZoom: self.Canvas.ZoomStopPx.setX(self.Canvas.width() + 1)

                self.Canvas.update()

        if event.type() == QEvent.Type.MouseButtonRelease:
            self.LeftButton  = False
            self.RightButton = False
            self.Hover       = True

            self.Canvas.MousePoint = None

            self.WaveWidget.EdgeActive = False
            self.WaveWidget.HoverTrace.hide()

            if self.Canvas.RectZoom:
                self.Canvas.ZoomStopPx = QPointF(event.position())

                if   self.Canvas.XZoom:
                    self.Canvas.ZoomStopPx.setY(self.Canvas.height())
                    self.XZoomCommand.emit(self.Canvas.mapToGlobal(self.Canvas.ZoomStartPx), self.Canvas.mapToGlobal(self.Canvas.ZoomStopPx))
                    self.XZoomStart.emit(False)

                elif self.Canvas.YZoom: self.Canvas.ZoomStopPx.setX(self.Canvas.width())

                self.ZoomStop = QPointF(
                    max(padding, min(self.Canvas.ZoomStopPx.x() - padding, self.Canvas.width() - padding)) * self.ViewPort.View_XRng/(self.Canvas.width() - 2 * padding),
                    ((self.Canvas.height() - 2 * padding) - max(padding, min(self.Canvas.ZoomStopPx.y() - padding, self.Canvas.height() - padding))) * self.ViewPort.View_YRng/(self.Canvas.height() - 2 * padding)
                )

                if ((abs(self.Canvas.ZoomStartPx.x() - self.Canvas.ZoomStopPx.x()) >= 7.5) and (abs(self.Canvas.ZoomStartPx.y() - self.Canvas.ZoomStopPx.y()) >= 7.5)):
                    self.ViewPort.RectZoomPort(self.ZoomStart, self.ZoomStop)
                
                self.Canvas.RectZoom    = False
                self.Canvas.ZoomStartPx = None
                self.Canvas.ZoomStopPx  = None

            self.Canvas.update()
            self.WaveWidget.EdgeWidet.hide()
            self.WaveWidget.TraceTransfer()

            self.Command = False
            self.Listen  = True
        
        if event.type() == QEvent.Type.KeyPress:
            self.Command = True
            self.Listen  = False
            if event.key() == Qt.Key_F:
                self.ViewPort.FitPort()
            elif event.key() == Qt.Key_X:
                self.Canvas.XZoom = True
                self.Canvas.YZoom = False
                self.XZoomEnable.emit(True)
                self.YZoomEnable.emit(False)
            elif event.key() == Qt.Key_Y:
                self.Canvas.XZoom = False
                self.Canvas.YZoom = True
                self.XZoomEnable.emit(False)
                self.YZoomEnable.emit(True)
            elif event.key() == Qt.Key_Z:
                self.Canvas.XZoom = False
                self.Canvas.YZoom = False
                self.XZoomEnable.emit(False)
                self.YZoomEnable.emit(False)
            elif event.key() == Qt.Key_Up:
                self.ViewPort.NavUp()
            elif event.key() == Qt.Key_Down:
                self.ViewPort.NavDn()
            elif event.key() == Qt.Key_Right:
                self.ViewPort.NavRt()
            elif event.key() == Qt.Key_Left:
                self.ViewPort.NavLt()
            elif event.key() == Qt.Key_Shift:
                self.AppendMode = True
            elif event.key() == Qt.Key_Delete:
                self.ViewModel.RemovePaneSignal()
            elif event.key() == Qt.Key_V:
                GlobalPosition = QCursor.pos()
                LocalPosition  = self.Canvas.mapFromGlobal(GlobalPosition)
                x = LocalPosition.x()
                y = LocalPosition.y()
                if (1 < x < self.Canvas.width() - 2) and (1 < y < self.Canvas.height() - 1):
                    self.AddGlobalCursor.emit(GlobalPosition)
        
        if event.type() == QEvent.Type.KeyRelease:
            self.Command = False
            self.Listen  = True
            if event.key() == Qt.Key_Shift:
                self.AppendMode = False

        if event.type() == QEvent.Type.Enter:
            self.Command = True
            self.Listen  = False

        if event.type() == QEvent.Type.Leave:
            self.Command = False
            self.Listen  = True

            self.Canvas.MousePoint = None
            self.HoverWidget.hide()
            self.Canvas.PointerFlag = False
            self.Canvas.update()

    def HELPERXZoomRespond(self, startPx, stopPx):
        if self.Command:
            return

        self.Canvas.ZoomStartPx = self.Canvas.mapFromGlobal(startPx)
        self.Canvas.ZoomStopPx  = self.Canvas.mapFromGlobal(stopPx )
        self.Canvas.ZoomStartPx.setY(-1)
        self.Canvas.ZoomStopPx.setY(self.Canvas.height() + 1)
        
        self.Canvas.update()

    def HELPERXZoomStart(self, decide):
        if self.Command:
            return

        self.Canvas.RectZoom = decide
        self.Canvas.update()


class PaneCursor(QWidget):
    pass

