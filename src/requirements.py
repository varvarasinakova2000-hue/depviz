"""Разбор строк зависимостей пакета в формате PEP 508.

Такие строки хранятся в поле Requires-Dist метаданных пакета,
например: ``idna<4,>=2.5`` или ``PySocks (>=1.5.6) ; extra == 'socks'``.
"""

import re
from dataclasses import dataclass

NAME_RE = re.compile(
    r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(\[[^\]]*\])?\s*(.*)$"
)
EXTRA_RE = re.compile(r"""\bextra\s*==\s*['"]([^'"]+)['"]""")
SPECIFIER_START = ("<", ">", "=", "!", "~", "@", "(")


class RequirementError(ValueError):
    """Строка зависимости не соответствует формату PEP 508."""


@dataclass(frozen=True)
class Requirement:
    """Одна прямая зависимость пакета."""

    name: str
    specifier: str
    marker: str

    @property
    def extra(self):
        """Вернуть имя extra, если зависимость необязательная."""
        match = EXTRA_RE.search(self.marker)
        return match.group(1) if match else None

    @property
    def is_optional(self):
        """Проверить, нужна ли зависимость только для extra."""
        return self.extra is not None

    def __str__(self):
        """Вернуть зависимость в виде: имя версия [условие]."""
        text = f"{self.name} {self.specifier}".strip()
        if self.marker:
            text += f" [{self.marker}]"
        return text


def normalize_name(name):
    """Привести имя пакета к нормальной форме (PEP 503)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_specifier(rest, text):
    """Выделить ограничение версии из остатка строки зависимости."""
    specifier = rest.strip()
    if specifier and not specifier.startswith(SPECIFIER_START):
        raise RequirementError(f"некорректная зависимость '{text}'")
    if specifier.startswith("(") and specifier.endswith(")"):
        specifier = specifier[1:-1].strip()
    return specifier


def parse_requirement(text):
    """Разобрать строку зависимости в объект Requirement."""
    requirement, _, marker = text.partition(";")
    match = NAME_RE.match(requirement)
    if not match:
        raise RequirementError(f"некорректная зависимость '{text}'")
    name, _, rest = match.groups()
    return Requirement(
        name=name,
        specifier=parse_specifier(rest, text),
        marker=marker.strip(),
    )
