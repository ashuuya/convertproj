"""
base_dialog.py — Базовый класс для безрамочных диалогов.
Содержит общий TitleBar, тень DWM и поддержку перетаскивания.
"""

import ctypes
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFrame,
)

from gui.title_bar import TitleBar


class BaseDialog(QDialog):
    """Безрамочный диалог с кастомным заголовком, тенью и перетаскиванием.

    Наследники вызывают super().__init__(title, width, height, parent)
    и реализуют свою логику в content_layout().
    """

    def __init__(self, title: str, width: int = 400, height: int = 200, parent=None):
        super().__init__(parent)
        self._drag_pos = QPoint()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog
        )
        self.setFixedSize(width, height)

        # Корневой layout
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # TitleBar
        self._title_bar = TitleBar(title, self)
        self._title_bar.set_dialog_mode(True)
        self._title_bar.closeClicked.connect(self.reject)
        root.addWidget(self._title_bar)

        # Контент (glassCard)
        self._content = QFrame()
        self._content.setObjectName("glassCard")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(24, 20, 24, 20)
        self._content_layout.setSpacing(14)
        root.addWidget(self._content, stretch=1)

        self._apply_shadow()

    def _apply_shadow(self):
        """Включить тень DWM для безрамочного окна."""
        try:
            hwnd = int(self.winId())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(ctypes.c_int(2)), ctypes.sizeof(ctypes.c_int(4))
            )
            class M(ctypes.Structure):
                _fields_ = [
                    ("cxLeftWidth", ctypes.c_int),
                    ("cxRightWidth", ctypes.c_int),
                    ("cyTopHeight", ctypes.c_int),
                    ("cyBottomHeight", ctypes.c_int),
                ]
            margins = M(0, 0, 1, 0)
            ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))
        except Exception:
            pass

    def content_layout(self) -> QVBoxLayout:
        """Вернуть layout контента для добавления виджетов."""
        return self._content_layout

    # ── Перетаскивание ──

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            tb = self._title_bar
            if event.pos().y() <= tb.y() + tb.height():
                self._drag_pos = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = QPoint()
        super().mouseReleaseEvent(event)
