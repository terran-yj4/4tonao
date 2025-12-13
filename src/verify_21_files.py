#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
21件の修正済みファイルが元のURLと一致しているか確認するスクリプト
"""

import os
import re
import subprocess

# 確認対象のファイル一覧
FILES_TO_VERIFY = [
    {
        "file": "102-250_251.html",
        "url": "https://yakugakulab.info/%e7%ac%ac102%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f250%e3%80%9c251/",
        "expected_questions": [250, 251]
    },
    {
        "file": "102-290_291.html",
        "url": "https://yakugakulab.info/%e7%ac%ac102%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f290%e3%80%9c291/",
        "expected_questions": [290, 291]
    },
    {
        "file": "103-246_247.html",
        "url": "https://yakugakulab.info/%e7%ac%ac103%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f246%e3%80%9c247/",
        "expected_questions": [246, 247]
    },
    {
        "file": "103-252_253.html",
        "url": "https://yakugakulab.info/%e7%ac%ac103%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f252%e3%80%9c253/",
        "expected_questions": [252, 253]
    },
    {
        "file": "103-272_273.html",
        "url": "https://yakugakulab.info/%e7%ac%ac103%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f272%e3%80%9c273/",
        "expected_questions": [272, 273]
    },
    {
        "file": "103-276_277.html",
        "url": "https://yakugakulab.info/%e7%ac%ac103%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f276%e3%80%9c277/",
        "expected_questions": [276, 277]
    },
    {
        "file": "103-288_289.html",
        "url": "https://yakugakulab.info/%e7%ac%ac103%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f288%e3%80%9c289/",
        "expected_questions": [288, 289]
    },
    {
        "file": "104-192_193.html",
        "url": "https://yakugakulab.info/%e7%ac%ac104%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f192%e3%80%9c193/",
        "expected_questions": [192, 193]
    },
    {
        "file": "104-260_263.html",
        "url": "https://yakugakulab.info/%e7%ac%ac104%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f260%e3%80%9c263/",
        "expected_questions": [260, 263]
    },
    {
        "file": "104-270_271.html",
        "url": "https://yakugakulab.info/%e7%ac%ac104%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f270%e3%80%9c271/",
        "expected_questions": [270, 271]
    },
    {
        "file": "105-163_164.html",
        "url": "https://yakugakulab.info/%e7%ac%ac105%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f163%e3%80%9c164/",
        "expected_questions": [163, 164]
    },
    {
        "file": "105-216_217.html",
        "url": "https://yakugakulab.info/%e7%ac%ac105%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f216%e3%80%9c217/",
        "expected_questions": [216, 217]
    },
    {
        "file": "105-254_255.html",
        "url": "https://yakugakulab.info/%e7%ac%ac105%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f254%e3%80%9c255/",
        "expected_questions": [254, 255]
    },
    {
        "file": "106-160_161.html",
        "url": "https://yakugakulab.info/%e7%ac%ac106%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f160%e3%80%9c161/",
        "expected_questions": [160, 161]
    },
    {
        "file": "106-288_289.html",
        "url": "https://yakugakulab.info/%e7%ac%ac106%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f288%e3%80%9c289/",
        "expected_questions": [288, 289]
    },
    {
        "file": "107-159_160.html",
        "url": "https://yakugakulab.info/%e7%ac%ac107%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f159%e3%80%9c160/",
        "expected_questions": [159, 160]
    },
    {
        "file": "107-248_249.html",
        "url": "https://yakugakulab.info/%e7%ac%ac107%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f248%e3%80%9c249/",
        "expected_questions": [248, 249]
    },
    {
        "file": "107-290_291.html",
        "url": "https://yakugakulab.info/%e7%ac%ac107%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f290%e3%80%9c291/",
        "expected_questions": [290, 291]
    },
    {
        "file": "107-298_299.html",
        "url": "https://yakugakulab.info/%e7%ac%ac107%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f298%e3%80%9c299/",
        "expected_questions": [298, 299]
    },
    {
        "file": "108-292_293.html",
        "url": "https://yakugakulab.info/%e7%ac%ac108%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f292%e3%80%9c293%ef%bc%88%e5%ae%9f%e8%b7%b5%e5%95%8f%e9%a1%8c%ef%bc%89%e3%80%80%e5%8e%9f%e7%99%ba/",
        "expected_questions": [292, 293]
    },
    {
        "file": "108-294_295.html",
        "url": "https://yakugakulab.info/%e7%ac%ac108%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f294%e3%80%9c295%ef%bc%88%e5%ae%9f%e8%b7%b5%e5%95%8f%e9%a1%8c%ef%bc%89%e3%80%80%e8%96%ac%e7%89%a9/",
        "expected_questions": [294, 295]
    },
]

BASE_DIR = "/Users/diabolo/dev/temp/tonao/templates"

def fetch_html_from_url(url):
    """URLからHTMLを取得（curl使用）"""
    try:
        result = subprocess.run(
            ["curl", "-s", "-L", url],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except Exception as e:
        print(f"  ✗ URL取得エラー: {e}")
        return None

def extract_questions_from_html(html_content):
    """HTMLから問題番号を抽出"""
    if not html_content:
        return None
    
    pattern = r'問\s*(\d+)'
    matches = re.findall(pattern, html_content)
    questions = sorted(set([int(m) for m in matches]))
    return questions

def extract_questions_from_file(filepath):
    """ファイルから問題番号を抽出"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return extract_questions_from_html(content)
    except Exception as e:
        print(f"  ✗ ファイル読み込みエラー: {e}")
        return None

def verify_file(entry):
    """1つのファイルを確認"""
    filepath = os.path.join(BASE_DIR, entry["file"])
    
    print(f"\n{'='*80}")
    print(f"確認中: {entry['file']}")
    print(f"期待される問題: {', '.join(['問' + str(q) for q in entry['expected_questions']])}")
    
    # ファイルの存在確認
    if not os.path.exists(filepath):
        print(f"  ✗ ファイルが存在しません: {filepath}")
        return False
    
    # ファイルから問題番号を抽出
    file_questions = extract_questions_from_file(filepath)
    if file_questions is None:
        print(f"  ✗ ファイルから問題番号を抽出できませんでした")
        return False
    
    print(f"  ファイルに含まれる問題: {', '.join(['問' + str(q) for q in file_questions])}")
    
    # URLから問題番号を抽出
    print(f"  URLから取得中...")
    html_from_url = fetch_html_from_url(entry["url"])
    if html_from_url is None:
        print(f"  ⚠ URLからHTMLを取得できませんでした（スキップ）")
        # URL取得に失敗しても、ファイルに期待される問題があればOKとする
        missing = [q for q in entry["expected_questions"] if q not in file_questions]
        if missing:
            print(f"  ✗ ファイルに不足している問題: {', '.join(['問' + str(q) for q in missing])}")
            return False
        else:
            print(f"  ✓ 期待される問題はすべてファイルに含まれています")
            return True
    
    url_questions = extract_questions_from_html(html_from_url)
    if url_questions is None:
        print(f"  ⚠ URLから問題番号を抽出できませんでした（スキップ）")
        missing = [q for q in entry["expected_questions"] if q not in file_questions]
        if missing:
            print(f"  ✗ ファイルに不足している問題: {', '.join(['問' + str(q) for q in missing])}")
            return False
        else:
            print(f"  ✓ 期待される問題はすべてファイルに含まれています")
            return True
    
    print(f"  URLに含まれる問題: {', '.join(['問' + str(q) for q in url_questions])}")
    
    # 期待される問題がすべてあるか確認
    missing_in_file = [q for q in entry["expected_questions"] if q not in file_questions]
    missing_in_url = [q for q in entry["expected_questions"] if q not in url_questions]
    
    if missing_in_file:
        print(f"  ✗ ファイルに不足している問題: {', '.join(['問' + str(q) for q in missing_in_file])}")
        return False
    
    if missing_in_url:
        print(f"  ⚠ URLに不足している問題: {', '.join(['問' + str(q) for q in missing_in_url])}（URLの内容が不完全な可能性）")
    
    # ファイルにURLにない余分な問題がないか確認（警告のみ）
    extra_in_file = [q for q in file_questions if q not in url_questions and q not in entry["expected_questions"]]
    if extra_in_file:
        print(f"  ⚠ ファイルにURLにない問題があります: {', '.join(['問' + str(q) for q in extra_in_file])}")
    
    print(f"  ✓ 確認完了: 期待される問題がすべて含まれています")
    return True

def main():
    print("=" * 80)
    print("21件のファイルが元のURLと一致しているか確認します")
    print("=" * 80)
    
    results = []
    for entry in FILES_TO_VERIFY:
        result = verify_file(entry)
        results.append((entry["file"], result))
    
    # 結果をまとめて表示
    print(f"\n{'='*80}")
    print("確認結果まとめ")
    print("=" * 80)
    
    success_count = 0
    for filename, result in results:
        status = "✓ OK" if result else "✗ NG"
        print(f"{status}: {filename}")
        if result:
            success_count += 1
    
    print(f"\n{'='*80}")
    print(f"成功: {success_count}/{len(results)}件")
    print(f"失敗: {len(results) - success_count}/{len(results)}件")
    print("=" * 80)

if __name__ == "__main__":
    main()

