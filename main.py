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

        print(f"🎲 準備為【{target['name']}】生成「開頭留言解鎖+開頭呼籲分享」純文字行銷貼文...")

        # 💡 大幅修改 Prompt：注入真人語氣 (Kokko)、痛點直擊與 APP 超強功能
        prompt = f"""
        你現在不是機器人，你是「Kokko」，一個熱愛出國自由行、講話超接地氣的旅遊狂熱者。
        你要發一篇 Threads 貼文，跟大家分享你整理的專屬【免費】旅遊APP『{target['name']}』。

        📖 **本次貼文要包裝的城市亮點：** {target['topic']}

        📝 **撰寫要求（請完全捨棄 AI 的官方腔調，用語氣詞、白話文、甚至一點點吐槽來寫）：**
        1. 【開頭破題與擴散呼籲】：第一段直接丟好康，請用類似這種語氣：「只要在下面留言『{target['name']}』，我就把這款超神又【完全免費】的 APP 連結私訊給你！👇 趕快把這篇轉發給那個每次出國都不排行程的雷隊友！」。
        2. 【痛點直擊】：用真人的口吻抱怨一下自由行有多崩潰（例如：一出機場不知怎麼搭車怕被當肥羊宰、找住宿怕踩雷、排行程找路找到快吵架...等）。
        3. 【解方與超強功能】：隆重介紹這個免費 APP 怎麼拯救大家。必須明確提到它能一次解決：「機場與市內交通攻略、精選住宿推薦、必吃美食地圖、一鍵自排行程，還直接帶出完整的交通轉乘方式」。
        4. 【城市亮點行銷】：用很嗨的語氣提一下 {target['topic']} 有多好玩，把這些亮點自然揉進去，讓人看了就想馬上買機票。
        5. 【排版規定（嚴格遵守）】：段落與段落之間『必須空一行』！多用短句。❌ 絕對禁止使用成語或客套詞（如：深入探討、不可否認、為您帶來、彷彿）。善用 Emoji，絕對不要把文字擠成一團。
        6. 【結尾規定】：像朋友一樣自然收尾就好，絕對不要在正文放上任何網址！
        7. 【字數限制】：總字數控制在 350 到 400 字左右（絕對不能超過 450 字）。
        8. 加上標籤 #旅遊 #自由行 #{target['name']}。
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        main_text = response.text.strip()
        
        # 💡 防呆機制：確保字數不會爆炸
        if len(main_text) > 480:
            print(f"⚠️ 警告：主文字數太長 ({len(main_text)} 字)，已觸發自動截斷！")
            main_text = main_text[:465] + f"...\n\n(留言『{target['name']}』免費拿連結👇)"

        # 📤 1. 建立純文字主貼文
        print("📤 1. 正在建立主貼文容器 (純文字)...")
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
            print("⏳ 等待 15 秒鐘，讓 Meta 伺服器建檔你的貼文...")
            time.sleep(15)
            
            # 📤 2. 建立留言容器
            print("📤 2. 正在建立留言區...")
            reply_text = f"👍 留言給我，我就會把【{target['name']}】的免費 APP 連結傳給你囉！"
            
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
                    print(f"🎉 留言發布成功！排版完美結束！")
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
