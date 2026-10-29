"""Тесты разбора и проверки параметров командной строки."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr

from config import (
    MODE_REMOTE,
    MODE_TEST,
    ConfigError,
    build_parser,
    make_config,
    validate_max_depth,
    validate_output,
    validate_version,
)
from main import EXIT_CONFIG_ERROR, main

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_REPO = os.path.join(TESTS_DIR, "repos", "simple.txt")
PYPI_URL = "https://pypi.org/pypi"
REMOTE = ["-r", PYPI_URL, "-v", "2.31.0"]


def parse(argv):
    """Разобрать аргументы и собрать конфигурацию."""
    return make_config(build_parser().parse_args(argv))


class ValidConfigTest(unittest.TestCase):
    """Корректные наборы параметров."""

    def test_defaults(self):
        """Необязательные параметры получают значения по умолчанию."""
        config = parse(["-p", "requests"] + REMOTE)
        self.assertEqual(config.mode, "remote")
        self.assertEqual(config.version, "2.31.0")
        self.assertEqual(config.output, "graph.svg")
        self.assertEqual(config.max_depth, 3)

    def test_all_options(self):
        """Все параметры заданы явно."""
        config = parse([
            "--package", "flask", "--repo", PYPI_URL,
            "--mode", "remote", "--version", "3.0.0",
            "--output", "flask.svg", "--max-depth", "5",
        ])
        self.assertEqual(config.package, "flask")
        self.assertEqual(config.version, "3.0.0")
        self.assertEqual(config.max_depth, 5)

    def test_latest_version(self):
        """Последняя версия задаётся явно словом latest."""
        config = parse(["-p", "requests", "-r", PYPI_URL, "-v", "latest"])
        self.assertEqual(config.version, "latest")

    def test_test_mode(self):
        """В тестовом режиме указывается путь к файлу, версия не нужна."""
        config = parse(["-p", "A", "-r", TEST_REPO, "-m", "test"])
        self.assertEqual(config.repository, TEST_REPO)
        self.assertEqual(config.version, "-")


class InvalidConfigTest(unittest.TestCase):
    """Ошибки в значениях параметров."""

    def assert_error(self, argv):
        """Проверить, что набор аргументов вызывает ConfigError."""
        with self.assertRaises(ConfigError):
            parse(argv)

    def test_bad_package_name(self):
        """Недопустимые имена пакетов."""
        self.assert_error(["-p", ""] + REMOTE)
        self.assert_error(["-p", "bad name"] + REMOTE)
        self.assert_error(["-p", "requests_"] + REMOTE)

    def test_test_mode_package_name(self):
        """В тестовом режиме имя пакета из больших латинских букв."""
        self.assert_error(["-p", "a", "-r", TEST_REPO, "-m", "test"])
        self.assert_error(["-p", "A1", "-r", TEST_REPO, "-m", "test"])

    def test_bad_url(self):
        """Некорректный URL репозитория."""
        for url in ("", "pypi.org", "ftp://pypi.org", "https://py pi.org"):
            with self.subTest(url=url):
                self.assert_error(["-p", "requests", "-r", url,
                                   "-v", "2.31.0"])

    def test_bad_test_repo(self):
        """Тестовый репозиторий не найден или не является файлом."""
        self.assert_error(["-p", "A", "-r", "missing.txt", "-m", "test"])
        self.assert_error(["-p", "A", "-r", TESTS_DIR, "-m", "test"])

    def test_test_repo_not_utf8(self):
        """Файл тестового репозитория не в кодировке UTF-8."""
        with tempfile.NamedTemporaryFile(delete=False) as repo_file:
            repo_file.write(b"\xff\xfe\xfa")
        try:
            self.assert_error(
                ["-p", "A", "-r", repo_file.name, "-m", "test"]
            )
        finally:
            os.remove(repo_file.name)

    def test_bad_mode(self):
        """Неизвестный режим работы."""
        self.assert_error(["-p", "A", "-r", TEST_REPO, "-m", "local"])

    def test_missing_version(self):
        """В режиме remote версия пакета обязательна."""
        self.assert_error(["-p", "requests", "-r", PYPI_URL])

    def test_bad_version(self):
        """Некорректная версия пакета."""
        for version in ("", "v1.0", "1..2", "abc"):
            for mode in (MODE_REMOTE, MODE_TEST):
                with self.subTest(version=version, mode=mode):
                    with self.assertRaises(ConfigError):
                        validate_version(version, mode)

    def test_bad_output(self):
        """Некорректное имя выходного файла."""
        for output in ("", "graph.png", "graph", "a*b.svg",
                       os.path.join("no_such_dir", "g.svg"), "dir/"):
            with self.subTest(output=output):
                with self.assertRaises(ConfigError):
                    validate_output(output)

    def test_bad_max_depth(self):
        """Глубина анализа не число или вне допустимого диапазона."""
        for depth in ("", "abc", "2.5", "0", "-1", "101"):
            with self.subTest(depth=depth):
                with self.assertRaises(ConfigError):
                    validate_max_depth(depth)

    def test_main_reports_error(self):
        """Функция main выводит ошибку и возвращает код ошибки."""
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["-p", "requests", "-d", "0"] + REMOTE)
        self.assertEqual(code, EXIT_CONFIG_ERROR)
        self.assertIn("Ошибка: глубина анализа", err.getvalue())

    def test_missing_required(self):
        """Без обязательных параметров argparse завершает работу."""
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(["-r", PYPI_URL])


if __name__ == "__main__":
    unittest.main()
