"""Модульные тесты depviz.

При импорте пакета tests каталог src добавляется в путь поиска
модулей, чтобы тесты могли импортировать модули приложения.
"""

import os
import sys

SRC_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "src")
)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
