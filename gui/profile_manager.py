"""
profile_manager.py — Загрузка / сохранение / сброс профилей конвертации из JSON.
"""

import json
import os
import copy
from pathlib import Path
from typing import Optional

from convertproj import get_default_profiles


def profiles_path(app_dir: Path) -> Path:
    return app_dir / "profiles_custom.json"


def load_profiles(app_dir: Path) -> dict:
    """Загрузить профили из JSON. Если файла нет — создать из заводских."""
    path = profiles_path(app_dir)
    if not path.exists():
        return _init_defaults(path)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Проверяем, что все ключи по умолчанию присутствуют (на случай добавления новых полей)
        defaults = get_default_profiles()
        changed = False
        for key, profile in defaults.items():
            if key not in data:
                data[key] = profile
                changed = True
        if changed:
            _save(path, data)
        return data
    except (json.JSONDecodeError, OSError):
        return _init_defaults(path)


def _init_defaults(path: Path) -> dict:
    """Записать заводские профили в JSON и вернуть их."""
    profiles = copy.deepcopy(get_default_profiles())
    _save(path, profiles)
    return profiles


def _save(path: Path, profiles: dict) -> None:
    """Записать словарь профилей в JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)


def save_profiles(app_dir: Path, profiles: dict) -> None:
    """Сохранить профили в JSON."""
    _save(profiles_path(app_dir), profiles)


def reset_to_factory(app_dir: Path) -> dict:
    """Перезаписать JSON заводскими профилями. Вернуть свежий словарь."""
    return _init_defaults(profiles_path(app_dir))


def add_profile(app_dir: Path, profiles: dict, name: str, settings: dict) -> dict:
    """Добавить или перезаписать кастомный профиль. Вернуть обновлённый словарь."""
    settings['builtin'] = False
    profiles[name] = settings
    save_profiles(app_dir, profiles)
    return profiles


def delete_profile(app_dir: Path, profiles: dict, name: str) -> dict:
    """Удалить кастомный профиль. Встроенные профили пропускаются."""
    if name in profiles and not profiles[name].get('builtin', False):
        del profiles[name]
        save_profiles(app_dir, profiles)
    return profiles
