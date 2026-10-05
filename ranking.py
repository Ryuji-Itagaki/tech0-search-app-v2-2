from sklearn.feature_extraction.text import TfidfVectorizer #数値の表に変換する
from sklearn.metrics.pairwise import cosine_similarity #数値どうしを比べて、どのぐらい近いかを計算する
from datetime import datetime #日時を管理する（デフォルト入れておく）
from typing import List #List[src]のように型を指定するためのもの

class SearchEngine:
    """TF-IDFベースの検索エンジン（ranking.py)の本体を作る"""

    def __init__(self):
        #TF-IDFのベクトライザーを初期化
        #日本語は単語の間にスペースがないため、既存の「単語区切り」では
        #「営業店DX推進レポート」が丸ごと1語になり、「DX」で検索をかけても一致しない
        #そこで、analyzer = "char_wb" （文字N-gram）で2~3文字のまとまりを特徴量にする
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",     #文字N-gram（日本語のまま使えるようにする）
            ngram_range=(2,3),      #2~3文字のまとまり
            max_features=5000,
            min_df=1,
            max_df=0.95,
            sublinear_tf=True       #TFの対数スケーリング
        )
        self.tfidf_matrix = None    #インデックス（後で構築）
        self.pages= []              #元のページデータを保持
        self.is_fitted = False      #インデックスが構築済みがのフラグ

    def build_index(self, pages:list):
        """
        全ページのTF-IDFインデックスを構築

        Args:
            pages:ページ情報の辞書リスト
        """
        if not pages:
            return

        self.pages = pages

        #各ページの「検索対象テキスト」を組み立て
        #タイトル・説明・キーワードに重みをつけるため、文字列を繰り返す
        corpus = []
        for p in pages:
            #keywordsがカンマ区切りの文字列の場合はリストに追加
            kw = p.get("keywords", "") or ""
            if isinstance(kw, str):
                kw_list = [k.strip() for k in kw.split(",") if k.strip()]
            else:
                kw_list = kw

            #重みづけを実施。タイトルは3倍、説明は2倍、キーワードは2倍の重み
            text = " ".join([
                (p.get("title","") + " ") * 3,          #タイトルは3倍
                (p.get("description","") + " ") * 2,    #説明は2倍
                (p.get("full_text","") + " ") * 1,      #本文は1倍
                (" ".join(kw_list) + " ") * 2,          #キーワードは2倍
            ])
            corpus.append(text)

        #YF-IDFマトリックスを構築
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.is_fitted = True
        #print(f"インデックス構築完了 :{len(pages)}ページ") これは不要

    def search(self,query: str,top_n: int = 20) -> list:
        """
        TF-IDFベースの検索を実行
        
        Args:
            query : 検索クエリ
            top_n : 返す結果の最大値
        
        Returns:
            スコア付きの検索結果リスト
        """
        if not self.is_fitted or not query.strip():
            return[]

        #クエリをベクトル化してコサイン炊事どを計算する（Step3で学んだ内容）
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec,self.tfidf_matrix)[0]

        #閾値以上のページだけ結果に含める
        results = []
        for idx, base_score in enumerate(similarities):
            if base_score > 0.01:
                page = self.pages[idx].copy()

                #追加スコアりんぐで最終スコアを計算
                final_score = self._calculate_final_score(page, base_score, query)

                #スコアをパーセント表示用に変換する
                page["relevance_score"] = round(float(final_score) *100, 1)
                page["base_score"] = round(float(base_score) * 100, 1)
                results.append(page)

        #スコアの高い順に並べて　top_n 件を返す
        results.sort(key=lambda x: x["relevance_score"],reverse=True)
        return results[:top_n]

    def _calculate_final_score(self, page: dict, base_score: float,query: str) -> float:
        """
        複数の要素を組み合わせて最終スコアを計算する（内部メソッド）
        Args：
            page: ページ情報
            base_score: TF-IDFベーススコア
            query: 検索クエリ
        
        Returns:
            最終スコア
        """

        score = base_score
        query_lower = query.lower()

        #1.タイトルマッチボーナス
        title = page.get("title", "").lower()
        if query_lower == title:
            score *=  1.8       #完全一致の場合、＋80%にする
        elif query_lower in title:
            score *= 1.4    #部分一致の場合、＋40%

        #2.キーワードマッチボーナス
        keywords = page.get("keywords",[])

        if isinstance(keywords, str):
            keywords = keywords.split(",")

        keywords_lower = [k.strip().lower() for k in keywords]

        if query_lower in keywords_lower:
            score *= 1.3    #キーワード数：＋30%

        #3.新鮮度ボーナス（90日以内おページは最大　＋20%）
        crawled_at = page.get("crawled_at","")
        if crawled_at:
            try:
                crawled = datetime.fromisoformat(crawled_at.replace("Z","+00:00"))
                days_old = (datetime.now() - crawled.replace(tzinfo=None)).days
                if days_old <= 90:
                    recency_bonus = 1 + (0.2 * (90 - days_old) / 90)
                    score *= recency_bonus
            except Exception:
                pass

        #4.文字数による調査
        word_count = page.get("word_count" ,0)
        if word_count < 50:
            score *= 0.7        #短すぎるページは70%に減点
        elif word_count > 10000:
            score *= 0.85       #長すぎるページは85%に減点

        return score


"""── シングルトン（アプリ全体で1つのエンジンを使いまわす）"""
_engine = None
def get_engine() -> SearchEngine:
    """
    検索エンジンのシングルトンインスタンスを取得
    """
    global _engine
    if _engine is None:
        _engine = SearchEngine()
    return _engine

def rebuild_index(pages: List[dict]):
    """
    検索エンジンのインデックスを再構築する（新しいページが追加された時に呼び出す）
    """
    engine = get_engine()
    engine.build_index(pages)