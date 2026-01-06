import os
import feedparser
import requests
import google.generativeai as genai
from datetime import datetime

# --- 設定 ---
# NHK RSS (主要ニュース)
# ユーザー指定のURL: https://news.web.nhk/n-data/conf/na/rss/cat0.xml が使える場合はこちらに書き換えてください
RSS_URL = "https://news.web.nhk/n-data/conf/na/rss/cat0.xml"

# APIキー類の取得 (GitHub Secretsから読み込む)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN")

def get_nhk_news():
    """RSSからニュースを取得してリスト形式で返す"""
    feed = feedparser.parse(RSS_URL)
    news_list = []
    
    # 最新15件程度を取得してAIに渡す
    for entry in feed.entries[:15]:
        title = entry.title
        link = entry.link
        news_list.append(f"・{title} ({link})")
    
    return "\n".join(news_list)

def summarize_with_gemini(news_text):
    """Geminiで重要なニュースを選別・要約する"""
    genai.configure(api_key=GEMINI_API_KEY)
    
    # 2.0 Flashなどの軽量・高速なモデルを指定
    model = genai.GenerativeModel("models/gemini-2.5-flash") 

    prompt = f"""
    あなたは優秀なニュース編集者です。
    以下のNHKニュースリストから、特に社会的影響が大きい、または重要度の高いニュースを「最大3つ」選んでください。
    それぞれを簡潔に要約し、以下のフォーマットで出力してください。
    冒頭の挨拶などは不要です。

    【出力フォーマット】
    📰 [タイトル]
    [要約を2行〜3行で]
    🔗 [リンク]

    ---
    ニュースリスト:
    {news_text}
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI生成エラー: {e}"

def send_line_notify(message):
    """LINEにメッセージを送る"""
    api_url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {LINE_NOTIFY_TOKEN}"}
    data = {"message": f"\n{message}"}
    
    requests.post(api_url, headers=headers, data=data)

def main():
    if not GEMINI_API_KEY or not LINE_NOTIFY_TOKEN:
        print("エラー: APIキーまたはLINEトークンが設定されていません。")
        return

    print("ニュースを取得中...")
    news_raw = get_nhk_news()
    
    if not news_raw:
        print("ニュースが取得できませんでした。")
        return

    print("Geminiで要約中...")
    summary = summarize_with_gemini(news_raw)
    
    # 日付を追加
    today = datetime.now().strftime("%Y/%m/%d")
    final_message = f"【NHK重要ニュース {today}】\n\n{summary}"
    
    print("LINEに送信中...")
    send_line_notify(final_message)
    print("完了")

if __name__ == "__main__":
    main()
