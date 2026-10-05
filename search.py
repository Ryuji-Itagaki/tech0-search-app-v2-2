# search_pages() の全体 — 1行ずつコメントで解説

def search_pages(query: str, pages: list) -> list:
    # ↑ 「: str」「: list」は型ヒント（なくても動くが読みやすくなる）
    # ↑ 「-> list」は「戻り値はリスト型」という宣言

    # ① キーワードが空欄ならすぐ終了（空リストを返す）
    if not query.strip():
        #  ↑ .strip() は前後の空白を取り除く
        #  ↑ not は「〜でない」 → 空欄なら True になる
        return []

    results = []                    # ② 結果を入れる空のリストを用意
    query_lower = query.lower()    # ③ "DX" → "dx" と小文字に統一（大文字小文字を無視するため）

    for page in pages:              # ④ ページを1件ずつ取り出してループ

        # ⑤ title + description + keywords を1つの文字列に結合して検索対象にする
        search_text = " ".join([
            page["title"],
            page["description"],
            " ".join(page["keywords"]),  # ["DX","営業店"] → "DX 営業店"
        ])
        # 例: "営業店DX推進レポート 窓口業務のペーパーレス化で… DX 営業店 業務効率"

        # ⑥ キーワードが search_text に含まれていたら results に追加
        if query_lower in search_text.lower():
            results.append(page)    # .append() でリストに追加

    return results  # ⑦ マッチしたページのリストを返す


# ── 実際に動かしてみよう ──
import json
with open("pages_w1.json", "r", encoding="utf-8") as f:
    all_pages = json.load(f)

hits = search_pages("DX", all_pages)
print(f"'DX' の検索結果: {len(hits)} 件")
print()
for h in hits:
    print(f"  ✅ {h['title']}  （{h['author']}）")


    import re  # re = Regular Expression（正規表現）標準ライブラリ、pip install 不要

def highlight_match(text: str, query: str) -> str:

    if not query:       # キーワードが空なら何もしない
        return text

    # re.compile() でパターン（検索ルール）を作る
    pattern = re.compile(
        re.escape(query),  # re.escape：「?」「+」などの特殊文字が含まれても壊れない安全策
        re.IGNORECASE      # IGNORECASE：大文字・小文字を区別しない
    )

    # pattern.sub(置換後の文字列, 元テキスト)：マッチした部分を置換する
    return pattern.sub(f"**{query}**", text)
    #                  ↑
    #   「**DX**」← Markdown で ** で囲むと太字になる！


# ── 動かしてみよう ──
original = "窓口業務のペーパーレス化で事務時間を30%削減したDXプロジェクトの記録"
result1  = highlight_match(original, "DX")
result2  = highlight_match(original, "dx")   # 小文字でもOK（IGNORECASE のおかげ）

print("【変換前】")   ; print(" ", original)
print("【変換後 DX】") ; print(" ", result1)
print("【変換後 dx】") ; print(" ", result2)
print()
print("※ Streamlit画面では **DX** の部分が太字で表示されます")