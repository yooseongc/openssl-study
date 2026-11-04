#!/bin/bash
set -eu
source_file=${1:?Usage: study-build source.cpp [program arguments ...]}
shift
case "$source_file" in
 *.cpp|*.cc|*.cxx) compiler=g++; standard=-std=c++20 ;;
 *.c) compiler=gcc; standard=-std=c11 ;;
 *) echo 'Supported: .cpp .cc .cxx .c' >&2; exit 1 ;;
esac
target=${STUDY_BUILD_OUTPUT:-${source_file%.*}}
"$compiler" "$standard" -Wall -Wextra -Werror -g -O0 -pthread -I /home/student/lab/examples/cpp "$source_file" -o "$target" -lssl -lcrypto
case "$target" in /*) ;; *) target="./$target";; esac
timeout 15 "$target" "$@"
