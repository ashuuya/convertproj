#!/usr/bin/env python3
"""
ConvertProj GUI — Точка входа.

Запуск:     python main.py
Сборка:     cd build && build.bat
"""

import sys
import os

# Добавляем корень проекта в sys.path для корректных импортов в dev и frozen режимах
if getattr(sys, 'frozen', False):
    # PyInstaller устанавливает sys.executable на путь к .exe
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import run

if __name__ == "__main__":
    run()
