"""Тесты тестового репозитория и источников данных."""

import os
import tempfile
import unittest
from unittest import mock

import sources
from errors import RepositoryError
from local_repo import load_local_repository, parse_local_repository
from pypi import PackageInfo
from requirements import parse_requirement
from sources import make_local_source, make_remote_source

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPOS_DIR = os.path.join(TESTS_DIR, "repos")
BROKEN_REPO = "broken.txt"
PYPI_URL = "https://pypi.org/pypi"


class ParseLocalRepositoryTest(unittest.TestCase):
    """Разбор файла с описанием графа."""

    def test_valid(self):
        """Пакеты, зависимости, комментарии и пустые строки."""
        text = "# граф\nA: B C\n\nB: C  # комментарий\nC:\n"
        self.assertEqual(parse_local_repository(text), {
            "A": ["B", "C"], "B": ["C"], "C": [],
        })

    def test_errors(self):
        """Ошибки формата описания графа."""
        bad = ["A B", "a: B", "A: b", "A1: B", "A: B B", "A: B\nA: C",
               ": B"]
        for text in bad:
            with self.subTest(text=text):
                with self.assertRaises(RepositoryError):
                    parse_local_repository(text)

    def test_error_line_number(self):
        """В сообщении об ошибке указан номер строки."""
        with self.assertRaisesRegex(RepositoryError, "строка 3"):
            parse_local_repository("A: B\n\nB C\n")

    def test_repository_files(self):
        """Все файлы-примеры, кроме broken.txt, корректны."""
        for name in sorted(os.listdir(REPOS_DIR)):
            path = os.path.join(REPOS_DIR, name)
            with self.subTest(name=name):
                if name == BROKEN_REPO:
                    with self.assertRaises(RepositoryError):
                        load_local_repository(path)
                else:
                    self.assertIn("A", load_local_repository(path))

    def test_unreadable_file(self):
        """Файл не найден или не в кодировке UTF-8."""
        with self.assertRaises(RepositoryError):
            load_local_repository(os.path.join(REPOS_DIR, "missing.txt"))
        with tempfile.NamedTemporaryFile(delete=False) as repo_file:
            repo_file.write(b"\xff\xfe")
        try:
            with self.assertRaises(RepositoryError):
                load_local_repository(repo_file.name)
        finally:
            os.remove(repo_file.name)


class LocalSourceTest(unittest.TestCase):
    """Источник зависимостей из тестового репозитория."""

    def test_dependencies(self):
        """Зависимости описанного и неописанного пакета."""
        root, dependencies = make_local_source(
            os.path.join(REPOS_DIR, "complex.txt"), "A"
        )
        self.assertEqual(root, "A")
        self.assertEqual(dependencies("A"), ["B", "C"])
        self.assertEqual(dependencies("I"), [])

    def test_unknown_root(self):
        """Корневого пакета нет в тестовом репозитории."""
        with self.assertRaisesRegex(RepositoryError, "Z не найден"):
            make_local_source(os.path.join(REPOS_DIR, "simple.txt"), "Z")


def package_info(*requirements):
    """Создать PackageInfo с заданными строками зависимостей."""
    parsed = tuple(parse_requirement(text) for text in requirements)
    return PackageInfo(name="x", version="1.0", requirements=parsed)


@mock.patch.object(sources, "get_package_info")
class RemoteSourceTest(unittest.TestCase):
    """Источник зависимостей из репозитория PyPI."""

    def test_versions(self, get_info):
        """Для корня берётся заданная версия, для остальных — latest."""
        get_info.return_value = package_info()
        root, dependencies = make_remote_source(PYPI_URL, "Flask", "3.0.0")
        self.assertEqual(root, "flask")
        dependencies("flask")
        dependencies("jinja2")
        self.assertEqual(get_info.call_args_list, [
            mock.call(PYPI_URL, "flask", "3.0.0"),
            mock.call(PYPI_URL, "jinja2", "latest"),
        ])

    def test_required_only(self, get_info):
        """Extras отбрасываются, имена нормализуются без повторов."""
        get_info.return_value = package_info(
            "Charset_Normalizer<4", "idna", "PySocks; extra == 'socks'",
            "idna>=2; python_version < '3.8'",
        )
        _, dependencies = make_remote_source(PYPI_URL, "requests", "2.0")
        self.assertEqual(dependencies("requests"),
                         ["charset-normalizer", "idna"])


if __name__ == "__main__":
    unittest.main()
