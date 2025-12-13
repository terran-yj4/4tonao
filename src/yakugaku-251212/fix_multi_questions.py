#!/usr/bin/env python3
"""
複数問題ページの不足している問題を追加するスクリプト
"""
import os
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup
import requests

# プロジェクトルートのパス
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# 修正対象のファイルとURLのマッピング
TARGET_FILES = [
    {
        "file": "103-252_253.html",
        "url": "https://yakugakulab.info/%e7%ac%ac103%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f252%e3%80%9c253/",
        "missing": "問253"
    },
    # 他のファイルも追加...
]


def fetch_html(url):
    """URLからHTMLを取得"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"  ✗ エラー: HTML取得失敗 - {e}")
        return None


def extract_post_content(html_content):
    """HTMLからpost_contentを抽出"""
    soup = BeautifulSoup(html_content, "html.parser")
    post_content = soup.find("div", class_="post_content")
    if not post_content:
        return None
    
    # 画像タグの簡略化
    for img in post_content.find_all("img"):
        # hrefからURLを取得（親のaタグから）
        parent_a = img.find_parent("a")
        if parent_a and parent_a.get("href"):
            img_url = parent_a["href"]
            # 画像URLを直接srcに設定
            if img_url and not img_url.startswith("http"):
                # 相対URLの場合は、data-srcまたはsrcsetから取得を試みる
                if img.get("data-src"):
                    img_url = img["data-src"]
                elif img.get("srcset"):
                    first_url = img["srcset"].split(",")[0].strip().split()[0]
                    if first_url:
                        img_url = first_url
            if img_url.startswith("http"):
                img["src"] = img_url
        
        # 不要な属性を削除
        for attr in ["data-src", "data-srcset", "srcset", "sizes", "data-aspectratio", "decoding", "class", "lazyload", "lazyloaded"]:
            if attr in img.attrs:
                del img.attrs[attr]
        
        # noscriptタグを削除
        noscript = img.find_parent("noscript")
        if noscript:
            noscript.decompose()
    
    return str(post_content)


def extract_missing_question(post_content_html, question_number):
    """指定された問題番号の内容を抽出"""
    soup = BeautifulSoup(post_content_html, "html.parser")
    
    # 問題番号のパターン（問253など）
    pattern = f"問{question_number}"
    
    # すべてのpタグとolタグを検索
    elements = soup.find_all(["p", "ol", "div"])
    
    question_start = None
    question_end = None
    
    for i, elem in enumerate(elements):
        text = elem.get_text()
        if pattern in text and question_start is None:
            question_start = i
        elif question_start is not None:
            # 次の問題が見つかったら終了
            if "問" in text and pattern not in text:
                question_end = i
                break
    
    if question_start is None:
        return None
    
    # 問題部分を抽出
    if question_end is None:
        question_end = len(elements)
    
    question_elements = elements[question_start:question_end]
    
    # HTMLに変換
    result = ""
    for elem in question_elements:
        result += str(elem)
    
    return result


def fix_file(file_path, url, missing_question_number):
    """ファイルを修正"""
    print(f"\n処理中: {file_path.name}")
    print(f"  URL: {url}")
    print(f"  不足: {missing_question_number}")
    
    # HTMLを取得
    html_content = fetch_html(url)
    if not html_content:
        print(f"  ✗ スキップ: HTML取得失敗")
        return False
    
    # post_contentを抽出
    post_content = extract_post_content(html_content)
    if not post_content:
        print(f"  ✗ スキップ: post_content抽出失敗")
        return False
    
    # 不足している問題を抽出
    missing_content = extract_missing_question(post_content, missing_question_number)
    if not missing_content:
        print(f"  ✗ スキップ: {missing_question_number}の抽出失敗")
        return False
    
    # 既存ファイルを読み込み
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
    
    # 修正（既存のpost_contentの最後に追加）
    # </div>で終わるpost_contentの前に追加
    pattern = r'(<p><span style="font-size: 100%;"></span></p></div>\s*</div>\s*</div>)'
    
    # 修正前の内容を確認
    if missing_question_number in file_content:
        print(f"  ✓ 既に含まれているようです")
        return True
    
    # <!--Ads2-->の後に追加するパターンを探す
    ads_pattern = r'(<!--Ads2-->)'
    if re.search(ads_pattern, file_content):
        replacement = f'\\1\n<p><span style="font-size: 100%;"></span></p>{missing_content}'
        file_content = re.sub(ads_pattern, replacement, file_content)
    else:
        # post_contentの終了タグの前に追加
        replacement = f'<p><span style="font-size: 100%;"><!--Ads2--></span></p>\n{missing_content}\\1'
        file_content = re.sub(pattern, replacement, file_content, count=1)
    
    # ファイルを保存
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(file_content)
    
    print(f"  ✓ 修正完了")
    return True


def main():
    """メイン処理"""
    print("=" * 60)
    print("複数問題ページの修正")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for target in TARGET_FILES:
        file_path = TEMPLATES_DIR / target["file"]
        if not file_path.exists():
            print(f"\n✗ ファイルが見つかりません: {target['file']}")
            fail_count += 1
            continue
        
        if fix_file(file_path, target["url"], target["missing"]):
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n{'='*60}")
    print(f"処理結果:")
    print(f"  成功: {success_count}件")
    print(f"  失敗: {fail_count}件")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

