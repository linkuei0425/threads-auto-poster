import os
import random
import requests
import sys
import time
import io
from PIL import Image
from google import genai

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
THREADS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

# 👉【請修改這裡】填入你的 GitHub 用戶名和專案名稱
GITHUB_USER = "linkuei0425"  # 如果這是你的用戶名請保留
REPO_NAME = "你的專案名稱"     # 填入你 GitHub 專案的名字
BASE_URL = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/images/food/"

def run():
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        
        # --- 第一步：讓 Gemini 隨機想一個美食主題並寫「英文繪圖咒語」 ---
        print("🤖 Gemini 正在構思今日的美食與繪圖咒語...")
        prompt_task = """
        請隨機選一個具有視覺吸引力的美食（如：熔岩巧克力、台式滷肉飯、五彩壽司）。
        執行任務：
        1. 寫一段 60 字內的 Threads 中文貼文。
        2. 寫一段專業的英文繪圖提示詞 (Image Prompt)，要求：美食攝影風格、極致細節、4k、光線誘人。
        請用 '---' 分隔貼文與提示詞。
        """
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt_task
        )
        
        parts = response.text.split('---')
        caption = parts[0].strip()
        image_prompt = parts[1].strip() if len(parts) > 1 else "Gourmet food photography"

        # --- 第二步：使用 Imagen 3 產生圖片 (這就是你問的第 3 部份代碼位置) ---
        print(f"🎨 Imagen 3 正在繪製：{image_prompt}")
        image_res = client.models.generate_image(
            model='imagen-3-001-generative',
            prompt=image_prompt,
            config={"number_of_images": 1, "aspect_ratio": "1:1"}
        )
        
        # 取得圖片數據並儲存
        generated_image = image_res.images[0]
        timestamp = int(time.time())
        img_filename = f"food_{timestamp}.jpg"
        img_dir = "images/food"
        
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
            
        img_path = os.path.join(img_dir, img_filename)
        img = Image.open(io.BytesIO(generated_image.image_bytes))
        img.save(img_path, "JPEG")
        print(f"✅ 圖片已儲存至：{img_path}")

        # --- 第三步：將圖文發布到 Threads ---
        # 注意：圖片網址必須是公開的（GitHub Pages 網址）
        public_img_url = f"{BASE_URL}{img_filename}"
        print(f"📤 準備發布貼文至 Threads，圖片網址：{public_img_url}")
        
        # 1. 建立媒體容器
        res = requests.post("https://graph.threads.net/v1.0/me/threads", params={
            'media_type': 'IMAGE', 'image_url': public_img_url, 'access_token': THREADS_TOKEN
        }).json()
        
        if 'id' in res:
            # 2. 正式發布 (給 Threads 5秒處理圖片)
            time.sleep(5)
            requests.post("https://graph.threads.net/v1.0/me/threads_publish", params={
                'creation_id': res['id'], 'text': caption, 'access_token': THREADS_TOKEN
            })
            print(f"🎉 美食圖文發布成功！")
        else:
            print(f"❌ 建立容器失敗，可能圖片網址尚未生效：{res}")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
