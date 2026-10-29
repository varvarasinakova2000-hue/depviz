#!/bin/sh
# Демонстрация обработки ошибок для всех параметров.
cd "$(dirname "$0")/.." || exit 1

URL=https://pypi.org/pypi
REPO=tests/repos/simple.txt

run() {
    echo "> run.sh $*"
    ./run.sh "$@"
    echo "exit code: $?"
    echo
}

echo "--- обязательные параметры ---"
run -r "$URL" -v 2.31.0
run -p requests -v 2.31.0

echo "--- имя пакета ---"
run -p "" -r "$URL" -v 2.31.0
run -p "bad name" -r "$URL" -v 2.31.0
run -p a -r "$REPO" -m test

echo "--- репозиторий ---"
run -p requests -r pypi.org -v 2.31.0
run -p requests -r ftp://pypi.org/pypi -v 2.31.0
run -p A -r missing.txt -m test
run -p A -r tests -m test

echo "--- режим ---"
run -p A -r "$REPO" -m local

echo "--- версия ---"
run -p requests -r "$URL"
run -p requests -r "$URL" -v v1.0

echo "--- выходной файл ---"
run -p requests -r "$URL" -v 2.31.0 -o graph.png
run -p requests -r "$URL" -v 2.31.0 -o "a*b.svg"
run -p requests -r "$URL" -v 2.31.0 -o no_such_dir/graph.svg
run -p requests -r "$URL" -v 2.31.0 -o src

echo "--- глубина анализа ---"
run -p requests -r "$URL" -v 2.31.0 -d abc
run -p requests -r "$URL" -v 2.31.0 -d 0
run -p requests -r "$URL" -v 2.31.0 -d 101

echo "--- репозиторий пакетов ---"
run -p requests -r "$URL" -v 99.0
run -p no-such-package-depviz -r "$URL" -v latest
run -p requests -r https://pypi.org/simple -v 2.31.0
run -p requests -r https://no-such-host.invalid/pypi -v 2.31.0
run -p A -r "$REPO" -m test
