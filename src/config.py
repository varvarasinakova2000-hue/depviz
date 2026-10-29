"""Разбор и проверка параметров командной строки.

Модуль описывает все настраиваемые пользователем параметры
инструмента визуализации графа зависимостей и проверяет их
корректность до начала работы.
"""

import argparse
import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

MODE_REMOTE = "remote"
MODE_TEST = "test"
MODES = (MODE_REMOTE, MODE_TEST)

LATEST_VERSION = "latest"
NO_VERSION = "-"
DEFAULT_OUTPUT = "graph.svg"
DEFAULT_MAX_DEPTH = 3
MIN_DEPTH = 1
MAX_DEPTH_LIMIT = 100

IMAGE_EXTENSION = ".svg"
URL_SCHEMES = ("http", "https")
FORBIDDEN_FILE_CHARS = set('<>:"/\\|?*')

PACKAGE_NAME_RE = re.compile(
    r"^([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9])$"
)
TEST_PACKAGE_NAME_RE = re.compile(r"^[A-Z]+$")
VERSION_RE = re.compile(
    r"^\d+(\.\d+)*((a|b|rc)\d+)?(\.post\d+)?(\.dev\d+)?$"
)


class ConfigError(Exception):
    """Ошибка в значении параметра командной строки."""


@dataclass(frozen=True)
class Config:
    """Проверенные параметры запуска приложения."""

    package: str
    repository: str
    mode: str
    version: str
    output: str
    max_depth: int

    def as_pairs(self):
        """Вернуть параметры списком пар (ключ, значение)."""
        return [
            ("package", self.package),
            ("repository", self.repository),
            ("mode", self.mode),
            ("version", self.version),
            ("output", self.output),
            ("max_depth", self.max_depth),
        ]


def build_parser():
    """Создать парсер параметров командной строки."""
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Визуализатор графа зависимостей пакетов Python.",
    )
    parser.add_argument(
        "-p", "--package", required=True,
        help="имя анализируемого пакета",
    )
    parser.add_argument(
        "-r", "--repo", required=True,
        help="URL репозитория или путь к файлу тестового репозитория",
    )
    parser.add_argument(
        "-m", "--mode", default=MODE_REMOTE,
        help="режим работы: remote (по URL) или test (тестовый файл); "
             "по умолчанию remote",
    )
    parser.add_argument(
        "-v", "--version",
        help="версия пакета, например 2.31.0, или latest (последняя); "
             "обязательна в режиме remote",
    )
    parser.add_argument(
        "-o", "--output", default=DEFAULT_OUTPUT,
        help="имя файла с изображением графа (.svg); "
             "по умолчанию graph.svg",
    )
    parser.add_argument(
        "-d", "--max-depth", default=str(DEFAULT_MAX_DEPTH),
        help="максимальная глубина анализа зависимостей; по умолчанию 3",
    )
    return parser


def validate_mode(mode):
    """Проверить режим работы с репозиторием."""
    if mode not in MODES:
        raise ConfigError(
            f"неизвестный режим '{mode}', "
            f"допустимые значения: {', '.join(MODES)}"
        )
    return mode


def validate_package(name, mode):
    """Проверить имя пакета с учётом режима работы."""
    if not name.strip():
        raise ConfigError("имя пакета не может быть пустым")
    if mode == MODE_TEST:
        if not TEST_PACKAGE_NAME_RE.match(name):
            raise ConfigError(
                f"в тестовом режиме имя пакета '{name}' должно состоять "
                "из больших латинских букв"
            )
    elif not PACKAGE_NAME_RE.match(name):
        raise ConfigError(
            f"недопустимое имя пакета '{name}': разрешены латинские "
            "буквы, цифры и символы '.', '_', '-' внутри имени"
        )
    return name


def validate_url(url):
    """Проверить URL-адрес репозитория пакетов."""
    if not url.strip():
        raise ConfigError("URL репозитория не может быть пустым")
    parsed = urlparse(url)
    if parsed.scheme not in URL_SCHEMES or not parsed.netloc:
        raise ConfigError(
            f"некорректный URL репозитория '{url}': ожидается адрес "
            "вида https://pypi.org/pypi (для файла укажите --mode test)"
        )
    if any(char.isspace() for char in url):
        raise ConfigError(f"URL репозитория '{url}' содержит пробелы")
    return url


def validate_test_repo(path):
    """Проверить путь к файлу тестового репозитория."""
    if not path.strip():
        raise ConfigError("путь к тестовому репозиторию не может быть пустым")
    if not os.path.exists(path):
        raise ConfigError(f"файл тестового репозитория '{path}' не найден")
    if not os.path.isfile(path):
        raise ConfigError(f"'{path}' не является файлом")
    try:
        with open(path, encoding="utf-8") as repo_file:
            repo_file.read()
    except UnicodeDecodeError:
        raise ConfigError(
            f"файл тестового репозитория '{path}' не в кодировке UTF-8"
        ) from None
    except OSError as error:
        raise ConfigError(
            f"не удалось прочитать файл '{path}': {error.strerror}"
        ) from None
    return path


def validate_repository(repository, mode):
    """Проверить источник данных о пакетах с учётом режима."""
    if mode == MODE_TEST:
        return validate_test_repo(repository)
    return validate_url(repository)


def validate_version(version, mode):
    """Проверить версию пакета (формат PEP 440 или latest)."""
    if version is None:
        if mode == MODE_TEST:
            return NO_VERSION
        raise ConfigError(
            "не указана версия пакета: задайте --version, "
            "например --version 2.31.0 или --version latest"
        )
    if version == LATEST_VERSION:
        return version
    if not VERSION_RE.match(version):
        raise ConfigError(
            f"некорректная версия пакета '{version}': ожидается "
            "формат вроде 1.0, 2.31.0, 3.0.0rc1 или latest"
        )
    return version


def validate_output(output):
    """Проверить имя файла для изображения графа."""
    if not output.strip():
        raise ConfigError("имя выходного файла не может быть пустым")
    if os.path.isdir(output):
        raise ConfigError(f"'{output}' является каталогом")
    directory, file_name = os.path.split(output)
    if not file_name:
        raise ConfigError(f"'{output}' не содержит имени файла")
    if FORBIDDEN_FILE_CHARS & set(file_name):
        raise ConfigError(
            f"имя файла '{file_name}' содержит недопустимые символы"
        )
    if not file_name.lower().endswith(IMAGE_EXTENSION):
        raise ConfigError(
            f"файл изображения '{file_name}' должен иметь "
            f"расширение {IMAGE_EXTENSION}"
        )
    if directory and not os.path.isdir(directory):
        raise ConfigError(f"каталог '{directory}' не существует")
    return output


def validate_max_depth(value):
    """Проверить и преобразовать максимальную глубину анализа."""
    try:
        depth = int(value)
    except ValueError:
        raise ConfigError(
            f"глубина анализа должна быть целым числом, получено '{value}'"
        ) from None
    if depth < MIN_DEPTH or depth > MAX_DEPTH_LIMIT:
        raise ConfigError(
            f"глубина анализа должна быть от {MIN_DEPTH} "
            f"до {MAX_DEPTH_LIMIT}, получено {depth}"
        )
    return depth


def make_config(args):
    """Проверить разобранные аргументы и собрать конфигурацию."""
    mode = validate_mode(args.mode)
    return Config(
        package=validate_package(args.package, mode),
        repository=validate_repository(args.repo, mode),
        mode=mode,
        version=validate_version(args.version, mode),
        output=validate_output(args.output),
        max_depth=validate_max_depth(args.max_depth),
    )
