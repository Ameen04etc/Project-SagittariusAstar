from importlib.resources import path
from Sagittarius_A import Ui_SagittariusA
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QSplitter, QVBoxLayout, QHBoxLayout,
                               QScrollBar)
from PySide6.QtCore import    (QProcess, Qt, QObject,
                               Signal, QRectF, QPointF,
                               Slot, QRect, QEvent,
                               QSize)
from PySide6.QtWidgets import (QFileSystemModel, QHeaderView, QSizePolicy,
                               QPushButton, QToolButton)
from PySide6.QtGui import     (QPainter, QColor, QPen,
                               QPixmap, QFont, QMouseEvent)
from numba import njit
import os
import numpy as np
from supernovaEngine import *
from epsilonMajoris import *


class MainWindow(QMainWindow):
    ScrollParameters = Signal(float, float, float)

    def __init__(self):
        print("MainWindow init called")
        super().__init__()
        self.ui = Ui_SagittariusA()
        self.setWindowTitle("Sagittarius A*")
        self.ui.setupUi(self)

        self.database_startup()
        self.Terminal = MainTermWidget(self.ui.terminalout)
        terminal_layout = QVBoxLayout(self.ui.terminalout)
        terminal_layout.setContentsMargins(0, 0, 0, 0)
        terminal_layout.addWidget(self.Terminal)


        self.x        = np.linspace(0,10,200000)
        self.signal1  = np.sin(self.x); """+ np.sin(100 * self.x)"""
        self.signal2  = np.cos(self.x)
        self.signal2  = np.ones(len(self.x))
        self.signal2[9990:10010] -= 1
        self.signal2[19980:20000] += 2
        self.signal3  = np.sinc(self.x)
        self.signal4  = self.signal1**3
        self.signal5  = np.sqrt(np.sqrt(self.x))
        T = 0.9
        self.signal6  = self.tanh_square_wave(self.x, T)

        self.wavewindow   = WaveWindow(self.ui.WaveWindow)
        self.wavewindow.SetAxis(self.x)
        self.wavewindow.AddSignal(self.signal1, "signal1")
        self.wavewindow.AddSignal(self.signal2, "signal2")
        self.wavewindow.AddSignal(self.signal3, "signal3")
        self.wavewindow.AddSignal(self.signal4, "signal4")
        self.wavewindow.AddSignal(self.signal5, "signal5")
        self.wavewindow.AddSignal(self.signal6, "signal6")
        self.wavewindow.AddSignal(self.signal6**2, "signal7")


    def database_startup(self):       
        self.setup_file_browser()
        self.ui.FileSystem_exec.setRootIndex(self.model.index(self.current_path))
        self.ui.FileSystem_run.setRootIndex(self.model.index(self.current_path))

        # Executables Header Customization
        header = self.ui.FileSystem_exec.header()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setStretchLastSection(False)
        header_2 = self.ui.FileSystem_run.header()
        header_2.setSectionResizeMode(QHeaderView.Stretch)
        header_2.setStretchLastSection(False)

        # Enable Header Sorting
        self.ui.FileSystem_exec.setModel(self.model)
        self.ui.FileSystem_run.setModel(self.model)
        self.ui.FileSystem_exec.setSortingEnabled(True)
        self.ui.FileSystem_run.setSortingEnabled(True)

        # Signals and Slots for Directory Navigation
        self.ui.FileSystem_exec.doubleClicked.connect(self.folder_double_clicked)
        self.ui.FileSystem_run.doubleClicked.connect(self.folder_double_clicked)      
        self.ui.up_exec.clicked.connect(self.go_up)
        self.ui.back_exec.clicked.connect(self.go_back)
        self.ui.fwd_exec.clicked.connect(self.go_forward)
        self.ui.up_run.clicked.connect(self.go_up)
        self.ui.back_run.clicked.connect(self.go_back)
        self.ui.fwd_run.clicked.connect(self.go_forward)
        self.ui.Executables_btn.clicked.connect(self.open_executables_folder)
        self.ui.Runs_btn.clicked.connect(self.open_runs_folder)

        # Initializations
        self.ui.Executables_btn.setChecked(True)
        self.open_executables_folder()

    def setup_file_browser(self):
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        self.ui.FileSystem_exec.setModel(self.model)
        self.ui.FileSystem_run.setModel(self.model)
        self.current_path = os.getcwd()
        self.back_history = []
        self.forward_history = []
        self.change_directory(self.current_path, 0)
        self.change_directory(self.current_path, 1)

    def change_directory(self, path, idx):
        self.current_path = path
        if idx == 0:
            self.ui.FileSystem_exec.setRootIndex(self.model.index(path))
            self.ui.path_exec.setText(path)
            self.ui.search_exec.setPlaceholderText("Search " + os.path.basename(self.current_path))

        if idx == 1:
            self.ui.FileSystem_run.setRootIndex(self.model.index(path))
            self.ui.path_run.setText(path)
            self.ui.search_run.setPlaceholderText("Search " + os.path.basename(self.current_path))

    def folder_double_clicked(self, index):
        path = self.model.filePath(index)
        path = os.path.normpath(path)
        idx = self.ui.stackedWidget.currentIndex()
        if os.path.isdir(path):
            self.back_history.append(self.current_path)
            self.forward_history.clear()
            self.change_directory(path, idx)

    def path_edit(self, path):
        path = os.path.normpath(path)
        index = self.model.index(path)

    def go_up(self):
        parent = os.path.dirname(self.current_path)
        idx = self.ui.stackedWidget.currentIndex()
        if parent != self.current_path:
            self.back_history.append(self.current_path)
            self.forward_history.clear()
            self.change_directory(parent, idx)

    def go_back(self):
        idx = self.ui.stackedWidget.currentIndex()
        if self.back_history:
            self.forward_history.append(self.current_path)
            path = self.back_history.pop()
            self.change_directory(path, idx)

    def go_forward(self):
        idx = self.ui.stackedWidget.currentIndex()
        if self.forward_history:
            self.back_history.append(self.current_path)
            path = self.forward_history.pop()
            self.change_directory(path, idx)

    def open_executables_folder(self):
        self.ui.Runs_btn.setChecked(False)
        self.ui.stackedWidget.setCurrentIndex(0)

    def open_runs_folder(self):
        self.ui.Executables_btn.setChecked(False)
        self.ui.stackedWidget.setCurrentIndex(1)

    # def setup_terminal(self):
    #     # Create PowerShell process
    #     self.process = QProcess(self)
    #     # Receive output
    #     self.process.readyReadStandardOutput.connect(self.handle_stdout)
    #     self.process.readyReadStandardError.connect(self.handle_stderr)
    #     # Execute command when Enter is pressed
    #     self.ui.commandline.returnPressed.connect(self.send_command)
    #     # Start PowerShell
    #     self.process.start("powershell.exe")

    # def handle_stdout(self):
    #     data = self.process.readAllStandardOutput()
    #     text = bytes(data).decode(errors="ignore")
    #     self.ui.terminalout.appendPlainText(text)

    # def handle_stderr(self):
    #     data = self.process.readAllStandardError()
    #     text = bytes(data).decode(errors="ignore")
    #     self.ui.terminalout.appendPlainText(text)

    # def send_command(self):
    #         command = self.ui.commandline.text()
    #         self.process.write(
    #             (command + "\n").encode()
    #         )
    #         self.ui.commandline.clear()

    def tanh_square_wave(self, t, T, steepness=5.0, low=-1.0, high=1.0):
        """
        Generates a 50% duty cycle square wave with tanh transitions.
        
        Parameters:
        t         : NumPy array of time values.
        T         : Time period of the wave.
        steepness : Controls edge sharpness (higher = closer to an ideal square wave).
        low       : Minimum value of the wave.
        high      : Maximum value of the wave.
        """
        # 1. Generate the periodic base using sine
        angular_freq = 2 * np.pi / T
        base_wave = np.sin(angular_freq * t)
        
        # 2. Apply tanh to create the smoothed square shape
        normalized_wave = np.tanh(steepness * base_wave)
        
        # 3. Scale and shift from [-1, 1] to the requested [low, high] range
        amplitude = (high - low) / 2.0
        offset = (high + low) / 2.0
        
        return amplitude * normalized_wave + offset

app = QApplication([])
window = MainWindow()
window.show()
app.exec()