"""Тесты разбора строк зависимостей (PEP 508)."""

import unittest

from requirements import (
    RequirementError,
    normalize_name,
    parse_requirement,
)


class ParseRequirementTest(unittest.TestCase):
    """Разбор строк поля Requires-Dist."""

    def test_name_only(self):
        """Зависимость без ограничений версии."""
        req = parse_requirement("python-dotenv")
        self.assertEqual(req.name, "python-dotenv")
        self.assertEqual(req.specifier, "")
        self.assertEqual(req.marker, "")
        self.assertEqual(str(req), "python-dotenv")

    def test_specifier(self):
        """Ограничение версии в современном формате."""
        req = parse_requirement("idna<4,>=2.5")
        self.assertEqual(req.name, "idna")
        self.assertEqual(req.specifier, "<4,>=2.5")
        self.assertFalse(req.is_optional)

    def test_specifier_in_parentheses(self):
        """Ограничение версии в скобках (старый формат)."""
        req = parse_requirement("charset-normalizer (<4,>=2)")
        self.assertEqual(req.name, "charset-normalizer")
        self.assertEqual(req.specifier, "<4,>=2")

    def test_marker(self):
        """Зависимость с условием окружения."""
        req = parse_requirement(
            "importlib-metadata>=3.6.0; python_version < '3.10'"
        )
        self.assertEqual(req.marker, "python_version < '3.10'")
        self.assertFalse(req.is_optional)
        self.assertEqual(
            str(req), "importlib-metadata >=3.6.0 [python_version < '3.10']"
        )

    def test_extra(self):
        """Необязательная зависимость для extra."""
        req = parse_requirement(
            "PySocks (!=1.5.7,>=1.5.6) ; extra == 'socks'"
        )
        self.assertEqual(req.name, "PySocks")
        self.assertEqual(req.specifier, "!=1.5.7,>=1.5.6")
        self.assertTrue(req.is_optional)
        self.assertEqual(req.extra, "socks")

    def test_dependency_extras(self):
        """Extras самой зависимости не входят в имя."""
        req = parse_requirement("urllib3[socks]>=1.26")
        self.assertEqual(req.name, "urllib3")
        self.assertEqual(req.specifier, ">=1.26")

    def test_invalid(self):
        """Строки, не соответствующие формату."""
        for text in ("", "   ", ">=1.0", "name version"):
            with self.subTest(text=text):
                with self.assertRaises(RequirementError):
                    parse_requirement(text)

    def test_normalize_name(self):
        """Нормализация имён пакетов по PEP 503."""
        self.assertEqual(normalize_name("Charset_Normalizer"),
                         "charset-normalizer")
        self.assertEqual(normalize_name("zope.interface"),
                         "zope-interface")


if __name__ == "__main__":
    unittest.main()
