import sys

from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QStylePainter,
    QStyleOptionButton,
    QStyle
)
from PySide6.QtCore import QSize


class VPushButton(QPushButton):

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(size.height(), size.width())

    def minimumSizeHint(self):
        # size = super().minimumSizeHint()
        # return QSize(size.height(), size.width())
        return QSize(0, 0)

    def paintEvent(self, event):

        painter = QStylePainter(self)

        painter.rotate(-90)
        painter.translate(-self.height(), 0)

        option = QStyleOptionButton()
        self.initStyleOption(option)

        option.rect.setRect(
            0,
            0,
            self.height(),
            self.width()
        )

        painter.drawControl(
            QStyle.ControlElement.CE_PushButton,
            option
        )