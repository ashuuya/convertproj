"""
translations.py — Лёгкая JSON-локализация для PyQt6.

Предоставляет JsonTranslator — подкласс QTranslator, так что все
существующие вызовы self.tr() работают без изменений.
"""

import json
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QTranslator


class JsonTranslator(QTranslator):
    """QTranslator, загружающий переводы из JSON-словаря.

    Формат JSON: { "исходный_текст": "переведённый_текст", ... }
    Если строка не найдена, возвращается исходный текст.
    """

    def __init__(self, json_path: Optional[Path] = None):
        super().__init__()
        self._strings: dict[str, str] = {}
        if json_path and json_path.exists():
            self.load(str(json_path))

    def load(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self._strings = json.load(f)
            return True
        except (OSError, json.JSONDecodeError):
            return False

    def translate(self, context: str, source_text: str,
                  disambiguation: Optional[str] = None,
                  n: int = -1) -> str:
        return self._strings.get(source_text, source_text)


_current_translator: Optional[JsonTranslator] = None


def install_translation(app, app_dir: Path, language: str) -> None:
    """Установить JsonTranslator для указанного кода языка.

    Ищет файл locales/<language>.json внутри app_dir.
    """
    global _current_translator
    # Удаляем предыдущий переводчик
    if _current_translator is not None:
        app.removeTranslator(_current_translator)
        _current_translator = None

    if language == 'ru':
        return  # Русский — исходный язык, перевод не нужен

    json_path = app_dir / 'locales' / f'{language}.json'
    if not json_path.exists():
        return

    _current_translator = JsonTranslator(json_path)
    app.installTranslator(_current_translator)


def get_translator() -> Optional[JsonTranslator]:
    """Вернуть текущий установленный переводчик (если есть)."""
    return _current_translator


def tr(source_text: str) -> str:
    """Перевести строку через текущий переводчик или вернуть как есть."""
    global _current_translator
    if _current_translator is not None:
        return _current_translator.translate("", source_text)
    return source_text
