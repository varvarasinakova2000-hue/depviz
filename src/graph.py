"""Построение графа зависимостей и поиск циклов.

Оба алгоритма — обход в глубину (DFS) без рекурсии: вместо стека
вызовов используется явный стек (список Python).
"""

from dataclasses import dataclass

VISITING = "visiting"
DONE = "done"
END = object()


@dataclass(frozen=True)
class DependencyGraph:
    """Граф зависимостей пакета.

    ``edges`` — зависимости каждого проанализированного пакета.
    ``depths`` — наименьшая глубина каждого найденного пакета
    (корень имеет глубину 0); порядок ключей — порядок обнаружения.
    Пакеты, которых нет в ``edges``, находятся на максимальной глубине,
    и их зависимости не анализировались.
    """

    root: str
    edges: dict
    depths: dict

    @property
    def nodes(self):
        """Вернуть пакеты графа в порядке их обнаружения."""
        return list(self.depths)

    def is_expanded(self, node):
        """Проверить, анализировались ли зависимости пакета."""
        return node in self.edges

    def edge_count(self):
        """Вернуть число рёбер (зависимостей) в графе."""
        return sum(len(deps) for deps in self.edges.values())


def build_graph(root, get_dependencies, max_depth):
    """Построить граф зависимостей обходом в глубину без рекурсии.

    ``get_dependencies(package)`` возвращает список прямых зависимостей
    пакета и вызывается для каждого пакета не более одного раза.
    Зависимости пакета анализируются, только если его глубина меньше
    ``max_depth``. Уже обработанный пакет повторно не раскрывается,
    поэтому циклические зависимости не приводят к зацикливанию;
    исключение — пакет, найденный позже по более короткому пути:
    он раскрывается заново с меньшей глубиной.
    """
    edges = {}
    depths = {}
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        if node in depths and depths[node] <= depth:
            continue
        depths[node] = depth
        if depth >= max_depth:
            continue
        if node not in edges:
            edges[node] = list(get_dependencies(node))
        for dependency in reversed(edges[node]):
            stack.append((dependency, depth + 1))
    return DependencyGraph(root=root, edges=edges, depths=depths)


def find_cycles(graph):
    """Найти циклические зависимости обходом в глубину без рекурсии.

    Цикл фиксируется, когда обход встречает пакет, который находится
    на текущем пути от корня. Каждый цикл возвращается списком
    пакетов, где первый и последний элементы совпадают.
    """
    cycles = []
    state = {graph.root: VISITING}
    path = [graph.root]
    stack = [iter(graph.edges.get(graph.root, ()))]
    while stack:
        dependency = next(stack[-1], END)
        if dependency is END:
            state[path.pop()] = DONE
            stack.pop()
        elif state.get(dependency) == VISITING:
            start = path.index(dependency)
            cycles.append(path[start:] + [dependency])
        elif dependency not in state:
            state[dependency] = VISITING
            path.append(dependency)
            stack.append(iter(graph.edges.get(dependency, ())))
    return cycles
