import os
import random
import requests
import sys
import time
from google import genai

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
THREADS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

# 👉 你的 GitHub 資訊
GITHUB_USER = "linkuei0425"
GITHUB_REPO = "threads-auto-poster"

def run():
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        
        # --- A. Gemini 2.5 生成 400 字深度文案與繪圖咒語 ---
        print("🤖 Gemini 2.5 Flash 正在撰寫深度美食評論...")
        
        task_prompt = (
            "你是一位資深美食評論家。任務：\n"
            "1. 隨機挑選一個全球美食主題（例如：老派西餐廳、職人手作壽司、或巷弄隱藏版甜點）。\n"
            "2. 撰寫一段約 400 字的 Threads 貼文（中文）。內容需包含食材來源、口感層次、環境氛圍及個人感悟。語氣要像與朋友對話般自然且富有熱情，多加 Emoji。\n"
            "3. 寫一段該場景的英文繪圖咒語 (Image Prompt)，要求專業食物攝影師風格、極致細節、4k、柔和自然光。請用 '---' 分隔貼文與咒語。"
        )
        
        # 🚀 使用你指定的 Gemini 2.5 Flash
        res = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=task_prompt
        )
        
        parts = res.text.split('---')
        caption = parts[0].strip()
        image_prompt = parts[1].strip() if len(parts) > 1 else "Gourmet food photography, hyper-realistic, 8k"

        # --- B. Imagen 3.0 生成圖片 ---
        print(f"🎨 正在繪製：{image_prompt}")
        
        # 修正後的 2026 SDK 官方生圖語法
        img_res = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=image_prompt,
            config={
                "number_of_images": 1,
                "aspect_ratio": "1:1",
                "output_mime_type": "image/jpeg"
            }
        )
        
        # 儲存圖片到 images/food 資料夾
        img_name = f"food_{int(time.time())}.jpg"
        img_dir = "images/food"
        img_path = f"{img_dir}/{img_name}"
        os.makedirs(img_dir, exist_ok=True)
        
        with open(img_path, "wb") as f:
            f.write(img_res.generated_images[0].image_bytes)
            
        print(f"✅ 圖片生成成功，文案字數：{len(caption)} 字")

        # 暫存數據供下一個步驟使用
        with open("post_data.txt", "w", encoding="utf-8") as f:
            f.write(f"{img_name}\n{caption}")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
