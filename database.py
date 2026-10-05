# =============================================================
# answers/w3/database.py — DB操作の一元管理（W3 完成版）
# ノートブック W3 Step 2 で作った get_connection / init_db / insert_page / get_all_pages
# =============================================================
import sqlite3
from pathlib import Path
from datetime import datetime

# DB ファイルのパス（data/ サブフォルダに保存する）
DB_PATH = Path("data/tech0_search.db")


def get_connection():
    """DB への接続を取得する（data/ フォルダが無ければ自動作成）"""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row        # 行データを辞書のように扱う
    return conn


def init_db():
    """schema.sql を読み込んで DB を初期化する"""
    conn = get_connection()
    with open("schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def _keywords_to_text(keywords) -> str:
    """keywords（リスト or 文字列）を DB 保存用のカンマ区切り文字列にする"""
    if not keywords:
        return ""
    if isinstance(keywords, str):
        return keywords
    return ",".join(keywords)


def insert_page(page: dict) -> int:
    """ページ情報を DB に登録する（同じURLは上書き）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO pages
            (url, title, description, full_text, author, category, keywords, word_count, crawled_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        page["url"],
        page["title"],
        page.get("description", ""),
        page.get("full_text", ""),
        page.get("author", ""),
        page.get("category", ""),
        _keywords_to_text(page.get("keywords")),   # リスト → "DX,営業店" にして保存
        page.get("word_count", 0),
        page.get("crawled_at", datetime.now().isoformat()),
    ))
    page_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return page_id


def get_all_pages() -> list:
    """全ページを登録日時の新しい順で取得する"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pages ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    pages = []
    for row in rows:
        p = dict(row)
        # 保存時にカンマ区切りにした keywords をリストに戻す
        p["keywords"] = [k.strip() for k in (p.get("keywords") or "").split(",") if k.strip()]
        pages.append(p)
    return pages


def migrate_from_json(json_path: str = "pages_w2.json") -> int:
    """pages_w2.json のデータを DB に移行する（W3 の移行作業用）"""
    import json as _json
    with open(json_path, "r", encoding="utf-8") as f:
        pages = _json.load(f)
    for p in pages:
        insert_page(p)   # keywords（リスト）はカンマ区切りに変換して保存される
    return len(pages)


def log_search(query: str, results_count: int, user_id: str = None) -> int:
    """検索ログを記録する（W6 の発展課題で実装予定のスタブ）"""
    pass  # W6 の発展課題で実装します
