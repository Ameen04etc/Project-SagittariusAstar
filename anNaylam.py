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
                               QTimer, QRegularExpression)
from PySide6.QtGui import     (QPainter, QColor, QPen,
                               QPixmap, QFont, QMouseEvent,
                               QImage, QCursor, QPainterPath,
                               QStandardItemModel, QStandardItem,
                               QFontMetrics, QKeySequence, QTextFormat,
                               QTextCursor, QTextBlock, QShortcut,
                               QTextCharFormat, QSyntaxHighlighter)
from enum import Enum, auto
from typing import cast
from pathlib import Path
from tree_sitter import Language, Parser
import tree_sitter_python
import json
import os
import sys
import re
import cv2
import math
import time
import shiboken6
import traceback

RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
BLUE   = "\033[34m"
RESET  = "\033[0m"

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

VS_CONTROL_FLOW = {
    "if", "elif", "else", "for", "while", "break", "continue", 
    "return", "yield", "try", "except", "finally", "raise", 
    "match", "case", "with"
}

VS_KEYWORDS = {
    "lambda", "global", "nonlocal", "pass", 
    "True", "False", "None", 
    "and", "or", "not", "is", "in", "async", "await"
}

VS_OPERATORS = {
    "+", "-", "*", "/", "%", "**", "//", "=", "==", "!=", 
    "<", ">", "<=", ">=", "@", "&", "|", "^", "~", "<<" , ">>"
}


class LineIndent(Enum):
    Indent = auto()
    Dedent = auto()
    Keep   = auto()


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
    scrollEmit     = Signal(object)
    lineSelectEmit = Signal(int, bool)

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
        self.TotalLines = 0
        painter = QPainter(self)
        painter.setFont(self.Font)
        painter.fillRect(self.rect(), QColor(20, 20, 20))

        block = self.editor.firstVisibleBlock()
        blockNumber = block.blockNumber()

        top = round(self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top())
        bottom = top + round(self.editor.blockBoundingRect(block).height())

        self.TopIdx = block.blockNumber() + 1

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                self.TotalLines += 1
                opacity = 80
                if blockNumber == self.CursIdx:
                    opacity = 150
                
                painter.setPen(QPen(QColor(255, 255, 255, opacity)))

                line_str = str(blockNumber + 1)
                textWidth = self.fontMetrics().horizontalAdvance(line_str)
                x = self.width() - self.RightMargin - textWidth

                painter.drawText(x, top + self.Ascent, line_str)

                # painter.drawRect(x, top, self.RightMargin + textWidth, self.cellHeight)
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

    def mousePressEvent(self, event):
        x = event.position().x()
        y = event.position().y()
        if self.LeftMargin < x < self.width() - self.RightMargin:
            LineSelect = int((y - round(self.editor.blockBoundingGeometry(self.editor.firstVisibleBlock()).translated(self.editor.contentOffset()).top())) / self.cellHeight) + self.TopIdx
            if self.TopIdx <= LineSelect <= self.TotalLines + self.TopIdx - 1:
                self.lineSelectEmit.emit((LineSelect - 1), False)
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        self.scrollEmit.emit(event)
        super().wheelEvent(event)

    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)


class CodeEditor(QPlainTextEdit):
    fileOpened = Signal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self.Language  = PythonLanguage(self.document(), self)
        self.version   = 1
        self.FilePath  = None
        self.FileExt   = "plaintext"
        self.NewFile   = False
        self.LoadFile  = False
        self.Selection = CodeSelection()

        self.errSelections = []
        self.errSquiggles  : list[Squiggle] = []
        self.warnSquiggles : list[Squiggle] = []

        self.Diagnostics = {}

        self.Font = QFont()
        self.Font.setFamilies(["Consolas", "Courier New"])
        self.Font.setPixelSize(15)
        self.setFont(self.Font)

        self.NormalFormat = QTextCharFormat()
        self.NormalFormat.setForeground(QColor("white"))
        self.textCursor().mergeCharFormat(self.NormalFormat)

        self.LineWidget = LineNumberArea(self.parent(), self, self.Font)

        self.cellWidth  = self.fontMetrics().horizontalAdvance("W")
        self.cellHeight = self.fontMetrics().height()
        self.Ascent     = self.fontMetrics().ascent()

        self.SpacePerTab = 4
        self.OldText     = self.document().toPlainText()

        self.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.NoWrap
            )
        self.setTabStopDistance(
            4 * self.fontMetrics().horizontalAdvance(" ")
        )
        self.StyleConfig()
        self.HighLightLine()
        self.SignalManager()

        self.Language.syntax.sourceUpdate(self.document().toPlainText().encode())
        # self.Language.syntax.printSyntax()
        self.oldTree = self.Language.syntax.Tree
        self.newTree = self.Language.syntax.Tree
        self.oldNode = self.Language.syntax.Tree.root_node
        self.newNode = self.Language.syntax.Tree.root_node

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
        if self.NewFile: self.version = 1
        else: self.version += 1

    def moveCursor(self, blockID, end = True):
        block = self.document().findBlockByNumber(blockID)
        if block.isValid():
            cursor = QTextCursor(block)
            if end:
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()

    def selectLine(self, blockID, *args):
        block = self.document().findBlockByNumber(blockID)
        if block.isValid():
            cursor = QTextCursor(block)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)

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

            self.LoadFile = True
            self.setPlainText(text)
            self.LoadFile = False
            self.Language.syntax.sourceUpdate(self.toPlainText().encode("utf-8"), incremental = False)
            # self.highlightNode()
            self.Language.Highlighter.rehighlight()

    def diagnose(self, uri, version, diagnostics : dict):
        print("Current =", self.version)
        print("Response =", version)
        print("FilePath =", self.FilePath)
        print("uri =", uri)
        if version != self.version:
            return
        # if uri != self.FilePath:
        #     return
        
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

    def LSPDocConfig(self):
        self.Language.client.Document.uri        = self.FilePath
        self.Language.client.Document.languageId = LANGUAGE_MAP.get(self.FileExt.lower(), "python")
        self.Language.client.Document.text       = self.toPlainText()
        if self.NewFile:
            self.Language.client.Document.version = 1
            self.NewFile = False
            self.Language.client.didOpenMessage()
        else:
            self.Language.client.Document.version += 1
            self.Language.client.didChangeMessage()

    def offsetToCoordinates(self, text, offset):
        preText = text[:offset]
        Row = preText.count('\n')

        lastNewline = preText.rfind('\n')
        lineStart   = lastNewline + 1
        lineText    = text[lineStart:offset]

        Colutf16 = len(lineText.encode("utf-16-le")) // 2
        Colutf8 = len(lineText.encode("utf-8"))
        byteOffset = len(preText.encode("utf-8"))

        return Row, Colutf16, Colutf8, byteOffset

    def byteToQOffset(self, text, byteOffset):
        encoded = text.encode("utf-8")
        prefix  = encoded[:byteOffset]
        decoded = prefix.decode("utf-8").encode("utf-16-le")
        return len(decoded) // 2

    def incrementCapture(self, position, charRem, charAdd):
        if self.LoadFile:
            return
        # print("---------------------------------------")
        newText = self.document().toPlainText()

        oldStart = position
        oldEnd   = position + charRem
        oldStartRow, oldStartCol16, oldStartCol8, oldStartByte = self.offsetToCoordinates(self.OldText, oldStart)
        oldEndRow  , oldEndCol16  , oldEndCol8  , oldEndByte   = self.offsetToCoordinates(self.OldText, oldEnd)

        newEnd   = position + charAdd
        newEndRow  , newEndCol16  , newEndCol8  , newEndByte   = self.offsetToCoordinates(newText, newEnd)

        self.Language.syntax.Tree.edit(
            start_byte   = oldStartByte,
            old_end_byte = oldEndByte,
            new_end_byte = newEndByte,

            start_point   = (oldStartRow, oldStartCol8),
            old_end_point = (oldEndRow, oldEndCol8),
            new_end_point = (newEndRow, newEndCol8),
        )
        self.Language.syntax.sourceUpdate(newText.encode("utf-8"))
        # self.Language.syntax.printSyntax()
        # print("---")
        changed_ranges = self.oldTree.changed_ranges(self.Language.syntax.Tree)

        for rng in changed_ranges:
            start_block_num = rng.start_point[0]
            end_block_num = rng.end_point[0]
            
            for block_num in range(start_block_num, end_block_num + 1):
                block = self.document().findBlockByNumber(block_num)
                if block.isValid():
                    self.Language.Highlighter.rehighlightBlock(block)

        self.newNode = self.fetchCursorNode()
        self.oldNode = self.newNode
        self.OldText = newText
        self.oldTree = self.Language.syntax.Tree

    def fetchCursorNode(self, Tree = None, position =  None):
        if Tree is None: Tree = self.Language.syntax.Tree
        cursor = self.textCursor()
        if position is None:
            position = cursor.position()
        elif position < 0:
            position += 1
        text = self.toPlainText()
        row, col16, col8, byteOffset = self.offsetToCoordinates(text, position)
        byteOffset = max(0, byteOffset - 1)

        node = Tree.root_node.named_descendant_for_byte_range(byteOffset, byteOffset)

        return node

    def fetchLastCommonParent(self, oldNode, newNode):
        # print("oldNode =", oldNode.type)
        # print("newNode =", newNode.type)
        if oldNode is None or newNode is None:
            return None

        oldAncestors = set()
        old = oldNode.parent
        while old is not None:
            oldAncestors.add(old.type)
            old = old.parent

        new = newNode.parent
        while new is not None:
            if new.type in oldAncestors:
                return new
            new = new.parent

        return None

    def inputMethodEvent(self, event):
        if event.commitString():
            cursor = self.textCursor()
            cursor.insertText(event.commitString())
            self.setTextCursor(cursor)

    def SignalManager(self):
        self.fileOpenShortcut = QShortcut(QKeySequence("Ctrl+O"), self)

        self.fileOpenShortcut.activated      .connect(self.openFile)
        self.blockCountChanged               .connect(self.updateLineData)
        self.cursorPositionChanged           .connect(self.updateLineData)
        self.cursorPositionChanged           .connect(self.HighLightLine)
        self.updateRequest                   .connect(self.LineWidget.update)
        self.selectionChanged                .connect(self.updateSelection)
        self.textChanged                     .connect(self.reportChange)
        self.LineWidget.scrollEmit           .connect(super().wheelEvent)
        self.LineWidget.lineSelectEmit       .connect(self.selectLine)
        self.document().contentsChange       .connect(self.incrementCapture)
        self.textChanged                     .connect(self.LSPDocConfig)
        self.Language.client.diagnosticsReady.connect(self.diagnose)

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
        self.oldNode = self.fetchCursorNode()

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.oldNode = self.fetchCursorNode()
        # self.Language.syntax.printSyntax()
        print("Node =", self.oldNode)
        if self.oldNode.parent:
            print("Parent =", self.oldNode.parent)
        print("------")
        # self.Language.syntax.printAllNodes()
        # self.highlightNode()
        # QTimer.singleShot(1000, lambda: self.clearHighlight(4, 7))


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


class syntaxTree:
    def __init__(self, language):
        self.Parser = Parser(language)
        self.Source = b""
        self.Tree   = self.Parser.parse(self.Source)
    
    def sourceUpdate(self, source, incremental = True):
        self.Source =  source
        if incremental: self.Tree   = self.Parser.parse(self.Source, self.Tree)
        else: self.Tree   = self.Parser.parse(self.Source)

    def printSyntax(self, node = None, prefix="", is_last=True, is_root=True, field_name=None):
        if node is None: node = self.Tree.root_node
        if is_root:
            print(f"({node.type})")
            new_prefix = ""
        else:
            connector = "└── " if is_last else "├── "
            field_str = f"{field_name}: " if field_name else ""
            print(f"{prefix}{connector}{field_str}({node.type})")

            new_prefix = prefix + ("    " if is_last else "│   ")

        children = []
        cursor = node.walk()
        if cursor.goto_first_child():
            while True:
                if cursor.node.is_named:
                    children.append((cursor.node, cursor.field_name))
                if not cursor.goto_next_sibling():
                    break
            cursor.goto_parent()

        # Recursion
        for i, (child_node, child_field) in enumerate(children):
            is_last_child = i == (len(children) - 1)
            self.printSyntax(child_node, new_prefix, is_last_child, False, child_field)

    def printAllNodes(self, node = None):
        if node is None: node = self.Tree.root_node
        print(node.type, node.start_point, node.end_point)

        for child in node.children:
            self.printAllNodes(child)


class PythonLanguage(codeLanguage):

    def __init__(self, document, editor):
        super().__init__()
        self.syntax      = syntaxTree(Language(tree_sitter_python.language()))
        self.Highlighter = syntaxHighlighter(document, self.syntax, editor)
        self.client      = LSPClient()
    
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

    def commentSyntax(self):
        return "#"

    def keyWords(self):
        return {
            "and", "as", "assert", "async", "await", "break", "case", "class", "continue", "def", "del", "elif", "else", "except",
            "False", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda", "None", "nonlocal", "not", "or",
            "pass", "raise", "return", "True", "try", "while", "with", "yield"
        }


class syntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document, syntax, editor):
        super().__init__(document)
        self.syntax = syntax
        self.editor = editor

    def highlightBlock(self, text):
        if not self.syntax.Tree: return

        blockNumber = self.currentBlock().blockNumber()
        
        line_bytes = text.encode("utf-8")

        stack = [self.syntax.Tree.root_node]

        while stack:
            currentNode = stack.pop()

            start_row = currentNode.start_point[0]
            end_row = currentNode.end_point[0]

            if end_row < blockNumber or start_row > blockNumber:
                continue
                
            stack.extend(reversed(currentNode.children))

            applied = False
            format = QTextCharFormat()
            format.setFontItalic(False)

            if currentNode.type in VS_CONTROL_FLOW:
                format.setForeground(QColor("#C586C0"))
                applied = True
            elif currentNode.type in VS_KEYWORDS:
                format.setForeground(QColor("#2679BD"))
                applied = True
            elif currentNode.type in {"import", "from", "as"}:
                format.setForeground(QColor("#c586c0"))
                applied = True
            elif currentNode.type in {"def", "class"}:
                format.setForeground(QColor("#fe7b72"))
                applied = True
            elif currentNode.type in {"integer", "float", "complex"}:
                format.setForeground(QColor("#B5CEA8"))
                applied = True
            elif currentNode.type == "escape_sequence":
                format.setForeground(QColor("#CE9178"))
                applied = True
            elif currentNode.type in {"string", "string_start", "string_content", "string_end"}:
                format.setForeground(QColor("#a5d6ff"))
                applied = True
            elif currentNode.type == "comment":
                format.setForeground(QColor("#8b949e")) 
                format.setFontItalic(True)
                applied = True
            elif currentNode.type == "identifier":
                parent = currentNode.parent
                applied = True
                if parent is not None:
                    if parent.type == "call" and parent.child_by_field_name("function") == currentNode:
                        format.setForeground(QColor("#d2a8f7"))
                    elif parent.type == "function_definition" and parent.child_by_field_name("name") == currentNode:
                        format.setForeground(QColor("#d2a8f7"))
                    elif parent.type == "class_definition" and parent.child_by_field_name("name") == currentNode:
                        format.setForeground(QColor("#4dc1a0"))
                    elif parent.type == "decorator":
                        format.setForeground(QColor("#DCDCAA"))
                    elif  parent.type == "dotted_name":
                        format.setForeground(QColor("#4bc9b0"))
                    elif parent.type == "argument_list":
                        format.setForeground(QColor("#4dc1a0"))
                    else:
                        format.setForeground(QColor("#FFFFFF"))
                else:
                    format.setForeground(QColor("#9CDCFE"))
            elif currentNode.type in VS_OPERATORS or currentNode.type in {"(", ")", "[", "]", "{", "}", ":", ",", "."}:
                format.setForeground(QColor("#FFFFFF"))
                applied = True
            else:
                format.setForeground(QColor("#FFFFFF"))
                applied = True

            if applied:
                start_byte_col = currentNode.start_point[1] if start_row == blockNumber else 0
                end_byte_col = currentNode.end_point[1] if end_row == blockNumber else len(line_bytes)
                
                try:
                    startChar = len(line_bytes[:start_byte_col].decode("utf-8").encode("utf-16-le")) // 2
                    endChar = len(line_bytes[:end_byte_col].decode("utf-8").encode("utf-16-le")) // 2
                    
                    length = endChar - startChar
                    if length > 0:
                        self.setFormat(startChar, length, format)
                except UnicodeDecodeError:
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
        print(version, uri)

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