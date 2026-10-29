"""Точка входа инструмента визуализации графа зависимостей."""

import sys

from config import ConfigError, build_parser, make_config

EXIT_SUCCESS = 0
EXIT_CONFIG_ERROR = 2


def print_config(config):
    """Вывести параметры запуска в формате ключ=значение."""
    for key, value in config.as_pairs():
        print(f"{key}={value}")


def main(argv=None):
    """Разобрать параметры, проверить их и вывести на экран."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = make_config(args)
    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    print_config(config)
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
