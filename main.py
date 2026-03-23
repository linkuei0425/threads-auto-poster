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
        print(f"🎲 準備為【{target['name']}】生成文案...")

        prompt = f"""
        你是一位充滿熱情且專業的旅遊部落客。請為『{target['name']}』寫一篇 Threads 貼文。
        主題是：{target['topic']}。
        要求：
        1. 總字數嚴格限制在 200 到 300 字之間。
        2. 善用生動的描述、適當的空行排版與 Emoji。
        3. 結尾必須有一個互動問句引導留言。
        4. 加上標籤 #旅遊 #自由行 #{target['name']}。
        5. 絕對不要在正文中包含任何網址連結！只要說「完整攻略請看一樓留言👇」即可。
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        main_text = response.text.strip()
        
        if len(main_text) > 480:
            main_text = main_text[:470] + "...\n\n(完整攻略請看一樓留言👇)"

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
            
            # 📤 2. 建立留言容器
            print("📤 2. 正在建立留言區連結...")
            reply_text = f"👇 專屬你的【{target['name']}】完整攻略與私房行程表，我整理在這邊了：\n{target['url']}"
            
            res_reply = requests.post("https://graph.threads.net/v1.0/me/threads", params={
                'media_type': 'TEXT', 
                'text': reply_text, 
                'reply_to_id': main_post_id, # 指定回覆給剛剛發佈的主貼文
                'access_token': THREADS_TOKEN
            }).json()
            
            if 'id' in res_reply:
                print("⏳ 留言容器已建立，等待 5 秒鐘進行最終發布...")
                time.sleep(5) # 再給一個小煞車，確保留言內容也被伺服器準備好
                
                # 發布留言
                publish_reply = requests.post("https://graph.threads.net/v1.0/me/threads_publish", params={
                    'creation_id': res_reply['id'], 
                    'access_token': THREADS_TOKEN
                }).json()
                
                if 'id' in publish_reply:
                    print(f"🎉 留言連結發布成功！【主文+留言】排版完美結束！")
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
