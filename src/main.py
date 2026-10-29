"""Точка входа инструмента визуализации графа зависимостей."""

import sys

from config import MODE_REMOTE, ConfigError, build_parser, make_config
from errors import RepositoryError
from graph import build_graph, find_cycles
from sources import make_source

EXIT_SUCCESS = 0
EXIT_REPOSITORY_ERROR = 1
EXIT_CONFIG_ERROR = 2


def build_dependency_graph(config):
    """Построить граф зависимостей пакета по настройкам запуска."""
    root, get_dependencies = make_source(config)
    return build_graph(root, get_dependencies, config.max_depth)


def format_node(graph, node):
    """Вернуть строку с пакетом и его прямыми зависимостями."""
    if not graph.is_expanded(node):
        return f"{node} -> ... (достигнута максимальная глубина)"
    dependencies = graph.edges[node]
    if not dependencies:
        return f"{node} -> (нет зависимостей)"
    return f"{node} -> {', '.join(dependencies)}"


def print_cycles(cycles):
    """Вывести найденные циклические зависимости."""
    if not cycles:
        print("Циклические зависимости: нет")
        return
    print("Циклические зависимости:")
    for cycle in cycles:
        print(f"  {' -> '.join(cycle)}")


def print_graph(graph, config):
    """Вывести граф зависимостей, сводку и найденные циклы."""
    title = config.package
    if config.mode == MODE_REMOTE:
        title += f" {config.version}"
    print(f"Граф зависимостей пакета {title} "
          f"(максимальная глубина {config.max_depth}):")
    for node in graph.nodes:
        print(f"  {format_node(graph, node)}")
    print(f"Пакетов: {len(graph.nodes)}, "
          f"зависимостей: {graph.edge_count()}")
    print_cycles(find_cycles(graph))


def main(argv=None):
    """Разобрать параметры, построить и вывести граф зависимостей."""
    args = build_parser().parse_args(argv)
    try:
        config = make_config(args)
        graph = build_dependency_graph(config)
    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    except RepositoryError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_REPOSITORY_ERROR
    print_graph(graph, config)
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
