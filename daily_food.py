import os
import random
import requests
import sys
import time
from google import genai

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def run():
    try:
        # 2026 年最新版 SDK 初始化
        client = genai.Client(api_key=GEMINI_KEY)
        
        # --- A. Gemini 2.5 生成長文、咒語與留言 ---
        print("🤖 Gemini 2.5 Flash 正在搜尋真實名店並撰寫長文...")
        
        task_prompt = (
            "你是一位專業美食評論家。任務：\n"
            "1. 隨機選一個『真實存在』的知名餐廳或隱藏版老店。\n"
            "2. 撰寫一段約 400 字的 Threads 貼文（中文）。描述口感細節與現場氛圍，語氣感性且生動，多用 Emoji。\n"
            "3. 撰寫一段該美食的英文繪圖咒語 (Image Prompt)。\n"
            "4. 撰寫一條留言內容，格式為：『📍 店名：XXX \\n📍 地址：XXX』。\n"
            "請嚴格使用 '---' 分隔這三部分（主文---咒語---留言內容）。"
        )
        
        res = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=task_prompt
        )
        
        # 拆分內容
        parts = res.text.split('---')
        caption = parts[0].strip()
        image_prompt = parts[1].strip() if len(parts) > 1 else "Professional gourmet food photography, 8k"
        comment_text = parts[2].strip() if len(parts) > 2 else "📍 地址資訊確認中..."

        # --- B. Imagen 3.0 生成圖片 (嘗試穩定型號名稱) ---
        print(f"🎨 正在繪製：{image_prompt}")
        
        # 修正：在 2026 SDK 中，這通常是付費帳戶最穩定的模型名稱
        img_res = client.models.generate_images(
            model='imagen-3.0-generate-001', 
            prompt=image_prompt,
            config={
                "number_of_images": 1,
                "aspect_ratio": "1:1",
                "output_mime_type": "image/jpeg"
            }
        )
        
        img_name = f"food_{int(time.time())}.jpg"
        img_dir = "images/food"
        os.makedirs(img_dir, exist_ok=True)
        
        with open(f"{img_dir}/{img_name}", "wb") as f:
            f.write(img_res.generated_images[0].image_bytes)

        # --- C. 寫入多個暫存檔 (解決 Shell 讀取換行問題) ---
        with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_name)
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        with open("comment.txt", "w", encoding="utf-8") as f: f.write(comment_text)
            
        print(f"✅ Gemini 2.5 任務完成！主文字數：{len(caption)}")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        # 如果 imagen-3.0-generate-001 還是報 404，這裡會噴出詳細錯誤
        sys.exit(1)

if __name__ == "__main__":
    run()
