#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
post_contentの中身をそのまま取得してHTMLを作成する
"""

from bs4 import BeautifulSoup
import requests
import re
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

    return page_title, str(post_content)


def create_html(contents):
    """post_contentのリストからHTMLを作成"""
    html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>過去問まとめ</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
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
    <h1 style="text-align: center; color: #2c3e50; margin-bottom: 40px;">過去問まとめ</h1>
"""

    for title, post_content_html in contents:
        html += f"""
    <div class="question-block">
        <div class="question-title">{title}</div>
        <div class="post-content">
{post_content_html}
        </div>
    </div>
"""

    html += """
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

    return html


def main():
    output_file = "/Users/diabolo/dev/temp/tonao/html/過去問まとめ.html"
    pages_file = "/Users/diabolo/dev/temp/tonao/yakugaku-251212/question_pages.json"

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

    contents = []
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
                    contents.append((title, post_content_html))
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

    if not contents:
        print("\n✗ エラー: 取得できた問題がありませんでした。")
        return

    # HTMLを作成
    print(f"\nHTMLファイルを生成中...")
    html_content = create_html(contents)

    # ファイルに保存
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✓ 成功: {len(contents)}問のHTMLファイルを作成しました")
        print(f"  保存先: {output_file}")
    except Exception as e:
        print(f"✗ エラー: ファイルの保存に失敗しました - {type(e).__name__}: {e}")
        return


if __name__ == "__main__":
    main()
