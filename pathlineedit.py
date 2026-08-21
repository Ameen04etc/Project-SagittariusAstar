from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import QTimer

class PathLineEdit(QLineEdit):

    def focusInEvent(self, event):
        super().focusInEvent(event)

        QTimer.singleShot(
            0,
            self.selectAll
        )