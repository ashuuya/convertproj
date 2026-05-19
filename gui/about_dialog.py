"""
about_dialog.py — Диалог «О программе» с проверкой версий ffmpeg/yt-dlp.
"""

import os
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QMessageBox, QProgressBar,
)

from gui.title_bar import TitleBar
from gui.base_dialog import BaseDialog


class UpdateChecker(QThread):
    result = pyqtSignal(dict)

    def __init__(self, bin_dir: Path):
        super().__init__()
        self._bin_dir = bin_dir

    def run(self):
        info = {"ffmpeg": None, "yt-dlp": None}
        ff = self._bin_dir / "ffmpeg.exe"
        if ff.is_file():
            try:
                r = subprocess.run([str(ff), "-version"], capture_output=True, text=True, timeout=10)
                info["ffmpeg"] = r.stdout.split("\n")[0].strip() if r.stdout else None
            except Exception:
                pass
        yt = self._bin_dir / "yt-dlp.exe"
        if yt.is_file():
            try:
                r = subprocess.run([str(yt), "--version"], capture_output=True, text=True, timeout=10)
                info["yt-dlp"] = r.stdout.strip()
            except Exception:
                pass
        self.result.emit(info)


class AboutDialog(BaseDialog):
    """Безрамочный диалог «О программе» с информацией о компонентах."""

    def __init__(self, app_dir: Path, bin_dir: Path):
        super().__init__("О программе", 420, 320)
        self._app_dir = app_dir
        self._bin_dir = bin_dir
        self._checker = None

        lo = self.content_layout()

        title = QLabel("ConvertProj")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo.addWidget(title)

        sub = QLabel("Скачивание и конвертация видео для кнопочных телефонов")
        sub.setObjectName("subtitleLabel")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        lo.addWidget(sub)

        self._ff_lbl = QLabel("FFmpeg: проверка…", objectName="monoLabel")
        lo.addWidget(self._ff_lbl)
        self._yt_lbl = QLabel("yt-dlp: проверка…", objectName="monoLabel")
        lo.addWidget(self._yt_lbl)
        self._py_lbl = QLabel(f"Python: {os.sys.version.split()[0]}", objectName="monoLabel")
        lo.addWidget(self._py_lbl)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        lo.addWidget(self._progress)

        bh = QHBoxLayout(); bh.setSpacing(8)
        self._upd_ff = QPushButton("Обновить FFmpeg")
        self._upd_ff.clicked.connect(self._update_ff)
        bh.addWidget(self._upd_ff)

        self._upd_yt = QPushButton("Обновить yt-dlp")
        self._upd_yt.clicked.connect(self._update_yt)
        bh.addWidget(self._upd_yt)

        self._ref_btn = QPushButton("🔄"); self._ref_btn.setObjectName("iconBtn")
        self._ref_btn.clicked.connect(self._check)
        bh.addWidget(self._ref_btn)
        lo.addLayout(bh)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        lo.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self._check()

    def _check(self):
        self._ff_lbl.setText("FFmpeg: проверка…")
        self._yt_lbl.setText("yt-dlp: проверка…")
        self._checker = UpdateChecker(self._bin_dir)
        self._checker.result.connect(self._on_result)
        self._checker.start()

    def _on_result(self, info):
        ff = info.get("ffmpeg") or "не найден"
        yt = info.get("yt-dlp") or "не найден"
        self._ff_lbl.setText(f"FFmpeg: {ff}")
        self._yt_lbl.setText(f"yt-dlp: {yt}")
        self._upd_ff.setEnabled(info.get("ffmpeg") is not None)
        self._upd_yt.setEnabled(info.get("yt-dlp") is not None)

    def _update_ff(self):
        try:
            import ffmpeg_downloader  # noqa
        except ImportError:
            QMessageBox.warning(self, "", "ffmpeg-downloader не установлен.")
            return
        self._progress.setVisible(True); self._progress.setMaximum(0)
        self._upd_ff.setEnabled(False)
        subprocess.Popen(["python", "-m", "ffmpeg_downloader", "--destination", str(self._bin_dir)],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        QMessageBox.information(self, "", "FFmpeg обновляется в фоне.")

    def _update_yt(self):
        yt = self._bin_dir / "yt-dlp.exe"
        if not yt.is_file():
            return
        self._progress.setVisible(True); self._progress.setMaximum(0)
        self._upd_yt.setEnabled(False)
        try:
            subprocess.run([str(yt), "--update"], check=True, capture_output=True, text=True)
            QMessageBox.information(self, "", "yt-dlp обновлён.")
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(self, "", f"Ошибка: {e.stderr or e}")
        finally:
            self._progress.setVisible(False)
            self._upd_yt.setEnabled(True)
            self._check()
