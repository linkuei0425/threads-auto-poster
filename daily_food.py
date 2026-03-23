import os
import random
import requests
import sys
import time
from google import genai
from google.genai import types # 修正 1：引入 types 模組來設定圖片生成的 config

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
        
        # 拆分內容 (加入長度檢查避免索引錯誤)
        parts = res.text.split('---')
        caption = parts[0].strip() if len(parts) > 0 else "無法生成貼文內容"
        image_prompt = parts[1].strip() if len(parts) > 1 else "Professional gourmet food photography, 8k, highly detailed"
        comment_text = parts[2].strip() if len(parts) > 2 else "📍 地址資訊確認中..."

        # --- B. Gemini Flash Image 生成圖片 (修正 2：改用統一的生成入口) ---
        print(f"🎨 正在繪製：{image_prompt}")
        
        img_res = client.models.generate_content(
            model='gemini-2.5-flash-image', # 替換成最新的圖像模型名稱
            contents=image_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="1:1" # 適合 Threads 和 IG 的比例
                )
            )
        )
        
        img_name = f"food_{int(time.time())}.jpg"
        img_dir = "images/food"
        os.makedirs(img_dir, exist_ok=True)
        
        # 修正 3：使用新版 SDK 的 as_image() 方法來儲存圖片
        for part in img_res.parts:
            if part.inline_data:
                generated_image = part.as_image()
                generated_image.save(f"{img_dir}/{img_name}")
                break # 確保只取第一張

        # --- C. 寫入多個暫存檔 (解決 Shell 讀取換行問題) ---
        with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_name)
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        with open("comment.txt", "w", encoding="utf-8") as f: f.write(comment_text)
            
        print(f"✅ 任務完成！主文字數：{len(caption)}")
        print(f"📁 圖片已順利儲存至：{img_dir}/{img_name}")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
