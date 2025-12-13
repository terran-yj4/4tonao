#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
問題ページのURLを探索して辞書にまとめる
"""

from bs4 import BeautifulSoup
import requests
from urllib.parse import quote, urljoin, unquote
import re
import time


def get_category_url(exam_number):
    """回数のカテゴリページURLを生成"""
    base_url = "https://yakugakulab.info/"
    path = f"第{exam_number}回薬剤師国家試験"
    encoded_path = quote(path, safe="")
    return base_url + "category/" + encoded_path + "/"


def fetch_html_from_url(url):
    """URLからHTMLコンテンツを取得"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = "utf-8"
        return response.text
    except Exception as e:
        print(f"  エラー: URLからHTMLを取得できませんでした - {e}")
        return None


def extract_question_numbers_from_url(url):
    """URLから問題番号を抽出（例：問292〜293 や 問57）"""
    # URLをデコードして問題番号を探す
    question_numbers = []
    
    # URLをデコード
    try:
        decoded_url = unquote(url)
    except:
        decoded_url = url
    
    # パターン1: 問292〜293 のような範囲（全角チルダ）
    range_pattern = r"問(\d+)〜(\d+)"
    match = re.search(range_pattern, decoded_url)
    if match:
        start = int(match.group(1))
        end = int(match.group(2))
        question_numbers = list(range(start, end + 1))
    else:
        # パターン2: 問292-293 のような範囲（ハイフン）
        range_pattern2 = r"問(\d+)[-－](\d+)"
        match = re.search(range_pattern2, decoded_url)
        if match:
            start = int(match.group(1))
            end = int(match.group(2))
            question_numbers = list(range(start, end + 1))
        else:
            # パターン3: 問57 のような単一
            single_pattern = r"問(\d+)"
            match = re.search(single_pattern, decoded_url)
            if match:
                question_numbers = [int(match.group(1))]
    
    return question_numbers


def find_question_pages_in_category(category_url, exam_number):
    """カテゴリページから問題ページを探す"""
    print(f"  カテゴリページを取得: {category_url}")
    html_content = fetch_html_from_url(category_url)
    if not html_content:
        return {}
    
    soup = BeautifulSoup(html_content, "html.parser")
    question_pages = {}
    
    # 記事へのリンクを探す
    # 通常、記事は <a> タグでリンクされている
    links = soup.find_all("a", href=True)
    
    for link in links:
        href = link.get("href", "")
        if not href:
            continue
        
        # 絶対URLに変換
        full_url = urljoin("https://yakugakulab.info/", href)
        
        # タイトルテキストを取得
        link_text = link.get_text(strip=True)
        
        # URLから問題番号を抽出
        question_numbers = extract_question_numbers_from_url(full_url)
        
        # タイトルからも問題番号を抽出（URLに含まれていない場合がある）
        if not question_numbers:
            question_numbers = extract_question_numbers_from_url(link_text)
        
        if question_numbers:
            # 第X回を含むか、または問題ページのURLパターンに一致するか
            if f"第{exam_number}回" in link_text or f"問" in link_text or f"第{exam_number}回" in full_url:
                for q_num in question_numbers:
                    if q_num not in question_pages:  # 既に登録されていない場合のみ
                        question_pages[q_num] = full_url
                        if len(question_numbers) > 1:
                            print(f"    見つかった: 問{question_numbers[0]}〜{question_numbers[-1]} -> {full_url}")
                        else:
                            print(f"    見つかった: 問{q_num} -> {full_url}")
    
    return question_pages


def find_all_question_pages(exam_number):
    """指定された回数のすべての問題ページを探索"""
    print(f"\n第{exam_number}回の問題ページを探索中...")
    
    # カテゴリページのURLを取得
    category_url = get_category_url(exam_number)
    print(f"カテゴリURL: {category_url}")
    
    # カテゴリページから問題ページを探す
    question_pages = find_question_pages_in_category(category_url, exam_number)
    
    # ページネーションがある場合、すべてのページを探索
    # まず、最初のページから次のページへのリンクを探す
    html_content = fetch_html_from_url(category_url)
    if html_content:
        soup = BeautifulSoup(html_content, "html.parser")
        # ページネーションリンクを探す
        pagination_links = soup.find_all("a", href=re.compile(r"page/\d+"))
        max_page = 1
        for link in pagination_links:
            href = link.get("href", "")
            page_match = re.search(r"page/(\d+)", href)
            if page_match:
                page_num = int(page_match.group(1))
                if page_num > max_page:
                    max_page = page_num
        
        # 見つかったすべてのページを探索
        for page_num in range(2, max_page + 1):
            next_url = f"{category_url}page/{page_num}/"
            next_pages = find_question_pages_in_category(next_url, exam_number)
            if next_pages:
                question_pages.update(next_pages)
            time.sleep(0.5)  # サーバー負荷を考慮
    
    print(f"  見つかった問題ページ数: {len(question_pages)}")
    return question_pages


def build_question_pages_dict(exam_numbers):
    """複数の回数の問題ページを探索して辞書にまとめる"""
    pages = {}
    
    for exam_number in exam_numbers:
        print(f"\n{'='*60}")
        print(f"第{exam_number}回を処理中...")
        question_pages = find_all_question_pages(exam_number)
        pages[exam_number] = question_pages
        
        # 少し待機（サーバー負荷を考慮）
        time.sleep(1)
    
    return pages


def save_pages_dict(pages, filepath="question_pages.json"):
    """問題ページの辞書をJSONファイルに保存"""
    import json
    # キーを文字列に変換して保存（JSONはキーを文字列にする必要がある）
    pages_str = {}
    for exam_num, question_pages in pages.items():
        pages_str[str(exam_num)] = {str(k): v for k, v in question_pages.items()}
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(pages_str, f, ensure_ascii=False, indent=2)
    print(f"\n問題ページの辞書を保存しました: {filepath}")


def load_pages_dict(filepath="question_pages.json"):
    """JSONファイルから問題ページの辞書を読み込む"""
    import json
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            pages_str = json.load(f)
            # キーを整数に変換
            pages = {}
            for exam_num_str, question_pages_str in pages_str.items():
                pages[int(exam_num_str)] = {int(k): v for k, v in question_pages_str.items()}
            return pages
    except FileNotFoundError:
        return {}


if __name__ == "__main__":
    # テスト: 第101回の問題ページを探索
    exam_numbers = [101]
    pages = build_question_pages_dict(exam_numbers)
    
    print(f"\n{'='*60}")
    print("結果:")
    for exam_num, question_pages in pages.items():
        print(f"\n第{exam_num}回: {len(question_pages)}問")
        # 最初の10問と最後の10問を表示
        sorted_keys = sorted(question_pages.keys())
        for q_num in sorted_keys[:10]:
            print(f"  問{q_num}: {question_pages[q_num]}")
        if len(sorted_keys) > 20:
            print(f"  ... ({len(sorted_keys) - 20}問省略) ...")
        for q_num in sorted_keys[-10:]:
            print(f"  問{q_num}: {question_pages[q_num]}")
    
    # 保存
    save_pages_dict(pages, "question_pages.json")
