#!/bin/sh
# Демонстрация запуска с корректными параметрами.
cd "$(dirname "$0")/.." || exit 1

run() {
    echo "> run.sh $*"
    ./run.sh "$@"
    echo "exit code: $?"
    echo
}

run -p requests -r https://pypi.org/pypi -v 2.31.0
run --package flask --repo https://pypi.org/pypi --mode remote \
    --version 3.0.0 --output flask.svg --max-depth 5
run -p requests -r https://pypi.org/pypi -v latest
run -p A -r tests/repos/simple.txt -m test -d 2 -o test_graph.svg
