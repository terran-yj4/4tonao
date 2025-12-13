#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
21件のファイルの内容が元のURLと一致しているか詳細に確認するスクリプト
問題文、選択肢、解答、解説の内容を比較
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

def normalize_text(text):
    """テキストを正規化（比較用）"""
    if not text:
        return ""
    # 連続する空白を1つに統一
    text = re.sub(r'\s+', ' ', text)
    # 前後の空白を削除
    text = text.strip()
    return text

def extract_question_content(post_content_html, question_number):
    """指定された問題番号の内容を抽出"""
    if not post_content_html:
        return None
    
    # 問題番号のパターン（より柔軟に）
    patterns = [
        rf"問\s*{question_number}\s*[（\(]",
        rf"問\s*{question_number}\s*",
        rf"問{question_number}[（\(]",
        rf"問{question_number}",
    ]
    
    match = None
    start_pos = None
    
    for pattern in patterns:
        match = re.search(pattern, post_content_html)
        if match:
            start_pos = match.start()
            break
    
    if not match:
        # テキストのみで検索を試す
        text = remove_html_tags(post_content_html)
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # テキストでの位置をHTMLでの位置に変換するのは困難なので、
                # テキストベースで処理
                start_pos_text = match.start()
                # 次の問題番号を探す
                next_pattern = rf"問\s*\d+"
                next_match = re.search(next_pattern, text[start_pos_text + 5:])
                if next_match:
                    question_text = text[start_pos_text:start_pos_text + 5 + next_match.start()]
                else:
                    question_text = text[start_pos_text:]
                return normalize_text(question_text)
        return None
    
    # HTMLのまま抽出
    text_after_html = post_content_html[start_pos:]
    
    # 次の問題番号を探す
    next_patterns = [
        rf"問\s*\d+[^0-9]",  # 数字の後に非数字
        rf"問\s*\d+",  # 数字のみ
    ]
    
    next_match = None
    for pattern in next_patterns:
        next_match = re.search(pattern, text_after_html[10:])  # 少し進めてから探す
        if next_match:
            break
    
    if next_match:
        # 次の問題が見つかった場合、その前まで
        end_pos = start_pos + 10 + next_match.start()
        question_html = post_content_html[start_pos:end_pos]
    else:
        # 次の問題が見つからない場合、終端まで
        question_html = post_content_html[start_pos:]
    
    # HTMLタグを除去してテキストを取得
    question_text = remove_html_tags(question_html)
    
    return normalize_text(question_text)

def extract_post_content_from_html(html_content):
    """HTMLからpost_contentを抽出（正規表現使用）"""
    # <div class="post_content">...</div>を抽出
    # より柔軟なパターンで試す
    patterns = [
        r'<div\s+class=["\']post_content["\'][^>]*>(.*?)</div>\s*</div>',  # </div></div>で終わる
        r'<div\s+class=["\']post_content["\'][^>]*>(.*?)(?=<div\s+class|<script|</body|$)',
        r'<div\s+class=["\']post_content["\'][^>]*>(.*?)</div>\s*(?=<div|</body|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.DOTALL)
        if match:
            content = match.group(1)
            # 問251のような数字が含まれているか確認（デバッグ用）
            return content
    
    # パターンが見つからない場合は全体を返す
    return html_content

def extract_post_content_from_file(filepath):
    """ファイルからpost_contentを抽出（正規表現使用）"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # <div class="post_content">...</div>を抽出
        pattern = r'<div\s+class=["\']post_content["\'][^>]*>(.*?)</div>\s*(?=<div|</body|$)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1)
        
        return content
    except Exception as e:
        print(f"  ✗ ファイル読み込みエラー: {e}")
        return None

def remove_html_tags(text):
    """HTMLタグを除去してテキストのみを取得"""
    # 基本的なHTMLタグを削除
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    # HTMLエンティティをデコード（基本的なもののみ）
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    return text

def compare_question_content(url_content, file_content, question_number):
    """問題の内容を比較"""
    url_q = extract_question_content(url_content, question_number)
    file_q = extract_question_content(file_content, question_number)
    
    if not url_q:
        return None, "URLから問題を抽出できません"
    
    if not file_q:
        return False, "ファイルから問題を抽出できません"
    
    # 文字列の類似度を簡易的にチェック
    # 最初の500文字を比較（問題文の重要な部分）
    url_preview = url_q[:500] if len(url_q) > 500 else url_q
    file_preview = file_q[:500] if len(file_q) > 500 else file_q
    
    # 解答・解説のキーワードが含まれているか
    url_has_answer = "解答" in url_q or "正解" in url_q or "答え" in url_q
    file_has_answer = "解答" in file_q or "正解" in file_q or "答え" in file_q
    
    url_has_explanation = "解説" in url_q
    file_has_explanation = "解説" in file_q
    
    # 選択肢のパターン（1) 2) など）が含まれているか
    url_has_options = bool(re.search(r'[1-5]\)', url_q))
    file_has_options = bool(re.search(r'[1-5]\)', file_q))
    
    issues = []
    
    if not file_has_answer and url_has_answer:
        issues.append("解答が見つかりません")
    
    if not file_has_explanation and url_has_explanation:
        issues.append("解説が見つかりません")
    
    if not file_has_options and url_has_options:
        issues.append("選択肢が見つかりません")
    
    # 長さが大きく異なる場合は警告
    length_ratio = len(file_q) / len(url_q) if len(url_q) > 0 else 0
    if length_ratio < 0.7:
        issues.append(f"内容が短すぎます（URLの{length_ratio*100:.1f}%）")
    elif length_ratio > 1.5:
        issues.append(f"内容が長すぎます（URLの{length_ratio*100:.1f}%）")
    
    if issues:
        return False, "; ".join(issues)
    
    # 最初の部分が一致しているか（問題文の最初の部分）
    if url_preview[:200] != file_preview[:200]:
        # 完全一致しない場合は、主要キーワードが含まれているかチェック
        # URLの最初の200文字から主要な単語を抽出
        url_words = set(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+', url_preview[:200]))
        file_words = set(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+', file_preview[:200]))
        
        common_words = url_words & file_words
        if len(common_words) < len(url_words) * 0.5:
            return False, "問題文の内容が大きく異なります"
    
    return True, "内容が一致しています"

def verify_file(entry):
    """1つのファイルの内容を詳細に確認"""
    filepath = os.path.join(BASE_DIR, entry["file"])
    
    print(f"\n{'='*80}")
    print(f"詳細確認中: {entry['file']}")
    print(f"期待される問題: {', '.join(['問' + str(q) for q in entry['expected_questions']])}")
    
    # ファイルの存在確認
    if not os.path.exists(filepath):
        print(f"  ✗ ファイルが存在しません")
        return False
    
    # URLからpost_contentを取得
    html_from_url = fetch_html_from_url(entry["url"])
    if html_from_url is None:
        print(f"  ✗ URLからHTMLを取得できませんでした")
        return False
    
    post_content_from_url = extract_post_content_from_html(html_from_url)
    if post_content_from_url is None:
        print(f"  ✗ URLからpost_contentを抽出できませんでした")
        return False
    
    # ファイルからpost_contentを取得
    post_content_from_file = extract_post_content_from_file(filepath)
    if post_content_from_file is None:
        print(f"  ✗ ファイルからpost_contentを抽出できませんでした")
        return False
    
    # 各問題の内容を確認
    all_ok = True
    for q_num in entry["expected_questions"]:
        print(f"\n  【問{q_num}の確認】")
        is_match, message = compare_question_content(
            post_content_from_url,
            post_content_from_file,
            q_num
        )
        
        if is_match is None:
            print(f"    ⚠ {message}")
        elif is_match:
            print(f"    ✓ {message}")
        else:
            print(f"    ✗ {message}")
            all_ok = False
    
    return all_ok

def main():
    print("=" * 80)
    print("21件のファイルの内容が元のURLと一致しているか詳細に確認します")
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

