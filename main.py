import os
import random
import requests
import sys
from google import genai

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
THREADS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

# 2. 八大旅遊通資料 (已加入曼谷通，並校對網址大小寫)
CITIES = [
    {"name": "曼谷通", "topic": "曼谷按摩、考山路與泰式美食", "url": "https://linkuei0425.github.io/Bangkok/"},
    {"name": "清邁通", "topic": "清邁古城、咖啡廳與大象營", "url": "https://linkuei0425.github.io/ChiangMai/"},
    {"name": "首爾通", "topic": "首爾逛街、漢江公園與韓式燒肉", "url": "https://linkuei0425.github.io/Seoul/"},
    {"name": "釜山通", "topic": "釜山海雲台、甘川洞文化村", "url": "https://linkuei0425.github.io/Busan/"},
    {"name": "沖繩通", "topic": "沖繩自駕、美麗海水族館與潛水", "url": "https://linkuei0425.github.io/Okinawa/"},
    {"name": "新加坡通", "topic": "新加坡環球影城與金沙酒店", "url": "https://linkuei0425.github.io/Singapore/"},
    {"name": "福岡通", "topic": "福岡博多拉麵與太宰府天滿宮", "url": "https://linkuei0425.github.io/FUKUOKA/"},
    {"name": "京・阪・神通", "topic": "京都花見小路、大阪心齋橋與環球影城", "url": "https://linkuei0425.github.io/Osaka/"}
]

def run():
    try:
        # 使用 Google 2025 最新版 SDK 語法
        client = genai.Client(api_key=GEMINI_KEY)
        
        target = random.choice(CITIES)
        print(f"🎲 準備為【{target['name']}】生成文案...")

        prompt = f"你是一位活潑的旅遊領隊。請為『{target['name']}』寫一段 80 字內的 Threads 貼文。主題是：{target['topic']}。必須包含網址 {target['url']}，多加 Emoji，結尾加 #旅遊 #自由行。"
        
        # 使用 1.5-flash (免費額度最穩)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        
        # 3. 發布到 Threads
        res = requests.post("https://graph.threads.net/v1.0/me/threads", params={
            'media_type': 'TEXT',
            'text': response.text,
            'access_token': THREADS_TOKEN
        }).json()
        
        if 'id' in res:
            publish = requests.post("https://graph.threads.net/v1.0/me/threads_publish", params={
                'creation_id': res['id'],
                'access_token': THREADS_TOKEN
            }).json()
            print(f"✅ 【{target['name']}】發布成功！")
        else:
            print(f"❌ Threads API 拒絕發文：{res}")
            sys.exit(1)

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        # 如果看到 "Resource has been exhausted"，代表要休息 10 分鐘
        sys.exit(1)

if __name__ == "__main__":
    run()
