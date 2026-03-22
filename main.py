import os
import random
import requests
import sys
import time
from google import genai

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
THREADS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

# 2. 八大旅遊通資料 (包含曼谷通)
CITIES = [
    {"name": "曼谷通", "topic": "曼谷按摩、考山路與泰式美食", "url": "https://linkuei0425.github.io/Bangkok/"},
    {"name": "清邁通", "topic": "清邁古城、文青咖啡廳與大象營", "url": "https://linkuei0425.github.io/ChiangMai/"},
    {"name": "首爾通", "topic": "首爾逛街、漢江公園與韓式燒肉", "url": "https://linkuei0425.github.io/Seoul/"},
    {"name": "釜山通", "topic": "釜山海雲台、甘川洞文化村與豬肉湯飯", "url": "https://linkuei0425.github.io/Busan/"},
    {"name": "沖繩通", "topic": "沖繩自駕、美麗海水族館與潛水", "url": "https://linkuei0425.github.io/Okinawa/"},
    {"name": "新加坡通", "topic": "新加坡環球影城、金沙酒店與肉骨茶", "url": "https://linkuei0425.github.io/Singapore/"},
    {"name": "福岡通", "topic": "福岡博多拉麵、太宰府天滿宮與屋台", "url": "https://linkuei0425.github.io/FUKUOKA/"},
    {"name": "京・阪・神通", "topic": "京都花見小路、大阪心齋橋與環球影城", "url": "https://linkuei0425.github.io/Osaka/"}
]

def run():
    if not GEMINI_KEY or not THREADS_TOKEN:
        print("❌ 錯誤：找不到 API Key 或 Token。")
        sys.exit(1)

    client = genai.Client(api_key=GEMINI_KEY)
    target = random.choice(CITIES)
    print(f"🎲 挑選城市：【{target['name']}】")

    prompt = f"你是一位活潑的旅遊部落客。請為『{target['name']}』寫一段 80 字內的 Threads 貼文。主題是：{target['topic']}。必須包含網址 {target['url']}，多加 Emoji，結尾加 #旅遊 #自由行。"

    # --- 模型自動切換邏輯 (避開 429 額度問題) ---
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-2.0-flash']
    content = None

    for model_name in models_to_try:
        try:
            print(f"🤖 嘗試使用模型：{model_name}...")
            response = client.models.generate_content(model=model_name, contents=prompt)
            if response.text:
                content = response.text
                print(f"✅ 模型 {model_name} 生成成功！")
                break
        except Exception as e:
            if "429" in str(e):
                print(f"⚠️ {model_name} 額度滿了，切換下一個...")
                continue
            else:
                print(f"💥 發生非預期錯誤：{e}")
                sys.exit(1)

    if not content:
        print("❌ 抱歉，所有的模型額度都用完了。請等 10 分鐘後再手動測試。")
        sys.exit(1)

    # 3. 發布到 Threads
    print("📤 正在發布到 Threads...")
    res = requests.post("https://graph.threads.net/v1.0/me/threads", params={
        'media_type': 'TEXT', 'text': content, 'access_token': THREADS_TOKEN
    }).json()
    
    if 'id' in res:
        requests.post("https://graph.threads.net/v1.0/me/threads_publish", params={
            'creation_id': res['id'], 'access_token': THREADS_TOKEN
        })
        print(f"🎉 【{target['name']}】發布成功！")
    else:
        print(f"❌ Threads 錯誤：{res}")
        sys.exit(1)

if __name__ == "__main__":
    run()
