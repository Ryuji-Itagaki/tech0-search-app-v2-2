##基本構造は、
## 1.webページ取得の部分を関数にまとめる→ fetch_page関数
##   ┗URLを受け取る→HTMLを返すという動作
## 2.取得したHTMLからタイトルなどの情報を抜き出す関数
##   ┗HTMLを受け取る→ページ情報の辞書を返すという関数
## 3.URLをクロールして、情報を返す（fetch →parseのワンストップ）

# Webページ取得に使うライブラリ
import requests
import re
from bs4 import BeautifulSoup #HTML解析に利用するライブラリ
from datetime import datetime #日時記録
from typing import Optional #Webページ取得の部分を、関数にまとめる

#1.webページ取得の部分を関数にまとめる→ fetch_page関数
def fetch_page(url:str,timeout: int= 10) ->Optional[str]:
    """指定URLのHTMLを取得する。失敗時は None"""
    try:
        headers = {"User-Agent":"Tech0SearchBot/1.0(Educational Purpose)"}
        resp = requests.get(url,headers=headers, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return resp.text
    except requests.RequestException as e:
        print(f"❌ 取得エラー: {e}")
        return None


#2.取得したHTMLからタイトルなどの情報を抜き出す関数
def parse_html(html: str, url:str ) -> dict:
    soup = BeautifulSoup(html,"html.parser")

    #不要タグを除去
    for tag in soup(["script","style","nav","footer","header"]):
        tag.decompose()

    #タイトル取得
    title = "No Title"
    if soup.find("title"):
        title = soup.find("title").get_text().strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text().strip()

    #meta description
    description = ""
    meta = soup.find("meta", attrs={"name":"description"})
    if meta and meta.get("content"):
        description = meta["content"][:200]

    #meta keywords
    keywords = []
    meta_kw = soup.find("meta", attrs={"name":"Keywords"})
    if meta_kw and meta_kw.get("content"):
        keywords = [kw.strip() for kw in meta_kw["content"].split(",")][:10]

    #テキスト
    elems = soup.find_all(["p","h1","h2","h3","h4","h5","h6","li","td"])
    full_text = " ".join(e.get_text().strip() for e in elems)
    full_text = re.sub(r"\s+", " ", full_text).strip()

    #リンク
    links = [
        a["href"]
        for a in soup.find_all("a",href=True)
        if a["href"].startswith("http")
    ]

    return {
        "url": url,
        "title": title,
        "description": description,
        "keywords": keywords,
        "full_text": full_text,
        "links": links,
        "word_count": len(full_text.split()),
        "crawled_at": datetime.now().isoformat(),
        "crawl_status": "success",
    }

# 3.URLをクロールして、情報を返す（fetch →parseのワンストップ）
def crawl_url(url: str) -> dict:
    #HTMLを取得
    html = fetch_page(url)
    #取得失敗時
    if not html:
        return {
            "url":url,
            "crawl_status":"failed",
            "crawled_at": datetime.now().isoformat(),
            "error":"Failed to fetch page"
        }

    #取得成功時の解析
    try:
        return parse_html(html,url)

    except Exception as e:
        #解析失敗時
        return {
            "url":url,
            "crawl_status":"error",
            "crawled_at": datetime.now().isoformat(),
            "error": str(e)
        }

##クローラーを試してみる
#result = crawl_url("https://www.apple.com/")
#if result.get("crawl_status") == "success":
#    print("✅ クロール成功!")
#    print(f"📄 タイトル: {result['title']}")
#    print(f"📝 説明: {result['description'][:100]}...")
#    print(f"📊 文字数: {result['word_count']}語")
#    print(f"🔗 リンク数: {len(result['links'])}件")
#else:
#    print(f"❌ クロール失敗: {result.get('error')}")


    
