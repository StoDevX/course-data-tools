#!/bin/bash

python3 -m cProfile -o prof $1
python3 scripts/dumpprof.py > stats.txt
