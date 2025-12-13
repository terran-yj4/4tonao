#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
templatesディレクトリ内のHTMLファイルで、questions_to_fetchに含まれていない問題番号を
(範囲外)問***に変更する
"""

import os
import re
import glob

# 取得する問題のリスト（辞書形式: {回数: [問番号のリスト]}）
questions_to_fetch = {
    101: [57, 182, 185, 200, 292, 293, 329],
    102: [57, 192, 250, 251, 290, 291, 304, 305, 324, 332],
    103: [68, 246, 247, 252, 253, 272, 273, 276, 277, 288, 289, 343],
    104: [56, 58, 60, 192, 193, 198, 208, 214, 252, 253, 260, 263, 270, 271, 314, 334],
    105: [56, 63, 163, 164, 185, 187, 216, 217, 254, 255, 329, 338, 339],
    106: [159, 160, 161, 185, 288, 289],
    107: [159, 160, 248, 249, 252, 253, 290, 291, 298, 299, 318, 324, 326, 344],
    108: [157, 159, 185, 186, 202, 252, 258, 292, 293, 294, 295, 297],
    109: [61, 160, 165, 166, 188, 220, 221, 254, 255, 290, 292, 293],
    110: [56, 58, 59, 111, 156, 157, 158, 197, 211, 254, 255, 292, 312],
}

templates_dir = "/Users/diabolo/dev/temp/tonao/templates"

def extract_question_numbers_from_filename(filename):
    """ファイル名から問題番号を抽出"""
    # 例: 101-200.html -> (101, [200])
    # 例: 102-250_251.html -> (102, [250, 251])
    match = re.match(r"(\d+)-(.+)\.html", filename)
    if match:
        exam_number = int(match.group(1))
        question_part = match.group(2)
        # 複数問題の場合は分割
        question_numbers = [int(q) for q in question_part.split('_')]
        return exam_number, question_numbers
    return None, []

def find_question_numbers_in_html(html_content, exam_number):
    """HTMLコンテンツ内のstrongタグから問題番号を抽出"""
    question_numbers = []
    
    # strongタグ内の「問***」パターンを探す
    pattern = r'<strong[^>]*>.*?問(\d+)'
    matches = re.findall(pattern, html_content)
    for match in matches:
        question_num = int(match)
        question_numbers.append(question_num)
    
    return question_numbers

def fix_out_of_range_questions(filepath, exam_number, valid_question_numbers):
    """範囲外の問題番号を(範囲外)問***に変更"""
    with open(filepath, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    modified = False
    modifications = []
    original_content = html_content
    
    # まず、既に「(範囲外)」が付いている場合は除去（重複を防ぐため）
    html_content = re.sub(r'\(範囲外\)\(範囲外\)', '(範囲外)', html_content)
    html_content = re.sub(r'\(範囲外\)問(\d+)', r'問\1', html_content)
    
    # strongタグ内の「問***」を探して修正（文字列レベルで処理）
    # パターン: <strong>問*** または <strong>...問***...（<br/>などのタグを含む可能性がある）
    # より柔軟なパターン: <strong>から</strong>までの間で「問数字」を探す
    pattern = r'(<strong[^>]*>)(.*?)(問(\d+))([^<]*(?:<[^>]+>[^<]*)*?)(</strong>)'
    
    def replace_question(match):
        nonlocal modified, modifications
        strong_open = match.group(1)
        before_text = match.group(2)
        question_match = match.group(3)  # 「問数字」の部分
        question_num = int(match.group(4))
        after_text = match.group(5)
        strong_close = match.group(6)
        
        # 範囲外の問題番号の場合（既に(範囲外)が付いていない場合のみ）
        if question_num not in valid_question_numbers and '(範囲外)' not in before_text:
            modified = True
            modifications.append(f"  問{question_num} → (範囲外)問{question_num}")
            # 「問***」を「(範囲外)問***」に置換
            return f"{strong_open}{before_text}(範囲外){question_match}{after_text}{strong_close}"
        else:
            # 変更なし
            return match.group(0)
    
    # 正規表現で置換（DOTALLフラグで改行もマッチ）
    new_content = re.sub(pattern, replace_question, html_content, flags=re.DOTALL)
    
    if modified:
        # ファイルを保存
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True, modifications
    return False, []

def main():
    # templatesディレクトリ内の全てのHTMLファイルを取得（過去問まとめ.htmlを除く）
    html_files = [f for f in glob.glob(os.path.join(templates_dir, "*.html"))
                  if os.path.basename(f) != "過去問まとめ.html"]
    
    print("範囲外の問題番号を修正中...")
    print("=" * 60)
    
    modified_files = []
    total_modifications = 0
    
    for filepath in sorted(html_files):
        filename = os.path.basename(filepath)
        exam_number, file_question_numbers = extract_question_numbers_from_filename(filename)
        
        if exam_number is None:
            continue
        
        # この回数の有効な問題番号を取得
        valid_question_numbers = set(questions_to_fetch.get(exam_number, []))
        
        # HTML内の全ての問題番号を抽出
        with open(filepath, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        html_question_numbers = find_question_numbers_in_html(html_content, exam_number)
        
        # 範囲外の問題番号があるか確認
        out_of_range = [q for q in html_question_numbers if q not in valid_question_numbers]
        
        if out_of_range:
            print(f"\n{filename}:")
            print(f"  範囲外の問題番号: {out_of_range}")
            
            # 修正を実行
            modified, modifications = fix_out_of_range_questions(filepath, exam_number, valid_question_numbers)
            
            if modified:
                modified_files.append((filename, modifications))
                total_modifications += len(modifications)
                print(f"  ✓ 修正完了")
                for mod in modifications:
                    print(mod)
    
    # 結果を表示
    print(f"\n{'='*60}")
    print(f"処理結果:")
    print(f"  修正したファイル数: {len(modified_files)}")
    print(f"  修正した問題数: {total_modifications}")
    print(f"{'='*60}")
    
    if modified_files:
        print("\n修正したファイル一覧:")
        for filename, modifications in modified_files:
            print(f"\n{filename}:")
            for mod in modifications:
                print(mod)

if __name__ == "__main__":
    main()

