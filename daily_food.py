import os
import random
import requests
import sys
import time
from google import genai
from PIL import Image
import io

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
THREADS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

# 👉 確認你的 GitHub 資訊
GITHUB_USER = "linkuei0425"
GITHUB_REPO = "threads-auto-poster"
BASE_IMAGE_URL = f"https://{GITHUB_USER}.github.io/{GITHUB_REPO}/images/food/"

def run():
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        
        # --- A. Gemini 2.5 寫文案 + 寫繪圖咒語 ---
        print("🤖 Gemini 正在構思今日美食主題...")
        task_prompt = "你是頂級美食博主。任務：1.隨機挑選一個全球美食主題。2.寫一段60字Threads貼文(中文)。3.寫一段該美食的英文繪圖咒語(Image Prompt)，要求極致美味感、專業攝影、8k。請用 '---' 分隔貼文與咒語。"
        
        # 既然你說 2.5 沒問題，我們就用 2.5
        res = client.models.generate_content(model='gemini-2.5-flash', contents=task_prompt)
        parts = res.text.split('---')
        caption = parts[0].strip()
        image_prompt = parts[1].strip() if len(parts) > 1 else "Professional food photography"

        # --- B. Imagen 3 生成圖片 ---
        print(f"🎨 正在為你繪製：{image_prompt}")
        img_res = client.models.generate_image(
            model='imagen-3-001-generative',
            prompt=image_prompt,
            config={"number_of_images": 1, "aspect_ratio": "1:1"}
        )
        
        # 確保資料夾存在並儲存圖片
        img_name = f"food_{int(time.time())}.jpg"
        img_path = f"images/food/{img_name}"
        os.makedirs("images/food", exist_ok=True)
        
        img = Image.open(io.BytesIO(img_res.images[0].image_bytes))
        img.save(img_path, "JPEG")
        print(f"✅ 圖片已存至：{img_path}")

        # 將文案與圖名存起來給下一個階段用
        with open("post_data.txt", "w", encoding="utf-8") as f:
            f.write(f"{img_name}\n{caption}")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
