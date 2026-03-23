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
        print(f"🎲 準備為【{target['name']}】生成專業行銷文案...")

        # 💡 全新升級的專業行銷 Prompt
        prompt = f"""
        你是一位資深的「專業旅遊專家」。請為這款專屬旅遊APP『{target['name']}』撰寫一篇 Threads 貼文，主題與涵蓋範圍為：{target['topic']}。

        📝 撰寫要求：
        1. 【語氣與身分】：展現專業、權威但又懂旅客心思的旅遊達人語氣。
        2. 【痛點與優點】：精準點出自由行旅客的痛點（例如：排行程排到心累、踩雷吃到難吃餐廳、迷路找路花時間等），並說明這款 APP 如何解決這些問題。
        3. 【強調免費】：強力主打這是一份「完全免費的終極攻略」，吸引讀者想要立刻獲取。
        4. 【排版規定（極度重要）】：段落與段落之間『必須空一行』！請多利用短句，善用列點與 Emoji，絕對不要把文字全部擠成一團，保持版面清爽好讀！
        5. 【字數限制】：總字數控制在 350 到 400 字左右（絕對不能超過 450 字，以符合 Threads 限制）。
        6. 【無網址規定】：絕對不要在正文中包含任何網址連結！結尾只要引導說「🔗 完整免費攻略連結我放在一樓留言👇」即可。
        7. 加上標籤 #旅遊 #自由行 #{target['name']}。
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        main_text = response.text.strip()
        
        # 💡 防呆機制：確保字數不會爆炸
        if len(main_text) > 480:
            print(f"⚠️ 警告：主文字數太長 ({len(main_text)} 字)，已觸發自動截斷！")
            main_text = main_text[:465] + "...\n\n(完整免費攻略請看一樓留言👇)"

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
            
            # ⏳ 加長煞車時間：給 Meta 全球伺服器 15 秒鐘同步資料
            print("⏳ 等待 15 秒鐘，讓 Meta 伺服器建檔你的主貼文...")
            time.sleep(15)
            
            # 📤 2. 建立留言容器 (網址放在這裡)
            print("📤 2. 正在建立留言區連結...")
            reply_text = f"👇 剛剛提到的【{target['name']}】完全免費攻略與私房地圖，連結幫大家整理好啦，直接點擊使用：\n{target['url']}"
            
            res_reply = requests.post("https://graph.threads.net/v1.0/me/threads", params={
                'media_type': 'TEXT', 
                'text': reply_text, 
                'reply_to_id': main_post_id, # 指定回覆給剛剛發佈的主貼文
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
                    print(f"🎉 留言連結發布成功！【專業推廣文+網址留言】排版完美結束！")
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
