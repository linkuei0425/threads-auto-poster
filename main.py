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
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        target = random.choice(CITIES)
        print(f"🎲 準備為【{target['name']}】生成痛點行銷貼文...")

        # 💡 強調痛點先行的專業行銷 Prompt
        prompt = f"""
        你是一位資深的「專業旅遊專家與行銷達人」。請為專屬旅遊APP『{target['name']}』撰寫一篇 Threads 貼文，涵蓋的城市亮點為：{target['topic']}。

        📝 撰寫要求：
        1. 【開頭直擊痛點與解方（極度重要）】：貼文一開始，請立刻點出自由行旅客的痛點（例如：排行程排到崩潰、找路迷路、怕踩雷吃到超雷餐廳等），並「緊接著」宣告這款『{target['name']}』APP 是完全免費的救星，能完美解決這些問題。
        2. 【城市亮點行銷】：在解決痛點後，用極具吸引力、讓人想立刻買機票的專業文案，包裝並介紹 {target['name']} 的魅力（{target['topic']}），讓讀者覺得有了這個 APP，就能完美享受這些行程。
        3. 【排版規定】：段落與段落之間『必須空一行』！請多利用短句，善用列點與 Emoji，保持版面清爽好讀，展現專業感。
        4. 【字數限制】：總字數控制在 350 到 400 字左右（絕對不能超過 450 字，以符合 Threads 限制）。
        5. 【無網址規定】：絕對不要在正文中包含任何網址連結！結尾只要強力呼籲「🔗 完全免費的 APP 與終極攻略連結，我放在一樓留言👇 趕快存起來！」即可。
        6. 加上標籤 #旅遊 #自由行 #{target['name']}。
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        main_text = response.text.strip()
        
        # 💡 防呆機制：確保字數不會爆炸
        if len(main_text) > 480:
            print(f"⚠️ 警告：主文字數太長 ({len(main_text)} 字)，已觸發自動截斷！")
            main_text = main_text[:465] + "...\n\n(完整免費 APP 連結請看一樓留言👇)"

        # 📤 1. 建立主貼文
        print("📤 1. 正在發布主貼文...")
        res_main = requests.post("https://graph.threads.net/v1.0/me/threads", params={
            'media_type': 'TEXT', 
            'text': main_text, 
            'access_token': THREADS_TOKEN
        }).json()
        
        if 'id' in res_main:
            # 發布主貼文
            publish_main = requests.post("https://graph.threads.net/v1.0/me/threads_publish", params={
                'creation_id': res_main['id'], 
                'access_token': THREADS_TOKEN
            }).json()
            main_post_id = publish_main.get('id')
            
            if not main_post_id:
                print(f"❌ 主貼文發布失敗：{publish_main}")
                sys.exit(1)
                
            print(f"✅ 主貼文發布成功！貼文 ID: {main_post_id}")
            
            # ⏳ 加長煞車時間
            print("⏳ 等待 15 秒鐘，讓 Meta 伺服器建檔你的主貼文...")
            time.sleep(15)
            
            # 📤 2. 建立留言容器 (網址放在這裡)
            print("📤 2. 正在建立留言區連結...")
            # 💡 留言處也保持專業高價值的行銷語氣
            reply_text = f"👇 剛剛提到的【{target['name']}】完全免費 APP 與終極攻略，連結幫大家準備好了，點擊馬上開始規劃你的完美旅程：\n{target['url']}"
            
            res_reply = requests.post("https://graph.threads.net/v1.0/me/threads", params={
                'media_type': 'TEXT', 
                'text': reply_text, 
                'reply_to_id': main_post_id, 
                'access_token': THREADS_TOKEN
            }).json()
            
            if 'id' in res_reply:
                print("⏳ 留言容器已建立，等待 5 秒鐘進行最終發布...")
                time.sleep(5) 
                
                # 發布留言
                publish_reply = requests.post("https://graph.threads.net/v1.0/me/threads_publish", params={
                    'creation_id': res_reply['id'], 
                    'access_token': THREADS_TOKEN
                }).json()
                
                if 'id' in publish_reply:
                    print(f"🎉 留言連結發布成功！【痛點行銷文+網址留言】排版完美結束！")
                else:
                    print(f"❌ 留言【發布】失敗：{publish_reply}")
            else:
                print(f"❌ 留言【建立】失敗：{res_reply}")
        else:
            print(f"❌ 建立主貼文失敗：{res_main}")
            sys.exit(1)

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
