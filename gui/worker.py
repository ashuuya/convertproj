"""
worker.py — QObject-воркеры для фоновой загрузки и конвертации.
Каждый воркер запускается в QThread и излучает сигналы прогресса.
"""

import os
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

from convertproj import (
    ProgressCallback,
    get_ffmpeg_path,
    get_ffprobe_path,
    batch_process,
)
from ytdload import DownloadCallback, get_ytdlp_path, download_videos


# ── Контейнер сигналов (общий для загрузки и конвертации) ──────────────

class _Signals(QObject):
    status = pyqtSignal(str)
    progress = pyqtSignal(float, str, int, int)  # проценты, имя файла, индекс, всего
    file_done = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(object)  # список результирующих путей


# ── Сборка callback'ов, излучающих сигналы ─────────────────────────────

def _make_progress_callback(sig: _Signals) -> ProgressCallback:
    class _CB(ProgressCallback):
        def on_status(self, msg):
            sig.status.emit(msg)
        def on_progress(self, pct, cur, idx, tot):
            sig.progress.emit(pct, cur, idx, tot)
        def on_file_done(self, fp):
            sig.file_done.emit(fp)
        def on_error(self, err):
            sig.error.emit(err)
        def on_finished(self, outputs):
            sig.finished.emit(outputs)
    return _CB()


def _make_download_callback(sig: _Signals) -> DownloadCallback:
    class _CB(DownloadCallback):
        def on_status(self, msg):
            sig.status.emit(msg)
        def on_progress(self, pct, cur, idx, tot):
            sig.progress.emit(pct, cur, idx, tot)
        def on_file_done(self, fp):
            sig.file_done.emit(fp)
        def on_error(self, err):
            sig.error.emit(err)
        def on_finished(self, outputs):
            sig.finished.emit(outputs)
    return _CB()


# ── Download Worker ─────────────────────────────────────────────────────────

class DownloadWorker(QObject):
    """Скачивание видео с YouTube. run() вызывается через QThread.started."""

    started = pyqtSignal()
    status = pyqtSignal(str)
    progress = pyqtSignal(float, str, int, int)
    file_done = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(object)

    def __init__(self, links: list, quality: str, output_dir: str, bin_dir: Optional[Path] = None, max_workers: int = 3):
        super().__init__()
        self._links = links
        self._quality = quality
        self._output_dir = output_dir
        self._bin_dir = bin_dir
        self._max_workers = max_workers

    def run(self):
        self.started.emit()
        sig = _Signals()
        sig.status.connect(self.status.emit)
        sig.progress.connect(self.progress.emit)
        sig.file_done.connect(self.file_done.emit)
        sig.error.connect(self.error.emit)
        sig.finished.connect(self.finished.emit)

        try:
            ytdlp = get_ytdlp_path(self._bin_dir)
        except FileNotFoundError as e:
            self.error.emit(str(e))
            self.finished.emit([])
            return

        cb = _make_download_callback(sig)
        result = download_videos(
            self._links, self._quality, self._output_dir, ytdlp, cb,
            max_workers=self._max_workers,
        )
        if result is not None:
            self.finished.emit(result)


# ── Convert Worker ──────────────────────────────────────────────────────────

class ConvertWorker(QObject):
    """Нормализация + конвертация под профиль телефона. run() в QThread."""

    started = pyqtSignal()
    status = pyqtSignal(str)
    progress = pyqtSignal(float, str, int, int)
    file_done = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(object)

    def __init__(
        self,
        file_paths: list,
        profile: dict,
        input_dir: str,
        output_dir: str,
        bin_dir: Optional[Path] = None,
        normalize_fps: int = 30,
        hardware_encoder: str = 'h264_nvenc',
        cpu_cores: int = 4,
    ):
        super().__init__()
        self._file_paths = file_paths
        self._profile = profile
        self._input_dir = input_dir
        self._output_dir = output_dir
        self._bin_dir = bin_dir
        self._normalize_fps = normalize_fps
        self._hardware_encoder = hardware_encoder
        self._cpu_cores = cpu_cores

    def run(self):
        self.started.emit()
        sig = _Signals()
        sig.status.connect(self.status.emit)
        sig.progress.connect(self.progress.emit)
        sig.file_done.connect(self.file_done.emit)
        sig.error.connect(self.error.emit)
        sig.finished.connect(self.finished.emit)

        try:
            ffmpeg = get_ffmpeg_path(self._bin_dir)
            ffprobe = get_ffprobe_path(self._bin_dir)
        except FileNotFoundError as e:
            self.error.emit(str(e))
            self.finished.emit([])
            return

        cb = _make_progress_callback(sig)
        try:
            result = batch_process(
                self._file_paths, self._profile,
                self._input_dir, self._output_dir,
                ffmpeg, ffprobe,
                self._normalize_fps, self._hardware_encoder,
                self._cpu_cores, cb,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit([])
