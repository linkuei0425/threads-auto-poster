import os
import sys
import time
from google import genai
from google.genai import types

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def run():
    try:
        if not GEMINI_KEY:
            raise Exception("缺少 GEMINI_API_KEY 環境變數")
            
        client = genai.Client(api_key=GEMINI_KEY)
        
        # --- A. Gemini 生成景點文案 ---
        print("🤖 Gemini 正在亞洲精選城市中尋找絕美景點...")
        target_cities = "曼谷、清邁、釜山、首爾、新加坡、沖繩、宮古島、福岡"
        
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的專業旅遊創作者。任務：\n"
            f"1. 從以下城市中『隨機挑選一個』：{target_cities}。\n"
            f"2. 挑選該城市中一個『真實存在』的知名地標、私房秘境或絕美打卡景點（請勿介紹餐廳或美食）。\n"
            f"3. 撰寫一段 Threads 貼文主文（中文）。以第一人稱（Kokko）分享，描述風景特色與旅遊當下的感動，語氣生動熱情，多用符合情境的 Emoji。\n"
            f"⚠️ 極度重要：主文字數（含標點符號與Emoji）『絕對不可以超過 350 字』！\n"
            f"4. 撰寫一段該景點的英文繪圖咒語 (Image Prompt)，風格必須是高畫質風景攝影 (high-quality landscape photography)、光影唯美、構圖大氣。\n"
            f"5. 撰寫一條留言內容，格式為：『📍 景點名稱：XXX \\n📍 所在城市：XXX \\n📍 交通方式/地址：XXX』。\n"
            f"請嚴格使用 '---' 分隔這三部分（主文---咒語---留言內容）。"
        )
        
        res = client.models.generate_content(model='gemini-2.5-flash', contents=task_prompt)
        parts = res.text.split('---')
        caption = parts[0].strip() if len(parts) > 0 else "無法生成貼文內容"
        image_prompt = parts[1].strip() if len(parts) > 1 else "Professional landscape photography, 8k, highly detailed"
        comment_text = parts[2].strip() if len(parts) > 2 else "📍 景點資訊確認中..."

        # 💡 防呆機制：超過 480 字直接強制卡掉，保護 API 不出錯
        if len(caption) > 480:
            print(f"⚠️ 警告：生成的字數太長 ({len(caption)} 字)，已觸發自動截斷機制！")
            caption = caption[:475] + "..."

        # 💡 曼谷推廣連結 (針對景點微調文案，記得換成真實網址！)
        if "曼谷" in caption or "曼谷" in comment_text:
            promo_text = "\n\n🇹🇭 想知道這附近還有什麼好玩的嗎？快用我的【曼谷通】APP 輕鬆查看看！ 👉 https://你的曼谷通網址.com"
            comment_text += promo_text

        # --- B. Gemini 生成圖片並儲存 ---
        print(f"🎨 正在繪製景點：{image_prompt}")
        img_res = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=image_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="1:1")
            )
        )
        
        img_name = f"spot_{int(time.time())}.jpg"
        img_dir = "images/spot" # 💡 存入不同的資料夾
        os.makedirs(img_dir, exist_ok=True)
        local_img_path = f"{img_dir}/{img_name}"
        
        for part in img_res.parts:
            if part.inline_data:
                part.as_image().save(local_img_path)
                break
                
        # --- C. 寫入暫存檔 ---
        with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_name)
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        with open("comment.txt", "w", encoding="utf-8") as f: f.write(comment_text)
            
        print(f"✅ 景點版任務完成！主文字數：{len(caption)}")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
