"""
convertproj.py — Библиотечный модуль для нормализации видео и конвертации под профиль телефона.
Переработан для GUI: без print()/input(), весь прогресс через callback.
"""

import os
import subprocess
import shutil
import multiprocessing
import json
from pathlib import Path
from typing import Optional, Callable


# ============================================================================
# ЗАВОДСКИЕ ПРОФИЛИ
# ============================================================================

def get_default_profiles() -> dict:
    """Вернуть встроенные заводские профили. Копия для изменений."""
    return {
        "itel_it2163r": {
            "description": "Профиль для Itel it2163R (160x128, 3GP/MPEG4)",
            "output_extension": ".3gp",
            "final_codec_video": "mpeg4",
            "final_bitrate_video": "200k",
            "final_resolution": "160x128",
            "scaling_algorithm": "lanczos",
            "final_codec_audio": "aac",
            "final_bitrate_audio": "96k",
            "final_samplerate_audio": 44100,
            "final_channels_audio": 2,
            "builtin": True,
        },
        "bq_3590": {
            "description": "Профиль для BQ 3590 (480x320, 3GP/MPEG4)",
            "output_extension": ".3gp",
            "final_codec_video": "mpeg4",
            "final_bitrate_video": "550k",
            "final_resolution": "480x320",
            "scaling_algorithm": "lanczos",
            "final_codec_audio": "aac",
            "final_bitrate_audio": "128k",
            "final_samplerate_audio": 44100,
            "final_channels_audio": 2,
            "builtin": True,
        },
    }


# ============================================================================
# ПРОТОКОЛ CALLBACK
# ============================================================================

class ProgressCallback:
    """Интерфейс callback для отчёта о прогрессе из рабочих потоков.

    Передаётся экземпляр, методы которого излучают Qt-сигналы из QThread.
    """
    def on_status(self, message: str) -> None: ...
    def on_progress(self, percent: float, current_file: str, file_index: int, total_files: int) -> None: ...
    def on_file_done(self, file_path: str) -> None: ...
    def on_error(self, error: str) -> None: ...
    def on_finished(self, output_files: list) -> None: ...


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def get_ffmpeg_path(bin_dir: Optional[Path] = None) -> str:
    """Вернуть путь к ffmpeg, предпочитая указанную bin_dir."""
    if bin_dir:
        candidate = str(bin_dir / "ffmpeg.exe")
        if os.path.isfile(candidate):
            return candidate
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise FileNotFoundError("ffmpeg не найден. Убедитесь, что он установлен или лежит в bin/.")

def get_ffprobe_path(bin_dir: Optional[Path] = None) -> str:
    """Вернуть путь к ffprobe."""
    if bin_dir:
        candidate = str(bin_dir / "ffprobe.exe")
        if os.path.isfile(candidate):
            return candidate
    found = shutil.which("ffprobe")
    if found:
        return found
    raise FileNotFoundError("ffprobe не найден.")

SUPPORTED_FORMATS = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm')

def is_vfr(file_path: str, ffprobe_executable: str) -> bool:
    """Проверить, имеет ли видео переменный FPS (VFR) в первых ~2 секундах."""
    cmd = [
        ffprobe_executable, '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'frame=pkt_duration_time',
        '-of', 'json',
        '-read_intervals', '%+2',
        file_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        durations = [float(f.get('pkt_duration_time', 0)) for f in data.get('frames', [])]
        if not durations:
            return False
        return len(set(round(d, 5) for d in durations)) > 1
    except Exception:
        return True  # Считаем VFR при ошибке для безопасности


# ============================================================================
# НОРМАЛИЗАЦИЯ (VFR → CFR)
# ============================================================================

def _normalize_one(args: tuple) -> Optional[str]:
    """Нормализовать один файл (используется внутри multiprocessing pool)."""
    file_path, ffmpeg_exe, output_dir, normalize_fps, hardware_encoder = args
    filename = os.path.basename(file_path)
    out_path = os.path.join(output_dir, filename)
    if os.path.exists(out_path):
        return out_path

    if hardware_encoder == 'libx264':
        cmd = [
            ffmpeg_exe, '-i', file_path,
            '-c:v', 'libx264', '-crf', '20', '-preset', 'fast',
            '-r', str(normalize_fps), '-vsync', 'cfr',
            '-c:a', 'copy',
            '-y', out_path,
        ]
    else:
        cmd = [
            ffmpeg_exe, '-i', file_path,
            '-c:v', hardware_encoder, '-preset', 'fast', '-cq', '24',
            '-r', str(normalize_fps), '-vsync', 'cfr',
            '-c:a', 'copy',
            '-y', out_path,
        ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_path
    except subprocess.CalledProcessError:
        return None


def normalize_videos(
    file_paths: list,
    ffmpeg_exe: str,
    ffprobe_exe: str,
    output_dir: str,
    normalize_fps: int = 30,
    hardware_encoder: str = 'h264_nvenc',
    cpu_cores: int = 4,
    callback: Optional[ProgressCallback] = None,
) -> list:
    """Проанализировать файлы на VFR, нормализовать нуждающиеся, вернуть все стабильные пути."""
    os.makedirs(output_dir, exist_ok=True)

    if callback:
        callback.on_status("Анализ файлов на VFR…")

    vfr_files = []
    cfr_files = []
    for i, fp in enumerate(file_paths):
        if callback:
            callback.on_progress(0, os.path.basename(fp), i + 1, len(file_paths))
        if is_vfr(fp, ffprobe_exe):
            vfr_files.append(fp)
        else:
            cfr_files.append(fp)

    if not vfr_files:
        if callback:
            callback.on_status("VFR-файлов не найдено, нормализация не требуется.")
        return cfr_files  # Все уже CFR

    if callback:
        callback.on_status(f"Нормализация {len(vfr_files)} VFR-файлов…")

    cores = min(cpu_cores, multiprocessing.cpu_count())
    pool_args = [(f, ffmpeg_exe, output_dir, normalize_fps, hardware_encoder) for f in vfr_files]

    with multiprocessing.Pool(processes=cores) as pool:
        results = list(pool.imap_unordered(_normalize_one, pool_args))

    normalized = [r for r in results if r is not None]
    failed = len(vfr_files) - len(normalized)

    if failed and callback:
        callback.on_error(f"{failed} файлов не удалось нормализовать.")

    return cfr_files + normalized


# ============================================================================
# КОНВЕРТАЦИЯ ПОД ТЕЛЕФОН
# ============================================================================

def _convert_one(args: tuple) -> Optional[str]:
    """Конвертировать один файл под профиль телефона (multiprocessing)."""
    file_path, ffmpeg_exe, profile, output_dir = args
    base = os.path.splitext(os.path.basename(file_path))[0]
    out_name = base + profile['output_extension']
    out_path = os.path.join(output_dir, out_name)
    if os.path.exists(out_path):
        return out_path

    filter_str = (
        f"scale={profile['final_resolution']}:force_original_aspect_ratio=decrease:"
        f"flags={profile['scaling_algorithm']},"
        f"pad={profile['final_resolution']}:-1:-1:color=black"
    )

    cmd = [
        ffmpeg_exe, '-i', file_path,
        '-c:v', profile['final_codec_video'],
        '-b:v', profile['final_bitrate_video'],
        '-vf', filter_str,
        '-c:a', profile['final_codec_audio'],
        '-b:a', profile['final_bitrate_audio'],
        '-ar', str(profile['final_samplerate_audio']),
        '-ac', str(profile['final_channels_audio']),
        '-y', out_path,
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_path
    except subprocess.CalledProcessError:
        return None


def convert_for_phone(
    file_paths: list,
    profile: dict,
    ffmpeg_exe: str,
    output_dir: str,
    cpu_cores: int = 4,
    callback: Optional[ProgressCallback] = None,
) -> list:
    """Пакетная конвертация файлов под профиль телефона."""
    os.makedirs(output_dir, exist_ok=True)

    if callback:
        callback.on_status(f"Конвертация {len(file_paths)} файлов…")

    cores = min(cpu_cores, multiprocessing.cpu_count())
    pool_args = [(f, ffmpeg_exe, profile, output_dir) for f in file_paths]

    with multiprocessing.Pool(processes=cores) as pool:
        results = list(pool.imap_unordered(_convert_one, pool_args))

    output_files = [r for r in results if r is not None]
    failed = len(file_paths) - len(output_files)

    if failed and callback:
        callback.on_error(f"{failed} файлов не удалось конвертировать.")
    if callback:
        callback.on_finished(output_files)

    return output_files


# ============================================================================
# ВЫСОКОУРОВНЕВЫЙ ПАЙПЛАЙН
# ============================================================================

def batch_process(
    file_paths: list,
    profile: dict,
    input_dir: str,
    output_dir: str,
    ffmpeg_exe: str,
    ffprobe_exe: str,
    normalize_fps: int = 30,
    hardware_encoder: str = 'h264_nvenc',
    cpu_cores: int = 4,
    callback: Optional[ProgressCallback] = None,
) -> list:
    """Полный пайплайн: нормализация (если VFR) → конвертация под профиль телефона.

    Файлы, уже имеющие CFR, пропускают нормализацию автоматически.
    """
    normalized_dir = os.path.join(os.path.dirname(output_dir), "NORMALIZED")

    # Этап 1: Нормализация
    if callback:
        callback.on_status("Этап 1: Проверка и нормализация VFR…")
    stable_files = normalize_videos(
        file_paths, ffmpeg_exe, ffprobe_exe,
        normalized_dir, normalize_fps, hardware_encoder,
        cpu_cores, callback,
    )

    # Этап 2: Конвертация
    if callback:
        callback.on_status("Этап 2: Конвертация под профиль телефона…")
    output = convert_for_phone(
        stable_files, profile, ffmpeg_exe,
        os.path.join(output_dir, profile.get('_profile_name', 'default')),
        cpu_cores, callback,
    )

    # Очистка временной папки
    if os.path.isdir(normalized_dir):
        try:
            shutil.rmtree(normalized_dir)
        except OSError:
            pass

    return output
