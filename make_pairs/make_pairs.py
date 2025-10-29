#!/usr/bin/env python3
# make_pairs.py

import sys

# 入力ファイルを指定（引数がなければ標準入力を使用）
path = sys.argv[1] if len(sys.argv) > 1 else None
lines = open(path).read().splitlines() if path else sys.stdin.read().splitlines()

# すべての順序なしペアを出力（自己ペアなし）
for i in range(len(lines)):
    for j in range(i + 1, len(lines)):
        print(f"{lines[i]}\t{lines[j]}")
