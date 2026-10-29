"""Тестовый репозиторий: граф пакетов, описанный в текстовом файле.

Формат файла — по одной строке на пакет::

    A: B C
    B: D
    D:

Слева от двоеточия — имя пакета, справа — его прямые зависимости
через пробел. Имена пакетов — большие латинские буквы. Пустые строки
и текст после символа ``#`` (комментарии) игнорируются. Пакет,
который упомянут только как зависимость, считается пакетом без
зависимостей.
"""

import re

from errors import RepositoryError

PACKAGE_RE = re.compile(r"^[A-Z]+$")
COMMENT = "#"


def check_name(name, number):
    """Проверить имя пакета в строке с заданным номером."""
    if not PACKAGE_RE.match(name):
        raise RepositoryError(
            f"строка {number}: недопустимое имя пакета '{name}', "
            "ожидаются большие латинские буквы"
        )
    return name


def parse_line(line, number):
    """Разобрать строку вида 'ПАКЕТ: ЗАВИСИМОСТИ'."""
    name, separator, rest = line.partition(":")
    if not separator:
        raise RepositoryError(
            f"строка {number}: ожидается формат 'ПАКЕТ: ЗАВИСИМОСТИ', "
            f"получено '{line}'"
        )
    package = check_name(name.strip(), number)
    dependencies = [check_name(dep, number) for dep in rest.split()]
    if len(set(dependencies)) != len(dependencies):
        raise RepositoryError(
            f"строка {number}: зависимость пакета {package} "
            "указана несколько раз"
        )
    return package, dependencies


def parse_local_repository(text):
    """Разобрать описание тестового репозитория в словарь пакетов."""
    packages = {}
    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split(COMMENT, 1)[0].strip()
        if not line:
            continue
        package, dependencies = parse_line(line, number)
        if package in packages:
            raise RepositoryError(
                f"строка {number}: пакет {package} описан повторно"
            )
        packages[package] = dependencies
    return packages


def load_local_repository(path):
    """Прочитать и разобрать файл тестового репозитория."""
    try:
        with open(path, encoding="utf-8") as repo_file:
            text = repo_file.read()
    except (OSError, UnicodeDecodeError) as error:
        raise RepositoryError(
            f"не удалось прочитать тестовый репозиторий '{path}': {error}"
        ) from None
    return parse_local_repository(text)
