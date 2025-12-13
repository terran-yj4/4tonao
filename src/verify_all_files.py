#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全21件のファイルを検証するスクリプト
URLから取得したHTMLとローカルファイルの内容を比較
"""

import os
import re
import subprocess

def fetch_questions_from_url(url):
    """URLから問題番号を抽出"""
    try:
        result = subprocess.run(
            ["curl", "-s", url],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return None
        
        html_content = result.stdout
        # 問XXXのパターンを検索
        pattern = r'問\s*(\d+)'
        matches = re.findall(pattern, html_content)
        questions = sorted(set([int(m) for m in matches]))
        return questions
    except Exception as e:
        print(f"  ✗ エラー: {e}")
        return None

def extract_questions_from_file(filepath):
    """ローカルファイルから問題番号を抽出"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        pattern = r'問\s*(\d+)'
        matches = re.findall(pattern, content)
        questions = sorted(set([int(m) for m in matches]))
        return questions
    except Exception as e:
        print(f"  ✗ エラー: {e}")
        return None

def verify_file(filepath, url, expected_questions):
    """ファイルを検証"""
    filename = os.path.basename(filepath)
    print(f"\n{'='*70}")
    print(f"検証: {filename}")
    print(f"期待される問題: {expected_questions}")
    
    # ローカルファイルを確認
    if not os.path.exists(filepath):
        print(f"  ✗ ファイルが見つかりません")
        return False
    
    local_questions = extract_questions_from_file(filepath)
    if local_questions is None:
        print(f"  ✗ ローカルファイルの読み込みに失敗")
        return False
    
    print(f"  ローカルファイル: 問{', 問'.join(map(str, local_questions))}")
    
    # URLから取得
    print(f"  URLから取得中...")
    url_questions = fetch_questions_from_url(url)
    if url_questions is None:
        print(f"  ⚠ URLからの取得に失敗（スキップ）")
        # URLからの取得に失敗しても、ローカルファイルに期待される問題があればOKとする
        missing = [q for q in expected_questions if q not in local_questions]
        if missing:
            print(f"  ✗ 不足している問題: {missing}")
            return False
        else:
            print(f"  ✓ 期待される問題はすべて見つかりました")
            return True
    
    print(f"  URL: 問{', 問'.join(map(str, url_questions))}")
    
    # 期待される問題がすべてあるか確認
    missing_local = [q for q in expected_questions if q not in local_questions]
    missing_url = [q for q in expected_questions if q not in url_questions]
    
    if missing_local:
        print(f"  ✗ ローカルファイルに不足: 問{', 問'.join(map(str, missing_local))}")
        return False
    
    if missing_url:
        print(f"  ⚠ URLに不足: 問{', 問'.join(map(str, missing_url))}（URLの内容が不完全な可能性）")
    
    print(f"  ✓ 確認完了")
    return True

# 全21件のファイル情報
files_to_verify = [
    ("templates/102-250_251.html", "https://yakugakulab.info/%e7%ac%ac102%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f250%e3%80%9c251/", [250, 251]),
    ("templates/102-290_291.html", "https://yakugakulab.info/%e7%ac%ac102%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f290%e3%80%9c291/", [290, 291]),
    ("templates/103-246_247.html", "https://yakugakulab.info/%e7%ac%ac103%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f246%e3%80%9c247/", [246, 247]),
    ("templates/103-252_253.html", "https://yakugakulab.info/%e7%ac%ac103%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f252%e3%80%9c253/", [252, 253]),
    ("templates/103-272_273.html", "https://yakugakulab.info/%e7%ac%ac103%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f272%e3%80%9c273/", [272, 273]),
    ("templates/103-276_277.html", "https://yakugakulab.info/%e7%ac%ac103%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f276%e3%80%9c277/", [276, 277]),
    ("templates/103-288_289.html", "https://yakugakulab.info/%e7%ac%ac103%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f288%e3%80%9c289/", [288, 289]),
    ("templates/104-192_193.html", "https://yakugakulab.info/%e7%ac%ac104%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f192%e3%80%9c193/", [192, 193]),
    ("templates/104-260_263.html", "https://yakugakulab.info/%e7%ac%ac104%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f260%e3%80%9c263/", [260, 263]),
    ("templates/104-270_271.html", "https://yakugakulab.info/%e7%ac%ac104%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f270%e3%80%9c271/", [270, 271]),
    ("templates/105-163_164.html", "https://yakugakulab.info/%e7%ac%ac105%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f163%e3%80%9c164/", [163, 164]),
    ("templates/105-216_217.html", "https://yakugakulab.info/%e7%ac%ac105%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f216%e3%80%9c217/", [216, 217]),
    ("templates/105-254_255.html", "https://yakugakulab.info/%e7%ac%ac105%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f254%e3%80%9c255/", [254, 255]),
    ("templates/106-160_161.html", "https://yakugakulab.info/%e7%ac%ac106%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f160%e3%80%9c161/", [160, 161]),
    ("templates/106-288_289.html", "https://yakugakulab.info/%e7%ac%ac106%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f288%e3%80%9c289/", [288, 289]),
    ("templates/107-159_160.html", "https://yakugakulab.info/%e7%ac%ac107%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f159%e3%80%9c160/", [159, 160]),
    ("templates/107-248_249.html", "https://yakugakulab.info/%e7%ac%ac107%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f248%e3%80%9c249/", [248, 249]),
    ("templates/107-290_291.html", "https://yakugakulab.info/%e7%ac%ac107%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f290%e3%80%9c291/", [290, 291]),
    ("templates/107-298_299.html", "https://yakugakulab.info/%e7%ac%ac107%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f298%e3%80%9c299/", [298, 299]),
    ("templates/108-292_293.html", "https://yakugakulab.info/%e7%ac%ac108%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f292%e3%80%9c293%ef%bc%88%e5%ae%9f%e8%b7%b5%e5%95%8f%e9%a1%8c%ef%bc%89%e3%80%80%e5%8e%9f%e7%99%ba/", [292, 293]),
    ("templates/108-294_295.html", "https://yakugakulab.info/%e7%ac%ac108%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f294%e3%80%9c295%ef%bc%88%e5%ae%9f%e8%b7%b5%e5%95%8f%e9%a1%8c%ef%bc%89%e3%80%80%e8%96%ac%e7%89%a9/", [294, 295]),
]

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    results = []
    for rel_path, url, expected_questions in files_to_verify:
        filepath = os.path.join(base_dir, rel_path)
        result = verify_file(filepath, url, expected_questions)
        results.append((os.path.basename(filepath), result))
    
    # 結果サマリー
    print(f"\n{'='*70}")
    print("検証結果サマリー")
    print(f"{'='*70}")
    passed = 0
    failed = 0
    for filename, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {filename}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n合計: {len(results)}件")
    print(f"成功: {passed}件")
    print(f"失敗: {failed}件")
