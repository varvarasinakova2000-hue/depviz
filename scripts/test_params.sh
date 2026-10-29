#!/bin/sh
# Демонстрация построения графа зависимостей пакетов из PyPI.
cd "$(dirname "$0")/.." || exit 1

URL=https://pypi.org/pypi

run() {
    echo "> run.sh $*"
    ./run.sh "$@"
    echo "exit code: $?"
    echo
}

run -p requests -r "$URL" -v 2.31.0
run --package flask --repo "$URL" --mode remote \
    --version 3.0.0 --output flask.svg --max-depth 2
run -p flask -r "$URL" -v 3.0.0 -d 1
run -p six -r "$URL" -v 1.16.0
