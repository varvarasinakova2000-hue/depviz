"""Источники данных о зависимостях пакетов.

Источник — это пара (корневой пакет, функция зависимостей):
функция принимает имя пакета и возвращает список его прямых
зависимостей.
"""

from functools import partial

from config import LATEST_VERSION, MODE_TEST
from errors import RepositoryError
from local_repo import load_local_repository
from pypi import get_package_info
from requirements import normalize_name


def make_local_source(path, package):
    """Создать источник из файла тестового репозитория.

    Пакет, который упомянут только как зависимость, считается
    пакетом без зависимостей. Корневой пакет должен быть упомянут
    в файле.
    """
    packages = load_local_repository(path)
    known = set(packages)
    for dependencies in packages.values():
        known.update(dependencies)
    if package not in known:
        raise RepositoryError(
            f"пакет {package} не найден в тестовом репозитории '{path}'"
        )
    return package, lambda name: packages.get(name, [])


def remote_dependencies(repository, root, version, package):
    """Загрузить обязательные прямые зависимости пакета из PyPI.

    Для корневого пакета берётся версия, заданная пользователем,
    для остальных — последняя. Необязательные зависимости (extras)
    не учитываются, имена приводятся к нормальной форме PEP 503.
    """
    package_version = version if package == root else LATEST_VERSION
    info = get_package_info(repository, package, package_version)
    names = []
    for requirement in info.requirements:
        name = normalize_name(requirement.name)
        if not requirement.is_optional and name not in names:
            names.append(name)
    return names


def make_remote_source(repository, package, version):
    """Создать источник из репозитория PyPI по URL."""
    root = normalize_name(package)
    return root, partial(remote_dependencies, repository, root, version)


def make_source(config):
    """Создать источник зависимостей по режиму работы."""
    if config.mode == MODE_TEST:
        return make_local_source(config.repository, config.package)
    return make_remote_source(
        config.repository, config.package, config.version
    )
