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
        
        # --- A. Gemini 2.5 生成內容 ---
        print("🤖 Gemini 2.5 Flash 正在構思圖文與留言內容...")
        
        task_prompt = (
            "你是一位專業美食家。任務：\n"
            "1. 隨機選一個真實存在的知名餐廳。\n"
            "2. 撰寫 400 字 Threads 主文（不含店名地址），描述口感與氛圍，語氣生動並多加 Emoji。\n"
            "3. 撰寫一條留言內容，格式為：『📍 店名：XXX \n📍 地址：XXX』。\n"
            "4. 撰寫一段該美食的英文繪圖咒語 (Image Prompt)。\n"
            "請嚴格使用 '---' 分隔這三部分（主文---咒語---留言）。"
        )
        
        res = client.models.generate_content(model='gemini-2.5-flash', contents=task_prompt)
        parts = res.text.split('---')
        
        # 確保三段都有產生
        caption = parts[0].strip()
        image_prompt = parts[1].strip() if len(parts) > 1 else "Gourmet food, 8k"
        comment_text = parts[2].strip() if len(parts) > 2 else "📍 地址資訊整理中..."

        # --- B. Imagen 3.0 生成圖片 ---
        print(f"🎨 繪製圖片中...")
        img_res = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=image_prompt,
            config={"number_of_images": 1, "aspect_ratio": "1:1"}
        )
        
        img_name = f"food_{int(time.time())}.jpg"
        os.makedirs("images/food", exist_ok=True)
        with open(f"images/food/{img_name}", "wb") as f:
            f.write(img_res.generated_images[0].image_bytes)

        # --- C. 儲存多個暫存檔供 Workflow 使用 ---
        with open("img_name.txt", "w") as f: f.write(img_name)
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        with open("comment.txt", "w", encoding="utf-8") as f: f.write(comment_text)
            
        print(f"✅ 內容處理完成！準備發布。")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
