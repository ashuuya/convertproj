# QWEN.md — ConvertProj GUI

## Обзор проекта

**ConvertProj** — десктопное приложение (PyQt6) для скачивания видео с YouTube и конвертации под старые кнопочные телефоны. Frosted Glass UI, две вкладки (скачивание / конвертация), редактор профилей, тёмная тема, локализация (RU/EN), drag & drop.

## Архитектура

### Ключевые файлы

| Файл | Назначение |
|---|---|
| `main.py` | Точка входа |
| `convertproj.py` | Библиотечный модуль: нормализация VFR→CFR + конвертация под профиль |
| `ytdload.py` | Библиотечный модуль: скачивание с YouTube через yt-dlp |
| `gui/app.py` | Загрузка приложения, определение путей, установка бинарников, перевод |
| `gui/main_window.py` | Главное окно (QMainWindow + QTabWidget), переключение темы/языка |
| `gui/download_tab.py` | Вкладка скачивания: список ссылок, выбор качества, прогресс |
| `gui/convert_tab.py` | Вкладка конвертации: очередь файлов, редактор профилей, drag & drop |
| `gui/worker.py` | QThread-воркеры для скачивания и конвертации |
| `gui/profile_manager.py` | JSON-based CRUD для профилей конвертации |
| `gui/styles.py` | QSS-таблицы для light/dark frosted glass темы |
| `gui/translations.py` | Кастомный QTranslator на JSON-файлах |
| `gui/about_dialog.py` | Инфо + обновление ffmpeg/yt-dlp |

### Профили конвертации

Хранятся в `profiles_custom.json` (создаётся при первом запуске из `get_default_profiles()`).
Поле `builtin: true/false` отличает встроенные от кастомных.
Сброс до заводских — удаляет кастомные и восстанавливает встроенные.

### Portable-пути

```python
def get_app_dir():
    if frozen: return Path(sys.executable).parent  # рядом с .exe
    else: return Path(__file__).parent.parent       # корень проекта

def get_bin_dir():
    if frozen: return app_dir / "_internal"         # внутри --onedir папки
    else: return app_dir / "bin"                    # dev-режим
```

Все данные (config, profiles, Downloads, логи) — внутри `get_app_dir()`. Никаких `%APPDATA%`.

### Локализация

- Исходный язык: русский (все `self.tr()` строки)
- Переводы: `locales/en.json` — плоский словарь `{ "русская строка": "english string" }`
- Механизм: `JsonTranslator(QTranslator)` подменяет `translate()` на lookup в JSON
- Переключение языка через кнопку в хедере **без перезапуска** — `install_translation()` + `retranslate_ui()` на всех виджетах
- `gui/translations.py` предоставляет функцию `tr()` для перевода отдельных строк

### Анимации

- `FadeStackedWidget` в `main_window.py` — QStackedWidget с fade-анимацией (200ms, OutCubic) при переключении вкладок

### Поля конвертации (FilterComboBox)

- Все поля на вкладке конвертации — нередактируемые QComboBox (только выбор из списка)
- Колёсико мыши отключено для избежания случайного переключения
- Клик по полю открывает выпадающий список

### Сборка .exe

```bash
cd build && build.bat
```

Использует PyInstaller `--onedir --noconsole`. Копирует ffmpeg/yt-dlp из `bin/` в `_internal/` внутри папки с .exe.

## Важные нюансы

- **FFmpeg/yt-dlp не встроены в репозиторий** — пользователь кладёт их в `bin/` сам. `ensure_binaries()` копирует их оттуда или с PATH.
- **requirements.txt** — только Python-зависимости (PyQt6, tqdm, darkdetect, ffmpeg-downloader)
- **multiprocessing.Pool** используется для параллельной нормализации/конвертации — блокирует поток. Работает внутри QThread, UI не зависает.
- **Тёмная тема** определяется через `darkdetect` при старте, если в config нет сохранённой темы.
- **Никаких системных следов** — всё портабельно. Даже логи не пишутся (пока).

## Поток данных

```
links.txt / вставка ссылок
       ↓
[ytdload.download_videos()]  ← DownloadWorker (QThread)
       ↓
Downloads/Recode/*.mp4
       ↓  (авто-добавление в очередь конвертации)
[convertproj.batch_process()]  ← ConvertWorker (QThread)
       ↓
  ┌──────────────┴──────────────┐
  ↓ VFR                         ↓ CFR
NORMALIZED/               (пропуск)
  └──────────────┬──────────────┘
                 ↓
Downloads/Recoded/<profile>/*.3gp
```

## TODO / Известные ограничения

- Логирование в файл пока не реализовано
- Нет авто-проверки обновлений при запуске (только вручную в About)
- ffmpeg-downloader интеграция требует доработки (сейчас открывает процесс в фоне)
- Нет прогресс-бара для обновления ffmpeg (используется indeterminate)

## Самопроверка перед выдачей результата

Перед выдачей результата пользователю:
1. **Читать все вовлечённые файлы** — не гадать, не менять вслепую.
2. **Вычислять sizeHint() / minimumSize()** — при layout-проблемах прикинуть, какой sizeHint даёт каждый дочерний виджет и layout в целом.
3. **Понимать цепочку Qt/WM** — порядок вызовов resize → show → showEvent, что и когда переопределяет размер.
4. **Проверять импорты** — `python -c "from module import Class; print('OK')"`.
5. **Проверять запуск без ошибок** — прогнать приложение (или сборку), убедиться что нет traceback.
6. Только потом писать пользователю «проверяй».
