from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize


class ScalableIconButton(QPushButton):
    def __init__(self, icon_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setIcon(QIcon(icon_path))
        self.default_icon_size = QSize(38, 38)  # Default icon size
        self.hover_icon_size = QSize(42, 42)  # Scaled icon size (110%)
        self.setIconSize(self.default_icon_size)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.setIconSize(self.hover_icon_size)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.setIconSize(self.default_icon_size)