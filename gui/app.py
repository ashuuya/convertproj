"""
app.py — Загрузчик приложения: QApplication, тема, локаль, бинарники.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from gui.main_window import MainWindow
from gui.styles import THEMES
from gui.translations import install_translation


def get_app_dir() -> Path:
    """Вернуть корневую директорию приложения.

    В frozen-режиме (PyInstaller --onedir): директория с .exe.
    В режиме разработки: корень проекта (родитель gui/).
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.resolve()


def get_bin_dir(app_dir: Path) -> Path:
    """Вернуть директорию для встроенных бинарников (ffmpeg, yt-dlp)."""
    if getattr(sys, 'frozen', False):
        return app_dir / "_internal"
    return app_dir / "bin"


def ensure_binaries(bin_dir: Path) -> None:
    """Проверить наличие ffmpeg/ffprobe/yt-dlp; скопировать при необходимости.

    В frozen-режиме бинарники берутся из _internal/ (PyInstaller data).
    В dev-режиме — из bin/ или system PATH.
    """
    bin_dir.mkdir(parents=True, exist_ok=True)

    # Проверяем, что уже есть
    for name in ("ffmpeg.exe", "ffprobe.exe", "yt-dlp.exe"):
        target = bin_dir / name
        if target.is_file():
            continue

        # Пробуем скопировать из _internal (PyInstaller bundle)
        meipass = Path(getattr(sys, '_MEIPASS', ''))
        if meipass.is_dir() and (meipass / name).is_file():
            shutil.copy2(str(meipass / name), str(target))
            continue

        # Пробуем system PATH
        which = shutil.which(name.replace(".exe", ""))
        if which:
            shutil.copy2(which, str(target))
            continue

        # ffprobe обычно рядом с ffmpeg
        if name == "ffprobe.exe":
            ffmpeg_path = bin_dir / "ffmpeg.exe"
            if ffmpeg_path.is_file():
                alt = ffmpeg_path.parent / "ffprobe.exe"
                if alt.is_file():
                    shutil.copy2(str(alt), str(target))


def detect_system_theme() -> str:
    """Определить системную тёмную/светлую тему через darkdetect."""
    try:
        import darkdetect
        return "dark" if darkdetect.isDark() else "light"
    except (ImportError, AttributeError):
        return "light"


def run() -> None:
    """Создать и запустить приложение."""
    app_dir = get_app_dir()
    bin_dir = get_bin_dir(app_dir)

    # Проверяем бинарники
    ensure_binaries(bin_dir)

    # QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("ConvertProj")
    app.setOrganizationName("ConvertProj")

    # High-DPI
    app.setStyle("Fusion")

    # Окно (загружает настройки, включая язык)
    window = MainWindow(app_dir, bin_dir)

    # Устанавливаем перевод, если язык не русский
    install_translation(app, app_dir, window._language)

    window.show()

    # Авто-тема при первом запуске
    if "theme" not in window._config or window._config.get("theme") == "system":
        detected = detect_system_theme()
        window._current_theme = detected
        window._apply_theme(detected)
        window._theme_btn.setText("☀️" if detected == "dark" else "🌙")

    sys.exit(app.exec())
