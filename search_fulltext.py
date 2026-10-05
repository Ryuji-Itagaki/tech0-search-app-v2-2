# =============================================================
# answers/w3/search_fulltext.py — 全文検索（W3 完成版）
# ノートブック W3 Step 3 で作った _make_preview / search_fulltext
# =============================================================


def _make_preview(text: str, query: str, ctx: int = 80) -> str:
    """マッチ箇所周辺のプレビューを生成する（補助関数）"""
    if not text or not query:
        return ""

    pos = text.lower().find(query.lower())

    # 見つからない場合は先頭200文字を返す
    if pos == -1:
        return (text[:200] + "...") if len(text) > 200 else text

    start = max(0, pos - ctx)
    end = min(len(text), pos + len(query) + ctx)

    preview = ""
    if start > 0:
        preview += "..."
    preview += text[start:end]
    if end < len(text):
        preview += "..."
    return preview


def search_fulltext(query: str, pages: list) -> list:
    """全文検索（本文含む）を実行し、マッチ数でスコアリングする"""
    if not query.strip():
        return []

    results = []
    q = query.lower()

    for page in pages:
        # 検索対象テキストを作る（title + description + full_text + keywords）
        kw = page.get("keywords", [])
        if isinstance(kw, str):                      # DB由来だと文字列の場合がある
            kw = [k.strip() for k in kw.split(",") if k.strip()]
        text = " ".join([
            page.get("title", "") or "",
            page.get("description", "") or "",
            page.get("full_text", "") or "",
            " ".join(kw),
        ]).lower()

        count = text.count(q)
        if count > 0:
            r = page.copy()
            r["match_count"] = count
            r["preview"] = _make_preview(
                page.get("full_text") or page.get("description", ""),
                query
            )
            results.append(r)

    # match_count順に並べる
    results.sort(key=lambda x: x["match_count"], reverse=True)
    return results
