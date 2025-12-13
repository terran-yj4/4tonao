#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spoiler構造を修正するスクリプト
解答・解説がsu-spoiler-contentの外にあるファイルを修正
"""

import os
import re
from pathlib import Path

BASE_DIR = Path("/Users/diabolo/dev/temp/tonao/templates")

def fix_spoiler_structure(filepath):
    """ファイルのspoiler構造を修正"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        original_content = content
        
        # パターン1: <p><span><div class="su-spoiler">...<div class="su-spoiler-content"></div></div></span></p>
        # その後、<p><span>解答</span>...</p> が続く
        pattern1 = r'(<p><span[^>]*>)<div class="su-spoiler[^"]*"[^>]*>(<div class="su-spoiler-title[^>]*>.*?</div>)<div class="su-spoiler-content[^>]*"[^>]*></div></div></span></p>\s*<p><span[^>]*><strong>解答</strong>.*?</p>(?:\s*<p><span[^>]*><strong>解説</strong>.*?</p>)*'
        
        def fix_match(match):
            span_open = match.group(1)
            spoiler_title = match.group(2)
            
            # 解答・解説の部分を抽出
            after_match = match.group(0)
            answer_section = re.search(r'<p><span[^>]*><strong>解答</strong>.*?(?=</div>|$)', after_match, re.DOTALL)
            if not answer_section:
                return match.group(0)  # 修正できない場合は元のまま
            
            answer_text = answer_section.group(0)
            # 解答・解説の後の不要なspanを削除
            answer_text = answer_text.rstrip()
            if answer_text.endswith('</p>'):
                # その後の解説も含める
                remaining = after_match[answer_section.end():]
                explanation_match = re.search(r'<p><span[^>]*><strong>解説</strong>.*?(?=<p><span[^>]*></span></p>|</div>|$)', remaining, re.DOTALL)
                if explanation_match:
                    answer_text += '\n' + explanation_match.group(0)
            
            # 正しい構造に修正
            fixed = f'<div class="su-spoiler su-spoiler-style-default su-spoiler-icon-plus su-spoiler-closed" data-anchor-in-url="no" data-scroll-offset="0">{spoiler_title}<div class="su-spoiler-content su-u-clearfix su-u-trim su-spoiler-closed" style="display: none !important;">\n<p></p>\n{answer_text}\n<p><span style="font-size: 100%;"></span></p></div></div>'
            
            return fixed
        
        # より確実なパターンマッチング
        # まず、spoiler-contentが空で、その後に解答があるパターンを探す
        pattern2 = r'(<p><span[^>]*>)?<div class="su-spoiler[^"]*"[^>]*>(<div class="su-spoiler-title[^>]*>.*?</div>)<div class="su-spoiler-content[^>]*"[^>]*></div></div>(</span></p>)?\s*(<p><span[^>]*><strong>解答</strong>.*?(?:<p><span[^>]*><strong>解説</strong>.*?)?)(?=<p><span[^>]*></span></p></div>|</div>)'
        
        def fix_match2(match):
            span_before = match.group(1) or ''
            spoiler_title = match.group(2)
            span_after = match.group(3) or ''
            answer_section = match.group(4)
            
            # 解答・解説をspanタグから外す（必要に応じて）
            answer_clean = re.sub(r'<span style="font-size: 100%;">', '', answer_section)
            answer_clean = re.sub(r'</span>', '', answer_clean)
            
            # 正しい構造に修正
            fixed = f'<div class="su-spoiler su-spoiler-style-default su-spoiler-icon-plus su-spoiler-closed" data-anchor-in-url="no" data-scroll-offset="0">{spoiler_title}<div class="su-spoiler-content su-u-clearfix su-u-trim su-spoiler-closed" style="display: none !important;">\n<p></p>\n{answer_clean}\n<p><span style="font-size: 100%;"></span></p></div></div>'
            
            return fixed
        
        # パターン2を適用
        content = re.sub(pattern2, fix_match2, content, flags=re.DOTALL)
        
        # さらに、pタグの中にdivがあるパターンを修正
        # <p><span><div>...</div></span></p> → <div>...</div>
        content = re.sub(r'<p><span[^>]*>(<div class="su-spoiler[^"]*"[^>]*>.*?</div>)</span></p>', r'\1', content, flags=re.DOTALL)
        
        if content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"  エラー: {e}")
        return False

if __name__ == "__main__":
    # すべてのHTMLファイルをチェック
    html_files = list(BASE_DIR.glob("*.html"))
    fixed_files = []
    
    for filepath in sorted(html_files):
        # 101-292_293.htmlは正しい例なのでスキップ
        if filepath.name == "101-292_293.html":
            continue
        
        # ファイルを読んで、spoiler-contentが空でその後に解答があるかチェック
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # パターンをチェック
            has_empty_spoiler = bool(re.search(r'<div class="su-spoiler-content[^>]*"[^>]*></div>', content))
            has_answer_outside = bool(re.search(r'<div class="su-spoiler-content[^>]*"[^>]*></div>.*?<p><span[^>]*><strong>解答</strong>', content, re.DOTALL))
            
            if has_empty_spoiler and has_answer_outside:
                print(f"修正中: {filepath.name}")
                if fix_spoiler_structure(filepath):
                    fixed_files.append(filepath.name)
                    print(f"  ✓ 修正完了")
                else:
                    print(f"  ⚠ 自動修正できませんでした（手動確認が必要）")
        except Exception as e:
            print(f"エラー ({filepath.name}): {e}")
    
    print(f"\n修正したファイル数: {len(fixed_files)}")
    for filename in fixed_files:
        print(f"  - {filename}")

