from importlib.resources import path
from Sagittarius_A import Ui_SagittariusA
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QSplitter, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QScrollBar, QSizePolicy,
                               QPushButton, QToolButton, QToolTip,
                               QFrame, QLabel, QTreeView,
                               QPlainTextEdit, QTextEdit)
from PySide6.QtCore import    (QProcess, Qt, QObject,
                               Signal, QRectF, QRect,
                               Slot, QPointF, QPoint,
                               QSize, QEvent, QSignalBlocker,
                               QTimer)
from PySide6.QtGui import     (QPainter, QColor, QPen,
                               QPixmap, QFont, QMouseEvent,
                               QImage, QCursor, QPainterPath,
                               QStandardItemModel, QStandardItem,
                               QFontMetrics, QKeySequence, QTextFormat,
                               QTextCursor, QTextBlock)
from enum import Enum, auto
from typing import cast
import numpy as np
import os
import sys
import re
import cv2
import math
import time
import shiboken6
import traceback

class MasterWidget(QWidget):
    
    def __init__(self, parent):
        super().__init__(parent)
        self.editor = CodeEditor(self)
        self.LayoutConfig()

    def LayoutConfig(self):
        Layout = QHBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(0)
        Layout.addWidget(self.editor.LineWidget)
        Layout.addWidget(self.editor)


class LineNumberArea(QWidget):

    def __init__(self, parent, editor : 'CodeEditor', Font : QFont):
        super().__init__(parent)
        self.editor     = editor
        self.Font       = Font

        self.cellWidth  = QFontMetrics(self.Font).horizontalAdvance("W")
        self.cellHeight = QFontMetrics(self.Font).height()
        self.Ascent     = QFontMetrics(self.Font).ascent()

        self.TotalLines = 1
        self.TopIdx     = 0
        self.BotIdx     = 0
        self.CursIdx    = 0

        self.LeftMargin  = 5
        self.RightMargin = 10

        self.updateWidth()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(self.Font)
        painter.fillRect(self.rect(), QColor(20, 20, 20))

        block = self.editor.firstVisibleBlock()
        blockNumber = block.blockNumber()

        top = round(self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top())
        bottom = top + round(self.editor.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                opacity = 80
                if blockNumber == self.CursIdx:
                    opacity = 150
                
                painter.setPen(QPen(QColor(255, 255, 255, opacity)))

                line_str = str(blockNumber + 1)
                textWidth = self.fontMetrics().horizontalAdvance(line_str)
                x = self.width() - self.RightMargin - textWidth

                painter.drawText(x, top + self.Ascent, line_str)

                # cellRect = QRect(
                #     x + 1, top + 1,
                #     self.cellWidth - 2, self.cellHeight - 2
                # )
                # painter.drawRect(cellRect)

            block = block.next()
            top = bottom
            bottom = top + round(self.editor.blockBoundingRect(block).height())
            blockNumber += 1

    def updateWidth(self):
        digits = max(2, len(str(self.TotalLines)))
        newWidth = self.LeftMargin + (digits * self.cellWidth) + self.RightMargin

        self.setFixedWidth(newWidth)
        self.update()


class CodeEditor(QPlainTextEdit):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.Language  = "Python"

        self.Selection = CodeSelection()

        self.Font = QFont()
        self.Font.setFamilies(["Consolas", "Courier New"])
        self.Font.setPixelSize(15)

        self.setFont(self.Font)

        self.LineWidget = LineNumberArea(self.parent(), self, self.Font)

        self.cellWidth  = self.fontMetrics().horizontalAdvance("W")
        self.cellHeight = self.fontMetrics().height()
        self.Ascent     = self.fontMetrics().ascent()

        self.SpacePerTab = 4

        self.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.NoWrap
            )
        self.setTabStopDistance(
            4 * self.fontMetrics().horizontalAdvance(" ")
        )
        self.StyleConfig()
        self.HighLightLine()
        self.SignalManager()
        self.selectionChanged.connect(self.updateSelection)

    def HighLightLine(self):
        line_color = QColor(255, 255, 255, 15)

        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(line_color)
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)

        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    def BlockIndent(self):
        cursor = self.textCursor()
        cursor.beginEditBlock()

        currentBlock = self.Selection.FirstBlock
        while currentBlock.isValid():
            self.Indent(currentBlock)

            if currentBlock == self.Selection.LastBlock: break
            currentBlock = currentBlock.next()

        cursor.endEditBlock()

    def BlockUnIndent(self):
        cursor   = self.textCursor()
        
        cursor.beginEditBlock()

        currentBlock = self.Selection.FirstBlock
        while currentBlock.isValid():
            self.unIndent(currentBlock)
            if currentBlock == self.Selection.LastBlock: break
            currentBlock = currentBlock.next()

        cursor.endEditBlock()

    def Indent(self, block : QTextBlock, InPlace = False):
        if InPlace:
            cursorPosition = self.textCursor().positionInBlock()
            preText = block.text()[:cursorPosition]
            totalSpace = len(preText) if preText else 0
            toInsert = self.SpacePerTab - totalSpace % self.SpacePerTab
            blockCursor = self.textCursor()

        else:
            toInsert = self.SpacePerTab
            blockCursor = QTextCursor(block)
        
        blockCursor.insertText(" " * toInsert)

    def unIndent(self, block : QTextBlock, InPlace = False):
        blockCursor = QTextCursor(block)
        codeText    = self.document()
        if InPlace:
            cursorPosition = self.textCursor().positionInBlock()
            preText = block.text()[:cursorPosition]
            spaces  = re.match(r"^\s+", preText)
        else:
            blockText   = block.text()
            spaces      = re.match(r"^\s+", blockText)
        totalSpace  = len(spaces.group(0).expandtabs(self.SpacePerTab)) if spaces else 0
        if totalSpace == 0:
            return
    
        toRem = totalSpace % self.SpacePerTab
        if toRem == 0: toRem = self.SpacePerTab

        print("Total =", totalSpace)
        print(toRem)

        spaceCount  = 0
        while True:
            char = codeText.characterAt(blockCursor.position())
            if char == "\t":
                remaining = toRem - spaceCount
                toAdd = self.SpacePerTab - remaining
                blockCursor.deleteChar()
                if toAdd > 0:
                    blockCursor.insertText(" " * toAdd)
                break

            elif char == " ":
                blockCursor.deleteChar()
                spaceCount += 1
                if spaceCount == toRem:
                    break
            else:
                break

    def updateLineData(self, *args):
        totalLines = self.blockCount()
        cursLine = self.textCursor().blockNumber()

        self.LineWidget.TotalLines = totalLines
        self.LineWidget.CursIdx    = cursLine

        self.LineWidget.updateWidth()
        self.LineWidget.update()

    def updateSelection(self):
        cursor = self.textCursor()

        if cursor.hasSelection():
            self.Selection.Select = True
            selectStart = cursor.selectionStart()
            selectStop  = cursor.selectionEnd()
            CodeText    = self.document()

            if selectStop > selectStart and CodeText.findBlock(selectStop).position() == selectStop:
                selectStop -= 1

            self.Selection.FirstBlock = CodeText.findBlock(selectStart)
            self.Selection.LastBlock  = CodeText.findBlock(selectStop)
        else:
            self.Selection.resetSelection()

        # print(self.Selection.Select,"\n",
        #       self.Selection.FirstBlock.blockNumber(), "\n",
        #       self.Selection.LastBlock.blockNumber())
    
    def SignalManager(self):
        self.blockCountChanged.connect(self.updateLineData)
        self.cursorPositionChanged.connect(self.updateLineData)
        self.cursorPositionChanged.connect(self.HighLightLine)
        self.updateRequest.connect(self.LineWidget.update)

    def StyleConfig(self):
        self.setStyleSheet(
            """
            QPlainTextEdit {
                border: none;
                background-color: rgb(20, 20, 20);
                selection-background-color: rgba(17, 168, 225, 100);
            }
            """
        )

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            text        = self.textCursor().block().text()
            match       = re.match(r"^\s+", text)
            indentation = match.group(0) if match else ""

            self.textCursor().insertText("\n" + indentation)
            return

        elif e.key() == Qt.Key_Tab:
            if self.Selection.Select:
                self.BlockIndent()
                return

            else:
                self.Indent(self.textCursor().block(), InPlace = True)
                return

        elif e.key() == Qt.Key_Backspace:
            if not self.Selection.Select:
                cursor = self.textCursor()
                blockText = cursor.block().text()
                preText =  blockText[:cursor.positionInBlock()]
                uniqChars = set(preText)
                if not (uniqChars - {" ", "\t"}) and uniqChars:
                    self.unIndent(cursor.block(), InPlace = True)
                    return

        elif e.key() == Qt.Key_Backtab:
            if self.Selection.Select:
                self.BlockUnIndent()
                return
            else:
                codeBlock = self.textCursor().block()
                self.unIndent(codeBlock)
                return

        super().keyPressEvent(e)


class CodeSelection:
    def __init__(self):
        self.Select     = False
        self.FirstBlock = None
        self.LastBlock  = None

    def resetSelection(self):
        self.Select     = False
        self.FirstBlock = None
        self.LastBlock  = None


class  MainWindow(QMainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)
        Main = MasterWidget(self)
        self.setWindowTitle("anNaylam")
        self.setCentralWidget(Main)

app = QApplication([])
window = MainWindow()

window.show()

screen = app.primaryScreen()
avail = screen.availableGeometry()

title_bar_height = window.frameGeometry().height() - window.geometry().height()
border_width = window.frameGeometry().width() - window.geometry().width()

target_width = (avail.width() // 2) - border_width
target_height = avail.height() - title_bar_height

window.resize(target_width, target_height)
window.move(avail.x() + (avail.width() // 2), avail.y())

sys.exit(app.exec())