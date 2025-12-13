#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTMLファイルから問題、解答、解説を抽出してシンプルなHTMLを作成する
"""

from bs4 import BeautifulSoup
import os
import re
import requests
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

        # 正常に取得できたかを確認
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


def extract_multiple_questions(html_content, source_name="問題"):
    """HTMLコンテンツから複数の問題を抽出（同じページに複数の問題がある場合に対応）"""
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

    # 問題番号を抽出（タイトルから、例：問292〜293 や 問192〜193）
    question_numbers = []
    if "問" in page_title:
        # 範囲パターン: 問292〜293
        range_match = re.search(r"問(\d+)〜(\d+)", page_title)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2))
            question_numbers = list(range(start, end + 1))
        else:
            # 単一パターン: 問57
            single_match = re.search(r"問(\d+)", page_title)
            if single_match:
                question_numbers = [int(single_match.group(1))]

    # 共通の問題文（症例など）を最初に取得
    common_context = ""
    first_p = post_content.find("p")
    if first_p:
        first_text = first_p.get_text(strip=True)
        if not re.search(r"問(\d+)", first_text):
            common_context = str(first_p)
    
    # すべての「問XXX」という見出しを探す
    question_sections = []
    
    # post_content内のすべてのpタグを取得（解答・解説セクションを除く）
    all_ps = []
    for p in post_content.find_all("p"):
        # 解答・解説セクション内の要素は除外
        if not p.find_parent("div", class_=re.compile("su-spoiler")):
            all_ps.append(p)
    
    current_question_num = None
    current_question_html = ""
    current_choices = []
    
    i = 0
    while i < len(all_ps):
        p = all_ps[i]
        p_text = p.get_text(strip=True)
        
        # 「問XXX」という見出しを探す
        question_match = re.search(r"問(\d+)", p_text)
        if question_match:
            # 前の問題を保存
            if current_question_num is not None:
                question_sections.append({
                    "question_number": current_question_num,
                    "question_html": current_question_html,
                    "choices": current_choices,
                    "answer_html": "",
                    "explanation_html": "",
                    "common_context": common_context
                })
            
            # 新しい問題を開始
            current_question_num = int(question_match.group(1))
            current_question_html = str(p)  # 「問XXX」を含むpタグも含める
            current_choices = []
            
            # このpタグの直後のolタグを探す
            next_sibling = p.find_next_sibling()
            while next_sibling:
                if next_sibling.name == "ol":
                    for li in next_sibling.find_all("li"):
                        span = li.find("span")
                        if span:
                            current_choices.append(span.get_text(strip=True))
                        else:
                            # spanがない場合はliのテキストを直接取得
                            current_choices.append(li.get_text(strip=True))
                    break
                # 次の「問XXX」を含むpタグが見つかったら終了
                if next_sibling.name == "p":
                    next_text = next_sibling.get_text(strip=True)
                    if re.search(r"問(\d+)", next_text):
                        break
                next_sibling = next_sibling.find_next_sibling()
            
            # この見出しの後のpタグを取得（次の「問XXX」まで）
            j = i + 1
            while j < len(all_ps):
                next_p = all_ps[j]
                next_text = next_p.get_text(strip=True)
                
                # 次の「問XXX」が見つかったら終了
                if re.search(r"問(\d+)", next_text):
                    break
                
                # 問題文として追加
                current_question_html += str(next_p)
                j += 1
        else:
            # 通常のpタグ（問題文の一部）
            if current_question_num is not None:
                current_question_html += str(p)
            # 共通コンテキストとして保存（最初の「問XXX」より前）
            elif not question_sections and not current_question_num:
                common_context += str(p)
        
        i += 1
    
    # 最後の問題を保存
    if current_question_num is not None:
        question_sections.append({
            "question_number": current_question_num,
            "question_html": current_question_html,
            "choices": current_choices,
            "answer_html": "",
            "explanation_html": "",
            "common_context": common_context
        })
    
    # 解答・解説を取得（spoiler-contentクラス内、複数ある場合に対応）
    all_spoiler_contents = post_content.find_all("div", class_="su-spoiler-content")
    if not all_spoiler_contents:
        raise ValueError(
            f"予期しないHTML構造: 解答・解説（div.su-spoiler-content）が見つかりません: {source_name}"
        )
    
    # 各問題の解答・解説を抽出
    # 各解答・解説セクションを順番に処理（問題の順番に対応）
    for q_index, spoiler_content in enumerate(all_spoiler_contents):
        if q_index >= len(question_sections):
            break
        
        section = question_sections[q_index]
        spoiler_ps = spoiler_content.find_all("p")
        
        # このセクション内の解答・解説を抽出
        for p in spoiler_ps:
            p_text = p.get_text(strip=True)
            
            # 空のpタグはスキップ
            if not p_text or p_text.strip() == "":
                continue
            
            # 解答を探す
            if "解答" in p_text:
                if not section["answer_html"]:
                    section["answer_html"] = str(p)
                else:
                    section["answer_html"] += "\n" + str(p)
            
            # 解説を探す
            elif "解説" in p_text:
                if not section["explanation_html"]:
                    section["explanation_html"] = str(p)
                else:
                    section["explanation_html"] += "\n" + str(p)
            
            # 解答・解説の内容を追加（「解答」「解説」という見出しの後の内容）
            elif section["answer_html"] or section["explanation_html"]:
                # 既に解答がある場合は解説に追加
                if section["answer_html"] and not section["explanation_html"]:
                    # 次の「解説」が見つかるまで待つ
                    pass
                elif section["explanation_html"]:
                    # 解説に追加
                    section["explanation_html"] += "\n" + str(p)
                elif section["answer_html"]:
                    # 解答に追加（「解答」の後の数値など）
                    section["answer_html"] += "\n" + str(p)
    
    # 結果を返す
    results = []
    for section in question_sections:
        title = f"{page_title} 問{section['question_number']}"
        results.append((
            title,
            section["common_context"] + section["question_html"] if section["common_context"] else section["question_html"],
            section["choices"],
            section["answer_html"],
            section["explanation_html"]
        ))
    
    # 問題が見つからなかった場合、従来の方法で抽出
    if not results:
        return [extract_single_question(html_content, source_name)]
    
    return results


def extract_single_question(html_content, source_name="問題"):
    """HTMLコンテンツから1つの問題を抽出（従来の方法）"""
    if not html_content:
        raise ValueError(f"HTMLコンテンツがNoneです: {source_name}")

    soup = BeautifulSoup(html_content, "html.parser")

    # タイトルを取得
    title_tag = soup.find("h1", class_="c-postTitle__ttl")
    if not title_tag:
        raise ValueError(
            f"予期しないHTML構造: タイトル（h1.c-postTitle__ttl）が見つかりません: {source_name}"
        )
    title = title_tag.get_text(strip=True)

    # post_contentクラス内のコンテンツを取得
    post_content = soup.find("div", class_="post_content")
    if not post_content:
        raise ValueError(
            f"予期しないHTML構造: post_contentクラスが見つかりません: {source_name}"
        )

    # 問題文を取得（最初のpタグ、画像も含む）
    question_html = ""
    question_p = post_content.find("p")
    if not question_p:
        raise ValueError(
            f"予期しないHTML構造: 問題文（pタグ）が見つかりません: {source_name}"
        )

    # HTMLコンテンツをそのまま取得（画像タグも含む）
    question_html = str(question_p)
    # 画像のパスを修正（URLから取得した場合は元のURLを保持）
    # ローカルファイルの場合は相対パスを修正
    if "_files" in question_html and source_name.endswith(".html"):
        html_basename = os.path.basename(source_name).replace(".html", "")
        question_html = question_html.replace(
            f"./{html_basename}_files/", f"{html_basename}_files/"
        )
        question_html = question_html.replace(
            f'data-src="./{html_basename}_files/', f'data-src="{html_basename}_files/'
        )

    # 選択肢を取得（olタグ内のliタグ）
    choices = []
    ol_tag = post_content.find("ol")
    if ol_tag:
        for li in ol_tag.find_all("li"):
            span = li.find("span")
            if span:
                choices.append(span.get_text(strip=True))

    # 解答・解説を取得（spoiler-contentクラス内、画像も含む）
    answer_html = ""
    explanation_html = ""
    spoiler_content = post_content.find("div", class_="su-spoiler-content")
    if not spoiler_content:
        raise ValueError(
            f"予期しないHTML構造: 解答・解説（div.su-spoiler-content）が見つかりません: {source_name}"
        )

    # 解答を取得（HTMLとして）
    # 「解答」というstrongタグを含むpタグを探す
    for p in spoiler_content.find_all("p"):
        strong = p.find("strong")
        if strong:
            strong_text = strong.get_text(strip=True)
            if "解答" in strong_text:
                # 解答のpタグ全体をHTMLとして取得
                answer_html = str(p)
                # 画像のパスを修正（ローカルファイルの場合のみ）
                if source_name.endswith(".html"):
                    html_basename = os.path.basename(source_name).replace(".html", "")
                    answer_html = answer_html.replace(
                        f"./{html_basename}_files/", f"{html_basename}_files/"
                    )
                    answer_html = answer_html.replace(
                        f'data-src="./{html_basename}_files/',
                        f'data-src="{html_basename}_files/',
                    )
                break

    # 解答が見つからない場合、テキストから直接探す
    if not answer_html:
        spoiler_text = spoiler_content.get_text()
        if "解答" in spoiler_text:
            # 解答セクション全体を取得
            for p in spoiler_content.find_all("p"):
                p_text = p.get_text()
                if "解答" in p_text and len(p_text) > 2:  # 「解答」だけではない
                    answer_html = str(p)
                    break

    # 解説を取得（HTMLとして、「解説」というstrongタグの後のすべての内容）
    explanation_parts = []
    found_explanation = False
    for p in spoiler_content.find_all("p"):
        strong = p.find("strong")
        if strong and "解説" in strong.get_text():
            found_explanation = True
            # 解説のstrongタグと同じpタグ内のspanタグも取得
            explanation_parts.append(str(p))
            continue
        if found_explanation:
            # pタグ全体をHTMLとして取得
            explanation_parts.append(str(p))

    explanation_html = "\n".join(explanation_parts)
    # 画像のパスを修正（ローカルファイルの場合のみ）
    if source_name.endswith(".html"):
        html_basename = os.path.basename(source_name).replace(".html", "")
        explanation_html = explanation_html.replace(
            f"./{html_basename}_files/", f"{html_basename}_files/"
        )
        explanation_html = explanation_html.replace(
            f'data-src="./{html_basename}_files/', f'data-src="{html_basename}_files/'
        )

    # 解答または解説が取得できたか確認
    if not answer_html and not explanation_html:
        raise ValueError(
            f"予期しないHTML構造: 解答・解説の内容が抽出できませんでした: {source_name}"
        )

    return title, question_html, choices, answer_html, explanation_html


def extract_question_content(html_content, source_name="問題"):
    """HTMLコンテンツから問題を抽出（複数の問題がある場合は複数返す）"""
    # まず複数の問題を抽出を試みる
    try:
        results = extract_multiple_questions(html_content, source_name)
        # 複数の問題が見つかった場合
        if len(results) > 1:
            return results
        # 1つの問題のみの場合
        elif len(results) == 1:
            return results[0]
    except Exception as e:
        print(f"  警告: 複数問題の抽出に失敗、単一問題として処理: {e}")
    
    # フォールバック: 単一問題として抽出
    return extract_single_question(html_content, source_name)


def create_question_html(title, question_html, choices, answer_html, explanation_html):
    """1つの問題のHTMLを生成"""
    choices_list_html = ""
    for i, choice in enumerate(choices, 1):
        choices_list_html += f"            <li>{choice}</li>\n"

    # 問題文からテキスト部分を抽出（画像タグはそのまま残す）
    question_display = question_html if question_html else ""

    # 解答から「解答」というstrongタグを除いた内容を取得
    answer_display = answer_html if answer_html else ""
    if answer_display:
        # BeautifulSoupでパースして「解答」のstrongタグを除去
        from bs4 import BeautifulSoup

        answer_soup = BeautifulSoup(answer_display, "html.parser")
        strong_tags = answer_soup.find_all("strong", string=re.compile("解答"))
        for strong in strong_tags:
            strong.decompose()
        answer_display = str(answer_soup)

    # 解説から「解説」というstrongタグを除いた内容を取得
    explanation_display = explanation_html if explanation_html else ""
    if explanation_display:
        explanation_soup = BeautifulSoup(explanation_display, "html.parser")
        strong_tags = explanation_soup.find_all("strong", string=re.compile("解説"))
        for strong in strong_tags:
            strong.decompose()
        explanation_display = str(explanation_soup)

    question_block_html = f"""    <div class="question-block">
        <h2 class="question-title">{title}</h2>
        
        <div class="question">
            <div class="section-title">問題</div>
            <div class="question-content">{question_display}</div>
            {f'<ol class="choices">{choices_list_html.rstrip()}</ol>' if choices_list_html.strip() else ''}
        </div>
        
        <div class="accordion">
            <div class="accordion-header" onclick="toggleAccordion(this)">
                解答・解説
            </div>
            <div class="accordion-content">
                <div class="accordion-inner">
                    <div class="answer-section">
                        <div class="section-title">解答</div>
                        <div class="answer-content">{answer_display}</div>
                    </div>
                    <div class="explanation-section">
                        <div class="section-title">解説</div>
                        <div class="explanation-content">{explanation_display}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
"""
    return question_block_html


def create_simple_html(questions_data):
    """複数の問題を含むHTMLを作成"""
    questions_html = ""
    for data in questions_data:
        title, question_html, choices, answer_html, explanation_html = data
        questions_html += create_question_html(
            title, question_html, choices, answer_html, explanation_html
        )

    html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>薬剤師国家試験 過去問</title>
    <style>
        body {{
            font-family: "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        .question-block {{
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 2px dashed #ddd;
        }}
        .question-block:last-child {{
            border-bottom: none;
        }}
        .question-title {{
            color: #333;
            font-size: 1.3em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #4CAF50;
        }}
        .question {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .choices {{
            margin: 15px 0;
            padding-left: 20px;
        }}
        .choices li {{
            margin: 8px 0;
        }}
        .accordion {{
            margin: 20px 0;
            border-radius: 5px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .accordion-header {{
            background-color: #4CAF50;
            color: white;
            padding: 15px 20px;
            cursor: pointer;
            user-select: none;
            font-weight: bold;
            font-size: 1.1em;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background-color 0.15s;
        }}
        .accordion-header:hover {{
            background-color: #45a049;
        }}
        .accordion-header::after {{
            content: '▼';
            font-size: 0.8em;
            transition: transform 0.15s;
        }}
        .accordion-header.active::after {{
            transform: rotate(180deg);
        }}
        .accordion-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.15s ease-out;
            background-color: #f9f9f9;
        }}
        .accordion-content.active {{
            max-height: 2000px;
        }}
        .accordion-inner {{
            padding: 20px;
        }}
        .answer-section {{
            background-color: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
            border-left: 4px solid #4CAF50;
        }}
        .explanation-section {{
            background-color: #fff3e0;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #ff9800;
        }}
        .section-title {{
            font-weight: bold;
            font-size: 1.1em;
            color: #555;
            margin-bottom: 10px;
        }}
        .question-content, .answer-content, .explanation-content {{
            line-height: 1.6;
        }}
        .question-content img, .answer-content img, .explanation-content img {{
            max-width: 100%;
            height: auto;
            margin: 10px 0;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .question-content p, .answer-content p, .explanation-content p {{
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <h1>薬剤師国家試験 過去問</h1>
    
{questions_html}
    
    <script>
        function toggleAccordion(header) {{
            const content = header.nextElementSibling;
            const isActive = header.classList.contains('active');
            
            // 同じ問題ブロック内のアコーディオンのみを操作
            const questionBlock = header.closest('.question-block');
            const accordionsInBlock = questionBlock.querySelectorAll('.accordion-header');
            const contentsInBlock = questionBlock.querySelectorAll('.accordion-content');
            
            // 同じブロック内のアコーディオンを閉じる
            accordionsInBlock.forEach(h => {{
                h.classList.remove('active');
            }});
            contentsInBlock.forEach(c => {{
                c.classList.remove('active');
            }});
            
            // クリックされたアコーディオンを開く（閉じていた場合）
            if (!isActive) {{
                header.classList.add('active');
                content.classList.add('active');
            }}
        }}
    </script>
</body>
</html>"""

    return html_template.format(questions_html=questions_html)


def main():
    # 出力ファイルのパス
    output_file = "/Users/diabolo/dev/temp/tonao/html/過去問まとめ.html"
    pages_file = "/Users/diabolo/dev/temp/tonao/yakugaku-251212/question_pages.json"

    # 取得する問題のリスト（回数: [問番号のリスト]）
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

    # 問題ページの辞書を取得（既存のファイルがあれば読み込み、なければ探索）
    print("問題ページの辞書を取得中...")
    pages = load_pages_dict(pages_file)
    
    # 必要な回数のページが不足している場合は探索
    needed_exam_numbers = set(questions_to_fetch.keys())
    existing_exam_numbers = set(pages.keys())
    missing_exam_numbers = needed_exam_numbers - existing_exam_numbers
    
    if missing_exam_numbers:
        print(f"不足している回数を探索します: {sorted(missing_exam_numbers)}")
        new_pages = build_question_pages_dict(sorted(missing_exam_numbers))
        # 辞書のキーを文字列から整数に変換
        for exam_num in new_pages:
            pages[int(exam_num)] = {int(k): v for k, v in new_pages[exam_num].items()}
        save_pages_dict(pages, pages_file)
    
    # 問題ページの辞書からURLを取得する関数
    def get_question_url_from_pages(exam_number, question_number):
        """問題ページの辞書からURLを取得"""
        if exam_number in pages:
            # 文字列キーの場合と整数キーの場合の両方に対応
            exam_pages = pages[exam_number]
            if question_number in exam_pages:
                return exam_pages[question_number]
            # 文字列キーの場合
            if str(question_number) in exam_pages:
                return exam_pages[str(question_number)]
        # フォールバック: 従来の方法でURLを生成
        return get_question_url(exam_number, question_number)

    # 各問題をURLから取得
    questions_data = []
    success_count = 0
    failure_count = 0

    for exam_number, question_numbers in questions_to_fetch.items():
        for question_number in question_numbers:
            print(f"\n処理中: 第{exam_number}回 問{question_number}")
            url = get_question_url_from_pages(exam_number, question_number)
            print(f"  URL: {url}")

            try:
                html_content = fetch_html_from_url(url)
                if not html_content:
                    print(f"  ✗ スキップ: HTMLを取得できませんでした")
                    failure_count += 1
                    continue

                # HTMLコンテンツから問題を抽出
                try:
                    result = extract_question_content(
                        html_content,
                        source_name=f"第{exam_number}回問{question_number}",
                    )
                    
                    # 複数の問題が返された場合（リスト）
                    if isinstance(result, list):
                        for title, question_html, choices, answer_html, explanation_html in result:
                            # 抽出結果の検証
                            if not question_html:
                                print(f"  ⚠ 警告: 問題文が抽出できませんでした - {title}")
                                continue
                            if not answer_html and not explanation_html:
                                print(f"  ⚠ 警告: 解答・解説が抽出できませんでした - {title}")
                                continue
                            
                            questions_data.append(
                                (title, question_html, choices, answer_html, explanation_html)
                            )
                            print(f"  ✓ 抽出成功: {title}")
                    else:
                        # 単一の問題が返された場合（タプル）
                        title, question_html, choices, answer_html, explanation_html = result
                        
                        # 抽出結果の検証
                        if not question_html:
                            raise ValueError(f"問題文が抽出できませんでした")
                        if not answer_html and not explanation_html:
                            raise ValueError(f"解答・解説が抽出できませんでした")

                        questions_data.append(
                            (title, question_html, choices, answer_html, explanation_html)
                        )
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

    if not questions_data:
        print("\n✗ エラー: 抽出できた問題がありませんでした。")
        return

    # HTMLを作成
    print(f"\nHTMLファイルを生成中...")
    html_content = create_simple_html(questions_data)

    # ファイルに保存
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✓ 成功: {len(questions_data)}問のHTMLファイルを作成しました")
        print(f"  保存先: {output_file}")
    except Exception as e:
        print(f"✗ エラー: ファイルの保存に失敗しました - {type(e).__name__}: {e}")
        return


if __name__ == "__main__":
    main()
