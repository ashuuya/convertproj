import os
import subprocess
import shutil

# ================================================================
# НАСТРОЙКИ
# ================================================================
# Папка, куда будут скачиваться видео
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Downloads", "Recode")

# Имя файла, в котором будут храниться ссылки для скачивания
LINKS_FILE = "links.txt"

# ================================================================
# КОД ПРОГРАММЫ
# ================================================================

def check_ytdlp():
    """Проверяет, доступен ли yt-dlp."""
    ytdlp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yt-dlp.exe")
    if not os.path.exists(ytdlp_path):
        # Если локально нет, ищем в PATH
        if not shutil.which("yt-dlp"):
            print("ОШИБКА: yt-dlp.exe не найден!")
            print("Пожалуйста, скачайте yt-dlp.exe и положите его в ту же папку, что и этот скрипт, или добавьте в PATH.")
            input("Нажмите Enter, чтобы выйти...")
            exit()
        return "yt-dlp"
    return ytdlp_path

def get_quality_args():
    """Спрашивает пользователя о качестве и возвращает аргументы формата."""
    print("\n=== ВЫБОР КАЧЕСТВА ===")
    print("1. 360p  (Низкое, экономия места)")
    print("2. 720p  (HD, оптимально)")
    print("3. 1080p (FullHD, стандарт)")
    print("4. Максимально доступное (2K/4K)")
    
    choice = input("Введите номер (1-4) и нажмите Enter [по умолчанию 3]: ").strip()
    
    # Базовая часть строки формата: предпочитаем mp4 видео и m4a аудио
    base_video = "bestvideo[ext=mp4]"
    base_audio = "bestaudio[ext=m4a]"
    fallback = "best[ext=mp4]/best"

    if choice == "1":
        print(">> Выбрано: 360p")
        height_limit = "[height<=360]"
    elif choice == "2":
        print(">> Выбрано: 720p")
        height_limit = "[height<=720]"
    elif choice == "4":
        print(">> Выбрано: Максимальное качество")
        # Для макс качества просто берем bestvideo+bestaudio без лимита высоты
        return f"{base_video}+{base_audio}/{fallback}"
    else:
        print(">> Выбрано: 1080p (или по умолчанию)")
        height_limit = "[height<=1080]"

    # Собираем строку для yt-dlp с ограничением высоты
    # Пример: bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]
    format_str = f"{base_video}{height_limit}+{base_audio}/{fallback}"
    return format_str

def main():
    """Главная функция для скачивания видео."""
    ytdlp_executable = check_ytdlp()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    links_file_path = os.path.join(script_dir, LINKS_FILE)

    # Проверка файла со ссылками
    if not os.path.exists(links_file_path):
        print(f"Файл {LINKS_FILE} не найден. Создаю его для вас.")
        with open(links_file_path, 'w') as f:
            f.write("# Вставьте сюда ссылки на видео с YouTube, каждая на новой строке\n")
        print(f"Откройте файл {LINKS_FILE}, вставьте ссылки и запустите скрипт снова.")
        input("Нажмите Enter, чтобы выйти...")
        return

    with open(links_file_path, 'r') as f:
        links = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    if not links:
        print(f"Файл {LINKS_FILE} пуст. Нечего скачивать.")
        input("Нажмите Enter, чтобы выйти...")
        return

    print(f"Найдено ссылок для скачивания: {len(links)}")
    
    # Спрашиваем качество ОДИН РАЗ для всего списка
    format_arg = get_quality_args()

    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    
    for i, link in enumerate(links, 1):
        print(f"\n--- [{i}/{len(links)}] Скачиваю видео: {link} ---")
        
        command = [
            ytdlp_executable,
            '-f', format_arg,               # Используем выбранное качество
            '--merge-output-format', 'mp4', # Собираем в MP4
            '--no-playlist',                # Если ссылка на плейлист, качаем только видео
            '--ignore-errors',              # Не падать, если видео удалено
            '-o', os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            link
        ]
        
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError:
            print(f"!!! ОШИБКА при скачивании: {link}")
            continue
    
    print(f"\nГотово! Все видео сохранены в: {DOWNLOAD_FOLDER}")
    input("Нажмите Enter, чтобы закрыть...")

if __name__ == "__main__":
    main()