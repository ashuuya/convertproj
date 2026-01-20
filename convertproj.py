import os
import sys
import subprocess
import shutil
import multiprocessing
from tqdm import tqdm
import json

# ==================================================================================================================================================================================================================================
# НАСТРОЙКИ ПРОФИЛЕЙ

PROFILES = {
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
    },
    "default": {
        "description": "Профиль по умолчанию (Itel it2163R)",
        "output_extension": ".3gp",
        "final_codec_video": "mpeg4",
        "final_bitrate_video": "200k",
        "final_resolution": "160x128",
        "scaling_algorithm": "lanczos",
        "final_codec_audio": "aac",
        "final_bitrate_audio": "96k",
        "final_samplerate_audio": 44100,
        "final_channels_audio": 2,
    }
}

# --- ОБЩИЕ НАСТРОЙКИ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE_DIR, "Downloads", "Recode")
OUTPUT_FOLDER_BASE = os.path.join(BASE_DIR, "Downloads", "Recoded")
CPU_CORES_TO_USE = 16 

# --- настройки нормализации ---
NORMALIZE_FPS = 30

# аппаратный кодировщик: 'h264_nvenc' (для NVIDIA), 'h264_amf' (для AMD), 'h264_qsv' (для Intel Quick Sync), возврат на процессор: 'libx264'
HARDWARE_ENCODER = 'h264_nvenc' 
#===================================================================================================================================================================================================================================

NORMALIZED_FOLDER = os.path.join(os.path.dirname(OUTPUT_FOLDER_BASE), "NORMALIZED")

def check_ffmpeg():
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"): print("ОШИБКА: FFmpeg или FFprobe не найдены в PATH!"); exit()
    return "ffmpeg", "ffprobe"

def get_video_files(folder):
    supported_formats = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm'); files = []
    for f in os.listdir(folder):
        if f.lower().endswith(supported_formats): files.append(os.path.join(folder, f))
    return files

def is_vfr(file_path, ffprobe_executable):
    command = [ffprobe_executable, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'frame=pkt_duration_time', '-of', 'json', '-read_intervals', '%+2', file_path]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout); durations = [float(frame.get('pkt_duration_time', 0)) for frame in data.get('frames', [])]
        if not durations: return False
        return len(set(round(d, 5) for d in durations)) > 1
    except Exception: return True

# ИЗМЕНЕНИЯ В ФУНКЦИИ НОРМАЛИЗАЦИИ
def normalize_video(args):
    """
    Этап 1: Нормализация видео с использованием аппаратного ускорения (GPU).
    """
    file_path, ffmpeg_executable, ffprobe_executable = args
    filename = os.path.basename(file_path)
    output_path = os.path.join(NORMALIZED_FOLDER, filename)
    if os.path.exists(output_path): return output_path

    # Собираем команду
    command = [
        ffmpeg_executable, '-i', file_path,
        '-c:v', HARDWARE_ENCODER, # Используем кодировщик из настроек
        '-preset', 'fast',      # Пресет скорости для GPU
        '-cq', '24',             # Режим качества для GPU (аналог CRF)
        '-r', str(NORMALIZE_FPS),
        '-vsync', 'cfr',
        '-c:a', 'copy',          # Копируем аудио без перекодирования
        '-y', output_path
    ]
    
    # Если используется процессор, меняем параметры
    if HARDWARE_ENCODER == 'libx264':
        command = [
            ffmpeg_executable, '-i', file_path,
            '-c:v', 'libx264',
            '-crf', '20',
            '-preset', 'fast',
            '-r', str(NORMALIZE_FPS),
            '-vsync', 'cfr',
            '-c:a', 'copy',
            '-y', output_path
        ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"\nОшибка при нормализации файла {filename}: {e}")
        print("Возможная причина: убедитесь, что у вас установлены драйверы видеокарты и FFmpeg скомпилирован с поддержкой вашего кодировщика.")
        return None

def convert_for_phone(args):
    file_path, ffmpeg_executable, ffprobe_executable, profile = args
    filename = os.path.splitext(os.path.basename(file_path))[0] + profile['output_extension']
    output_folder_profile = os.path.join(OUTPUT_FOLDER_BASE, profile_name)
    os.makedirs(output_folder_profile, exist_ok=True)
    output_path = os.path.join(output_folder_profile, filename)
    if os.path.exists(output_path): return
    try:
        probe_command = [ffprobe_executable, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
        result = subprocess.run(probe_command, capture_output=True, text=True, check=True)
        target_fps_str = result.stdout.strip()
        if not target_fps_str: raise ValueError("ffprobe не вернул значение FPS")
    except Exception as e:
        print(f"\nНе удалось определить FPS для {os.path.basename(file_path)}: {e}. Используется значение по умолчанию {NORMALIZE_FPS}.")
        target_fps_str = str(NORMALIZE_FPS)
    
    video_filter = f"scale={profile['final_resolution']}:force_original_aspect_ratio=decrease:flags={profile['scaling_algorithm']},pad={profile['final_resolution']}:-1:-1:color=black"
    
    command = [ffmpeg_executable, '-i', file_path]
    command.extend(['-c:v', profile['final_codec_video'], '-b:v', profile['final_bitrate_video'], '-r', target_fps_str])
    if profile['final_codec_video'] == 'libx264':
        if 'h264_profile' in profile: command.extend(['-profile:v', profile['h264_profile']])
        if 'h264_level' in profile: command.extend(['-level:v', profile['h264_level']])
    command.extend(['-vf', video_filter])
    command.extend(['-c:a', profile['final_codec_audio'], '-b:a', profile['final_bitrate_audio'], '-ar', str(profile['final_samplerate_audio']), '-ac', str(profile['final_channels_audio'])])
    command.extend(['-y', output_path])
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"\nОшибка при финальной конвертации файла {filename}: {e}")

def main():
    global profile_name
    if len(sys.argv) > 1 and sys.argv[1] in PROFILES:
        profile_name = sys.argv[1]
    else:
        profile_name = "default"
    
    selected_profile = PROFILES[profile_name]
    
    print(f"========================================================")
    print(f"ЗАПУСК КОНВЕРТАЦИИ С ПРОФИЛЕМ: '{profile_name}'")
    print(f"Описание: {selected_profile['description']}")
    print(f"Ускорение нормализации: {HARDWARE_ENCODER}")
    print(f"========================================================")
    
    ffmpeg_executable, ffprobe_executable = check_ffmpeg()
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    
    normalized_folder = os.path.join(os.path.dirname(OUTPUT_FOLDER_BASE), "NORMALIZED")
    os.makedirs(normalized_folder, exist_ok=True)
    
    all_files = get_video_files(INPUT_FOLDER)
    if not all_files: print(f"В папке '{INPUT_FOLDER}' не найдено видеофайлов."); return

    print(f"\nНайдено видеофайлов: {len(all_files)}. Анализ на VFR...")
    files_to_normalize, files_to_convert_directly = [], []
    for f in tqdm(all_files, desc="Анализ файлов"):
        if is_vfr(f, ffprobe_executable): files_to_normalize.append(f)
        else: files_to_convert_directly.append(f)
    
    print(f"\nТребуют нормализации (VFR): {len(files_to_normalize)} шт.")
    print(f"Готовы к конвертации (CFR): {len(files_to_convert_directly)} шт.")

    cores = multiprocessing.cpu_count() if CPU_CORES_TO_USE == 0 else min(CPU_CORES_TO_USE, multiprocessing.cpu_count())
    source_for_final_conversion = [] + files_to_convert_directly

    if files_to_normalize:
        print(f"\n--- ЭТАП 1: Нормализация VFR видео ---")
        tasks = [(f, ffmpeg_executable, ffprobe_executable) for f in files_to_normalize]
        with multiprocessing.Pool(processes=cores) as pool:
            normalized_files = list(tqdm(pool.imap_unordered(normalize_video, tasks), total=len(tasks), desc="Нормализация"))
        source_for_final_conversion.extend([f for f in normalized_files if f is not None])

    if not source_for_final_conversion: print("\nНет файлов для финальной конвертации."); return

    print("\n--- ЭТАП 2: Финальная конвертация для телефона ---")
    tasks = [(f, ffmpeg_executable, ffprobe_executable, selected_profile) for f in source_for_final_conversion]
    with multiprocessing.Pool(processes=cores) as pool:
        list(tqdm(pool.imap_unordered(convert_for_phone, tasks), total=len(tasks), desc="Конвертация"))
    
    print("\nКонвертация завершена!")
    if files_to_normalize:
        try:
            if input(f"Удалить временную папку '{normalized_folder}'? (y/n): ").lower() == 'y':
                shutil.rmtree(normalized_folder); print("Временные файлы удалены.")
        except Exception as e: print(f"Не удалось удалить временную папку: {e}")

if __name__ == '__main__':
    main()