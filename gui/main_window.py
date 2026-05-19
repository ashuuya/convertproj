"""
main_window.py — Главное окно приложения.
Безрамочное окно, кастомный TitleBar, пилюльные вкладки, QStackedWidget.
"""

import os
import json
from pathlib import Path

from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QButtonGroup, QStackedWidget,
    QMessageBox, QFrame, QSizePolicy,
)
from PyQt6.QtWidgets import QGraphicsOpacityEffect

from gui.title_bar import TitleBar
from gui.download_tab import DownloadTab
from gui.convert_tab import ConvertTab
from gui.about_dialog import AboutDialog
from gui.styles import THEMES
from gui.translations import tr


CONFIG_FILE = "config.json"


class FadeStackedWidget(QStackedWidget):
    """QStackedWidget с fade-анимацией при переключении."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._anim = None

    def _cleanup(self):
        """Удалить остаточный graphics effect."""
        if self._anim:
            try:
                self._anim.stop()
            except RuntimeError:
                pass
            self._anim = None
        w = self.currentWidget()
        if w:
            try:
                w.setGraphicsEffect(None)
            except RuntimeError:
                pass

    def setCurrentIndex(self, index: int):
        self._cleanup()
        current = self.currentWidget()
        super().setCurrentIndex(index)
        next_w = self.currentWidget()
        if current and next_w and current != next_w:
            self._fade_in(next_w)

    def _fade_in(self, widget):
        self._cleanup()
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(self._on_fade_done)
        self._anim = anim
        anim.start()

    def _on_fade_done(self):
        self._cleanup()


class PillSlider(QWidget):
    """Виджет-ползунок, который плавно переезжает под активной вкладкой."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pillSlider")
        self.setVisible(False)

    def slide_to(self, target_btn: QPushButton, parent_widget: QWidget):
        """Плавно переместиться под target_btn внутри parent_widget."""
        target_geo = target_btn.geometry()
        start_rect = self.geometry()

        # Целевые координаты относительно родителя
        end_rect = QRect(
            target_geo.x(),
            parent_widget.height() - 3,
            target_geo.width(),
            3,
        )

        if self.isVisible():
            anim = QPropertyAnimation(self, b"geometry")
            anim.setDuration(180)
            anim.setStartValue(start_rect)
            anim.setEndValue(end_rect)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.start()
        else:
            self.setVisible(True)
            self.setGeometry(end_rect)


class MainWindow(QMainWindow):
    """Безрамочное главное окно с кастомным заголовком и пилюльными вкладками."""

    def __init__(self, app_dir: Path, bin_dir: Path):
        super().__init__()
        self._app_dir = app_dir
        self._bin_dir = bin_dir
        self._config = self._load_config()
        self._current_theme = self._config.get("theme", "light")
        self._language = self._config.get("language", "ru")

        # Безрамочное окно
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinMaxButtonsHint
        )

        self._drag_pos = QPoint()
        self._setup_ui()
        self._apply_theme(self._current_theme)
        self._restore_geometry()

    # ── DWM shadow ─────────────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        self._enable_shadow()
        # Применить желаемый размер ПОСЛЕ показа окна, иначе Qt/WM переопределяет
        # под sizeHint() layout-a (≈714px из-за двух колонок ConvertTab).
        self.resize(1480, 540)

    def _enable_shadow(self):
        try:
            import ctypes
            hwnd = int(self.winId())
            # DWMWA_WINDOW_CORNER_PREFERENCE = 33 → round = 2
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(ctypes.c_int(2)), ctypes.sizeof(ctypes.c_int(4))
            )
            class MARGINS(ctypes.Structure):
                _fields_ = [("cxLeftWidth", ctypes.c_int), ("cxRightWidth", ctypes.c_int),
                            ("cyTopHeight", ctypes.c_int), ("cyBottomHeight", ctypes.c_int)]
            margins = MARGINS(0, 0, 1, 0)
            ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))
        except Exception:
            pass

    # ── Config ─────────────────────────────────────────────────────────────

    def _load_config(self) -> dict:
        path = self._app_dir / CONFIG_FILE
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save_config(self):
        path = self._app_dir / CONFIG_FILE
        self._config["theme"] = self._current_theme
        self._config["language"] = self._language
        g = self.geometry()
        self._config["window_geometry"] = f"{g.x()},{g.y()},{g.width()},{g.height()}"
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _restore_geometry(self):
        g = self._config.get("window_geometry", "")
        if g:
            try:
                p = [int(x) for x in g.split(",")]
                if len(p) == 4:
                    self.setGeometry(*p)
                    return
            except (ValueError, TypeError):
                pass
        self.resize(540, 960)

    # ── UI ─────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        # Корневой контейнер
        root_frame = QFrame()
        root_frame.setObjectName("rootFrame")
        self.setCentralWidget(root_frame)
        root = QVBoxLayout(root_frame)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Кастомный заголовок ──
        self._title_bar = TitleBar("ConvertProj", self)
        self._title_bar.closeClicked.connect(self.close)
        self._title_bar.minimizeClicked.connect(self.showMinimized)
        self._title_bar.maximizeClicked.connect(self._toggle_max)

        # Кнопки утилит в правой части заголовка
        rl = self._title_bar.right_layout()

        self._theme_btn = QPushButton("🌙" if self._current_theme == "light" else "☀️")
        self._theme_btn.setObjectName("iconBtn")
        self._theme_btn.setToolTip("Переключить тему")
        self._theme_btn.clicked.connect(self._toggle_theme)
        rl.addWidget(self._theme_btn)

        self._lang_btn = QPushButton("EN" if self._language == "ru" else "RU")
        self._lang_btn.setObjectName("iconBtn")
        self._lang_btn.setToolTip("Язык / Language")
        self._lang_btn.clicked.connect(self._toggle_language)
        rl.addWidget(self._lang_btn)

        self._about_btn = QPushButton("ⓘ")
        self._about_btn.setObjectName("iconBtn")
        self._about_btn.setToolTip("О программе")
        self._about_btn.clicked.connect(self._show_about)
        rl.addWidget(self._about_btn)

        root.addWidget(self._title_bar)

        # ── Пилюльные вкладки ──
        pill_wrap = QHBoxLayout()
        pill_wrap.setContentsMargins(16, 10, 16, 0)

        pill_container = QWidget()
        pill_container.setObjectName("pillContainer")
        pill_container.setFixedHeight(56)
        pl = QHBoxLayout(pill_container)
        pl.setContentsMargins(4, 4, 4, 4)
        pl.setSpacing(4)
        pl.addStretch()

        self._tab_group = QButtonGroup(self)
        self._tab_group.setExclusive(True)

        self._pill_dl = QPushButton("📥 Скачивание")
        self._pill_dl.setObjectName("pillTab")
        self._pill_dl.setCheckable(True)
        self._pill_dl.setChecked(True)
        self._pill_dl.setProperty("active", True)
        self._tab_group.addButton(self._pill_dl, 0)
        pl.addWidget(self._pill_dl)

        pl.addSpacing(4)

        self._pill_cv = QPushButton("⚙️ Конвертация")
        self._pill_cv.setObjectName("pillTab")
        self._pill_cv.setCheckable(True)
        self._pill_cv.setProperty("active", False)
        self._tab_group.addButton(self._pill_cv, 1)
        pl.addWidget(self._pill_cv)

        pl.addStretch()

        # Ползунок под активной вкладкой
        self._pill_slider = PillSlider(pill_container)
        self._tab_group.idClicked.connect(self._switch_tab)

        pill_wrap.addWidget(pill_container)
        root.addLayout(pill_wrap)

        # ── Контент ──
        content_margin = QVBoxLayout()
        content_margin.setContentsMargins(16, 8, 16, 16)

        self._stack = FadeStackedWidget()
        self._download_tab = DownloadTab(self._app_dir, self._bin_dir, self._config)
        self._convert_tab = ConvertTab(self._app_dir, self._bin_dir, self._config)
        # Актуализируем cpu_cores в config при каждом изменении spinbox'а
        self._convert_tab._core_spin.valueChanged.connect(
            lambda v: self._config.__setitem__("cpu_cores", v)
        )
        self._stack.addWidget(self._download_tab)
        self._stack.addWidget(self._convert_tab)
        content_margin.addWidget(self._stack)
        root.addLayout(content_margin)

        # Авто-добавление скачанного в очередь конвертации
        self._download_tab.downloads_finished.connect(self._on_dl_finished)
        self._retranslate()

    # ── Слоты ──────────────────────────────────────────────────────────────

    def _switch_tab(self, tab_id: int):
        for btn in (self._pill_dl, self._pill_cv):
            active = self._tab_group.id(btn) == tab_id
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Анимация ползунка
        active_btn = self._pill_dl if tab_id == 0 else self._pill_cv
        self._pill_slider.slide_to(active_btn, active_btn.parentWidget())

        self._stack.setCurrentIndex(tab_id)

    def _on_dl_finished(self, files: list):
        if files:
            self._switch_tab(1)
            self._convert_tab.add_files(files)

    def _toggle_theme(self):
        self._current_theme = "dark" if self._current_theme == "light" else "light"
        self._apply_theme(self._current_theme)
        self._theme_btn.setText("☀️" if self._current_theme == "dark" else "🌙")
        self._save_config()

    def _apply_theme(self, theme: str):
        qss = THEMES.get(theme, THEMES["light"])
        self.setStyleSheet(qss)

    def _retranslate(self):
        """Обновить все тексты UI для текущего языка."""
        self._pill_dl.setText(f"📥 {tr('Скачивание')}")
        self._pill_cv.setText(f"⚙️ {tr('Конвертация')}")
        self._theme_btn.setToolTip(tr("Переключить тему"))
        self._lang_btn.setToolTip(tr("Язык / Language"))
        self._about_btn.setToolTip(tr("О программе"))
        # Прокинуть во вкладки
        self._download_tab.retranslate_ui()
        self._convert_tab.retranslate_ui()

    def _toggle_language(self):
        self._language = "en" if self._language == "ru" else "ru"
        self._lang_btn.setText("EN" if self._language == "ru" else "RU")
        from PyQt6.QtWidgets import QApplication
        from gui.translations import install_translation
        install_translation(QApplication.instance(), self._app_dir, self._language)
        self._retranslate()
        self._save_config()

    def _show_about(self):
        dlg = AboutDialog(self._app_dir, self._bin_dir)
        dlg.exec()

    def _toggle_max(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    # ── Drag ───────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            tb = self._title_bar
            if event.pos().y() <= tb.y() + tb.height():
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            tb = self._title_bar
            if event.pos().y() <= tb.y() + tb.height() + 5:
                if self.isMaximized():
                    self.showNormal()
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = QPoint()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        tb = self._title_bar
        if event.pos().y() <= tb.y() + tb.height():
            self._toggle_max()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    # ── Close ──────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._config["last_profile"] = self._convert_tab._profile_cb.currentText()
        self._config["hardware_encoder"] = self._convert_tab._encoder_cb.currentText()
        self._config["cpu_cores"] = self._convert_tab._core_spin.value()
        checked = self._download_tab._qg.checkedButton()
        qm = {self._download_tab._rb_360: "360p", self._download_tab._rb_720: "720p",
              self._download_tab._rb_1080: "1080p", self._download_tab._rb_max: "max"}
        self._config["download_quality"] = qm.get(checked, "1080p")
        self._save_config()
        super().closeEvent(event)
