import os
import random
import requests
import google.generativeai as genai

# 1. 讀取 Secrets 鑰匙
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
THREADS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

# 2. 設定 7 大城市清單 (你可以之後隨時改 URL)
CITIES = [
    {"name": "曼谷通", "topic": "曼谷旅遊、泰式按摩與夜市", "url": "https://linkuei0425.github.io/BANGKOK/"},
    {"name": "清邁通", "topic": "清邁古城、文青咖啡廳與大象營", "url": "https://linkuei0425.github.io/ChiangMai/"},
    {"name": "首爾通", "topic": "首爾逛街、韓式燒肉與樂天世界", "url": "https://linkuei0425.github.io/Seoul/"},
    {"name": "釜山通", "topic": "釜山海景、海雲台與豬肉湯飯", "url": "https://linkuei0425.github.io/Busan/"},
    {"name": "沖繩通", "topic": "沖繩自駕、美麗海水族館與海灘", "url": "https://linkuei0425.github.io/Okinawa/"},
    {"name": "新加坡通", "topic": "新加坡環球影城、魚尾獅與美食", "url": "https://linkuei0425.github.io/Singapore/"},
    {"name": "福岡通", "topic": "福岡博多拉麵、屋台文化與太宰府", "url": "https://linkuei0425.github.io/FUKUOKA/"}
]

# 3. 設定 Gemini 3.1 Pro
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-3.1-pro')

def generate_and_post():
    try:
        # 隨機挑選一個城市
        target = random.choice(CITIES)
        print(f"🎲 準備生成：{target['name']}")

        # 叫 Gemini 3.1 Pro 寫文案
        prompt = f"你是一位幽默的旅遊部落客。請為『{target['name']}』寫一段 80 字內的 Threads 貼文，主題是：{target['topic']}。必須包含網址 {target['url']} 並多加 Emoji，結尾加 #旅遊 #自由行。"
        
        response = model.generate_content(prompt)
        content = response.text

        # 4. 發布到 Threads
        base_url = "https://graph.threads.net/v1.0/me"
        res = requests.post(f"{base_url}/threads", params={
            'media_type': 'TEXT',
            'text': content,
            'access_token': THREADS_TOKEN
        }).json()
        
        if 'id' in res:
            publish = requests.post(f"{base_url}/threads_publish", params={
                'creation_id': res['id'],
                'access_token': THREADS_TOKEN
            }).json()
            print(f"✅ 【{target['name']}】發布成功！貼文 ID: {publish.get('id')}")
        else:
            print(f"❌ Threads API 錯誤：{res}")
    except Exception as e:
        print(f"❌ 發生錯誤：{e}")

if __name__ == "__main__":
    generate_and_post()generate_and_post()
