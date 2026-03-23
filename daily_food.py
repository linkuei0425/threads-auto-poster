import os
import random
import requests
import sys
import time
from google import genai

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
THREADS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

CITIES = [
    {"name": "曼谷", "topic": "在地街頭美食（如烤豬肉串、青木瓜沙拉）的層次感", "url": "https://linkuei0425.github.io/Bangkok/"},
    {"name": "清邁", "topic": "蘭納風格咖啡廳的慢活氛圍與特色特調", "url": "https://linkuei0425.github.io/ChiangMai/"},
    {"name": "首爾", "topic": "布帳馬車的深夜療癒美食與在地飲酒文化", "url": "https://linkuei0425.github.io/Seoul/"},
    {"name": "釜山", "topic": "札嘎其市場的新鮮海產或豬肉湯飯的濃厚滋味", "url": "https://linkuei0425.github.io/Busan/"},
    {"name": "沖繩", "topic": "石垣牛入口即化的口感或萬座毛的壯麗海景", "url": "https://linkuei0425.github.io/Okinawa/"},
    {"name": "新加坡", "topic": "老巴剎或麥士威熟食中心的海南雞飯與族群融合氣息", "url": "https://linkuei0425.github.io/Singapore/"},
    {"name": "福岡", "topic": "博多拉麵的濃厚湯頭與屋台文化的獨特體驗", "url": "https://linkuei0425.github.io/FUKUOKA/"},
    {"name": "京阪神", "topic": "京都宇治抹香、大阪道頓堀的熱鬧食道或是神戶牛排", "url": "https://linkuei0425.github.io/Osaka/"}
]

def run():
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        target = random.choice(CITIES)
        print(f"🎲 準備生成【{target['name']}】深度文案...")

        prompt = f"""
        你是一位感性且專業的深度旅遊作家。請為『{target['name']}』寫一篇 Threads 貼文，介紹【{target['topic']}】。
        要求：
        1. 內容豐富，字數嚴格控制在 400 到 450 字之間（不含地址）。
        2. 請用第一人稱敘事，描寫詳細的視覺、嗅覺、味覺體驗，排版要有空行感。
        3. 結尾設計一個引起共鳴的互動問題。
        4. 加上標籤 #旅遊 #自由行 #{target['name']}。
        5. ⚠️ 禁止正文出現連結！
        6. 重要格式：文章結束後，請輸入標籤 [ADDRESS]，隨後寫出文中提到的具體地點的正確地址。
        """
        
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        full_output = response.text.strip()
        
        # 拆分主文與地址
        if "[ADDRESS]" in full_output:
            parts = full_output.split("[ADDRESS]")
            main_text = parts[0].strip()
            spot_address = parts[1].strip()
        else:
            main_text = full_output
            spot_address = "查看攻略地圖獲取詳細位置"

        # Threads 500字保險絲
        if len(main_text) > 485:
            main_text = main_text[:475] + "..."

        # --- 第一步：發布主文 ---
        print("📤 1. 發布深度主文...")
        res_main = requests.post("https://graph.threads.net/v1.0/me/threads", params={'media_type': 'TEXT', 'text': main_text, 'access_token': THREADS_TOKEN}).json()
        
        if 'id' in res_main:
            publish_main = requests.post("https://graph.threads.net/v1.0/me/threads_publish", params={'creation_id': res_main['id'], 'access_token': THREADS_TOKEN}).json()
            main_id = publish_main.get('id')
            
            # 煞車時間（關鍵）
            print("⏳ 等待 20 秒鐘讓伺服器建檔...")
            time.sleep(20)
            
            # --- 第二步：建立並發布留言 ---
            print("📤 2. 正在發布地址與連結...")
            reply_text = f"📍 詳細地址資訊：\n{spot_address}\n\n---\n👇 想看更多【{target['name']}】的私房行程表與完整攻略：\n{target['url']}"
            
            res_reply = requests.post("https://graph.threads.net/v1.0/me/threads", params={'media_type': 'TEXT', 'text': reply_text, 'reply_to_id': main_id, 'access_token': THREADS_TOKEN}).json()
            
            if 'id' in res_reply:
                time.sleep(5)
                requests.post("https://graph.threads.net/v1.0/me/threads_publish", params={'creation_id': res_reply['id'], 'access_token': THREADS_TOKEN})
                print(f"🎉 【{target['name']}】全自動發文完成！")
            else:
                print(f"❌ 留言建立失敗：{res_reply}")
        else:
            print(f"❌ 主文建立失敗：{res_main}")
            sys.exit(1)

    except Exception as e:
        print(f"💥 發生錯誤：{e}")

if __name__ == "__main__":
    run()
