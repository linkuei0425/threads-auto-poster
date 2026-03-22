import os
import random
import requests
import google.generativeai as genai

# 1. 讀取 Secrets 鑰匙
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
THREADS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

# 2. 7 大城市旅遊通 (隨機發文清單)
CITIES = [
    {"name": "曼谷通", "topic": "曼谷按摩、考山路與夜市", "url": "https://linkuei0425.github.io/BANGKOK/"},
    {"name": "清邁通", "topic": "清邁古城、文青咖啡廳與大象營", "url": "https://linkuei0425.github.io/ChiangMai/"},
    {"name": "首爾通", "topic": "首爾逛街、漢江公園與韓式燒肉", "url": "https://linkuei0425.github.io/Seoul/"},
    {"name": "釜山通", "topic": "釜山海雲台、甘川洞文化村與豬肉湯飯", "url": "https://linkuei0425.github.io/Busan/"},
    {"name": "沖繩通", "topic": "沖繩自駕、美麗海水族館與潛水", "url": "https://linkuei0425.github.io/Okinawa/"},
    {"name": "新加坡通", "topic": "新加坡環球影城、金沙酒店與肉骨茶", "url": "https://linkuei0425.github.io/Singapore/"},
    {"name": "福岡通", "topic": "福岡博多拉麵、太宰府天滿宮與屋台", "url": "https://linkuei0425.github.io/FUKUOKA/"},
 {"name": "京．阪．神通", "topic": "京都花見小路、大阪心齋橋逛街", "url": "https://linkuei0425.github.io/Osaka/"}
]

# 3. 設定 Gemini 2.0 Flash
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def generate_and_post():
    try:
        target = random.choice(CITIES)
        print(f"🚀 正在為【{target['name']}】準備文案...")
        prompt = f"你是一位風趣的旅遊達人。請為『{target['name']}』寫一段 80 字內的 Threads 貼文，主題是：{target['topic']}。必須包含網址 {target['url']} 並多加 Emoji，結尾加 #旅遊 #自由行。"
        
        response = model.generate_content(prompt)
        content = response.text

        # 4. 發布到 Threads
        base_url = "https://graph.threads.net/v1.0/me"
        res = requests.post(f"{base_url}/threads", params={
            'media_type': 'TEXT', 'text': content, 'access_token': THREADS_TOKEN
        }).json()
        
        if 'id' in res:
            publish = requests.post(f"{base_url}/threads_publish", params={
                'creation_id': res['id'], 'access_token': THREADS_TOKEN
            }).json()
            print(f"✅ 【{target['name']}】發布成功！")
        else:
            print(f"❌ Threads API 錯誤：{res}")
    except Exception as e:
        print(f"❌ 發生錯誤：{e}")

if __name__ == "__main__":
    generate_and_post()
