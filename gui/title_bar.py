"""
title_bar.py — Многоразовый кастомный заголовок в стиле macOS.
Используется в MainWindow и диалогах для единого стиля.
"""

from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton,
)


class TitleBar(QWidget):
    """Заголовок в стиле macOS с точками-светофорами и центрированным названием."""

    closeClicked = pyqtSignal()
    minimizeClicked = pyqtSignal()
    maximizeClicked = pyqtSignal()

    def __init__(self, title: str = "ConvertProj", parent=None):
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(42)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Слева: светофоры (фикс. ~120px для центрирования) ──
        left = QWidget()
        left.setObjectName("tbLeft")
        left.setFixedWidth(110)
        llo = QHBoxLayout(left)
        llo.setContentsMargins(16, 0, 0, 0)
        llo.setSpacing(7)

        self._close = QPushButton()
        self._close.setObjectName("tbClose")
        self._close.setFixedSize(13, 13)
        self._close.clicked.connect(self.closeClicked.emit)
        llo.addWidget(self._close)

        self._min = QPushButton()
        self._min.setObjectName("tbMin")
        self._min.setFixedSize(13, 13)
        self._min.clicked.connect(self.minimizeClicked.emit)
        llo.addWidget(self._min)

        self._max = QPushButton()
        self._max.setObjectName("tbMax")
        self._max.setFixedSize(13, 13)
        self._max.clicked.connect(self.maximizeClicked.emit)
        llo.addWidget(self._max)

        llo.addStretch()
        layout.addWidget(left)

        # ── Центр: заголовок ──
        self._title = QLabel(title)
        self._title.setObjectName("tbTitle")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title, stretch=1)

        # ── Справа: утилиты (та же ширина для баланса) ──
        self._right = QWidget()
        self._right.setObjectName("tbRight")
        self._right.setFixedWidth(110)
        self._right_layout = QHBoxLayout(self._right)
        self._right_layout.setContentsMargins(0, 0, 16, 0)
        self._right_layout.setSpacing(4)
        self._right_layout.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self._right)

    # ── Публичное API ─────────────────────────────────────────────────────

    def right_layout(self) -> QHBoxLayout:
        return self._right_layout

    def set_title(self, text: str):
        self._title.setText(text)

    def set_dialog_mode(self, dialog: bool = True):
        """Скрыть кнопки свернуть/развернуть для диалогов."""
        self._min.setVisible(not dialog)
        self._max.setVisible(not dialog)

    def theme_widgets(self):
        """Вернуть (close, min, max) для внешнего доступа к стилям."""
        return self._close, self._min, self._max
