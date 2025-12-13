#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
post_contentの中身をそのまま取得してHTMLを作成する
"""

from bs4 import BeautifulSoup
import requests
import re
import os
from urllib.parse import quote
from pages import build_question_pages_dict, save_pages_dict, load_pages_dict


def get_question_url(exam_number, question_number):
    """回数と問番号からURLを生成"""
    base_url = "https://yakugakulab.info/"
    path = f"第{exam_number}回薬剤師国家試験　問{question_number}"
    encoded_path = quote(path, safe="")
    return base_url + encoded_path + "/"


def fetch_html_from_url(url):
    """URLからHTMLコンテンツを取得"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = "utf-8"
        html_content = response.text

        if html_content and len(html_content) > 0:
            print(f"  ✓ HTML取得成功 (サイズ: {len(html_content)} bytes)")
            return html_content
        else:
            print(f"  ✗ エラー: HTMLコンテンツが空です")
            return None
    except requests.exceptions.HTTPError as e:
        print(f"  ✗ HTTPエラー: {e.response.status_code} - {e}")
        return None
    except requests.exceptions.Timeout as e:
        print(f"  ✗ タイムアウトエラー: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  ✗ リクエストエラー: {e}")
        return None
    except Exception as e:
        print(f"  ✗ 予期しないエラー: {type(e).__name__} - {e}")
        return None


def extract_questions_250_251_from_url(url):
    """
    指定されたURL（第102回 問250〜251）から問250と問251の両方を確実に取得する専用関数
    
    Args:
        url: 取得するURL（例: https://yakugakulab.info/%e7%ac%ac102%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f250%e3%80%9c251/）
    
    Returns:
        tuple: (page_title, post_content_html) または None（エラー時）
    """
    print(f"\n[専用関数] 問250〜251を取得中: {url}")
    
    # HTMLを取得
    html_content = fetch_html_from_url(url)
    if not html_content:
        print(f"  ✗ エラー: HTMLを取得できませんでした")
        return None
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # タイトルを取得
    title_tag = soup.find("h1", class_="c-postTitle__ttl")
    if not title_tag:
        print(f"  ✗ エラー: タイトルが見つかりません")
        return None
    page_title = title_tag.get_text(strip=True)
    print(f"  タイトル: {page_title}")
    
    # post_contentクラス内のコンテンツを取得
    post_content = soup.find("div", class_="post_content")
    if not post_content:
        print(f"  ✗ エラー: post_contentが見つかりません")
        return None
    
    # 画像タグのsrc属性を修正
    for img in post_content.find_all("img"):
        if img.get("data-src"):
            img["src"] = img["data-src"]
        elif img.get("src") and img.get("src").startswith("./"):
            srcset = img.get("srcset", "")
            if srcset:
                first_url = srcset.split(",")[0].strip().split()[0]
                if first_url:
                    img["src"] = first_url
            elif img.get("data-src"):
                img["src"] = img["data-src"]
    
    # post_contentを文字列に変換
    post_content_str = str(post_content)
    
    # 問250と問251が含まれているか確認
    question_250_match = re.search(r'問250[^<]*<strong|問250[^<]*</strong>', post_content_str)
    question_251_match = re.search(r'問251[^<]*<strong|問251[^<]*</strong>', post_content_str)
    
    if not question_250_match:
        print(f"  ⚠ 警告: 問250が見つかりません")
    else:
        print(f"  ✓ 問250を検出")
    
    if not question_251_match:
        print(f"  ⚠ 警告: 問251が見つかりません")
    else:
        print(f"  ✓ 問251を検出")
    
    # su-spoiler-contentが空の場合、その直後の「解答」や「解説」を含む要素を移動
    # 複数問題に対応したパターン
    pattern1 = r'(<div[^>]*class="[^"]*su-spoiler-content[^"]*"[^>]*>)\s*</div>(\s*</div>\s*</span>\s*</p>\s*<p[^>]*>.*?(?:解答|解説).*?</p>(?:\s*<p[^>]*>.*?</p>)*?)(?=<div[^>]*class="[^"]*su-spoiler[^"]*"[^>]*>|問\d+[^<]*<strong|<!--Ads|</div>\s*</div>\s*</div>\s*$)'
    pattern2 = r'(<div[^>]*class="[^"]*su-spoiler-content[^"]*"[^>]*>)\s*<p></p>\s*</div>(\s*</div>\s*</p>\s*<p[^>]*>.*?(?:解答|解説).*?</p>(?:\s*<p[^>]*>.*?</p>)*?)(?=<div[^>]*class="[^"]*su-spoiler[^"]*"[^>]*>|問\d+[^<]*<strong|<!--Ads|</div>\s*</div>\s*</div>\s*$)'
    
    def move_content_to_spoiler(match):
        spoiler_content_start = match.group(1)
        content_to_move = match.group(2)
        content_cleaned = re.sub(r'</div>\s*</span>\s*</p>\s*', '', content_to_move)
        content_cleaned = re.sub(r'</div>\s*</p>\s*', '', content_cleaned)
        return spoiler_content_start + content_cleaned + "</div>"
    
    # 正規表現で置換（複数回マッチする可能性があるため、繰り返し処理）
    max_iterations = 10
    iteration = 0
    while iteration < max_iterations:
        new_str = re.sub(pattern1, move_content_to_spoiler, post_content_str, flags=re.DOTALL)
        new_str = re.sub(pattern2, move_content_to_spoiler, new_str, flags=re.DOTALL)
        if new_str == post_content_str:
            break
        post_content_str = new_str
        iteration += 1
    
    # 修正した文字列を再パース
    post_content = BeautifulSoup(post_content_str, "html.parser")
    if isinstance(post_content, BeautifulSoup):
        post_content = post_content.find("div", class_="post_content") or post_content
    
    # su-spoiler要素を初期状態（閉じた状態）にリセット
    for spoiler in post_content.find_all("div", class_=re.compile("su-spoiler")):
        classes = spoiler.get("class", [])
        if isinstance(classes, list):
            classes = [c for c in classes if c not in ["su-spoiler-open", "open"]]
            if "su-spoiler-closed" not in classes:
                classes.append("su-spoiler-closed")
            spoiler["class"] = classes
        
        content = spoiler.find("div", class_=re.compile("su-spoiler-content"))
        if content:
            existing_style = content.get("style", "")
            if "display" not in existing_style.lower():
                content["style"] = existing_style + ("; " if existing_style else "") + "display: none !important;"
            elif "display: none" not in existing_style.lower() and "display:none" not in existing_style.lower():
                content["style"] = re.sub(r'display\s*:\s*[^;]+', 'display: none !important', existing_style)
                if "display: none !important" not in content["style"]:
                    content["style"] = content["style"] + "; display: none !important;"
    
    # 最終確認: 問250と問251が含まれているか
    final_content_str = str(post_content)
    all_question_numbers = set(re.findall(r'<strong[^>]*>.*?問(\d+)', final_content_str, re.DOTALL))
    
    print(f"  検出された問題番号: {sorted([int(q) for q in all_question_numbers])}")
    print(f"  post_contentの長さ: {len(final_content_str)} 文字")
    
    if "250" in all_question_numbers and "251" in all_question_numbers:
        print(f"  ✓ 問250と問251の両方が含まれています")
    else:
        print(f"  ⚠ 警告: 問250と問251の両方が含まれていない可能性があります")
        if "250" not in all_question_numbers:
            print(f"    問250が見つかりません")
        if "251" not in all_question_numbers:
            print(f"    問251が見つかりません")
    
    return page_title, final_content_str


def extract_post_content(html_content, source_name="問題"):
    """HTMLコンテンツからpost_contentを抽出"""
    if not html_content:
        raise ValueError(f"HTMLコンテンツがNoneです: {source_name}")

    soup = BeautifulSoup(html_content, "html.parser")

    # タイトルを取得
    title_tag = soup.find("h1", class_="c-postTitle__ttl")
    if not title_tag:
        raise ValueError(
            f"予期しないHTML構造: タイトル（h1.c-postTitle__ttl）が見つかりません: {source_name}"
        )
    page_title = title_tag.get_text(strip=True)

    # post_contentクラス内のコンテンツを取得
    post_content = soup.find("div", class_="post_content")
    if not post_content:
        raise ValueError(
            f"予期しないHTML構造: post_contentクラスが見つかりません: {source_name}"
        )

    # 画像タグのsrc属性を修正（data-srcがあればそれを使用、相対パスの場合は絶対URLに変換）
    for img in post_content.find_all("img"):
        # data-srcがあれば、それをsrcに設定
        if img.get("data-src"):
            img["src"] = img["data-src"]
        # srcが相対パス（./で始まる）の場合、srcsetから最初のURLを取得
        elif img.get("src") and img.get("src").startswith("./"):
            # srcsetから最初のURLを取得
            srcset = img.get("srcset", "")
            if srcset:
                # srcsetの形式: "url1 size1, url2 size2, ..."
                first_url = srcset.split(",")[0].strip().split()[0]
                if first_url:
                    img["src"] = first_url
            # srcsetがない場合はdata-srcを確認
            elif img.get("data-src"):
                img["src"] = img["data-src"]

    # su-spoiler-contentが空の場合、その直後の「解答」や「解説」を含む要素を移動
    # まず、post_contentを文字列に変換して処理
    post_content_str = str(post_content)
    
    # su-spoiler-contentが空の場合、その直後の要素を移動するパターン
    # 複数問題に対応: 各su-spoiler-contentごとに処理
    # パターン1: </div></span></p>の後に<p><span><strong>解答</strong>などがある場合（従来のパターン）
    # パターン2: </div></p>の後に<p><span><strong>解答</strong>などがある場合（新しいパターン）
    # 次のsu-spoiler、問***、またはpost_contentの終わりまで
    pattern1 = r'(<div[^>]*class="[^"]*su-spoiler-content[^"]*"[^>]*>)\s*</div>(\s*</div>\s*</span>\s*</p>\s*<p[^>]*>.*?(?:解答|解説).*?</p>(?:\s*<p[^>]*>.*?</p>)*?)(?=<div[^>]*class="[^"]*su-spoiler[^"]*"[^>]*>|問\d+[^<]*<strong|<!--Ads|</div>\s*</div>\s*</div>\s*$)'
    pattern2 = r'(<div[^>]*class="[^"]*su-spoiler-content[^"]*"[^>]*>)\s*<p></p>\s*</div>(\s*</div>\s*</p>\s*<p[^>]*>.*?(?:解答|解説).*?</p>(?:\s*<p[^>]*>.*?</p>)*?)(?=<div[^>]*class="[^"]*su-spoiler[^"]*"[^>]*>|問\d+[^<]*<strong|<!--Ads|</div>\s*</div>\s*</div>\s*$)'
    
    def move_content_to_spoiler(match):
        spoiler_content_start = match.group(1)
        content_to_move = match.group(2)
        # 移動するコンテンツから、su-spoilerの終了タグ部分を除去
        # </div></span></p>または</div></p>の部分を除去し、<p>以降の内容のみを取得
        content_cleaned = re.sub(r'</div>\s*</span>\s*</p>\s*', '', content_to_move)
        content_cleaned = re.sub(r'</div>\s*</p>\s*', '', content_cleaned)
        return spoiler_content_start + content_cleaned + "</div>"
    
    # 正規表現で置換（複数回マッチする可能性があるため、繰り返し処理）
    max_iterations = 10
    iteration = 0
    while iteration < max_iterations:
        new_str = re.sub(pattern1, move_content_to_spoiler, post_content_str, flags=re.DOTALL)
        new_str = re.sub(pattern2, move_content_to_spoiler, new_str, flags=re.DOTALL)
        if new_str == post_content_str:
            break
        post_content_str = new_str
        iteration += 1
    
    # 修正した文字列を再パース
    post_content = BeautifulSoup(post_content_str, "html.parser")
    if isinstance(post_content, BeautifulSoup):
        post_content = post_content.find("div", class_="post_content") or post_content
    
    # su-spoiler要素を初期状態（閉じた状態）にリセット
    
    # su-spoiler要素を初期状態（閉じた状態）にリセット
    for spoiler in post_content.find_all("div", class_=re.compile("su-spoiler")):
        # openクラスを削除して閉じた状態にする
        classes = spoiler.get("class", [])
        if isinstance(classes, list):
            # open関連のクラスを削除
            classes = [c for c in classes if c not in ["su-spoiler-open", "open"]]
            # closedクラスを追加（まだない場合）
            if "su-spoiler-closed" not in classes:
                classes.append("su-spoiler-closed")
            spoiler["class"] = classes
        
        # su-spoiler-contentを非表示にする
        content = spoiler.find("div", class_=re.compile("su-spoiler-content"))
        if content:
            # インラインスタイルで確実に非表示にする
            existing_style = content.get("style", "")
            if "display" not in existing_style.lower():
                content["style"] = existing_style + ("; " if existing_style else "") + "display: none !important;"
            elif "display: none" not in existing_style.lower() and "display:none" not in existing_style.lower():
                # displayが既にあるが、noneでない場合は上書き
                content["style"] = re.sub(r'display\s*:\s*[^;]+', 'display: none !important', existing_style)
                if "display: none !important" not in content["style"]:
                    content["style"] = content["style"] + "; display: none !important;"

    # 複数問題が含まれている場合、全ての問題が正しく含まれているか確認
    # post_content内の全ての「問***」を探す（strongタグ内、複数問題に対応）
    # パターン1: <strong>問***</strong>
    # パターン2: <strong>問***<br></strong>
    all_question_numbers = set(re.findall(r'<strong[^>]*>.*?問(\d+)', str(post_content), re.DOTALL))
    
    # デバッグ情報（必要に応じて）
    if len(all_question_numbers) > 1:
        print(f"    複数問題を検出: {sorted([int(q) for q in all_question_numbers])}")
        print(f"    post_contentの長さ: {len(str(post_content))} 文字")
    
    # post_content全体を返す（複数問題が含まれている場合は全て含まれる）
    # これにより、問250と問251の両方が含まれる
    return page_title, str(post_content)


def create_single_question_html(title, post_content_html, url):
    """単一問題用のHTMLを作成"""
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .question-block {{
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 40px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .question-title {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #4CAF50;
        }}
        .post-content {{
            font-size: 16px;
            color: #444;
        }}
        .post-content p {{
            margin: 15px 0;
        }}
        .post-content ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        .post-content li {{
            margin: 8px 0;
        }}
        .post-content img {{
            max-width: 100%;
            height: auto;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .post-content strong {{
            color: #2c3e50;
        }}
        .post-content a {{
            color: #4CAF50;
            text-decoration: none;
        }}
        .post-content a:hover {{
            text-decoration: underline;
        }}
        .question-title a {{
            color: #333;
            text-decoration: none;
        }}
        .question-title a:hover {{
            color: #4CAF50;
            text-decoration: underline;
        }}
        /* su-spoilerの簡易スタイルと挙動 */
        .su-spoiler {{
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            margin: 18px 0;
            background: #fafafa;
            overflow: hidden;
        }}
        .su-spoiler-title {{
            cursor: pointer;
            padding: 12px 14px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            color: #2c3e50;
            user-select: none;
        }}
        .su-spoiler-title:focus {{
            outline: 2px solid #4CAF50;
        }}
        .su-spoiler-icon {{
            width: 10px;
            height: 10px;
            border-left: 2px solid #4CAF50;
            border-bottom: 2px solid #4CAF50;
            transform: rotate(-45deg);
            transition: transform 0.15s ease-out;
            display: inline-block;
        }}
        .su-spoiler.open .su-spoiler-icon {{
            transform: rotate(135deg);
        }}
        .su-spoiler-content {{
            display: none !important;
            padding: 12px 14px 18px 14px;
            background: #fff;
            border-top: 1px solid #e0e0e0;
        }}
        .su-spoiler.open .su-spoiler-content {{
            display: block !important;
        }}
        /* 初期状態で確実に閉じる */
        .su-spoiler:not(.open) .su-spoiler-content {{
            display: none !important;
        }}
    </style>
</head>
<body>
    <div class="question-block">
        <div class="question-title"><a href="{url}" target="_blank">{title}</a></div>
        <div class="post-content">
{post_content_html}
        </div>
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', () => {{
        document.querySelectorAll('.su-spoiler').forEach(spoiler => {{
            const title = spoiler.querySelector('.su-spoiler-title');
            const content = spoiler.querySelector('.su-spoiler-content');

            if (!content) return;

            // 初期は確実に閉じる
            spoiler.classList.remove('su-spoiler-open', 'open');
            spoiler.classList.add('su-spoiler-closed');
            // インラインスタイルで確実に非表示にする
            content.style.setProperty('display', 'none', 'important');

            const toggle = () => {{
                const isOpen = spoiler.classList.toggle('open');
                spoiler.classList.toggle('su-spoiler-closed', !isOpen);
                spoiler.classList.toggle('su-spoiler-open', isOpen);
                if (isOpen) {{
                    content.style.setProperty('display', 'block', 'important');
                }} else {{
                    content.style.setProperty('display', 'none', 'important');
                }}
            }};

            if (title) {{
                title.addEventListener('click', (e) => {{
                    e.preventDefault();
                    e.stopPropagation();
                    toggle();
                }});
                title.addEventListener('keydown', (e) => {{
                    if (e.key === 'Enter' || e.key === ' ') {{
                        e.preventDefault();
                        e.stopPropagation();
                        toggle();
                    }}
                }});
                // フォーカスできるように
                if (!title.hasAttribute('tabindex')) {{
                    title.setAttribute('tabindex', '0');
                }}
            }} else {{
                // titleがない場合はspoiler全体をクリック可能にする
                spoiler.style.cursor = 'pointer';
                spoiler.addEventListener('click', (e) => {{
                    e.preventDefault();
                    e.stopPropagation();
                    toggle();
                }});
            }}
        }});
    }});
    </script>
</body>
</html>
"""
    return html


def main():
    import os
    templates_dir = "/Users/diabolo/dev/temp/tonao/templates"
    pages_file = "/Users/diabolo/dev/temp/tonao/yakugaku-251212/question_pages.json"

    # templatesディレクトリが存在しない場合は作成
    os.makedirs(templates_dir, exist_ok=True)

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
        # 必要に応じて追加
    }

    # ページ辞書を読み込む
    pages = load_pages_dict(pages_file)

    # 不足している回数のページを構築
    missing_exams = [exam for exam in questions_to_fetch.keys() if exam not in pages]
    if missing_exams:
        print(f"不足している回数のページを構築中: {missing_exams}")
        new_pages = build_question_pages_dict(missing_exams)
        pages.update(new_pages)
        save_pages_dict(pages, pages_file)

    def get_question_url_from_pages(exam_number, question_number):
        """pages辞書からURLを取得、なければ生成"""
        if exam_number in pages and question_number in pages[exam_number]:
            return pages[exam_number][question_number]
        else:
            return get_question_url(exam_number, question_number)

    # URLごとに問題をグループ化
    # 構造: {url: [(exam_number, question_number, title, post_content_html, url), ...]}
    url_groups = {}
    success_count = 0
    failure_count = 0

    print("問題を取得中...")
    print("=" * 60)

    for exam_number, question_numbers in questions_to_fetch.items():
        for question_number in question_numbers:
            print(f"\n第{exam_number}回 問{question_number} を処理中...")

            try:
                # URLを取得
                url = get_question_url_from_pages(exam_number, question_number)
                print(f"  URL: {url}")

                # HTMLを取得
                html_content = fetch_html_from_url(url)
                if not html_content:
                    print(f"  ✗ スキップ: HTMLを取得できませんでした")
                    failure_count += 1
                    continue

                # post_contentを抽出
                try:
                    page_title, post_content_html = extract_post_content(
                        html_content,
                        source_name=f"第{exam_number}回問{question_number}",
                    )
                    
                    title = f"第{exam_number}回 問{question_number}"
                    
                    # URLごとにグループ化
                    # 同じURLの場合は、最初の1回だけHTMLを取得して、そのpost_content_htmlを共有
                    if url not in url_groups:
                        url_groups[url] = {
                            'post_content_html': post_content_html,
                            'exam_number': exam_number,
                            'questions': [],
                            'url': url
                        }
                    
                    # 問題番号を追加
                    url_groups[url]['questions'].append((exam_number, question_number, title))
                    print(f"  ✓ 抽出成功: {title}")
                    success_count += 1

                except ValueError as e:
                    print(f"  ✗ エラー: {e}")
                    failure_count += 1
                    continue
                except Exception as e:
                    print(f"  ✗ 予期しないエラー: {type(e).__name__} - {e}")
                    failure_count += 1
                    continue

            except Exception as e:
                print(f"  ✗ 予期しないエラー: {type(e).__name__} - {e}")
                failure_count += 1
                continue

    # 統計情報を表示
    total_count = success_count + failure_count
    print(f"\n{'='*60}")
    print(f"処理結果:")
    print(f"  成功: {success_count}問")
    print(f"  失敗: {failure_count}問")
    print(f"  合計: {total_count}問")
    print(f"{'='*60}")

    if not url_groups:
        print("\n✗ エラー: 取得できた問題がありませんでした。")
        return

    # 各URLグループごとにファイルを作成
    print(f"\nHTMLファイルを生成中...")
    file_count = 0
    
    # 複数問題ページで問題が正しく反映されなかったものを記録
    failed_multi_question_pages = []
    
    for url, group_data in url_groups.items():
        post_content_html = group_data['post_content_html']
        exam_number = group_data['exam_number']
        questions = group_data['questions']
        url = group_data.get('url', url)
        
        # 問題番号をソート
        questions_sorted = sorted(questions, key=lambda x: x[1])  # question_numberでソート
        
        # タイトルとファイル名を生成
        if len(questions_sorted) == 1:
            # 単一問題
            _, question_number, title = questions_sorted[0]
            filename = f"{exam_number}-{question_number}.html"
        else:
            # 複数問題（同じURL）
            question_numbers = [q[1] for q in questions_sorted]
            question_numbers_str = "、".join([f"問{q}" for q in question_numbers])
            title = f"第{exam_number}回 {question_numbers_str}"
            filename = f"{exam_number}-{'_'.join([str(q) for q in question_numbers])}.html"
            
            # 複数問題の場合、post_content_htmlに全ての問題が含まれているか確認
            # HTML内の「問***」パターンを探して、必要な問題番号が全て含まれているか確認
            import re
            # strongタグ内の「問***」を探す（より正確なパターン）
            found_questions = set(re.findall(r'<strong[^>]*>.*?問(\d+)', post_content_html, re.DOTALL))
            expected_questions = set(str(q) for q in question_numbers)
            
            # 不足している問題がある場合、警告を表示してデバッグ情報を出力
            missing_questions = expected_questions - found_questions
            if missing_questions:
                print(f"  ⚠ 警告: {filename} に以下の問題が含まれていません: {', '.join(['問' + q for q in sorted(missing_questions)])}")
                print(f"     見つかった問題: {', '.join(['問' + q for q in sorted(found_questions)])}")
                print(f"     期待される問題: {', '.join(['問' + q for q in sorted(expected_questions)])}")
                print(f"     post_content_htmlの長さ: {len(post_content_html)} 文字")
                # デバッグ: post_content_htmlの一部を表示
                if '問' + sorted(missing_questions)[0] in post_content_html:
                    print(f"     ⚠ 注意: 問{sorted(missing_questions)[0]}は文字列として存在しますが、strongタグ内に見つかりませんでした")
                
                # 失敗した複数問題ページの情報を記録
                failed_multi_question_pages.append({
                    'exam_number': exam_number,
                    'expected_questions': sorted([int(q) for q in expected_questions]),
                    'found_questions': sorted([int(q) for q in found_questions]),
                    'missing_questions': sorted([int(q) for q in missing_questions]),
                    'url': url,
                    'filename': filename
                })
        
        filepath = os.path.join(templates_dir, filename)
        
        # HTMLを作成
        html_content = create_single_question_html(title, post_content_html, url)
        
        # ファイルに保存
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"  ✓ {filename} を作成しました")
            file_count += 1
        except Exception as e:
            print(f"  ✗ エラー: {filename} の保存に失敗しました - {type(e).__name__}: {e}")
            continue
    
    print(f"\n✓ 成功: {file_count}個のHTMLファイルを作成しました")
    print(f"  保存先: {templates_dir}")
    
    # 複数問題ページで問題が正しく反映されなかったものを.txtファイルに出力
    if failed_multi_question_pages:
        output_file = os.path.join(os.path.dirname(templates_dir), "failed_multi_question_pages.txt")
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("複数問題ページで問題が正しく反映されなかったもの\n")
                f.write("=" * 80 + "\n\n")
                for i, item in enumerate(failed_multi_question_pages, 1):
                    f.write(f"{i}. 第{item['exam_number']}回\n")
                    f.write(f"   期待される問題: {', '.join(['問' + str(q) for q in item['expected_questions']])}\n")
                    f.write(f"   見つかった問題: {', '.join(['問' + str(q) for q in item['found_questions']])}\n")
                    f.write(f"   不足している問題: {', '.join(['問' + str(q) for q in item['missing_questions']])}\n")
                    f.write(f"   ファイル名: {item['filename']}\n")
                    f.write(f"   URL: {item['url']}\n")
                    f.write("\n")
            print(f"\n⚠ 警告: {len(failed_multi_question_pages)}件の複数問題ページで問題が正しく反映されませんでした")
            print(f"   詳細は {output_file} を確認してください")
        except Exception as e:
            print(f"\n✗ エラー: 失敗情報の出力に失敗しました - {type(e).__name__}: {e}")
    else:
        print(f"\n✓ 全ての複数問題ページで問題が正しく反映されました")
    
    # 全てのHTMLファイルを順番に読み込むインデックスHTMLを作成
    create_index_html(templates_dir)


def create_index_html(templates_dir):
    """templatesディレクトリ内の全てのHTMLファイルを順番に読み込むHTMLを作成"""
    import glob
    from bs4 import BeautifulSoup
    
    # templatesディレクトリ内の全てのHTMLファイルを取得（index.htmlを除く）
    html_files = [f for f in glob.glob(os.path.join(templates_dir, "*.html")) 
                  if os.path.basename(f) != "index.html"]
    
    if not html_files:
        print("\n⚠ 警告: templatesディレクトリにHTMLファイルが見つかりませんでした")
        return
    
    # ファイル名から順番を決定（回数と問番号でソート）
    def get_sort_key(filepath):
        filename = os.path.basename(filepath)
        # ファイル名の形式: {exam_number}-{question_number(s)}.html
        match = re.match(r"(\d+)-(.+)\.html", filename)
        if match:
            exam_number = int(match.group(1))
            question_part = match.group(2)
            # 複数問題の場合は最初の問番号を使用
            first_question = int(question_part.split('_')[0])
            return (exam_number, first_question)
        return (9999, 9999)  # パースできない場合は最後に
    
    html_files_sorted = sorted(html_files, key=get_sort_key)
    
    # 各HTMLファイルからbodyの内容を抽出
    question_sections = []
    for filepath in html_files_sorted:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, "html.parser")
            body = soup.find("body")
            if body:
                # question-blockの内容を取得
                question_block = body.find("div", class_="question-block")
                if question_block:
                    question_sections.append(str(question_block))
                else:
                    # question-blockがない場合はbody全体を使用
                    question_sections.append(body.decode_contents())
        except Exception as e:
            print(f"  ⚠ 警告: {os.path.basename(filepath)} の読み込みに失敗しました - {e}")
            continue
    
    # インデックスHTMLを作成
    index_html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>過去問まとめ - 全問題</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .question-block {
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 40px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .question-title {
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #4CAF50;
        }
        .post-content {
            font-size: 16px;
            color: #444;
        }
        .post-content p {
            margin: 15px 0;
        }
        .post-content ol {
            margin: 15px 0;
            padding-left: 30px;
        }
        .post-content li {
            margin: 8px 0;
        }
        .post-content img {
            max-width: 100%;
            height: auto;
            margin: 15px 0;
            border-radius: 4px;
        }
        .post-content strong {
            color: #2c3e50;
        }
        .post-content a {
            color: #4CAF50;
            text-decoration: none;
        }
        .post-content a:hover {
            text-decoration: underline;
        }
        .question-title a {
            color: #333;
            text-decoration: none;
        }
        .question-title a:hover {
            color: #4CAF50;
            text-decoration: underline;
        }
        /* su-spoilerの簡易スタイルと挙動 */
        .su-spoiler {
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            margin: 18px 0;
            background: #fafafa;
            overflow: hidden;
        }
        .su-spoiler-title {
            cursor: pointer;
            padding: 12px 14px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            color: #2c3e50;
            user-select: none;
        }
        .su-spoiler-title:focus {
            outline: 2px solid #4CAF50;
        }
        .su-spoiler-icon {
            width: 10px;
            height: 10px;
            border-left: 2px solid #4CAF50;
            border-bottom: 2px solid #4CAF50;
            transform: rotate(-45deg);
            transition: transform 0.15s ease-out;
            display: inline-block;
        }
        .su-spoiler.open .su-spoiler-icon {
            transform: rotate(135deg);
        }
        .su-spoiler-content {
            display: none !important;
            padding: 12px 14px 18px 14px;
            background: #fff;
            border-top: 1px solid #e0e0e0;
        }
        .su-spoiler.open .su-spoiler-content {
            display: block !important;
        }
        /* 初期状態で確実に閉じる */
        .su-spoiler:not(.open) .su-spoiler-content {
            display: none !important;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>過去問まとめ - 全問題</h1>
    </div>
    <div class="container">
""" + "\n".join(question_sections) + """
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.su-spoiler').forEach(spoiler => {
            const title = spoiler.querySelector('.su-spoiler-title');
            const content = spoiler.querySelector('.su-spoiler-content');

            if (!content) return;

            // 初期は確実に閉じる
            spoiler.classList.remove('su-spoiler-open', 'open');
            spoiler.classList.add('su-spoiler-closed');
            // インラインスタイルで確実に非表示にする
            content.style.setProperty('display', 'none', 'important');

            const toggle = () => {
                const isOpen = spoiler.classList.toggle('open');
                spoiler.classList.toggle('su-spoiler-closed', !isOpen);
                spoiler.classList.toggle('su-spoiler-open', isOpen);
                if (isOpen) {
                    content.style.setProperty('display', 'block', 'important');
                } else {
                    content.style.setProperty('display', 'none', 'important');
                }
            };

            if (title) {
                title.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    toggle();
                });
                title.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        e.stopPropagation();
                        toggle();
                    }
                });
                // フォーカスできるように
                if (!title.hasAttribute('tabindex')) {
                    title.setAttribute('tabindex', '0');
                }
            } else {
                // titleがない場合はspoiler全体をクリック可能にする
                spoiler.style.cursor = 'pointer';
                spoiler.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    toggle();
                });
            }
        });
    });
    </script>
</body>
</html>
"""
    
    # インデックスHTMLを保存（templatesと同じ階層のhtmlディレクトリに保存）
    html_dir = os.path.join(os.path.dirname(templates_dir), "html")
    os.makedirs(html_dir, exist_ok=True)
    index_file = os.path.join(html_dir, "index.html")
    
    try:
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(index_html)
        print(f"\n✓ インデックスHTMLを作成しました")
        print(f"  保存先: {index_file}")
        print(f"  読み込んだファイル数: {len(question_sections)}")
    except Exception as e:
        print(f"\n✗ エラー: インデックスHTMLの保存に失敗しました - {type(e).__name__}: {e}")


def test_extract_250_251():
    """問250〜251を取得する専用関数のテスト"""
    url = "https://yakugakulab.info/%e7%ac%ac102%e5%9b%9e%e8%96%ac%e5%89%a4%e5%b8%ab%e5%9b%bd%e5%ae%b6%e8%a9%a6%e9%a8%93%e3%80%80%e5%95%8f250%e3%80%9c251/"
    result = extract_questions_250_251_from_url(url)
    if result:
        page_title, post_content_html = result
        print(f"\n✓ 取得成功")
        print(f"  タイトル: {page_title}")
        print(f"  コンテンツ長: {len(post_content_html)} 文字")
        
        # 問250と問251が含まれているか最終確認
        import re
        questions = set(re.findall(r'<strong[^>]*>.*?問(\d+)', post_content_html, re.DOTALL))
        print(f"  含まれている問題: {sorted([int(q) for q in questions])}")
        
        return result
    else:
        print(f"\n✗ 取得失敗")
        return None


if __name__ == "__main__":
    # テスト用: 問250〜251の専用関数をテスト
    # test_extract_250_251()
    
    # main()
    create_index_html("/Users/diabolo/dev/temp/tonao/templates")
