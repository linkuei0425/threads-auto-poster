import os
import sys
import json
from datetime import datetime
from google import genai
from google.genai import types

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def run():
    try:
        if not GEMINI_KEY: raise Exception("缺少 GEMINI_API_KEY")
        client = genai.Client(api_key=GEMINI_KEY)

        # 核心修改 1：改用「日期」作為檔名
        today_str = datetime.now().strftime("%Y-%m-%d")
        img_name = f"food_{today_str}.jpg"
        img_dir = "images/food"
        os.makedirs(img_dir, exist_ok=True)
        local_img_path = f"{img_dir}/{img_name}"

        # 核心修改 2：止血鎖。如果檔案存在，代表今天生過了，直接結束
        if os.path.exists(local_img_path):
            print(f"✅ 今日圖片已存在 ({img_name})，跳過 API 生成以節省費用。")
            with open("img_name.txt", "w") as f: f.write(img_name)
            return

        # --- 以下為原本的生成邏輯 ---
        print("🤖 正在為今日貼文生成全新內容...")
        target_cities = "曼谷、清邁、釜山、首爾、新加坡、沖繩、宮古島、福岡、大阪、京都、神戶、東京、宇治、奈良、香港、澳門"
        task_prompt = (f"你是一位經營『Kokko愛旅行』的創作者... (略，保持你原本的 Prompt)")
        
        res = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=task_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.7)
        )
        data = json.loads(res.text)
        
        # 影像生成
        image_prompt = data.get("image_prompt", "Professional food photography...")
        img_res = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=image_prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"], image_config=types.ImageConfig(aspect_ratio="1:1"))
        )
        
        # 儲存影像
        for part in img_res.parts:
            if part.inline_data:
                part.as_image().save(local_img_path)
                break

        # 寫入暫存檔
        with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_name)
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(data.get("caption", ""))
        with open("comment.txt", "w", encoding="utf-8") as f: f.write(data.get("comment1", ""))
        with open("comment2.txt", "w", encoding="utf-8") as f: 
            f.write(f"📍 店名：{data.get('store_name')}\n📍 地址：{data.get('address')}")

    except Exception as e:
        print(f"💥 錯誤：{e}"); sys.exit(1)

if __name__ == "__main__": run()
