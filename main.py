import os
import random
import requests
import google.generativeai as genai
import sys

# 1. 讀取金鑰
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
THREADS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

# 2. 七大旅遊通資料 (依據你的截圖修正網址)
CITIES = [
    {"name": "清邁通", "topic": "清邁古城、文青咖啡廳與大象營", "url": "https://linkuei0425.github.io/ChiangMai/"},
    {"name": "首爾通", "topic": "首爾逛街、漢江公園與韓式燒肉", "url": "https://linkuei0425.github.io/Seoul/"},
    {"name": "釜山通", "topic": "釜山海雲台、甘川洞文化村與豬肉湯飯", "url": "https://linkuei0425.github.io/Busan/"},
    {"name": "沖繩通", "topic": "沖繩自駕、美麗海水族館與潛水", "url": "https://linkuei0425.github.io/Okinawa/"},
    {"name": "新加坡通", "topic": "新加坡環球影城、金沙酒店與肉骨茶", "url": "https://linkuei0425.github.io/Singapore/"},
    {"name": "福岡通", "topic": "福岡博多拉麵、太宰府天滿宮與屋台", "url": "https://linkuei0425.github.io/FUKUOKA/"},
    {"name": "京・阪・神通", "topic": "京都花見小路、大阪心齋橋逛街", "url": "https://linkuei0425.github.io/Osaka/"}
]

def run():
    try:
        # 3. 使用最穩定的配置語法
        genai.configure(api_key=GEMINI_KEY)
        # 這裡我們用最通用的 1.5-flash，避開 404
        model = genai.GenerativeModel('gemini-1.5-flash')

        target = random.choice(CITIES)
        print(f"🎲 準備生成：【{target['name']}】")

        prompt = f"你是一位活潑的旅遊領隊。請為『{target['name']}』寫一段 80 字內的 Threads 貼文，主題是：{target['topic']}。必須包含網址 {target['url']}，多加 Emoji，結尾加 #旅遊 #自由行。"
        
        response = model.generate_content(prompt)
        content = response.text

        # 4. 發布到 Threads
        res = requests.post("https://graph.threads.net/v1.0/me/threads", params={
            'media_type': 'TEXT',
            'text': content,
            'access_token': THREADS_TOKEN
        }).json()
        
        if 'id' in res:
            publish = requests.post("https://graph.threads.net/v1.0/me/threads_publish", params={
                'creation_id': res['id'],
                'access_token': THREADS_TOKEN
            }).json()
            print(f"✅ 發布成功！貼文 ID: {publish.get('id')}")
        else:
            print(f"❌ Threads API 錯誤：{res}")
            sys.exit(1)

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
