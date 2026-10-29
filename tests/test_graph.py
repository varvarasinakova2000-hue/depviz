"""Тесты построения графа зависимостей и поиска циклов."""

import ast
import inspect
import unittest

import graph as graph_module
from graph import build_graph, find_cycles


def getter(packages):
    """Создать функцию зависимостей по словарю и счётчик её вызовов."""
    calls = []

    def get_dependencies(package):
        """Вернуть зависимости пакета из словаря."""
        calls.append(package)
        return packages.get(package, [])

    return get_dependencies, calls


class BuildGraphTest(unittest.TestCase):
    """Построение графа обходом в глубину."""

    def test_diamond(self):
        """Общая зависимость входит в граф один раз."""
        deps, calls = getter({"A": ["B", "C"], "B": ["D"], "C": ["D"]})
        graph = build_graph("A", deps, 5)
        self.assertEqual(graph.nodes, ["A", "B", "D", "C"])
        self.assertEqual(graph.edges["C"], ["D"])
        self.assertEqual(graph.edge_count(), 4)
        self.assertEqual(sorted(calls), ["A", "B", "C", "D"])

    def test_depth_first_order(self):
        """Пакеты обходятся в глубину: сначала вся ветка B."""
        deps, _ = getter({"A": ["B", "E"], "B": ["C"], "C": ["D"]})
        graph = build_graph("A", deps, 5)
        self.assertEqual(graph.nodes, ["A", "B", "C", "D", "E"])

    def test_max_depth(self):
        """Пакеты на максимальной глубине не раскрываются."""
        chain = {"A": ["B"], "B": ["C"], "C": ["D"], "D": ["E"]}
        deps, calls = getter(chain)
        graph = build_graph("A", deps, 2)
        self.assertEqual(graph.nodes, ["A", "B", "C"])
        self.assertFalse(graph.is_expanded("C"))
        self.assertEqual(graph.depths["C"], 2)
        self.assertEqual(calls, ["A", "B"])

    def test_depth_one(self):
        """При глубине 1 анализируются только прямые зависимости."""
        deps, _ = getter({"A": ["B", "C"], "B": ["D"]})
        graph = build_graph("A", deps, 1)
        self.assertEqual(graph.nodes, ["A", "B", "C"])
        self.assertEqual(list(graph.edges), ["A"])

    def test_shorter_path_expands_node(self):
        """Пакет, найденный позже по короткому пути, раскрывается."""
        deps, calls = getter({"A": ["B", "C"], "B": ["C"], "C": ["D"]})
        graph = build_graph("A", deps, 2)
        self.assertEqual(graph.depths["C"], 1)
        self.assertEqual(graph.edges["C"], ["D"])
        self.assertEqual(calls.count("C"), 1)

    def test_cycle_terminates(self):
        """Циклическая зависимость не приводит к зацикливанию."""
        deps, calls = getter({"A": ["B"], "B": ["C"], "C": ["A"]})
        graph = build_graph("A", deps, 100)
        self.assertEqual(graph.nodes, ["A", "B", "C"])
        self.assertEqual(graph.edges["C"], ["A"])
        self.assertEqual(calls, ["A", "B", "C"])

    def test_self_dependency(self):
        """Пакет, зависящий от самого себя."""
        deps, _ = getter({"A": ["A", "B"]})
        graph = build_graph("A", deps, 3)
        self.assertEqual(graph.nodes, ["A", "B"])

    def test_long_chain(self):
        """Длинная цепочка обрабатывается без переполнения стека."""
        names = [f"P{index}" for index in range(5000)]
        chain = dict(zip(names, ([name] for name in names[1:])))
        deps, _ = getter(chain)
        graph = build_graph("P0", deps, 10000)
        self.assertEqual(len(graph.nodes), len(names))

    def test_no_recursion(self):
        """Функции обхода не вызывают сами себя."""
        for function in (build_graph, find_cycles):
            tree = ast.parse(inspect.getsource(function))
            called = {node.func.id for node in ast.walk(tree)
                      if isinstance(node, ast.Call)
                      and isinstance(node.func, ast.Name)}
            self.assertNotIn(function.__name__, called)
        self.assertIsNotNone(graph_module.END)


class FindCyclesTest(unittest.TestCase):
    """Поиск циклических зависимостей."""

    def cycles(self, packages, max_depth=100):
        """Построить граф из словаря и найти в нём циклы."""
        deps, _ = getter(packages)
        return find_cycles(build_graph("A", deps, max_depth))

    def test_no_cycles(self):
        """В графе без циклов ничего не находится."""
        self.assertEqual(self.cycles({"A": ["B", "C"], "B": ["C"]}), [])

    def test_simple_cycle(self):
        """Цикл из трёх пакетов."""
        found = self.cycles({"A": ["B"], "B": ["C"], "C": ["A", "D"]})
        self.assertEqual(found, [["A", "B", "C", "A"]])

    def test_self_cycle(self):
        """Зависимость пакета от самого себя."""
        self.assertEqual(self.cycles({"A": ["A"]}), [["A", "A"]])

    def test_several_cycles(self):
        """Несколько независимых циклов."""
        found = self.cycles({"A": ["B", "C"], "B": ["A"], "C": ["C"]})
        self.assertEqual(found, [["A", "B", "A"], ["C", "C"]])

    def test_cycle_beyond_depth(self):
        """Цикл за пределами максимальной глубины не учитывается."""
        found = self.cycles({"A": ["B"], "B": ["C"], "C": ["A"]}, 2)
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
