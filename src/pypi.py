"""Получение метаданных пакета из репозитория PyPI.

Используется JSON API репозитория:
``<URL>/<пакет>/json`` для последней версии и
``<URL>/<пакет>/<версия>/json`` для заданной версии.
"""

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from config import LATEST_VERSION
from requirements import RequirementError, parse_requirement

TIMEOUT_SECONDS = 5
MAX_ATTEMPTS = 3
HTTP_NOT_FOUND = 404
USER_AGENT = "depviz/0.2"


class RepositoryError(Exception):
    """Ошибка получения данных из репозитория пакетов."""


class PackageNotFoundError(RepositoryError):
    """Пакет или его версия отсутствуют в репозитории."""


class NetworkError(RepositoryError):
    """Сбой сети: нет соединения или истекло время ожидания."""


@dataclass(frozen=True)
class PackageInfo:
    """Имя, версия и прямые зависимости пакета."""

    name: str
    version: str
    requirements: tuple


def build_url(repository, package, version):
    """Сформировать URL метаданных пакета в JSON API."""
    base = repository.rstrip("/")
    if version == LATEST_VERSION:
        return f"{base}/{quote(package)}/json"
    return f"{base}/{quote(package)}/{quote(version)}/json"


def request_once(url):
    """Выполнить один HTTP-запрос и вернуть тело ответа."""
    request = Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.read()
    except HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            raise PackageNotFoundError(url) from None
        raise RepositoryError(
            f"репозиторий вернул ошибку HTTP {error.code} для {url}"
        ) from None
    except URLError as error:
        raise NetworkError(
            f"не удалось подключиться к {url}: {error.reason}"
        ) from None
    except OSError as error:
        raise NetworkError(
            f"ошибка при загрузке {url}: {error}"
        ) from None


def download(url):
    """Скачать содержимое по URL, повторяя запрос при сбое сети."""
    last_error = None
    for _ in range(MAX_ATTEMPTS):
        try:
            return request_once(url)
        except NetworkError as error:
            last_error = error
    raise last_error


def fetch_json(url):
    """Скачать и разобрать JSON-документ по URL."""
    body = download(url)
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise RepositoryError(
            f"ответ {url} не является JSON-документом; проверьте, что "
            "URL указывает на JSON API, например https://pypi.org/pypi"
        ) from None


def parse_requirements(requires_dist):
    """Разобрать список строк Requires-Dist."""
    if requires_dist is None:
        return ()
    if not isinstance(requires_dist, list):
        raise RepositoryError("поле requires_dist должно быть списком")
    try:
        return tuple(parse_requirement(item) for item in requires_dist)
    except RequirementError as error:
        raise RepositoryError(str(error)) from None


def parse_package_info(data):
    """Извлечь имя, версию и зависимости из ответа JSON API."""
    info = data.get("info") if isinstance(data, dict) else None
    if not isinstance(info, dict):
        raise RepositoryError("в ответе репозитория нет раздела info")
    return PackageInfo(
        name=str(info.get("name", "")),
        version=str(info.get("version", "")),
        requirements=parse_requirements(info.get("requires_dist")),
    )


def package_exists(repository, package):
    """Проверить, есть ли пакет в репозитории (в любой версии)."""
    try:
        download(build_url(repository, package, LATEST_VERSION))
    except PackageNotFoundError:
        return False
    return True


def not_found_message(repository, package, version):
    """Сформировать сообщение об отсутствии пакета или его версии."""
    if version != LATEST_VERSION and package_exists(repository, package):
        return (
            f"версия {version} пакета '{package}' "
            "не найдена в репозитории"
        )
    return (
        f"пакет '{package}' не найден в репозитории {repository}; "
        "проверьте имя пакета и URL репозитория"
    )


def get_package_info(repository, package, version):
    """Получить прямые зависимости пакета заданной версии."""
    url = build_url(repository, package, version)
    try:
        data = fetch_json(url)
    except PackageNotFoundError:
        raise RepositoryError(
            not_found_message(repository, package, version)
        ) from None
    return parse_package_info(data)
