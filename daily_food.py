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
        client = genai.Client(api_key=GEMINI_KEY)
        
        # --- A. Gemini 2.5 生成深度內容 ---
        print("🤖 Gemini 2.5 Flash 正在構思 400 字深度食記...")
        
        task_prompt = (
            "你是一位專業美食評論家。任務：\n"
            "1. 隨機選一個『真實存在』的知名餐廳。\n"
            "2. 撰寫一段約 400 字的 Threads 貼文（中文）。內容需感性且生動，描述食物靈魂與現場氛圍，多加 Emoji。\n"
            "3. 撰寫一條留言內容，格式為：『📍 店名：XXX \\n📍 地址：XXX』。\n"
            "4. 撰寫該美食的英文繪圖咒語 (Image Prompt)。\n"
            "請嚴格使用 '---' 分隔這三部分（主文---咒語---留言）。"
        )
        
        # 使用你指定的 2.5 Flash 模型
        res = client.models.generate_content(model='gemini-2.5-flash', contents=task_prompt)
        parts = res.text.split('---')
        
        caption = parts[0].strip()
        image_prompt = parts[1].strip() if len(parts) > 1 else "Professional food photography, 8k"
        comment_text = parts[2].strip() if len(parts) > 2 else "📍 地址資訊確認中..."

        # --- B. Imagen 3.0 生成圖片 (使用完整型號) ---
        print(f"🎨 正在繪圖：{image_prompt}")
        
        # 修正：使用完整型號名稱 imagen-3.0-generate-001
        img_res = client.models.generate_images(
            model='imagen-4.0-generate-001', 
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

        # --- C. 寫入暫存檔 ---
        with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_name)
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        with open("comment.txt", "w", encoding="utf-8") as f: f.write(comment_text)
            
        print(f"✅ 內容與圖片處理完成！字數：{len(caption)}")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
