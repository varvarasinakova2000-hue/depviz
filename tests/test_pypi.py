"""Тесты получения зависимостей из репозитория (без доступа к сети)."""

import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock
from urllib.error import HTTPError, URLError

import pypi
from main import EXIT_REPOSITORY_ERROR, EXIT_SUCCESS, main
from pypi import (
    RepositoryError,
    build_url,
    get_package_info,
    parse_package_info,
)

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PYPI_URL = "https://pypi.org/pypi"
TEST_REPO = os.path.join(TESTS_DIR, "repos", "simple.txt")
REQUESTS_INFO = {
    "info": {
        "name": "requests",
        "version": "2.31.0",
        "requires_dist": [
            "charset-normalizer (<4,>=2)",
            "idna (<4,>=2.5)",
            "PySocks (!=1.5.7,>=1.5.6) ; extra == 'socks'",
        ],
    }
}


def fake_response(data):
    """Создать подмену ответа urlopen с заданным телом."""
    body = data if isinstance(data, bytes) else json.dumps(data).encode()
    response = mock.MagicMock()
    response.read.return_value = body
    response.__enter__.return_value = response
    return response


def http_error(code):
    """Создать исключение HTTPError с заданным кодом."""
    return HTTPError(PYPI_URL, code, "error", {}, None)


class BuildUrlTest(unittest.TestCase):
    """Формирование адреса JSON API."""

    def test_latest(self):
        """Для latest версия в адрес не добавляется."""
        self.assertEqual(build_url(PYPI_URL, "flask", "latest"),
                         "https://pypi.org/pypi/flask/json")

    def test_version(self):
        """Заданная версия входит в адрес."""
        self.assertEqual(build_url(PYPI_URL + "/", "flask", "3.0.0"),
                         "https://pypi.org/pypi/flask/3.0.0/json")


class ParsePackageInfoTest(unittest.TestCase):
    """Разбор ответа JSON API."""

    def test_requirements(self):
        """Из ответа извлекаются имя, версия и зависимости."""
        info = parse_package_info(REQUESTS_INFO)
        self.assertEqual(info.name, "requests")
        self.assertEqual(info.version, "2.31.0")
        names = [req.name for req in info.requirements]
        self.assertEqual(names, ["charset-normalizer", "idna", "PySocks"])

    def test_no_requirements(self):
        """Пакет без зависимостей (requires_dist = null)."""
        data = {"info": {"name": "six", "version": "1.16.0",
                         "requires_dist": None}}
        self.assertEqual(parse_package_info(data).requirements, ())

    def test_bad_structure(self):
        """Ответ без раздела info или с неверным полем зависимостей."""
        bad = [[], {}, {"info": "x"},
               {"info": {"requires_dist": "idna"}},
               {"info": {"requires_dist": [">=1.0"]}}]
        for data in bad:
            with self.subTest(data=data):
                with self.assertRaises(RepositoryError):
                    parse_package_info(data)


@mock.patch.object(pypi, "urlopen")
class GetPackageInfoTest(unittest.TestCase):
    """Загрузка данных о пакете с подменой сети."""

    def test_success(self, urlopen):
        """Запрос идёт по адресу заданной версии."""
        urlopen.return_value = fake_response(REQUESTS_INFO)
        info = get_package_info(PYPI_URL, "requests", "2.31.0")
        self.assertEqual(info.version, "2.31.0")
        request = urlopen.call_args[0][0]
        self.assertEqual(request.full_url,
                         "https://pypi.org/pypi/requests/2.31.0/json")

    def test_version_not_found(self, urlopen):
        """Пакет есть в репозитории, а заданной версии нет."""
        urlopen.side_effect = [
            http_error(404), fake_response(REQUESTS_INFO),
        ]
        with self.assertRaisesRegex(RepositoryError, "версия 9.9"):
            get_package_info(PYPI_URL, "requests", "9.9")
        request = urlopen.call_args[0][0]
        self.assertEqual(request.full_url,
                         "https://pypi.org/pypi/requests/json")

    def test_package_not_found(self, urlopen):
        """Несуществующий пакет."""
        urlopen.side_effect = http_error(404)
        with self.assertRaisesRegex(RepositoryError, "пакет .* не найден"):
            get_package_info(PYPI_URL, "no-such-pkg", "latest")

    def test_wrong_repository_url(self, urlopen):
        """По URL нет ни версии, ни пакета: подсказка проверить URL."""
        urlopen.side_effect = http_error(404)
        with self.assertRaisesRegex(RepositoryError, "URL репозитория"):
            get_package_info("https://pypi.org/simple", "requests", "1.0")
        self.assertEqual(urlopen.call_count, 2)

    def test_server_error(self, urlopen):
        """Ошибка сервера репозитория."""
        urlopen.side_effect = http_error(500)
        with self.assertRaisesRegex(RepositoryError, "HTTP 500"):
            get_package_info(PYPI_URL, "requests", "latest")

    def test_connection_error(self, urlopen):
        """Репозиторий недоступен: все попытки запроса неудачны."""
        urlopen.side_effect = URLError("no host")
        with self.assertRaisesRegex(RepositoryError, "подключиться"):
            get_package_info(PYPI_URL, "requests", "latest")
        self.assertEqual(urlopen.call_count, pypi.MAX_ATTEMPTS)

    def test_retry_after_network_error(self, urlopen):
        """После разового сбоя сети запрос повторяется."""
        urlopen.side_effect = [
            TimeoutError("timed out"), fake_response(REQUESTS_INFO),
        ]
        info = get_package_info(PYPI_URL, "requests", "2.31.0")
        self.assertEqual(info.name, "requests")
        self.assertEqual(urlopen.call_count, 2)

    def test_http_error_not_retried(self, urlopen):
        """Ответ 404 не повторяется."""
        urlopen.side_effect = http_error(404)
        with self.assertRaises(RepositoryError):
            get_package_info(PYPI_URL, "requests", "latest")
        self.assertEqual(urlopen.call_count, 1)

    def test_timeout(self, urlopen):
        """Превышено время ожидания ответа."""
        urlopen.side_effect = TimeoutError("timed out")
        with self.assertRaises(RepositoryError):
            get_package_info(PYPI_URL, "requests", "latest")

    def test_not_json(self, urlopen):
        """Ответ не является JSON-документом."""
        urlopen.return_value = fake_response(b"<html></html>")
        with self.assertRaisesRegex(RepositoryError, "JSON"):
            get_package_info(PYPI_URL, "requests", "latest")


@mock.patch.object(pypi, "urlopen")
class MainTest(unittest.TestCase):
    """Вывод прямых зависимостей при запуске приложения."""

    def test_prints_dependencies(self, urlopen):
        """Выводятся обязательные и необязательные зависимости."""
        urlopen.return_value = fake_response(REQUESTS_INFO)
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["-p", "requests", "-r", PYPI_URL,
                         "-v", "2.31.0"])
        self.assertEqual(code, EXIT_SUCCESS)
        self.assertEqual(out.getvalue().splitlines(), [
            "Прямые зависимости пакета requests 2.31.0:",
            "  charset-normalizer <4,>=2",
            "  idna <4,>=2.5",
            "Необязательные зависимости (extras):",
            "  PySocks !=1.5.7,>=1.5.6 [extra == 'socks']",
        ])

    def test_reports_repository_error(self, urlopen):
        """Ошибка репозитория выводится в stderr с кодом 1."""
        urlopen.side_effect = [
            http_error(404), fake_response(REQUESTS_INFO),
        ]
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["-p", "requests", "-r", PYPI_URL, "-v", "9.9"])
        self.assertEqual(code, EXIT_REPOSITORY_ERROR)
        self.assertIn("Ошибка: версия 9.9", err.getvalue())

    def test_test_mode_not_supported(self, urlopen):
        """Режим test на этом этапе не поддерживается."""
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["-p", "A", "-r", TEST_REPO, "-m", "test"])
        self.assertEqual(code, EXIT_REPOSITORY_ERROR)
        self.assertIn("режим test", err.getvalue())
        urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
