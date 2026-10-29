#!/bin/sh
# Демонстрация работы с тестовыми репозиториями (режим test).
cd "$(dirname "$0")/.." || exit 1

REPOS=tests/repos

run() {
    echo "> run.sh $*"
    ./run.sh "$@"
    echo "exit code: $?"
    echo
}

echo "--- общая зависимость (ромб) ---"
run -p A -r "$REPOS/simple.txt" -m test
run -p B -r "$REPOS/simple.txt" -m test

echo "--- максимальная глубина ---"
run -p A -r "$REPOS/chain.txt" -m test -d 1
run -p A -r "$REPOS/chain.txt" -m test -d 3
run -p A -r "$REPOS/chain.txt" -m test -d 10

echo "--- циклические зависимости ---"
run -p A -r "$REPOS/cycle.txt" -m test -d 5
run -p A -r "$REPOS/cycle.txt" -m test -d 2
run -p A -r "$REPOS/self_cycle.txt" -m test
run -p A -r "$REPOS/complex.txt" -m test -d 10
