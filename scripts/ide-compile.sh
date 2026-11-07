#!/bin/bash
set -eu
source_file=${1:?Source file required}
case "$source_file" in
 *.cpp|*.cc|*.cxx) compiler=g++; standard=-std=c++20 ;;
 *.c) compiler=gcc; standard=-std=c11 ;;
 *) echo 'Select a C or C++ source file.' >&2; exit 1 ;;
esac
"$compiler" "$standard" -Wall -Wextra -Werror -g -O0 -pthread -I /home/student/lab/examples/cpp "$source_file" -o "${source_file%.*}" -lssl -lcrypto
