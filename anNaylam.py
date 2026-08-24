from importlib.resources import path
from Sagittarius_A import Ui_SagittariusA
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QSplitter, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QScrollBar, QSizePolicy,
                               QPushButton, QToolButton, QToolTip,
                               QFrame, QLabel, QTreeView,
                               QPlainTextEdit, QTextEdit, QFileDialog)
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
                               QTextCursor, QTextBlock, QShortcut,
                               QTextCharFormat)
from enum import Enum, auto
from typing import cast
from pathlib import Path
import json
import os
import sys
import re
import cv2
import math
import time
import shiboken6
import traceback

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"

LANGUAGE_MAP = {
    ".py"   : "python",
    ".js"   : "javascript",
    ".ts"   : "typescript",
    ".html" : "html",
    ".css"  : "css",
    ".json" : "json",
    ".cpp"  : "cpp",
    ".c"    : "c"
}


class LineIndent(Enum):
    Indent = auto()
    Dedent = auto()
    Keep   = auto()


class MasterWidget(QWidget):
    
    def __init__(self, parent):
        super().__init__(parent)
        self.editor = CodeEditor(self)
        self.client = LSPClient()
        self.LayoutConfig()
        self.SignalManager()

    def LayoutConfig(self):
        Layout = QHBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(0)
        Layout.addWidget(self.editor.LineWidget)
        Layout.addWidget(self.editor)

    def LSPDocConfig(self):
        self.client.Document.uri        = self.editor.FilePath
        self.client.Document.languageId = LANGUAGE_MAP.get(self.editor.FileExt.lower(), "python")
        self.client.Document.text       = self.editor.toPlainText()
        if self.editor.NewFile:
            self.client.Document.version = 1
            self.editor.NewFile = False
            self.client.didOpenMessage()
        else:
            self.client.Document.version += 1
            self.client.didChangeMessage()

    def SignalManager(self):
        self.editor.textChanged.connect(self.LSPDocConfig)
        self.client.diagnosticsReady.connect(self.editor.diagnose)


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
    fileOpened = Signal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self.Language  = PythonLanguage()
        self.version   = 1
        self.FilePath  = None
        self.FileExt   = "plaintext"
        self.NewFile   = False
        self.Selection = CodeSelection()

        self.errSelections = []
        self.errSquiggles  : list[Squiggle] = []
        self.warnSquiggles : list[Squiggle] = []

        self.Diagnostics = {}

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

    def paintEvent(self, e):
        painter = QPainter(self.viewport())
        painter.fillRect(e.rect(), QColor(20, 20, 20))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(QPen(QColor(205, 49, 49), 1.5))
        for squiggle in self.errSquiggles: self.drawSquiggle(painter, squiggle)

        painter.setPen(QPen(QColor(229, 229, 16), 1.5))
        for squiggle in self.warnSquiggles: self.drawSquiggle(painter, squiggle)

        super().paintEvent(e)

    def drawSquiggle(self, painter : QPainter, squiggle : Squiggle):
        for line in range(squiggle.start.row, squiggle.end.row + 1):
            block = self.document().findBlockByNumber(line)
            if not block.isValid():
                continue

            blockLen = max(0, block.length() - 1)
            if line == squiggle.start.row:
                colStart = min(squiggle.start.col, blockLen)
                cursor = QTextCursor(block)
                cursor.setPosition(block.position() + colStart)
                startRect = self.cursorRect(cursor)
                x0 = startRect.x()
            else:
                cursor = QTextCursor(block)
                cursor.setPosition(block.position())
                startRect = self.cursorRect(cursor)
                x0 = startRect.x()

            if line == squiggle.end.row:
                if line > squiggle.start.row and squiggle.end.col == 0:
                    continue
                colEnd = min(squiggle.end.col, blockLen)
                cursor = QTextCursor(block)
                cursor.setPosition(block.position() + colEnd)
                endRect = self.cursorRect(cursor)
                x1 = endRect.x()
            else:
                cursor = QTextCursor(block)
                cursor.setPosition(block.position() + block.length() - 1)
                endRect = self.cursorRect(cursor)
                x1 = endRect.right()
            
            if x0 == x1: 
                x0 -= self.cellWidth // 2
                x1 += self.cellWidth // 2

            yoff = startRect.bottom()
            locus = QPainterPath()
            locus.moveTo(x0, yoff)

            A = 1.4
            l = 6

            for x in range(int(x0), int(x1) + 1):
                y = A * math.sin((x) * (2 * math.pi / l)) + yoff
                locus.lineTo(x, y)

            painter.drawPath(locus)

    def reportChange(self):
        print("changed")
        if self.NewFile: self.version = 1
        else: self.version += 1

    def HighLightLine(self):
        line_color = QColor(255, 255, 255, 15)

        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(line_color)
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)

        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection] + self.errSelections)
        # self.setExtraSelections(self.errSelections)

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

    def openFile(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "All Files (*);;Python Files (*.py)"
        )

        if filepath:
            self.NewFile = True
            self.FilePath   = Path(filepath).as_uri()
            _, self.FileExt = os.path.splitext(filepath)    # Splits "C:/scripts/main.py" into ("C:/scripts/main", ".py")
            with open(filepath, "r", encoding = "utf-8") as file:
                text = file.read()
            self.setPlainText(text)

    def diagnose(self, uri, version, diagnostics : dict):
        if version != self.version:
            return
        if uri != self.FilePath:
            return
        
        self.Diagnostics = diagnostics
        self.errSquiggles.clear()
        self.warnSquiggles.clear()

        for  diagnostic in self.Diagnostics:
            if "range" in diagnostic.keys():
                if diagnostic["severity"] == 1:
                    err = Squiggle()
                    err.start.row = diagnostic["range"]["start"]["line"]
                    err.start.col = diagnostic["range"]["start"]["character"]
                    err.end.row = diagnostic["range"]["end"]["line"]
                    err.end.col = diagnostic["range"]["end"]["character"]
                    self.errSquiggles.append(err)
                elif diagnostic["severity"] == 2:
                    warn = Squiggle()
                    warn.start.row = diagnostic["range"]["start"]["line"]
                    warn.start.col = diagnostic["range"]["start"]["character"]
                    warn.end.row = diagnostic["range"]["end"]["line"]
                    warn.end.col = diagnostic["range"]["end"]["character"]
                    self.warnSquiggles.append(warn)
        self.viewport().update()

    def SignalManager(self):
        self.fileOpenShortcut = QShortcut(QKeySequence("Ctrl+O"), self)

        self.fileOpenShortcut.activated.connect(self.openFile)
        self.blockCountChanged.connect(self.updateLineData)
        self.cursorPositionChanged.connect(self.updateLineData)
        self.cursorPositionChanged.connect(self.HighLightLine)
        self.updateRequest.connect(self.LineWidget.update)
        self.selectionChanged.connect(self.updateSelection)
        self.textChanged.connect(self.reportChange)

    def StyleConfig(self):
        self.setStyleSheet(
            """
            QPlainTextEdit {
                border: none;
                background-color: transparent;
                selection-background-color: rgba(17, 168, 225, 100);
            }
            """
        )

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor      = self.textCursor()
            nextIndent  = self.Language.nextIndentation(cursor)
            
            text        = self.textCursor().block().text()
            match       = re.match(r"^[ \t]*", text)
            indentation = match.group(0) if match else ""

            self.textCursor().insertText("\n" + indentation)
            if nextIndent == LineIndent.Indent: self.Indent(cursor.block())

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
                cursor    = self.textCursor()
                blockText = cursor.block().text()
                preText   =  blockText[:cursor.positionInBlock()]
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


class Squiggle:
    def __init__(self):
        self.start = Coordinate()
        self.end   = Coordinate()


class Coordinate:
    def __init__(self, lineId = 0, chId = 0):
        self.row = lineId
        self.col = chId


class codeLanguage:
    def nextIndentation(self, cursor : QTextCursor):
        raise NotImplementedError

    def commentSyntax(self):
        raise NotImplementedError

    def keyWords(self):
        raise NotImplementedError


class PythonLanguage(codeLanguage):

    def nextIndentation(self, cursor : QTextCursor):
        block = cursor.block()
        preText = block.text()[:cursor.positionInBlock()]

        """
            rstrip ---> goes to the end of a string (preText in this case) and strips off
            the characters passed in its argument from the right (" " and "\t" in this case) INPLACE
            endswith operates on a string checks if its last element is the passed argument or not
        """
        decision = preText.rstrip(" \t").endswith(":")
        if decision:
            return LineIndent.Indent
        else:
            return LineIndent.Keep

    def commentSyntax():
        return "#"

    def keyWords():
        pass


class readBufferState(Enum):
    HEADER = auto()
    BODY   = auto()


class readBuffer:
    def __init__(self):
        self.Buffer = b""
        self.State  = readBufferState.HEADER


class LSPClient(QObject):
    diagnosticsReady = Signal(object, object, object)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.process      = QProcess()
        self.OutputBuffer = readBuffer()
        self.BodyLength   = 0
        self.ReceivedLen  = 0
        self.Document     = LSPDocument(None, "python", "")

        self.process.readyReadStandardOutput.connect(self.readOutput)
        self.process.readyReadStandardError.connect(self.readError)

        self.startLSP()

        initialize = {
            "jsonrpc"   : "2.0",
            "id"        : 1,
            "method"    : "initialize",
            "params"    : {
                "processId"     : os.getpid(),
                "clientInfo"    : {
                    "name"      : "Sagittarius A*",
                    "version"   : "1.0"
                },
                "rootUri"       : None,
                "capabilities"  : {}

            }
        }
        self.sendMessage(initialize)

        initialized = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        self.sendMessage(initialized)

    def startLSP(self):
        command = "pyright-langserver.cmd" if sys.platform == "win32" else "pyright-langserver"
        self.process.start(
            command,
            ["--stdio"]
        )

        started = self.process.waitForStarted()
        print(f"{BLUE}waiting{RESET}")

        if not started:
            print("Failed to start language server")
            return

        print("Language server started")

    def sendMessage(self, message):
        body = json.dumps(message).encode("utf-8")
        header = (
            f"Content-Length: {len(body)}\r\n"
            f"\r\n"
        ).encode("ascii")

        self.process.write(header + body)

    def didOpenMessage(self):
        message = {
            "jsonrpc"   : "2.0",
            "method"    : "textDocument/didOpen",
            "params"    : {
                "textDocument"  : {
                    "uri"           : self.Document.uri,
                    "languageId"    : self.Document.languageId,
                    "version"       : self.Document.version,
                    "text"          : self.Document.text
                }
            }
        }

        self.sendMessage(message)

    def didChangeMessage(self):
        message = {
            "jsonrpc"   : "2.0",
            "method"    : "textDocument/didChange",
            "params"    : {
                "textDocument"  : {
                    "uri"       : self.Document.uri,
                    "version"   : self.Document.version
                },
                "contentChanges": [
                    {
                        "text"  : self.Document.text
                    }
                ]
            }
        }

        self.sendMessage(message)

    def readOutput(self):
        data = bytes(self.process.readAllStandardOutput())
        self.OutputBuffer.Buffer += data

        self.checkBuffer()

    def checkBuffer(self):
        # print("----------")
        # print("Buffer State =", self.OutputBuffer.State, "\r\n")
        # print(self.OutputBuffer.Buffer.decode("utf-8"), "\r\n\r\n")
        # print("----------")
        while True:
            if self.OutputBuffer.State == readBufferState.HEADER:
                headerEnd = self.OutputBuffer.Buffer.find(b"\r\n\r\n")
                if headerEnd != -1:
                    Header = self.OutputBuffer.Buffer[:headerEnd].decode("utf-8")
                    self.OutputBuffer.Buffer = self.OutputBuffer.Buffer[(headerEnd + 4):]       # <---- "\r\n\r\n" (total 4 bytes)
                    # print("Header =", Header)
                    for line in Header.split("\r\n"):
                        if line.startswith("Content-Length"):
                            self.BodyLength = int(line.split(":")[1].strip())
                            break
                    self.OutputBuffer.State = readBufferState.BODY
                    if len(self.OutputBuffer.Buffer) == 0:
                        break

            if self.OutputBuffer.State == readBufferState.BODY:
                if len(self.OutputBuffer.Buffer) >= self.BodyLength:
                    Body = self.OutputBuffer.Buffer[:self.BodyLength].decode("utf-8")
                    self.OutputBuffer.Buffer = self.OutputBuffer.Buffer[self.BodyLength:]
                    # print("Body =", json.loads(Body))
                    self.readMessage(message = Body)

                    self.OutputBuffer.State = readBufferState.HEADER
                    if self.OutputBuffer.Buffer: continue
                    else: break
                else: break

    def readMessage(self, message):
        message = json.loads(message)
        if "id" in message:
            if "result" in message:
                self.handleResponse(message)
            elif "error" in message:
                self.handleError(message)

        elif "method" in message:
            self.handleNotification(message)

    def handleError(self, message):
        print("Error:\r\n", message, "\r\n\r\n")

    def handleResponse(self, message):
        # print("Response:\r\n", message, "\r\n\r\n")
        pass

    def handleNotification(self, message):
        # print("Notification:\r\n", message, "\r\n\r\n")
        if message["method"] == "textDocument/publishDiagnostics":
            self.handleDiagnostics(message)

    def handleDiagnostics(self, message):
        colorMap = {
            0   : f"{RED}",
            1   : f"{GREEN}",
            2   : f"{YELLOW}",
            3   : f"{BLUE}"
        }
        params  = message["params"]
        uri     = params["uri"]
        version = params["version"]
        diagnostics = params["diagnostics"]

        self.diagnosticsReady.emit(uri, version, diagnostics)

        for i, diagnostic in enumerate(diagnostics):
            k = i % 4
            print(colorMap[k], diagnostic)
            print(f"{RESET}")
        pass

    def readError(self):
        print("Error")


class LSPDocument:
    def __init__(self, uri, languageId, text):
        self.uri        = uri
        self.languageId = languageId
        self.text       = text
        self.version    = 1


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