#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正後のファイルをチェック
"""

import os
import re
from pathlib import Path

BASE_DIR = Path("/Users/diabolo/dev/temp/tonao/templates")

fixed_files = []
still_broken = []

for filepath in sorted(BASE_DIR.glob("*.html")):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 問題があるパターンをチェック
        # 1. su-spoiler-contentが空で、その後に解答がある
        has_empty_spoiler = bool(re.search(r'<div class="su-spoiler-content[^>]*"[^>]*></div>.*?<p><span[^>]*><strong>解答</strong>', content, re.DOTALL))
        
        # 2. pタグの中にdivがある（不正なHTML構造）
        has_invalid_structure = bool(re.search(r'<p><span[^>]*><div class="su-spoiler', content))
        
        # 3. 正しい構造：su-spoiler-contentの中に解答がある
        has_correct_structure = bool(re.search(r'<div class="su-spoiler-content[^>]*"[^>]*>.*?<p><strong>解答</strong>', content, re.DOTALL))
        
        if has_empty_spoiler or has_invalid_structure:
            still_broken.append(filepath.name)
        elif has_correct_structure:
            fixed_files.append(filepath.name)
    except Exception as e:
        print(f"エラー ({filepath.name}): {e}")

print(f"✓ 正しく修正されたファイル: {len(fixed_files)}")
print(f"✗ まだ問題があるファイル: {len(still_broken)}")

if still_broken:
    print("\nまだ問題があるファイル:")
    for f in still_broken:
        print(f"  - {f}")

