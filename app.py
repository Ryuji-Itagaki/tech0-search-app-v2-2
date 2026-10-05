# =============================================================
# answers/w4/app.py — Tech0 Search v1.0（W4 完成版）
# 起動： streamlit run app.py
# （ranking.py / database.py / schema.sql / crawler.py が同じフォルダに必要）
# =============================================================
import re
import streamlit as st
from database import init_db, get_all_pages, insert_page, log_search  # log_searchは発展用に残してある
from ranking  import get_engine, rebuild_index
from crawler  import crawl_url

#アプリ起動時にDBを初期化
init_db()

##ページ設定・タイトル─────────────────────────────
st.set_page_config(
    page_title='Tech0 Search v1.0', 
    page_icon="🔍",
    layout="wide"
)

##キャッシュ付きインデックス構築 ─────────────────────────────
@st.cache_resource
def load_and_index():
    """全ページを DB から読み込み TF-IDF インデックスを構築する。
    @st.cache_resource により、アプリ起動中は一度だけ実行される。"""
    pages = get_all_pages()
    if pages:
        rebuild_index(pages)
    return pages

pages = load_and_index()
engine = get_engine()

##ヘッダー ─────────────────────────────
st.title("🔍 Tech0 Search v1.0")
st.caption("PROJECT ZERO — 社内ナレッジ検索エンジン【W4 TF-IDFランキング搭載】")


##　②データの読み書き関数 ここがイマイチ分からない
with st.sidebar:
    st.header("DBの状態")

    if st.session_state.get("migrated") is not None:
        st.success(f"{st.session_state['migrated']}件をDBに移行しました")
        st.session_state["migrated"] = None
    pages = get_all_pages()
    st.metric("登録ページ数",f"{len(pages)}件")
    if st.button("📦 pages_w2.json から DB へ移行"):    
        n = migrate_from_json("page_w2.json")
        st.session_state["migrated"] = n
        st.rerun()
    
##　タブを作る─────────────────────────────
tab_search, tab_crawl, tab_list = st.tabs(
    ['検索','クロール登録','一覧']
)

##　検索タブ─────────────────────────────
with tab_search:
    st.subheader("キーワードで検索")

    col_search, col_options = st.columns([3, 1])
    with col_search:
        query = st.text_input("🔍 キーワードを入力", placeholder="例: DX, AI, 融資",
                              label_visibility="collapsed")
    with col_options:
        top_n = st.selectbox("表示件数", [10, 20, 50], index=0)

    if query:
        results = engine.search(query, top_n=top_n)
        log_search(query, len(results))    # 検索するたびに自動記録（W6発展で実装）

        st.markdown(f"**📊 検索結果：{len(results)} 件**（TF-IDFスコア順）")
        st.divider()

        if results:
            for i, page in enumerate(results, 1):
                with st.container():
                    col_rank, col_title, col_score = st.columns([0.5, 4, 1])
                    with col_rank:
                        medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else str(i)
                        st.markdown(f"### {medal}")
                    with col_title:
                        st.markdown(f"### {page['title']}")
                    with col_score:
                        st.metric("スコア", f"{page['relevance_score']}",
                                  delta=f"基準: {page['base_score']}")

                    desc = page.get("description", "")
                    if desc:
                        st.markdown(f"*{desc[:200]}{'...' if len(desc) > 200 else ''}*")

                    kw = page.get("keywords", "") or ""
                    if kw:
                        # keywords は DB から読むと list、手動で入れると "A,B,C" の文字列になる。
                        # ranking.py と同じく、どちらでも動くようにしておく。
                        kw_list = [k.strip() for k in kw.split(",")] if isinstance(kw, str) else list(kw)
                        tags = " ".join([f"`{k}`" for k in kw_list[:5] if k])
                        st.markdown(f"🏷️ {tags}")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1: st.caption(f"👤 {page.get('author', '不明') or '不明'}")
                    with col2: st.caption(f"📊 {page.get('word_count', 0)} 語")
                    with col3: st.caption(f"📁 {page.get('category', '未分類') or '未分類'}")
                    with col4: st.caption(f"📅 {(page.get('crawled_at', '') or '')[:10]}")

                    st.markdown(f"🔗 [{page['url']}]({page['url']})")
                    st.divider()
        else:
            st.info("該当するページが見つかりませんでした")
##　クローラータブ─────────────────────────────
if "crawl_results" not in st.session_state:
    st.session_state.crawl_results = []

with tab_crawl:
    st.subheader("🤖 自動クローラー")

    # st.rerun() をまたいで「登録できた」メッセージを持ち越す（W1 と同じ仕組み）
    if st.session_state.get("registered_count"):
        st.success(f"{st.session_state['registered_count']}件 登録完了！")
        st.session_state["registered_count"] = 0
    st.caption("URLを入力してクロールし、インデックスに登録する")

    crawl_url_input = st.text_area(
        "クロール対象URL",
        placeholder="URLを改行またはスペース区切りで入力してください",
        height=150
    )

    if st.button("🤖 クロール実行", type="primary"):
        if crawl_url_input:
            raw_parts = re.split(r'[\s]+', crawl_url_input.strip())
            urls = [p for p in raw_parts if p.startswith(("http://", "https://"))]

            if not urls:
                st.error("有効なURLが見つかりませんでした")
            else:
                st.write(f"🔗 {len(urls)}件のURLを処理します")
                st.session_state.crawl_results = []

                for url in urls:
                    with st.spinner(f"クロール中: {url}"):
                        result = crawl_url(url)

                    if result and result.get('crawl_status') == 'success':
                        st.success(f"✅ 成功: {url}")
                        col1, col2 = st.columns(2)
                        with col1:
                            title = result.get('title', '')
                            st.metric("📄 タイトル", (title[:30] + "...") if len(title) > 30 else title)
                        with col2:
                            st.metric("📊 文字数", f"{result.get('word_count', 0)}語")
                        st.session_state.crawl_results.append(result)
                    else:
                        st.error(f"❌ 失敗: {url}")

    if st.session_state.crawl_results:
        st.info(f"{len(st.session_state.crawl_results)}件のクロール結果を登録できます。")

        if st.button("💾 全てインデックスに登録"):
            total = len(st.session_state.crawl_results)
            progress_text = st.empty()
            progress_bar = st.progress(0)

            for i, r in enumerate(st.session_state.crawl_results, start=1):
                progress_text.write(f"📥 {i} / {total} 件登録中...")
                insert_page(r)
                progress_bar.progress(i / total)

            st.session_state["registered_count"] = total   # 件数を印として残す
            st.session_state.crawl_results = []
            st.cache_resource.clear()
            st.rerun()

## 一覧タブ─────────────────────────────
with tab_list:
    st.subheader(f"📋 登録済みページ一覧（{len(pages)} 件）")
    if not pages:
        st.info("登録されているページがありません。クローラータブからページを追加してください。")
    else:
        for page in pages:
            with st.expander(f"📄 {page['title']}"):
                st.markdown(f"**URL：** {page['url']}")
                st.markdown(f"**説明：** {page.get('description', '（なし）') or '（なし）'}")
                col1, col2, col3 = st.columns(3)
                with col1: st.caption(f"語数：{page.get('word_count', 0)}")
                with col2: st.caption(f"作成者：{page.get('author', '不明') or '不明'}")
                with col3: st.caption(f"カテゴリ：{page.get('category', '未分類') or '未分類'}")

st.divider()
st.caption("© PROJECT ZERO — Tech0 Search v1.0 | Powered by TF-IDF")
 
        
