import os
import random
import requests
import sys
import time
import datetime
from google import genai

# 1. 讀取 Secrets 與環境變數
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
THREADS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
EVENT_NAME = os.getenv("GITHUB_EVENT_NAME") # 用來判斷是不是手動點擊

# --- 隔週五發文判斷邏輯 ---
current_week = datetime.datetime.now().isocalendar()[1]
if EVENT_NAME != "workflow_dispatch" and current_week % 2 != 0:
    print(f"💡 目前為第 {current_week} 週 (奇數週)，今日休息不發文！")
    sys.exit(0)

# 2. 城市清單 (img_count 代表該城市要抓幾張圖，Threads 最高限制為 10)
CITIES = [
    {"name": "曼谷通", "topic": "曼谷按摩、考山路與泰式美食", "image_name": "BANGKOK", "img_count": 10},
    {"name": "清邁通", "topic": "清邁古城、文青咖啡廳與大象營", "image_name": "ChiangMai", "img_count": 9},
    {"name": "首爾通", "topic": "首爾逛街、漢江公園與韓式燒肉", "image_name": "Seoul", "img_count": 9},
    {"name": "釜山通", "topic": "釜山海雲台、甘川洞文化村與豬肉湯飯", "image_name": "Busan", "img_count": 9},
    {"name": "沖繩通", "topic": "沖繩自駕、美麗海水族館與潛水", "image_name": "Okinawa", "img_count": 9},
    {"name": "新加坡通", "topic": "新加坡環球影城、金沙酒店與肉骨茶", "image_name": "Singapore", "img_count": 9},
    {"name": "福岡通", "topic": "福岡博多拉麵、太宰府天滿宮與屋台", "image_name": "FUKUOKA", "img_count": 9},
    {"name": "京・阪・神通", "topic": "京都花見小路、大阪心齋橋與環球影城", "image_name": "Osaka", "img_count": 9}
]

def run():
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        target = random.choice(CITIES)

        print(f"🎲 準備為【{target['name']}】生成「多圖輪播行銷貼文」...")

        prompt = f"""
        你現在是「Kokko」，一個熱愛出國自由行、講話超接地氣的旅遊狂熱者。
        你要發一篇 Threads 貼文，跟大家分享你整理的專屬【免費】旅遊APP『{target['name']}』。

        📖 **本次貼文要包裝的城市亮點：** {target['topic']}

        📝 **撰寫要求（請完全捨棄 AI 的官方腔調與購物台推銷語氣，用白話文寫）：**
        1. 【直接用痛點開場】：文章第一段『直接』抱怨自由行的痛點，像真人在發牢騷。❌ 絕對禁止使用「吼唷、看過來、挖到寶了、大放送」這種假嗨的開場白！
        2. 【解方與超強功能】：抱怨完後，自然帶出這款【完全免費】的 APP 是救星。必須明確提到它能一次解決：「機場與市內交通攻略、精選住宿推薦、必吃美食地圖、一鍵自排行程，還直接帶出完整的交通轉乘方式」。
        3. 【城市亮點行銷】：用朋友推坑的語氣提一下 {target['topic']} 有多好玩，揉進內文中。
        4. 【留言解鎖與呼籲】：在介紹完之後（文章最後面），說：「只要在下面留言『{target['name']}』，我就把這款神級免費 APP 的連結私訊給你！👇 順便把這篇轉發給那個每次出國都不排行程的雷隊友！」。
        5. 【排版規定】：段落與段落之間『必須空一行』！多用短句。❌ 絕對禁止使用成語或客套詞。善用 Emoji。
        6. 【結尾規定】：留完言呼籲後自然收尾，絕對不要在正文放上任何網址！
        7. 【字數限制】：總字數控制在 350 到 400 字左右（絕對不能超過 450 字）。
        8. 加上標籤 #旅遊 #自由行 #{target['name']}。
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        main_text = response.text.strip()
        
        if len(main_text) > 480:
            print(f"⚠️ 警告：主文字數太長 ({len(main_text)} 字)，已觸發自動截斷！")
            main_text = main_text[:465] + f"...\n\n(留言『{target['name']}』免費拿連結👇)"

        print(f"📸 正在打包【{target['name']}】的 {target['img_count']} 張圖片...")
        children_ids = []
        
        for i in range(1, target['img_count'] + 1):
            # 💡 乾淨俐落的網址，不加任何編碼，直接對應你修改好的檔名
            image_url = f"https://linkuei0425.github.io/images/SPOT/{target['image_name']}({i}).png"
            
            print(f"  - 處理圖片 {i}/{target['img_count']}: {image_url}")
            
            res_item = requests.post("https://graph.threads.net/v1.0/me/threads", params={
                'media_type': 'IMAGE', 
                'image_url': image_url,
                'is_carousel_item': 'true',
                'access_token': THREADS_TOKEN
            }).json()
            
            if 'id' in res_item:
                children_ids.append(res_item['id'])
            else:
                print(f"  ❌ 圖片 {i} 處理失敗：{res_item}")
                
        if not children_ids:
            print("❌ 所有圖片都建立失敗，程式結束。")
            sys.exit(1)
            
        children_str = ",".join(children_ids)

        print(f"📤 1. 正在建立主貼文容器 (Carousel 多圖輪播)...")
        res_main = requests.post("https://graph.threads.net/v1.0/me/threads", params={
            'media_type': 'CAROUSEL', 
            'children': children_str,
            'text': main_text, 
            'access_token': THREADS_TOKEN
        }).json()
        
        if 'id' in res_main:
            publish_main = requests.post("https://graph.threads.net/v1.0/me/threads_publish", params={
                'creation_id': res_main['id'], 
                'access_token': THREADS_TOKEN
            }).json()
            main_post_id = publish_main.get('id')
            
            if not main_post_id:
                print(f"❌ 主貼文發布失敗：{publish_main}")
                sys.exit(1)
                
            print(f"✅ 主貼文發布成功！貼文 ID: {main_post_id}")
            
            print("⏳ 等待 15 秒鐘，讓 Meta 伺服器建檔你的貼文...")
            time.sleep(15)
            
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
                
                publish_reply = requests.post("https://graph.threads.net/v1.0/me/threads_publish", params={
                    'creation_id': res_reply['id'], 
                    'access_token': THREADS_TOKEN
                }).json()
                
                if 'id' in publish_reply:
                    print(f"🎉 留言發布成功！多圖輪播排版完美結束！")
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
