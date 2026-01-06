import os
import feedparser
import requests
import google.generativeai as genai
from datetime import datetime

# --- 設定 ---
# ユーザー指定のRSS URL
RSS_URL = "https://www.nhk.or.jp/rss/news/cat0.xml"

# 環境変数からキーを取得
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

def get_news():
    """RSSから記事を取得する"""
    print(f"RSSを取得中: {RSS_URL}")
    # タイムアウト設定を追加してフリーズを防ぐ
    try:
        feed = feedparser.parse(RSS_URL)
        
        if not feed.entries:
            print("記事が見つかりませんでした。URLがアクセス制限されている可能性があります。")
            return None

        news_text = []
        # 最新15件を抽出
        for entry in feed.entries[:15]:
            title = entry.title
            link = entry.link
            news_text.append(f"{title} ({link})")
        
        return "\n".join(news_text)
    except Exception as e:
        print(f"RSS取得エラー: {e}")
        return None

def summarize_news(news_data):
    """Geminiで重要ニュースを選別・要約"""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("models/gemini-2.5-flash") # 動作が速いモデル

    prompt = f"""
    あなたはニュース編集者です。
    以下のNHKニュースリストから、特に社会的影響の大きい重要なニュースを「最大3本」選んでください。
    それぞれを「簡潔な要約（2行）」にし、以下の形式で出力してください。
    
    【形式】
    タイトル
    要約: [ここに要約]
    リンク
    
    【ニュースリスト】
    {news_data}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI生成エラー: {e}"

def send_line_broadcast(text):
    """LINE Messaging API (Broadcast) で送信"""
    url = "https://api.line.me/v2/bot/message/broadcast"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    payload = {
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("LINE送信成功")
    else:
        print(f"LINE送信失敗: {response.status_code} {response.text}")

def main():
    if not GEMINI_API_KEY or not LINE_CHANNEL_ACCESS_TOKEN:
        print("エラー: APIキーが設定されていません。")
        return

    # 1. ニュース取得
    news_data = get_news()
    if not news_data:
        # エラー通知を送るか、ここで終了するか
        print("ニュース取得失敗のため終了します。")
        return

    # 2. AIによる選別・要約
    print("Geminiで分析中...")
    summary = summarize_news(news_data)

    # 3. メッセージ作成
    today = datetime.now().strftime('%Y/%m/%d')
    message = f"【NHK重要ニュース {today}】\n\n{summary}"

    # 4. LINE送信
    send_line_broadcast(message)

if __name__ == "__main__":
    main()
