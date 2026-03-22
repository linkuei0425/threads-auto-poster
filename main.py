import os
import random
import requests
import google.generativeai as genai
import sys

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
THREADS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

# 2. 7 大城市旅遊通
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

def run():
    try:
        genai.configure(api_key=GEMINI_KEY)
        
        # 【核心修正】自動尋找可用的模型名稱
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"✅ 你的帳號可用模型列表: {available_models}")
        
        # 優先順序：2.0 Flash -> 1.5 Pro -> 1.5 Flash -> 隨便一個能用的
        selected_model = ""
        for preferred in ['models/gemini-2.0-flash', 'models/gemini-1.5-pro', 'models/gemini-1.5-flash']:
            if preferred in available_models:
                selected_model = preferred
                break
        if not selected_model:
            selected_model = available_models[0]
            
        print(f"🎯 最終決定使用：{selected_model}")
        model = genai.GenerativeModel(selected_model)

        # 隨機選城市寫文案
        target = random.choice(CITIES)
        prompt = f"你是一位活潑的旅遊領隊。請為『{target['name']}』寫一段 80 字內的 Threads 旅遊貼文，主題是：{target['topic']}。必須包含網址 {target['url']}，多加 Emoji，結尾加 #旅遊 #自由行。"
        
        response = model.generate_content(prompt)
        
        # Threads 發文
        res = requests.post("https://graph.threads.net/v1.0/me/threads", params={
            'media_type': 'TEXT', 'text': response.text, 'access_token': THREADS_TOKEN
        }).json()
        
        if 'id' in res:
            requests.post("https://graph.threads.net/v1.0/me/threads_publish", params={
                'creation_id': res['id'], 'access_token': THREADS_TOKEN
            })
            print(f"🚀 【{target['name']}】發布成功！")
        else:
            print(f"❌ Threads 錯誤：{res}")
            sys.exit(1)

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
