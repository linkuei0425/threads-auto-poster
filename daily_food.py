import os
import sys
import time
import json
import random
from google import genai
from google.genai import types

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def run():
    try:
        if not GEMINI_KEY:
            raise Exception("缺少 GEMINI_API_KEY 環境變數")
            
        client = genai.Client(api_key=GEMINI_KEY)
        
        # --- A. Gemini 生成 Threads 專屬閒聊風文案與雙留言 ---
        print("🤖 系統正在隨機抽取城市與美食主題...")
        
        # 💡 將字串改為 List，由 Python 來進行絕對隨機抽取
        target_cities = ["曼谷", "清邁", "釜山", "首爾", "新加坡", "沖繩", "宮古島", "福岡", "大阪", "京都", "神戶", "東京", "宇治", "奈良", "香港", "澳門"]
        themes = ["在地人推薦街頭小吃", "必吃百年老店", "視覺系網美甜點", "深夜排隊宵夜", "隱藏版巷弄美食", "高CP值平價美食"]
        
        selected_city = random.choice(target_cities)
        selected_theme = random.choice(themes)
        
        print(f"🎯 本次抽中：【{selected_city}】的【{selected_theme}】，準備交由 Gemini 生成...")
        
        # 💡 核心修改區：直接命令 AI 針對抽中的城市與主題撰寫
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。你要發一篇 Threads 貼文。\n"
            f"1. 請針對【{selected_city}】這個城市，挑選一家符合【{selected_theme}】主題的真實存在特色美食或隱藏版餐廳。\n"
            f"請你生成以下 6 個欄位的資料，並『嚴格』遵守各欄位的規則：\n"
            f"- caption: (主文) 第一人稱發牢騷或表達興奮，結尾拋出引發討論的問題。這裡『絕對不要』寫地址。150字內。\n"
            f"- image_prompt: (英文咒語) 請撰寫一個具體且專業的英文美食攝影咒語。咒語應包含以下元素，以確保真實、高品質且非AI感：'Professional candid food photography, shot on a full-frame camera (e.g., Canon EOS R5) with a 50mm f/1.8 lens. Specify a shallow depth of field (e.g., natural bokeh background), use soft natural window light, focus sharply on the key ingredients/textures (e.g., glisten on noodles, fresh herbs). Include small, realistic food imperfections for authenticity (e.g., slightly irregular shape, natural crumbs). Describe a simple, rustic table or restaurant setting in the background that is naturally blurred. **嚴禁使用**以下關鍵字：'AI', 'CGI', 'render', 'perfect', 'flawless', '8k', 'highly detailed', 'photorealistic', 'fantasy lighting'。旨在呈現未經過度修飾、紀錄片式的專業質感。'\n"
            f"- comment1: (第一則留言) 語氣像回覆朋友，簡單帶出店名和必點菜色。例如『這家叫 XXX...』。\n"
            f"- store_name: (店名) 餐廳的精準名稱。\n"
            f"- address: (詳細地址) 餐廳的真實詳細地址。\n"
            f"- google_maps_keyword: (Google Maps搜尋關鍵字) 最容易搜到這家店的關鍵字。\n\n"
            f"請務必以純 JSON 格式輸出，不要包含任何 Markdown 標記。並且確保所有輸出內容（除了 image_prompt 外）都必須是全中文。"
        )
        
        # 💡 開啟 Gemini 原生的 JSON Mode
        res = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=task_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.8 # 💡 稍微調高溫度增加多樣性
            )
        )
        
        # 💡 將 AI 的回覆轉換為 Python 字典
        try:
            data = json.loads(res.text)
        except json.JSONDecodeError:
            print("⚠️ 警告：AI 輸出的不是有效的 JSON！原始輸出如下：")
            print(res.text)
            sys.exit(1)
            
        caption = data.get("caption", "無法生成主文")
        image_prompt = data.get("image_prompt", "Candid professional food photography, natural window light, shallow depth of field, sharp focus on the main dish, rustic table setting, slightly blurred background bokeh, f/1.8 aperture, realistic food textures and imperfections. DO NOT include AI or CGI elements.")
        comment_text = data.get("comment1", "📍 餐廳資訊確認中...")
        
        store_name = data.get("store_name", "未知店名")
        address = data.get("address", "未知地址")
        google_maps_keyword = data.get("google_maps_keyword", "未知關鍵字")
        
        comment2_text = (
            f"📍 店名：{store_name}\n"
            f"📍 詳細地址：{address}\n"
            f"📍 Google Maps 搜尋關鍵字：{google_maps_keyword}"
        )

        # 💡 字數防呆機制
        if len(caption) > 480: caption = caption[:475] + "..."
        if len(comment_text) > 480: comment_text = comment_text[:475] + "..."
        if len(comment2_text) > 480: comment2_text = comment2_text[:475] + "..."

        # --- B. Gemini 生成圖片並儲存 ---
        print(f"🎨 正在以專業攝影風格繪製美食：{image_prompt}")
        img_res = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=image_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="1:1")
            )
        )
        
        img_name = f"food_{int(time.time())}.jpg"
        img_dir = "images/food"
        
        if os.path.exists(img_dir) and not os.path.isdir(img_dir):
            print(f"⚠️ 發現同名檔案，正在清空以建立正確的資料夾...")
            os.remove(img_dir)
        os.makedirs(img_dir, exist_ok=True)
        
        local_img_path = f"{img_dir}/{img_name}"
        
        for part in img_res.parts:
            if part.inline_data:
                part.as_image().save(local_img_path)
                break
                
        # --- C. 寫入暫存檔 (供 GitHub Actions 讀取) ---
        with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_name)
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        with open("comment.txt", "w", encoding="utf-8") as f: f.write(comment_text)
        with open("comment2.txt", "w", encoding="utf-8") as f: f.write(comment2_text)
            
        print(f"👉 檔案寫入完成：主文({len(caption)}字) / 留言1({len(comment_text)}字) / 留言2({len(comment2_text)}字)")
        
        # 在終端機印出來讓你馬上檢查
        print("\n--- 📝 產出預覽 ---")
        print(f"[主文預覽]:\n{caption}\n")
        print(f"[留言1預覽]:\n{comment_text}\n")
        print(f"[留言2預覽]:\n{comment2_text}")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()