from importlib.resources import path
from Sagittarius_A import Ui_SagittariusA
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QSplitter, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QScrollBar, QSizePolicy,
                               QPushButton, QToolButton, QToolTip,
                               QFrame, QLabel, QTreeView)
from PySide6.QtCore import    (QProcess, Qt, QObject,
                               Signal, QRectF, QRect,
                               Slot, QPointF, QPoint,
                               QSize, QEvent, QSignalBlocker,
                               QTimer)
from PySide6.QtGui import     (QPainter, QColor, QPen,
                               QPixmap, QFont, QMouseEvent,
                               QImage, QCursor, QPainterPath,
                               QStandardItemModel, QStandardItem,
                               QFontMetrics, QKeySequence)
from enum import Enum, auto
from typing import cast
import termCore
import os
import numpy as np
import cv2
import math
import time
import shiboken6
import traceback

"""
TerminalWidget
│
├── paints the screen
│
├── handles mouse
│
└── forwards keyboard
            │
            ▼
TerminalBuffer
│
├── Screen Cells
├── Cursor
├── Scrollback
└── Selection
            ▲
            │
TerminalParser
│
├── Printable chars
├── Newlines
├── ANSI sequences
└── Cursor commands
            ▲
            │
TerminalSession
│
├── ConPTY
├── stdin
├── stdout
└── stderr"""


"""
terminal/
│
├── widget/
│   ├── TerminalWidget.py
│   └── TerminalRenderer.py
│
├── model/
│   ├── TerminalBuffer.py
│   ├── TerminalCell.py
│   └── TerminalCursor.py
│
├── parser/
│   ├── TerminalParser.py
│   └── AnsiParser.py
│
├── session/
│   ├── TerminalSession.py
│   └── ConPTYSession.py
│
└── utils/
"""


RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"

class MainTermWidget(QWidget):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.TermWidget = TerminalWidget()
        self.ScrollBar  = ScrollBar(self.TermWidget)
        self.LayoutConfig()
        self.TermWidget.ScrollCommand.connect(self.UpdateScrollbar)
        self.ScrollBar.valueChanged.connect(self.ScrollCommand)

    def LayoutConfig(self):
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        Layout = QHBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(0)

        Layout.addWidget(self.TermWidget)
        Layout.addWidget(self.ScrollBar)

    def UpdateScrollbar(self):
        with QSignalBlocker(self.ScrollBar):
            self.ScrollBar.setMinimum(0)
            self.ScrollBar.setSingleStep(1)
            self.ScrollBar.setPageStep(len(self.TermWidget.Buffer.lines))
            self.ScrollBar.setValue(self.TermWidget.Buffer.TopRow)
            self.ScrollBar.setMaximum(self.TermWidget.Buffer.TotalLines - self.ScrollBar.pageStep() + self.ScrollBar.minimum())
            
        self.ScrollBar.StyleConfig()

    def ScrollCommand(self, value):
        self.TermWidget.Buffer.TopRow = min(max(value, 0), len(self.TermWidget.Buffer.ScrollBack))
        self.TermWidget.update()


class TerminalWidget(QWidget):
    ScrollCommand = Signal()
    Send_Back     = Signal()

    @property
    def pixelRatio(self): return self.devicePixelRatioF()

    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.Buffer        = TerminalBuffer()
        self.Parser        = TerminalParser(self.Buffer)
        self.Session       = TerminalSession(self.Parser)
        self.TermRenderer  = TerminalRenderer(self)
        self.TopMargin     = 5
        self.LeftMargin    = 10
        self.Font          = QFont()
        self.Resizecounter = 0
        self.Scrollcounter = 0
        self.UpdateCounter = 0
        self.CleanDirt     = False
        self.ResizeActive  = False
        self.ScrollActive  = False
        self.ScrollArea    = []
        self.StoredTop     = None
        self.StoredBottom  = None
        self.LineImages    : list[QImage] = []
        self.MouseClick    = False
        self.MouseMove     = False
        self.CursorVisible = True
        self.CursorTimer   = QTimer(self)
        
        self.Font.setPixelSize(15)
        self.Font.setFamilies(["Consolas", "Courier New"])
        self.Font.setStyleHint(QFont.StyleHint.Monospace)
        self.Font.setFixedPitch(True)

        FontMetrics        = QFontMetrics(self.Font)
        self.CellWidth     = FontMetrics.horizontalAdvance("W")
        self.CellHeight    = FontMetrics.height()
        self.Ascent        = FontMetrics.ascent()

        for _ in self.Buffer.lines:
            img = QImage(
                int(self.width() * self.pixelRatio),
                int(self.CellHeight * self.pixelRatio),
                QImage.Format.Format_ARGB32_Premultiplied
            )
            img.setDevicePixelRatio(self.pixelRatio)
            img.fill(Qt.GlobalColor.transparent)
            self.LineImages.append(img)
        
        self.Font.setWeight(QFont.Weight.Normal)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        self.Send_Back.connect(lambda: setattr(self.Buffer, 'BackSpace', True))
        self.Session.OutputReceived.connect(self.update)
        self.CursorTimer.timeout.connect(self.CursorToggle)
        self.CursorTimer.start(500)

        self.setMinimumSize(QSize(500, 50))

    def paintEvent(self, event):
        termPainter = QPainter(self)
        termPainter.setFont(self.Font)

        termPainter.fillRect(
            event.rect(), QColor(24, 24, 24)
        )

        self.TermRenderer.RenderCells(self.LineImages)
        for line, image in enumerate(self.LineImages):
            termPainter.drawImage(0, line * self.CellHeight + self.TopMargin, image)
        self.TermRenderer.RenderCursor(termPainter, self.Parser.CursVis)
        self.TermRenderer.RenderSelection(termPainter)


        gridPen = QPen(QColor(255, 255, 255, 70))
        termPainter.setPen(gridPen)
        
        # gridFont = QFont(self.Font)
        # gridFont.setPointSize(max(5, self.Font.pointSize() - 10))
        # termPainter.setFont(gridFont)
        
        # for row in range(len(self.Buffer.lines)):
                
        #     for col in range(self.Buffer.MaxCols):
        #         x = col * self.CellWidth + self.LeftMargin
        #         y_top = (row) * self.CellHeight + self.TopMargin - 3
                
        #         cellRect = QRect(
        #             x, y_top, 
        #             self.CellWidth, self.CellHeight
        #         )
                
        #         termPainter.drawRect(cellRect)
                
        #         termPainter.drawText(cellRect, Qt.AlignmentFlag.AlignCenter, f"{col}")

        termPainter.end()
        self.ScrollCommand.emit()

    def CursorToggle(self):
        self.CursorVisible = not self.CursorVisible

        CursScreenRow = self.Buffer.Cursor.Row + len(self.Buffer.ScrollBack) - self.Buffer.TopRow
        if 0 <= CursScreenRow < self.Buffer.MaxRows:
            self.UpdateCounter += 1
            self.update()
        else:
            if self.UpdateCounter != 0: self.update
            self.UpdateCounter = 0

    def PixelToCell(self, xPix, yPix):
        CellCol = min(max(int((xPix - self.LeftMargin) // self.CellWidth), 0), self.Buffer.MaxCols - 1)
        CellRow = min(max(int((yPix - self.TopMargin - self.Ascent) // self.CellHeight + 1), 0), self.Buffer.MaxRows - 1)

        return CellRow, CellCol

    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()
        self.Buffer.ScrollActive = False

        # 1. Handle special keys (Arrow keys, Enter, Backspace)
        if key == Qt.Key_Right:
            self.Session.Send("\x1b[C")
        elif key == Qt.Key_Left:
            self.Session.Send("\x1b[D")
        elif key == Qt.Key_Up:
            self.Session.Send("\x1b[A")
        elif key == Qt.Key_Down:
            self.Session.Send("\x1b[B")
        elif key == Qt.Key_Backspace:
            if self.Buffer.Cursor.Col == 0 or self.Buffer.Cursor.Col == self.Buffer.MaxCols: self.Send_Back.emit()
            self.Session.Send("\x7f")
        elif key == Qt.Key_Delete:
            self.Session.Send("\x1b[3~")
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            self.Session.Send("\r")
            
        # 2. Handle normal typing (letters, numbers, space)
        elif text:
            # self.Parser.feed(text)
            self.Session.Send(text)

        print("KEY PRESSED:", repr(text), "QT_KEY:", key)

        # self.Buffer.Dirty.Screen = True
        self.StoredTop        = self.Buffer.TopRow
        self.StoredBottom     = self.Buffer.BottomRow
        self.Buffer.TopRow    = len(self.Buffer.ScrollBack)
        self.Buffer.BottomRow = self.Buffer.TopRow + len(self.Buffer.lines) - 1

        ScrollLength  = self.StoredTop - self.Buffer.TopRow
        if ScrollLength <= self.Buffer.MaxRows - 1: self.ScrollActive = True
        else:
            self.ScrollActive = False
            self.Buffer.Dirty.Screen = True

        self.CleanDirt = True

        print("TOPROW =", self.Buffer.TopRow)
        print("SCROLLBACK =", len(self.Buffer.ScrollBack))
        self.ScrollCommand.emit()
        self.update()
        # QTimer.singleShot(10, self.update)
        # QTimer.singleShot(20, self.update)

    def resizeEvent(self, event):
        def CountIncrease():
            PrevCount   = self.Resizecounter
            self.Resizecounter += 1
            if (PrevCount <= 0) and (self.Resizecounter > 0):
                self.ResizeActive = True
        
        def CountDecrease():
            PrevCount   = self.Resizecounter
            self.Resizecounter -= 1
            print(len(self.Buffer.lines))
            if (PrevCount > 0) and (self.Resizecounter <= 0):
                self.ResizeActive = False

        self.Buffer.MaxRows = (self.height() - self.TopMargin) // self.CellHeight
        self.Buffer.MaxCols = (self.width() - self.LeftMargin) // self.CellWidth

        self.Buffer.Buffer_Resize()
        self.Session.Resize(self.Buffer.MaxCols, self.Buffer.MaxRows)

        CountIncrease()
        QTimer.singleShot(100, CountDecrease)
        
        self.LineImages = []
        for _ in self.Buffer.lines:
            img = QImage(
                int(self.width() * self.pixelRatio),
                int(self.CellHeight * self.pixelRatio),
                QImage.Format.Format_ARGB32_Premultiplied
            )
            img.setDevicePixelRatio(self.pixelRatio)
            img.fill(Qt.GlobalColor.transparent)
            self.LineImages.append(img)

        self.ScrollCommand.emit()
        self.update()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        print(f"{BLUE}SCROLLACTIVE =", self.ScrollActive,f"{RESET}")
        self.PrintBuffer()
        self.MouseClick = True
        self.Buffer.Selection.SelectActive = False
        self.Buffer.Selection.SelectStart.Row, self.Buffer.Selection.SelectStart.Col = self.PixelToCell(event.position().x(), event.position().y())
        self.Buffer.Selection.SelectStop.Reset()
        self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.MouseClick:
            self.Buffer.Selection.SelectActive = True
            self.MouseMove = True
            self.Buffer.Selection.SelectStop.Row, self.Buffer.Selection.SelectStop.Col = self.PixelToCell(event.position().x(), event.position().y())
            print(self.Buffer.Selection.SelectStop.Row)
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.MouseClick = False
        if self.MouseMove:
            self.Buffer.Selection.SelectStop.Row, self.Buffer.Selection.SelectStop.Col = self.PixelToCell(event.position().x(), event.position().y())
            self.MouseMove = False
        else:
            self.Buffer.Selection.SelectStart.Reset()
            self.Buffer.Selection.SelectStop .Reset()
        
        self.update()
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        pixel_delta = event.pixelDelta().y()
        angle_delta = event.angleDelta().y()
        scroll_step = 0

        if pixel_delta != 0:
            scroll_step = -(pixel_delta // (2 * self.CellHeight))
        elif angle_delta != 0:
            rows_per_click = 1
            scroll_step = -int((angle_delta / 120.0) * rows_per_click)

        if scroll_step == 0:
            if angle_delta > 0 or pixel_delta > 0:
                scroll_step = -1
            elif angle_delta < 0 or pixel_delta < 0:
                scroll_step = 1
        
        self.StoredTop    = self.Buffer.TopRow
        self.StoredBottom = self.Buffer.BottomRow

        self.Buffer.TopRow    = min(max((self.Buffer.TopRow + scroll_step), 0), len(self.Buffer.ScrollBack))
        self.Buffer.BottomRow = self.Buffer.TopRow - self.StoredTop + self.StoredBottom

        if self.Buffer.TopRow == len(self.Buffer.ScrollBack): self.Buffer.ScrollActive = False
        else: self.Buffer.ScrollActive = True

        if self.StoredTop == self.Buffer.TopRow: self.ScrollActive = False
        else: self.ScrollActive = True

        self.ScrollCommand.emit()
        # self.LineScroll(scroll_step)
        self.update()
        event.accept()

    # def LineScroll(self, dy):
    #     if not self.ScrollActive:
    #         return
    #     rows = abs(dy)
    #     if dy <= 0:
    #         self.ScrollArea = [0, rows - 1]
    #     elif dy > 0:
    #         self.ScrollArea = [(self.Buffer.MaxRows - rows), self.Buffer.MaxRows - 1]
    #     # print(self.ScrollArea)
    #     # if not self.ScrollActive:
    #     #     return
    #     self.update()

    def PrintBuffer(self):
        print("BUFFER START AT LINE NO =", len(self.Buffer.ScrollBack))
        print(f"{YELLOW}", end="")
        for line in self.Buffer.lines:
            for cell in line.cells:
                print(cell.char, end="")
                # print(repr(cell.char), end="")
            print()
        print(f"{RESET}")


class TerminalRenderer(QObject):

    def __init__(self, parent : 'TerminalWidget'):
        super().__init__(parent)
        self.font_cache = {}

    def parent(self) -> 'TerminalWidget':
        return cast('TerminalWidget', super().parent())

    def RenderCells(self, Images : list[QImage]):
        base_font     = self.parent().Font
        self.LineFont = QFont(base_font)
        Buffer        = self.parent().Buffer
        CurrentTop    = self.parent().Buffer.TopRow
        StoredTop     = self.parent().StoredTop
        CurrentBottom = self.parent().Buffer.BottomRow
        StoredBottom  = self.parent().StoredBottom

        self.LineFont.setPointSize(8)

        def StampCell(painter : QPainter, col, cell : TerminalCell):
            x = col * self.parent().CellWidth + self.parent().LeftMargin
            # y = row * self.parent().CellHeight + self.parent().TopMargin + self.parent().Ascent
            y = self.parent().Ascent

            cellRect = QRect(
                x, y - self.parent().Ascent,
                self.parent().CellWidth, self.parent().CellHeight
            )


            fg_color = QColor(cell.SelfColor)
            bg_color = QColor(cell.BackColor)

            if cell.Reverse:
                fg_color, bg_color = bg_color, fg_color
            if cell.Faint:
                fg_color.setAlpha(128)
            
            painter.fillRect(cellRect, bg_color)

            if cell.Conceal:
                return

            font_key = (cell.Bold, cell.Italic, cell.UndLine, cell.StrikeThru)

            if font_key not in self.font_cache:
                new_font = QFont(base_font)
                if cell.Bold:       new_font.setBold(True)
                if cell.Italic:     new_font.setItalic(True)
                if cell.UndLine:    new_font.setUnderline(True)
                if cell.StrikeThru: new_font.setStrikeOut(True)

                self.font_cache[font_key] = new_font

            painter.setFont(self.font_cache[font_key])
            painter.setPen(QPen(fg_color))

            painter.drawText(x, y, cell.char)
            if cell.DbUndLine:
                line_y1 = y + 2
                line_y2 = y + 4
                painter.drawLine(x, line_y1, x + self.parent().CellWidth, line_y1)
                painter.drawLine(x, line_y2, x + self.parent().CellWidth, line_y2)

        if self.parent().ScrollActive:
            ScrollLength  = StoredTop - CurrentTop
            print("SCROLL LENGTH = ", ScrollLength)
            
            if abs(ScrollLength) >= Buffer.MaxRows:
                self.parent().ScrollActive = False
            else:
                if ScrollLength > 0:
                    for _ in range(ScrollLength): Images.insert(0, Images.pop())
                    for screenIDX, lineIDX in enumerate(range(CurrentTop, StoredTop)):
                        if screenIDX >= len(Images): 
                            break

                        if lineIDX >= len(Buffer.ScrollBack): line = Buffer.lines[lineIDX - len(Buffer.ScrollBack)]
                        else: line = Buffer.ScrollBack[lineIDX]

                        Images[screenIDX].fill(Qt.GlobalColor.transparent)
                        painter = QPainter(Images[screenIDX])
                        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
                        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

                        # painter.setFont(self.LineFont)
                        # painter.setPen(QPen(QColor(100, 100, 100)))
                        # painter.drawText(0, self.parent().Ascent, str(lineIDX))

                        for col, cell in enumerate(line.cells): StampCell(painter, col, cell)

                        painter.end()
                else:
                    for _ in range(abs(ScrollLength)): Images.append(Images.pop(0))
                    screenIDX = len(Images) - 1
                    for lineIDX in range(CurrentBottom, StoredBottom, -1):
                        if lineIDX >= len(Buffer.ScrollBack): line = Buffer.lines[lineIDX - len(Buffer.ScrollBack)]
                        else: line = Buffer.ScrollBack[lineIDX]

                        Images[screenIDX].fill(Qt.GlobalColor.transparent)
                        painter = QPainter(Images[screenIDX])
                        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
                        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

                        # painter.setFont(self.LineFont)
                        # painter.setPen(QPen(QColor(100, 100, 100)))
                        # painter.drawText(0, self.parent().Ascent, str(lineIDX))

                        for col, cell in enumerate(line.cells): StampCell(painter, col, cell)
                        screenIDX -= 1

                        painter.end()

        if (not self.parent().ScrollActive) or self.parent().CleanDirt:
            self.parent().CleanDirt = False
            for screenIDX, lineIDX in enumerate(range(CurrentTop, CurrentBottom + 1)):
                termIDX = lineIDX - len(Buffer.ScrollBack)
                if not (0 <= termIDX < Buffer.MaxRows): continue

                if termIDX in Buffer.DirtyLines:
                    Images[screenIDX].fill(Qt.GlobalColor.transparent)
                    painter = QPainter(Images[screenIDX])
                    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
                    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

                    for Col, cell in enumerate(line.cells): StampCell(painter, Col, cell)
                    painter.end()

                elif Buffer.DirtyCells[termIDX]:
                    painter = QPainter(Images[screenIDX])
                    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
                    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

                    for Col in Buffer.DirtyCells[termIDX]: StampCell(painter, Col, Buffer.lines[termIDX].cells[Col])
                    painter.end()


            # if Buffer.Dirty.Screen:
            #     for screenIDX, lineIDX in enumerate(range(CurrentTop, CurrentBottom + 1)):
            #         if screenIDX >= len(Images):
            #             break

            #         if lineIDX >= len(Buffer.ScrollBack): line = Buffer.lines[lineIDX - len(Buffer.ScrollBack)]
            #         else: line = Buffer.ScrollBack[lineIDX]

            #         Images[screenIDX].fill(Qt.GlobalColor.transparent)
            #         painter = QPainter(Images[screenIDX])
            #         painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            #         painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            #         for Col, cell in enumerate(line.cells): StampCell(painter, Col, cell)
            #         painter.end()
                
            #     Buffer.Dirty.Screen = False
            # else:
            #     for row, line in enumerate(Buffer.lines):
            #         if row in Buffer.DirtyLines:
            #             pass

            #     if Buffer.Dirty.ShiftUp > 0:
            #         for _ in range(Buffer.Dirty.ShiftUp):
            #             Images.append(Images.pop(0))
            #             Images[-1].fill(Qt.GlobalColor.transparent) 
            #         Buffer.Dirty.ShiftUp = 0

            #     if Buffer.Dirty.Lines:
            #         for screenIDX, lineIDX in enumerate(range(CurrentTop, CurrentBottom + 1)):
            #             if screenIDX >= len(Images):
            #                 break
            #             elif lineIDX not in Buffer.Dirty.Lines:
            #                 continue
                        
            #             if lineIDX >= len(Buffer.ScrollBack): line = Buffer.lines[lineIDX - len(Buffer.ScrollBack)]
            #             else: line = Buffer.ScrollBack[lineIDX]

            #             # Images[screenIDX].fill(Qt.GlobalColor.transparent)
            #             painter = QPainter(Images[screenIDX])
            #             painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            #             painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    
            #             for Col, cell in enumerate(line.cells): StampCell(painter, Col, cell)
            #             painter.end()
                    
            #         Buffer.Dirty.Lines.clear()

            #     for Dcell in Buffer.Dirty.cells:
            #         if not (CurrentTop <= Dcell.Row <= CurrentBottom): continue
            #         screenIDX = Dcell.Row - CurrentTop

            #         if Dcell.Row >= len(Buffer.ScrollBack): 
            #             line = Buffer.lines[Dcell.Row - len(Buffer.ScrollBack)]
            #         else:
            #             line = Buffer.ScrollBack[Dcell.Row]

            #         # Images[screenIDX].fill(Qt.GlobalColor.transparent)
            #         painter = QPainter(Images[screenIDX])
            #         painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            #         painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            #         StampCell(painter, Dcell.Col, line.cells[Dcell.Col])
            #         painter.end()

            #     Buffer.Dirty.cells.clear()

        self.parent().ScrollActive = False

    def RenderCursor(self, painter : QPainter, Vis : bool):
        if Vis:
            if self.parent().Buffer.Cursor.Col == self.parent().Buffer.MaxCols:
                CursorX = self.parent().LeftMargin
                CursorY = (self.parent().Buffer.Cursor.Row + 1 + len(self.parent().Buffer.ScrollBack) - self.parent().Buffer.TopRow) * self.parent().CellHeight + self.parent().TopMargin
            else:
                CursorX = self.parent().Buffer.Cursor.Col * self.parent().CellWidth + self.parent().LeftMargin
                CursorY = (self.parent().Buffer.Cursor.Row + len(self.parent().Buffer.ScrollBack) - self.parent().Buffer.TopRow) * self.parent().CellHeight + self.parent().TopMargin

            if self.parent().Buffer.Cursor.Col == self.parent().Buffer.MaxCols: opacity = 255
            else:
                if self.parent().Buffer.lines[self.parent().Buffer.Cursor.Row].cells[self.parent().Buffer.Cursor.Col].char == " ": opacity = 255
                else: opacity = 90

            CursorRect = QRect(
                CursorX, CursorY,
                self.parent().CellWidth, self.parent().CellHeight
                )

            if self.parent().CursorVisible: painter.fillRect(CursorRect, QColor(255, 255, 255, opacity))

    def RenderSelection(self, painter : QPainter):
        if self.parent().Buffer.Selection.SelectActive and self.parent().Buffer.Selection.SelectStart.Row is not None and self.parent().Buffer.Selection.SelectStop.Row is not None:
            StartRow = min(self.parent().Buffer.Selection.SelectStart.Row, self.parent().Buffer.Selection.SelectStop.Row)
            StopRow  = max(self.parent().Buffer.Selection.SelectStart.Row, self.parent().Buffer.Selection.SelectStop.Row)

            if StartRow == self.parent().Buffer.Selection.SelectStart.Row:
                StopCol  = self.parent().Buffer.Selection.SelectStop .Col
                StartCol = self.parent().Buffer.Selection.SelectStart.Col
            else:
                StopCol  = self.parent().Buffer.Selection.SelectStart.Col
                StartCol = self.parent().Buffer.Selection.SelectStop .Col
            
            if StopRow == StartRow:
                StartRow_X = max(StartCol * self.parent().CellWidth + self.parent().LeftMargin, self.parent().LeftMargin)
                StartRow_Y = (StartRow) * self.parent().CellHeight + self.parent().TopMargin
                StartRow_W = (StopCol + 1 - StartCol) * self.parent().CellWidth
                StartRow_H = self.parent().CellHeight

                painter.fillRect(
                    QRect(
                        StartRow_X, StartRow_Y,
                        StartRow_W, StartRow_H
                    ),
                    QColor(255, 255, 255, 50)
                )

            elif StopRow > StartRow:
                StartRow_X = max(StartCol * self.parent().CellWidth + self.parent().LeftMargin, self.parent().LeftMargin)
                StartRow_Y = (StartRow) * self.parent().CellHeight + self.parent().TopMargin
                StartRow_W = (self.parent().Buffer.MaxCols - StartCol) * self.parent().CellWidth
                StartRow_H = self.parent().CellHeight

                painter.fillRect(
                    QRect(
                        StartRow_X, StartRow_Y,
                        StartRow_W, StartRow_H
                    ),
                    QColor(255, 255, 255, 50)
                )

                StopRow_X = self.parent().LeftMargin
                StopRow_Y = (StopRow) * self.parent().CellHeight + self.parent().TopMargin
                StopRow_W = (StopCol + 1) * self.parent().CellWidth
                StopRow_H = self.parent().CellHeight

                painter.fillRect(
                    QRect(
                        StopRow_X, StopRow_Y,
                        StopRow_W, StopRow_H
                    ),
                    QColor(255, 255, 255, 50)
                )

            if StopRow - StartRow > 1:
                StartX = self.parent().LeftMargin
                StartY = (StartRow + 1) * self.parent().CellHeight + self.parent().TopMargin

                StopX  = self.parent().Buffer.MaxCols * self.parent().CellWidth + self.parent().LeftMargin
                StopY  = (StopRow) * self.parent().CellHeight + self.parent().TopMargin

                painter.fillRect(
                    QRect(
                        StartX, StartY,
                        StopX - StartX, StopY - StartY
                    ),
                    QColor(255, 255, 255, 50)
                )


class TerminalSession(QObject):
    OutputReceived = Signal()

    def __init__(self, Parser : TerminalParser):
        super().__init__()
        self.Parser     = Parser
        self.Session    = termCore.TerminalSession()
        self.Session.set_output_callback(self.Read)
        self.Start()

    def Start(self):
        self.Session.start()

    def Stop(self):
        self.Session.stop()

    def Send(self, char):
        self.Session.send(char.encode())

    def Resize(self, cols, rows):
        if self.Session.is_running():
            self.Session.resize(cols, rows)

    def Read(self, data : bytes):
        print("PTY OUTPUT:", repr(data))
        decoded_text = data.decode('utf-8', errors='ignore')
        # print(decoded_text, end='', flush=True)
        self.Parser.feed(data.decode())
        self.OutputReceived.emit()


class ParserState(Enum):
    GROUND      = auto()  # Normal text processing
    ESCAPE      = auto()  # Just received '\x1b'
    CSI_ENTRY   = auto()  # Just received '\x1b['
    CSI_PARAM   = auto()  # Collecting numbers like '31' or '2'
    OSC_STRING  = auto()


class TerminalParser:
    
    def __init__(self, Buffer : TerminalBuffer):
        self.Buffer = Buffer
        self.state = ParserState.GROUND
        
        # We only need one buffer for parameters now!
        self.CursVis = False
        self.csi_params = []
        self.SGRStatesRST()
        self.BuildPalette()
        self.SGR_Dict = {
            # Reset
            0   : self.SGRStatesRST,

            # Intensity
            1   : lambda: (setattr(self, 'Bold', True), setattr(self, 'Faint', False)),     # Bold
            2   : lambda: (setattr(self, 'Bold', False), setattr(self, 'Faint', True)),     # Faint
            22  : lambda: (setattr(self, 'Bold', False), setattr(self, 'Faint', False)),    # Normal Intensity

            # Italic
            3   : lambda: setattr(self, 'Italic', True),    # Italic
            23  : lambda: setattr(self, 'Italic', False),   # Normal

            # UnderLine
            4   : lambda: (setattr(self, 'UndLine', True), setattr(self, 'Db_UndLine', False)),
            21  : lambda: (setattr(self, 'UndLine', False), setattr(self, 'Db_UndLine', True)),
            24  : lambda: (setattr(self, 'UndLine', False), setattr(self, 'Db_UndLine', False)),

            # Blink
            5   : lambda: (setattr(self, 'Blink', True), setattr(self, 'RapidBlink', False)),
            6   : lambda: (setattr(self, 'Blink', False), setattr(self, 'RapidBlink', True)),
            25  : lambda: (setattr(self, 'Blink', False), setattr(self, 'RapidBlink', False)),

            # Reverse
            7   : lambda: setattr(self, 'Reverse', True),
            27  : lambda: setattr(self, 'Reverse', False),

            # Conceal
            8   : lambda: setattr(self, 'Conceal', True),
            28  : lambda: setattr(self, 'Conceal', False),  # Reveal

            # StrikeThrough
            9   : lambda: setattr(self, 'StrikeThru', True),
            29  : lambda: setattr(self, 'StrikeThru', False),

            # ForeGround
            30  : lambda: setattr(self, 'Color', QColor(*self.Palette[0])),
            31  : lambda: setattr(self, 'Color', QColor(*self.Palette[1])),
            32  : lambda: setattr(self, 'Color', QColor(*self.Palette[2])),
            33  : lambda: setattr(self, 'Color', QColor(*self.Palette[3])),
            34  : lambda: setattr(self, 'Color', QColor(*self.Palette[4])),
            35  : lambda: setattr(self, 'Color', QColor(*self.Palette[5])),
            36  : lambda: setattr(self, 'Color', QColor(*self.Palette[6])),
            37  : lambda: setattr(self, 'Color', QColor(*self.Palette[7])),

            # BackGround
            40  : lambda: setattr(self, 'BackGround', QColor(*self.Palette[0])),
            41  : lambda: setattr(self, 'BackGround', QColor(*self.Palette[1])),
            42  : lambda: setattr(self, 'BackGround', QColor(*self.Palette[2])),
            43  : lambda: setattr(self, 'BackGround', QColor(*self.Palette[3])),
            44  : lambda: setattr(self, 'BackGround', QColor(*self.Palette[4])),
            45  : lambda: setattr(self, 'BackGround', QColor(*self.Palette[5])),
            46  : lambda: setattr(self, 'BackGround', QColor(*self.Palette[6])),
            47  : lambda: setattr(self, 'BackGround', QColor(*self.Palette[7])),

            # Bright ForeGround
            90  : lambda: setattr(self, 'Color', QColor(*self.Palette[ 8])),
            91  : lambda: setattr(self, 'Color', QColor(*self.Palette[ 9])),
            92  : lambda: setattr(self, 'Color', QColor(*self.Palette[10])),
            93  : lambda: setattr(self, 'Color', QColor(*self.Palette[11])),
            94  : lambda: setattr(self, 'Color', QColor(*self.Palette[12])),
            95  : lambda: setattr(self, 'Color', QColor(*self.Palette[13])),
            96  : lambda: setattr(self, 'Color', QColor(*self.Palette[14])),
            97  : lambda: setattr(self, 'Color', QColor(*self.Palette[15])),

            # Bright BackGround
            100 : lambda: setattr(self, 'BackGround', QColor(*self.Palette[ 8])),
            101 : lambda: setattr(self, 'BackGround', QColor(*self.Palette[ 9])),
            102 : lambda: setattr(self, 'BackGround', QColor(*self.Palette[10])),
            103 : lambda: setattr(self, 'BackGround', QColor(*self.Palette[11])),
            104 : lambda: setattr(self, 'BackGround', QColor(*self.Palette[12])),
            105 : lambda: setattr(self, 'BackGround', QColor(*self.Palette[13])),
            106 : lambda: setattr(self, 'BackGround', QColor(*self.Palette[14])),
            107 : lambda: setattr(self, 'BackGround', QColor(*self.Palette[15]))
        }

    def SGRStatesRST(self):
        self.SGR_Enable = False
        self.Color      = QColor(229, 229, 229)
        self.BackGround = QColor(24, 24, 24)
        self.Bold       = False
        self.Faint      = False
        self.Italic     = False
        self.UndLine    = False
        self.Db_UndLine = False
        self.Blink      = False
        self.RapidBlink = False
        self.StrikeThru = False
        self.Reverse    = False
        self.Conceal    = False

    def feed(self, text):
        for ch in text:
            if   ch == '\r':
                self.Buffer.Cursor.Col = 0
                continue
            elif ch == '\n':
                self.Buffer.NewLine(Logical = True, Append = True)
                continue
            elif ch == '\x08':
                if self.Buffer.Cursor.Col > 0:
                    self.Buffer.Cursor.Col -= 1
                continue
            
            # 2. State Machine Routing
            if self.state == ParserState.GROUND:
                self._state_ground(ch)
                
            elif self.state == ParserState.ESCAPE:
                self._state_escape(ch)

            elif self.state == ParserState.OSC_STRING:
                self._state_osc(ch)
                
            elif self.state in (ParserState.CSI_ENTRY, ParserState.CSI_PARAM):
                self._state_csi(ch)

    def _state_ground(self, ch):
        if ch == '\x1b':
            self.state = ParserState.ESCAPE
        else:
            # Just normal text, print it to the screen!
            self.Buffer.InsertCharacter(ch, self.Color, self.BackGround, self.Bold, self.Faint, self.Italic, self.UndLine, self.Db_UndLine, self.StrikeThru, self.Reverse, self.Conceal)

    def _state_escape(self, ch):
        if ch == '[':
            # We entered a Control Sequence Indicator (CSI)
            self.state = ParserState.CSI_ENTRY
            self.csi_params = [""] # Reset our parameter buffer
        elif ch == ']':
            # It's a window title/OSC command!
            self.state = ParserState.OSC_STRING
        else:
            # It was a different escape code (like \x1bM for reverse index)
            # Handle it, then go back to ground
            self.state = ParserState.GROUND

    def _state_csi(self, ch):
        if ch.isdigit() or ch == '?':
            self.state = ParserState.CSI_PARAM
            self.csi_params[-1] += ch
            
        elif ch == ';':
            self.state = ParserState.CSI_PARAM
            self.csi_params.append("") # Get ready for the next number
            
        elif ch.isalpha():
            # An alphabetical letter means the sequence is DONE!
            self._dispatch_csi(ch)
            self.state = ParserState.GROUND  # Reset back to normal text!

    def _state_osc(self, ch):
        # The sequence ends when we hit the Bell (\x07) 
        # or the String Terminator (\x1b\\)
        if ch == '\x07' or ch == '\x9c':
            self.state = ParserState.GROUND

    def _dispatch_csi(self, final_char):
        # Helper to safely get the first parameter as an integer, defaulting to 1 or 0
        def get_param(index=0, default=1):
            if index < len(self.csi_params) and self.csi_params[index]:
                # Ignore private mode markers like '?' for simple int conversion
                clean_param = self.csi_params[index].replace('?', '')
                return int(clean_param) if clean_param.isdigit() else default
            return default

        # ----------------------------------------------------
        # SGR (Select Graphic Rendition) - Colors & Formatting
        # ----------------------------------------------------
        if final_char == 'm':
            # Default to reset (0) if no parameters are provided
            if not self.csi_params or self.csi_params == [""]:
                self.SGR_Dict[0]()
            
            # Standard 1-code SGR (e.g., \x1b[31m)
            elif len(self.csi_params) == 1:
                code = get_param(0, 0)
                self.SGR_Dict.get(code, lambda: None)()
                
            # 256-Color Mode (e.g., \x1b[38;5;214m)
            elif len(self.csi_params) == 3 and self.csi_params[1] == "5":
                idx = get_param(2, 0)
                if self.csi_params[0] == "38":
                    self.Color = QColor(*self.Palette[idx])
                elif self.csi_params[0] == "48":
                    self.BackGround = QColor(*self.Palette[idx])
                    
            # True Color RGB Mode (e.g., \x1b[38;2;255;100;50m)
            elif len(self.csi_params) == 5 and self.csi_params[1] == "2":
                r, g, b = get_param(2), get_param(3), get_param(4)
                if self.csi_params[0] == "38":
                    self.Color = QColor(r, g, b)
                elif self.csi_params[0] == "48":
                    self.BackGround = QColor(r, g, b)

        # ----------------------------------------------------
        # Cursor Relocation
        # ----------------------------------------------------
        elif final_char in ('H', 'f'):
            row = get_param(0, 1)
            col = get_param(1, 1)
            self.Buffer.Cursor.Row = row - 1
            self.Buffer.Cursor.Col = col - 1

        elif final_char == 'A': # Cursor Up
            self.Buffer.Cursor.Row -= get_param(0, 1)
        elif final_char == 'B': # Cursor Down
            self.Buffer.Cursor.Row += get_param(0, 1)
        elif final_char == 'C': # Cursor Forward
            self.Buffer.Cursor.Col += get_param(0, 1)
        elif final_char == 'D': # Cursor Back
            self.Buffer.Cursor.Col -= get_param(0, 1)
        elif final_char == 'G': # Cursor Horizontal Absolute
            self.Buffer.Cursor.Col = get_param(0, 1) - 1
        elif final_char == 'd': # Cursor Vertical Absolute
            self.Buffer.Cursor.Row = get_param(0, 1) - 1

        # ----------------------------------------------------
        # Screen / Line Erasing
        # ----------------------------------------------------
        elif final_char == 'J':
            param = get_param(0, 0)
            if param == 0:
                self.Buffer.Erase_Scrn_Curs_End()
            elif param == 1:
                self.Buffer.Erase_Scrn_Start_Curs()
            elif param == 2:
                self.Buffer.ClearBuffer()

        elif final_char == 'K':
            param = get_param(0, 0)
            if param == 0:
                self.Buffer.Erase_Line_Curs_End()
            elif param == 1:
                self.Buffer.Erase_Line_Start_Curs()
            elif param == 2:
                self.Buffer.ClearLine()
        # ----------------------------------------------------
        # Screen / Line Erasing
        # ----------------------------------------------------
        elif final_char == 'X': # Erase Character (ECH)
            count = get_param(0, 1)
            row = self.Buffer.Cursor.Row
            col = self.Buffer.Cursor.Col
            
            # Make sure we don't crash if the row doesn't exist
            if 0 <= row < len(self.Buffer.lines):
                cells = self.Buffer.lines[row].cells
                # Replace the characters with spaces
                for i in range(count):
                    if col + i < len(cells):
                        cells[col + i].char = " "
                        if (col + i) not in self.Buffer.DirtyCells[row]:
                            self.Buffer.DirtyCells[row].append(col + i)

        # ----------------------------------------------------
        # Private Modes (Like Cursor Visibility: ?25h / ?25l)
        # ----------------------------------------------------
        elif final_char == 'h':
            if self.csi_params and "?25" in self.csi_params[0]:
                self.CursVis = True
        elif final_char == 'l':
            if self.csi_params and "?25" in self.csi_params[0]:
                self.CursVis = False

    def BuildPalette(self):
        palette = []

        # --------------------------------------------------
        # 0-15
        # Standard + bright terminal colors (VS Code Dark Modern)
        # --------------------------------------------------

        palette.extend([
            (  0,   0,   0),      # 0  Black
            (205,  49,  49),      # 1  Red          (#cd3131)
            ( 13, 188, 121),      # 2  Green        (#0dbc79)
            (229, 229,  16),      # 3  Yellow       (#e5e510)
            ( 36, 114, 200),      # 4  Blue         (#2472c8)
            (188,  63, 188),      # 5  Magenta      (#bc3fbc)
            ( 17, 168, 205),      # 6  Cyan         (#11a8cd)
            (229, 229, 229),      # 7  White        (#e5e5e5)

            (102, 102, 102),     # 8  Bright Black (#666666)
            (241, 76,  76),      # 9  Bright Red   (#f14c4c)
            (35,  209, 139),     # 10 Bright Green (#23d18b)
            (245, 245, 67),      # 11 Bright Yellow(#f5f543)
            (59,  142, 234),     # 12 Bright Blue  (#3b8eea)
            (214, 112, 214),     # 13 Bright Magenta(#d670d6)
            (41,  184, 219),     # 14 Bright Cyan  (#29b8db)
            (255, 255, 255),     # 15 Bright White (#ffffff)
        ])

        # --------------------------------------------------
        # 16-231
        # 6 × 6 × 6 RGB cube
        # --------------------------------------------------

        levels = [0, 95, 135, 175, 215, 255]
        for r in levels:
            for g in levels:
                for b in levels:
                    palette.append((r, g, b))

        # --------------------------------------------------
        # 232-255
        # 24 shades of gray
        # --------------------------------------------------

        for i in range(24):
            value = 8 + (i * 10)
            palette.append(
                (value, value, value)
            )


        self.Palette = palette


class TerminalBuffer:

    def __init__(self):
        self.MaxRows      = 10
        self.MaxCols      = 10
        self.ScrollActive = False
        self.BackSpace    = False
        self.ScrollBack   : list[TerminalLine] = []
        self.lines        = [TerminalLine(self.MaxCols) for _ in range(self.MaxRows)]
        self.Cursor       = TerminalCoordinate(0, 0)
        self.Selection    = TerminalSelection()
        self.DirtyScreen  = False
        self.DirtyLines   = []
        self.DirtyCells   = [[] for _ in range(self.MaxRows)]
        self.TotalLines   = len(self.lines) + len(self.ScrollBack)
        self.TopRow       = 0
        self.BottomRow    = self.TopRow + self.MaxRows - 1

    def InsertCharacter(self, Character, color, backColor, Bold, Faint, Italic, UndLine, DoubleUndLine, StrikeThru, Reverse, Conceal):

        if self.Cursor.Col >= self.MaxCols:
            self.NewLine(Wrapped = True)

        prevChar = self.lines[self.Cursor.Row].cells[self.Cursor.Col].char
        self.lines[self.Cursor.Row].cells[self.Cursor.Col] = TerminalCell(
            Character,
            color,
            backColor,
            Bold,
            Faint,
            Italic,
            UndLine,
            DoubleUndLine,
            StrikeThru,
            Reverse,
            Conceal
        )

        if self.Cursor.Col not in self.DirtyCells[self.Cursor.Row]:
            self.DirtyCells[self.Cursor.Row].append(self.Cursor.Col)

        # print(
        #     "INSERT:",
        #     repr(Character),
        #     "ROW =", self.Cursor.Row,
        #     "COL =", self.Cursor.Col
        # )
        self.Cursor.Col += 1
        
        if self.Cursor.Col >= self.MaxCols:
            if self.Cursor.Row == self.MaxRows - 1: self.NewLine(FakeCursor = True)
            elif self.BackSpace:
                self.Cursor.Col -= 1
                self.BackSpace = False

    def NewLine(self, Logical = False, Wrapped = False, Append = False, FakeCursor = False):
        if Append:
            if self.Cursor.Row >= self.MaxRows - 1:
                self.ScrollBack.append(self.lines.pop(0))
                self.lines.append(TerminalLine(self.MaxCols))
                self.TotalLines += 1
                if not self.ScrollActive:
                    self.TopRow    += 1
                    self.BottomRow += 1

            else: self.Cursor.Row += 1

        else:
            if FakeCursor:
                self.ScrollBack.append(self.lines.pop(0))
                self.lines.append(TerminalLine(self.MaxCols))
                self.TotalLines += 1
                if not self.ScrollActive:
                    self.TopRow    += 1
                    self.BottomRow += 1
                self.Cursor.Row -= 1
                return
            
            else:
                self.Cursor.Row += 1

        self.lines[self.Cursor.Row].Logical = Logical
        self.lines[self.Cursor.Row].Wrapped = Wrapped
        self.Cursor.Col = 0

    def ClearBuffer(self):
        self.lines      = [TerminalLine(self.MaxCols) for _ in range(self.MaxRows)]
        self.TotalLines = len(self.lines) + len(self.ScrollBack)
        self.DirtyScreen = True
    
    def ClearLine(self):
        self.lines[self.Cursor.Row] = TerminalLine(self.MaxCols)
        if self.Cursor.Row not in self.DirtyLines:
            self.DirtyLines.append(self.Cursor.Row)
        
    def Erase_Line_Start_Curs(self):
        for i, cell in enumerate(self.lines[self.Cursor.Row].cells[:(self.Cursor.Col + 1)]):
            cell.char = " "
            if (self.Cursor.Col + i) not in self.DirtyCells[self.Cursor.Row]:
                self.DirtyCells[self.Cursor.Row].append(self.Cursor.Col + i)

    def Erase_Line_Curs_End(self):
        for i, cell in enumerate(self.lines[self.Cursor.Row].cells[self.Cursor.Col:]):
            cell.char = " "
            if (self.Cursor.Col + i) not in self.DirtyCells[self.Cursor.Row]:
                self.DirtyCells[self.Cursor.Row].append(self.Cursor.Col + i)

    def Erase_Scrn_Start_Curs(self):
        for i in range(self.Cursor.Row):
            self.lines[i] = TerminalLine(self.MaxCols)
            if i not in self.DirtyLines:
                self.DirtyLines.append(i)
        self.Erase_Line_Start_Curs()

    def Erase_Scrn_Curs_End(self):
        self.Erase_Line_Curs_End()
        for i in range(self.Cursor.Row + 1, len(self.lines)):
            self.lines[i] = TerminalLine(self.MaxCols)
            if i not in self.DirtyLines:
                self.DirtyLines.append(i)

    def Buffer_Resize(self):
        # self.DirtyScreen = False
        # self.DirtyLines  = []
        self.DirtyCells  = [[] for _ in range(self.MaxRows)]
        self.lines       = [TerminalLine(self.MaxCols) for _ in range(self.MaxRows)]
        self.ScrollBack_Resize()
        self.TotalLines  = len(self.lines) + len(self.ScrollBack)
        self.BottomRow   = self.TopRow + self.MaxRows - 1

    def ScrollBack_Resize(self):
        Temp : list[TerminalLine] = []
        CellsFilled = 0

        print("SCROLLBACK =", self.ScrollBack)
        for line in self.ScrollBack:
            if not Temp or line.Logical:
                Temp.append(TerminalLine(MaxCols = self.MaxCols, Logical = True))
                CellsFilled = 0

            for cell in line.cells:
                if CellsFilled >= self.MaxCols:
                    Temp.append(TerminalLine(MaxCols = self.MaxCols, Wrapped = True))
                    CellsFilled = 0
                
                Temp[-1].cells[CellsFilled] = cell
                CellsFilled += 1

        self.ScrollBack = Temp


class TerminalLine:

    def __init__(self, MaxCols, Logical = False, Wrapped = False):
        self.cells   = [TerminalCell(" ") for _ in range(MaxCols)]
        self.Logical = Logical
        self.Wrapped = Wrapped


class TerminalCell:

    def __init__(self, Char = "", SelfColor=None, BackColor=None, Bold = False, Faint = False, Italic = False, UndLine = False, DoubleUndline = False, StrikeThru = False, Reverse = False, Conceal = False):
        self.char       = Char
        self.BackColor  = BackColor if BackColor is not None else QColor(24, 24, 24)
        self.SelfColor  = SelfColor if SelfColor is not None else QColor(229, 229, 229)
        self.Bold       = Bold
        self.Faint      = Faint
        self.Italic     = Italic
        self.UndLine    = UndLine
        self.DbUndLine  = DoubleUndline
        self.StrikeThru = StrikeThru
        self.Reverse    = Reverse
        self.Conceal    = Conceal


class TerminalSelection:

    def __init__(self):
        self.SelectActive = []
        self.SelectStart  = TerminalCoordinate(None, None)
        self.SelectStop   = TerminalCoordinate(None, None)
        self.CopyBuffer   = []


class TerminalCoordinate:

    def __init__(self, row, col):
        self.Row = row
        self.Col = col

    def Reset(self):
        self.Row = None
        self.Col = None


class ScrollBar(QScrollBar):
    @property
    def page(self): return self.pageStep()

    @property
    def total(self): return self.maximum() - self.minimum() + self.pageStep()

    @property
    def ratio(self): return self.page / self.total

    def  __init__(self, parent):
        super().__init__(parent)
        self.setFixedWidth(8)

        policy = self.sizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Policy.Ignored)
        self.setSizePolicy(policy)
        self.StyleConfig()

    def StyleConfig(self):
            self.setStyleSheet("""
                QScrollBar:vertical {
                    background: rgb(24,24,24);
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
                        background: rgb(24,24,24);
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


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.Widget = MainTermWidget()
        self.setCentralWidget(self.Widget)
        self.setWindowTitle("Terminal")


# app = QApplication([])
# window = MainWindow()
# window.show()
# app.exec()