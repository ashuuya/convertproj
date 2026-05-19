"""
ytdload.py — Библиотечный модуль для скачивания видео с YouTube через yt-dlp.
Переработан для GUI: без print()/input(), весь прогресс через callback.
Поддерживает многопоточную загрузку через ThreadPoolExecutor.
"""

import os
import subprocess
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional


# ============================================================================
# CALLBACK
# ============================================================================

class DownloadCallback:
    def on_status(self, message: str) -> None: ...
    def on_progress(self, percent: float, current_file: str, file_index: int, total_files: int) -> None: ...
    def on_file_done(self, file_path: str) -> None: ...
    def on_error(self, error: str) -> None: ...
    def on_finished(self, downloaded_files: list) -> None: ...


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def get_ytdlp_path(bin_dir: Optional[Path] = None) -> str:
    """Вернуть путь к yt-dlp."""
    if bin_dir:
        candidate = str(bin_dir / "yt-dlp.exe")
        if os.path.isfile(candidate):
            return candidate
    found = shutil.which("yt-dlp")
    if found:
        return found
    # Запасной вариант: рядом со скриптом
    script_dir = Path(__file__).parent
    local = script_dir / "yt-dlp.exe"
    if local.is_file():
        return str(local)
    raise FileNotFoundError("yt-dlp.exe не найден. Положите его в папку bin/ или добавьте в PATH.")


def parse_links(links_file: str) -> list:
    """Прочитать ссылки из файла, пропуская комментарии и пустые строки."""
    links = []
    with open(links_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                links.append(line)
    return links


def build_format_string(quality: str) -> str:
    """Собрать строку формата yt-dlp из названия пресета качества."""
    base_video = "bestvideo[ext=mp4]"
    base_audio = "bestaudio[ext=m4a]"
    fallback = "best[ext=mp4]/best"

    quality = quality.strip().lower()

    if quality == "360p":
        return f"{base_video}[height<=360]+{base_audio}/{fallback}"
    elif quality == "720p":
        return f"{base_video}[height<=720]+{base_audio}/{fallback}"
    elif quality == "1080p":
        return f"{base_video}[height<=1080]+{base_audio}/{fallback}"
    elif quality == "max":
        return f"{base_video}+{base_audio}/{fallback}"
    else:
        # По умолчанию 1080p
        return f"{base_video}[height<=1080]+{base_audio}/{fallback}"


# ============================================================================
# СКАЧИВАНИЕ
# ============================================================================

def _download_one(
    link: str,
    index: int,
    total: int,
    format_arg: str,
    output_dir: str,
    ytdlp_exe: str,
    callback: Optional[DownloadCallback],
    lock: threading.Lock,
    progress_state: dict,
) -> Optional[str]:
    """Скачать одно видео. Возвращает путь к файлу или None при ошибке.

    Работает в отдельном потоке ThreadPoolExecutor.
    """
    if callback:
        callback.on_status(f"[{index}/{total}] Скачивание: {link}")

    with lock:
        progress_state[index] = (0, link)

    cmd = [
        ytdlp_exe,
        '-f', format_arg,
        '--merge-output-format', 'mp4',
        '--no-playlist',
        '--ignore-errors',
        '--no-progress',
        '-o', os.path.join(output_dir, '%(title)s.%(ext)s'),
        link,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        mp4s = [os.path.join(output_dir, f) for f in os.listdir(output_dir)
                if f.lower().endswith('.mp4') and os.path.isfile(os.path.join(output_dir, f))]
        if mp4s:
            latest = max(mp4s, key=os.path.getmtime)
            with lock:
                progress_state[index] = (100, os.path.basename(latest))
            if callback:
                callback.on_file_done(latest)
            return latest
    except subprocess.CalledProcessError as e:
        with lock:
            progress_state[index] = (0, link)
        if callback:
            callback.on_error(f"Ошибка скачивания: {link}\n{e.stderr or e}")
    return None


def _emit_aggregated_progress(
    callback: Optional[DownloadCallback],
    progress_state: dict,
    total: int,
    lock: threading.Lock,
):
    """Посчитать и излучить средний прогресс по всем активным загрузкам."""
    with lock:
        if not progress_state:
            return
        total_pct = sum(v[0] for v in progress_state.values())
        avg_pct = total_pct / len(progress_state)
        # Показываем имя файла, который ближе всего к среднему прогрессу
        current_file = ""
        for idx, (pct, name) in progress_state.items():
            if abs(pct - avg_pct) < 5 or not current_file:
                current_file = name or f"файл {idx}"
    if callback:
        callback.on_progress(avg_pct, current_file, 1, total)


def download_videos(
    links: list,
    quality: str,
    output_dir: str,
    ytdlp_exe: str,
    callback: Optional[DownloadCallback] = None,
    max_workers: int = 3,
) -> list:
    """Скачать список YouTube-ссылок в нескольких потоках.

    Args:
        links: Список URL для скачивания.
        quality: Желаемое качество (360p, 720p, 1080p, max).
        output_dir: Папка для сохранения.
        ytdlp_exe: Путь к yt-dlp.exe.
        callback: Колбэк для отслеживания прогресса.
        max_workers: Количество параллельных загрузок (по умолчанию 3).

    Returns:
        Список путей к скачанным файлам.
    """
    os.makedirs(output_dir, exist_ok=True)

    if not links:
        if callback:
            callback.on_status("Нет ссылок для скачивания.")
        return []

    format_arg = build_format_string(quality)
    total = len(links)

    lock = threading.Lock()
    progress_state: dict = {}  # {index: (percent, filename)}

    downloaded = []

    if callback:
        callback.on_status(f"Загрузка {total} видео ({max_workers} потоков)…")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _download_one, link, i, total, format_arg,
                output_dir, ytdlp_exe, callback, lock, progress_state,
            ): i
            for i, link in enumerate(links, 1)
        }

        # По мере завершения — собираем результаты и обновляем прогресс
        for future in as_completed(futures):
            result = future.result()
            if result:
                downloaded.append(result)
            _emit_aggregated_progress(callback, progress_state, total, lock)

    if callback:
        callback.on_finished(downloaded)
        callback.on_status(f"Скачано {len(downloaded)} из {total} видео.")

    return downloaded
