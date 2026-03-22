import os
import random
import requests
import sys
from google import genai # 注意：這是 2025 新版 SDK

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
THREADS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

# 2. 八大旅遊通資料 (包含曼谷通)
CITIES = [
    {"name": "曼谷通", "topic": "曼谷按摩、考山路與泰式美食", "url": "https://linkuei0425.github.io/Bangkok/"},
    {"name": "清邁通", "topic": "清邁古城、咖啡廳與大象營", "url": "https://linkuei0425.github.io/ChiangMai/"},
    {"name": "首爾通", "topic": "首爾逛街、漢江公園與韓式燒肉", "url": "https://linkuei0425.github.io/Seoul/"},
    {"name": "釜山通", "topic": "釜山海雲台、甘川洞文化村", "url": "https://linkuei0425.github.io/Busan/"},
    {"name": "沖繩通", "topic": "沖繩自駕、美麗海水族館與海灘", "url": "https://linkuei0425.github.io/Okinawa/"},
    {"name": "新加坡通", "topic": "新加坡環球影城與金沙酒店", "url": "https://linkuei0425.github.io/Singapore/"},
    {"name": "福岡通", "topic": "福岡博多拉麵與太宰府天滿宮", "url": "https://linkuei0425.github.io/FUKUOKA/"},
    {"name": "京・阪・神通", "topic": "京都花見小路、大阪心齋橋與環球影城", "url": "https://linkuei0425.github.io/Osaka/"}
]

def run():
    try:
        # 3. 使用 Google 最新 Client 語法 (自動對接正確 API 版本)
        client = genai.Client(api_key=GEMINI_KEY)
        
        target = random.choice(CITIES)
        print(f"📡 正在處理：{target['name']}...")

        prompt = f"你是一位活潑的旅遊領隊。請為『{target['name']}』寫一段 80 字內的 Threads 貼文。主題是：{target['topic']}。必須包含網址 {target['url']}，多加 Emoji，結尾加 #旅遊 #自由行。"
        
        # 這裡不加 models/ 前綴，直接寫名字，這是新版 SDK 的標準備配
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        
        # 4. 發布到 Threads
        res = requests.post("https://graph.threads.net/v1.0/me/threads", params={
            'media_type': 'TEXT',
            'text': response.text,
            'access_token': THREADS_TOKEN
        }).json()
        
        if 'id' in res:
            requests.post("https://graph.threads.net/v1.0/me/threads_publish", params={
                'creation_id': res['id'],
                'access_token': THREADS_TOKEN
            })
            print(f"✅ 【{target['name']}】發布成功！")
        else:
            print(f"❌ Threads API 拒絕發文：{res}")
            sys.exit(1)

    except Exception as e:
        print(f"💥 運行異常：{e}")
        # 如果看到 "Resource exhausted"，代表今天測太多次了，要等明天或等一小時
        sys.exit(1)

if __name__ == "__main__":
    run()
