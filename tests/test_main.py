"""Тесты вывода графа зависимостей при запуске приложения."""

import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock
from urllib.error import HTTPError

import pypi
from main import EXIT_REPOSITORY_ERROR, EXIT_SUCCESS, main

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPOS_DIR = os.path.join(TESTS_DIR, "repos")
PYPI_URL = "https://pypi.org/pypi"
PYPI_DATA = {
    "flask": ["Werkzeug>=3.0", "Jinja2>=3.1", "asgiref; extra == 'async'"],
    "werkzeug": ["MarkupSafe>=2.1"],
    "jinja2": ["MarkupSafe>=2.0"],
    "markupsafe": None,
}


def run(argv):
    """Запустить приложение и вернуть код, stdout и stderr."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue().splitlines(), err.getvalue()


def fake_urlopen(request, timeout):
    """Подменить ответ PyPI данными из словаря PYPI_DATA."""
    package = request.full_url[len(PYPI_URL):].split("/")[1]
    if package not in PYPI_DATA:
        raise HTTPError(request.full_url, 404, "not found", {}, None)
    body = {"info": {"name": package, "version": "1.0",
                     "requires_dist": PYPI_DATA[package]}}
    response = mock.MagicMock()
    response.read.return_value = json.dumps(body).encode()
    response.__enter__.return_value = response
    assert timeout
    return response


class TestModeTest(unittest.TestCase):
    """Режим тестового репозитория."""

    def test_graph(self):
        """Граф с общей зависимостью выводится полностью."""
        code, out, _ = run(["-p", "A", "-m", "test", "-r",
                            os.path.join(REPOS_DIR, "simple.txt")])
        self.assertEqual(code, EXIT_SUCCESS)
        self.assertEqual(out, [
            "Граф зависимостей пакета A (максимальная глубина 3):",
            "  A -> B, C",
            "  B -> D",
            "  D -> (нет зависимостей)",
            "  C -> D",
            "Пакетов: 4, зависимостей: 4",
            "Циклические зависимости: нет",
        ])

    def test_depth_and_cycle(self):
        """Ограничение глубины и вывод найденного цикла."""
        repo = os.path.join(REPOS_DIR, "cycle.txt")
        _, out, _ = run(["-p", "A", "-r", repo, "-m", "test", "-d", "2"])
        self.assertIn("  C -> ... (достигнута максимальная глубина)", out)
        self.assertEqual(out[-1], "Циклические зависимости: нет")
        _, out, _ = run(["-p", "A", "-r", repo, "-m", "test", "-d", "3"])
        self.assertEqual(out[-2:], [
            "Циклические зависимости:", "  A -> B -> C -> A",
        ])

    def test_errors(self):
        """Ошибка в файле и неизвестный корневой пакет."""
        for name, package in (("broken.txt", "A"), ("simple.txt", "Z")):
            with self.subTest(name=name):
                code, out, err = run(["-p", package, "-m", "test", "-r",
                                      os.path.join(REPOS_DIR, name)])
                self.assertEqual(code, EXIT_REPOSITORY_ERROR)
                self.assertEqual(out, [])
                self.assertIn("Ошибка:", err)


@mock.patch.object(pypi, "urlopen", side_effect=fake_urlopen)
class RemoteModeTest(unittest.TestCase):
    """Режим работы с репозиторием PyPI (сеть подменяется)."""

    def test_graph(self, _):
        """Транзитивные зависимости без extras."""
        code, out, _ = run(["-p", "Flask", "-r", PYPI_URL, "-v", "3.0.0"])
        self.assertEqual(code, EXIT_SUCCESS)
        self.assertEqual(out, [
            "Граф зависимостей пакета Flask 3.0.0 "
            "(максимальная глубина 3):",
            "  flask -> werkzeug, jinja2",
            "  werkzeug -> markupsafe",
            "  markupsafe -> (нет зависимостей)",
            "  jinja2 -> markupsafe",
            "Пакетов: 4, зависимостей: 4",
            "Циклические зависимости: нет",
        ])

    def test_missing_dependency(self, _):
        """Зависимость не найдена в репозитории — ошибка с кодом 1."""
        PYPI_DATA["broken"] = ["no-such-package"]
        try:
            code, out, err = run(["-p", "broken", "-r", PYPI_URL,
                                  "-v", "latest"])
        finally:
            del PYPI_DATA["broken"]
        self.assertEqual(code, EXIT_REPOSITORY_ERROR)
        self.assertEqual(out, [])
        self.assertIn("no-such-package", err)


if __name__ == "__main__":
    unittest.main()
