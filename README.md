# depviz — визуализатор графа зависимостей пакетов Python

Практическая работа № 2 по дисциплине «Конфигурационное управление»,
вариант 25.

## Общее описание

`depviz` — CLI-инструмент для построения и визуализации графа
зависимостей пакетов Python (pip). Готовые менеджеры пакетов и библиотеки
для получения зависимостей не используются.

Текущее состояние — **этап 1: минимальный прототип с конфигурацией**.
Приложение принимает параметры из командной строки, проверяет их
и выводит в формате `ключ=значение`. При ошибке в любом параметре
выводится понятное сообщение, и программа завершается с кодом `2`.

Требования: Python 3.8+ (используется только стандартная библиотека).

## Структура репозитория

```
src/
  main.py           точка входа: разбор параметров и вывод
  config.py         описание и проверка параметров командной строки
tests/
  __init__.py       подключение каталога src для тестов
  test_config.py    модульные тесты (unittest)
  repos/simple.txt  файл тестового репозитория для режима test
scripts/
  test_params.*     демонстрация запуска с корректными параметрами
  test_errors.*     демонстрация обработки ошибок всех параметров
run.sh, run.bat     скрипты запуска приложения
```

## Параметры командной строки

| Параметр | Обязательный | По умолчанию | Описание |
|---|---|---|---|
| `-p`, `--package` | да | — | имя анализируемого пакета |
| `-r`, `--repo` | да | — | URL репозитория или путь к файлу тестового репозитория |
| `-m`, `--mode` | нет | `remote` | режим работы: `remote` или `test` |
| `-v`, `--version` | в режиме `remote` | — | версия пакета или `latest` |
| `-o`, `--output` | нет | `graph.svg` | имя файла с изображением графа |
| `-d`, `--max-depth` | нет | `3` | максимальная глубина анализа зависимостей |
| `-h`, `--help` | нет | — | справка по параметрам |

### Проверка параметров

- **package** — не пустое; в режиме `remote` — имя по правилам PyPI
  (латинские буквы, цифры, а также `.`, `_`, `-` внутри имени);
  в режиме `test` — только большие латинские буквы (`A`, `B`, `AB`).
- **repo** — в режиме `remote` — URL со схемой `http` или `https`,
  с адресом сервера и без пробелов; в режиме `test` — существующий
  файл в кодировке UTF-8 (не каталог).
- **mode** — только `remote` или `test`.
- **version** — номер версии в формате PEP 440 (`1.0`, `2.31.0`,
  `3.0.0rc1`, `1.2.post1`, `1.0.dev3`) или слово `latest` — последняя
  версия. В режиме `remote` версию нужно указать обязательно;
  в режиме `test` у пакетов нет версий, и параметр можно не задавать
  (выводится значение `-`).
- **output** — не пустое имя файла с расширением `.svg`,
  без символов `< > : " / \ | ? *`; каталог файла должен существовать;
  путь не должен указывать на существующий каталог.
- **max-depth** — целое число от 1 до 100.

Отсутствие обязательных параметров и неизвестные опции обрабатывает
`argparse` (вывод подсказки `usage` и код возврата `2`).

### Режимы работы

- `remote` — данные о пакетах берутся из репозитория по URL
  (например, `https://pypi.org/pypi`).
- `test` — вместо реального репозитория используется файл описания
  графа, в котором пакеты обозначаются большими латинскими буквами
  (пример — `tests/repos/simple.txt`).

## Описание функций

### src/config.py

| Функция / класс | Назначение |
|---|---|
| `ConfigError` | исключение: ошибка в значении параметра |
| `Config` | проверенные параметры запуска; метод `as_pairs()` возвращает их списком пар (ключ, значение) |
| `build_parser()` | создаёт парсер `argparse` со всеми параметрами |
| `validate_mode(mode)` | проверяет режим работы |
| `validate_package(name, mode)` | проверяет имя пакета с учётом режима |
| `validate_url(url)` | проверяет URL репозитория |
| `validate_test_repo(path)` | проверяет, что файл тестового репозитория существует и читается в UTF-8 |
| `validate_repository(repository, mode)` | выбирает проверку URL или файла в зависимости от режима |
| `validate_version(version, mode)` | проверяет версию пакета, в режиме `remote` — её наличие |
| `validate_output(output)` | проверяет имя файла с изображением графа |
| `validate_max_depth(value)` | преобразует глубину анализа в число и проверяет диапазон |
| `make_config(args)` | проверяет все разобранные аргументы и собирает `Config` |

### src/main.py

| Функция | Назначение |
|---|---|
| `print_config(config)` | выводит параметры в формате `ключ=значение` |
| `main(argv=None)` | точка входа: разбор и проверка параметров, вывод; возвращает код завершения |

## Сборка и запуск тестов

Сборка не требуется. Запуск приложения:

```bash
./run.sh -p requests -r https://pypi.org/pypi -v 2.31.0
```

```bat
run.bat -p requests -r https://pypi.org/pypi -v 2.31.0
```

Запуск модульных тестов (из корня репозитория):

```bash
python -m unittest -v
```

Демонстрационные скрипты (Linux / Windows):

```bash
./scripts/test_params.sh
./scripts/test_errors.sh
```

```bat
scripts\test_params.bat
scripts\test_errors.bat
```

## Примеры использования

Обязательные параметры, остальные — по умолчанию:

```
$ ./run.sh -p requests -r https://pypi.org/pypi -v 2.31.0
package=requests
repository=https://pypi.org/pypi
mode=remote
version=2.31.0
output=graph.svg
max_depth=3
```

Все параметры заданы явно:

```
$ ./run.sh --package flask --repo https://pypi.org/pypi --mode remote \
    --version 3.0.0 --output flask.svg --max-depth 5
package=flask
repository=https://pypi.org/pypi
mode=remote
version=3.0.0
output=flask.svg
max_depth=5
```

Режим тестового репозитория (версия не нужна):

```
$ ./run.sh -p A -r tests/repos/simple.txt -m test -d 2 -o test_graph.svg
package=A
repository=tests/repos/simple.txt
mode=test
version=-
output=test_graph.svg
max_depth=2
```

### Обработка ошибок

```
$ ./run.sh -r https://pypi.org/pypi -v 2.31.0
usage: depviz [-h] -p PACKAGE -r REPO [-m MODE] [-v VERSION] [-o OUTPUT]
              [-d MAX_DEPTH]
depviz: error: the following arguments are required: -p/--package

$ ./run.sh -p "bad name" -r https://pypi.org/pypi -v 2.31.0
Ошибка: недопустимое имя пакета 'bad name': разрешены латинские буквы,
цифры и символы '.', '_', '-' внутри имени

$ ./run.sh -p a -r tests/repos/simple.txt -m test
Ошибка: в тестовом режиме имя пакета 'a' должно состоять из больших
латинских букв

$ ./run.sh -p requests -r pypi.org -v 2.31.0
Ошибка: некорректный URL репозитория 'pypi.org': ожидается адрес вида
https://pypi.org/pypi (для файла укажите --mode test)

$ ./run.sh -p A -r missing.txt -m test
Ошибка: файл тестового репозитория 'missing.txt' не найден

$ ./run.sh -p A -r tests -m test
Ошибка: 'tests' не является файлом

$ ./run.sh -p A -r tests/repos/simple.txt -m local
Ошибка: неизвестный режим 'local', допустимые значения: remote, test

$ ./run.sh -p requests -r https://pypi.org/pypi
Ошибка: не указана версия пакета: задайте --version, например
--version 2.31.0 или --version latest

$ ./run.sh -p requests -r https://pypi.org/pypi -v v1.0
Ошибка: некорректная версия пакета 'v1.0': ожидается формат вроде
1.0, 2.31.0, 3.0.0rc1 или latest

$ ./run.sh -p requests -r https://pypi.org/pypi -v 2.31.0 -o graph.png
Ошибка: файл изображения 'graph.png' должен иметь расширение .svg

$ ./run.sh -p requests -r https://pypi.org/pypi -v 2.31.0 \
    -o no_such_dir/graph.svg
Ошибка: каталог 'no_such_dir' не существует

$ ./run.sh -p requests -r https://pypi.org/pypi -v 2.31.0 -o src
Ошибка: 'src' является каталогом

$ ./run.sh -p requests -r https://pypi.org/pypi -v 2.31.0 -d abc
Ошибка: глубина анализа должна быть целым числом, получено 'abc'

$ ./run.sh -p requests -r https://pypi.org/pypi -v 2.31.0 -d 0
Ошибка: глубина анализа должна быть от 1 до 100, получено 0
```

(Длинные сообщения об ошибках в примерах перенесены для удобства чтения,
программа выводит их одной строкой.)

Полный набор проверок — в скриптах `scripts/test_errors.sh`
и `scripts/test_errors.bat`.
