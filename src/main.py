"""Точка входа инструмента визуализации графа зависимостей."""

import sys

from config import MODE_TEST, ConfigError, build_parser, make_config
from pypi import RepositoryError, get_package_info

EXIT_SUCCESS = 0
EXIT_REPOSITORY_ERROR = 1
EXIT_CONFIG_ERROR = 2


def load_package(config):
    """Получить сведения о пакете из источника, заданного в настройках."""
    if config.mode == MODE_TEST:
        raise RepositoryError(
            "режим test пока не поддерживается: прямые зависимости "
            "извлекаются только из репозитория по URL (--mode remote)"
        )
    return get_package_info(
        config.repository, config.package, config.version
    )


def print_requirements(requirements):
    """Вывести список зависимостей, по одной на строке."""
    if not requirements:
        print("  (нет)")
    for requirement in requirements:
        print(f"  {requirement}")


def print_dependencies(info):
    """Вывести все прямые зависимости пакета."""
    required = [req for req in info.requirements if not req.is_optional]
    optional = [req for req in info.requirements if req.is_optional]
    print(f"Прямые зависимости пакета {info.name} {info.version}:")
    print_requirements(required)
    if optional:
        print("Необязательные зависимости (extras):")
        print_requirements(optional)


def main(argv=None):
    """Разобрать параметры и вывести прямые зависимости пакета."""
    args = build_parser().parse_args(argv)
    try:
        config = make_config(args)
        info = load_package(config)
    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    except RepositoryError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_REPOSITORY_ERROR
    print_dependencies(info)
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
