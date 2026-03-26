import os
import sys
import json
from datetime import datetime
from google import genai
from google.genai import types

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def run():
    try:
        if not GEMINI_KEY: raise Exception("缺少 GEMINI_API_KEY 環境變數")
        client = genai.Client(api_key=GEMINI_KEY)

        # 1. 改為日期命名，防止重複生圖扣錢
        today_str = datetime.now().strftime("%Y-%m-%d")
        img_name = f"spot_{today_str}.jpg"
        img_dir = "images/spot"
        os.makedirs(img_dir, exist_ok=True)
        local_img_path = f"{img_dir}/{img_name}"

        # 2. 升級版止血鎖：檢查圖片存在，且文案檔裡面確實有字 (>10 bytes)
        is_text_valid = os.path.exists("caption.txt") and os.path.getsize("caption.txt") > 10
        
        if os.path.exists(local_img_path) and is_text_valid:
            print(f"✅ 今日景點圖片與文案皆已存在 ({img_name})，跳過 API 生成，直接發文。")
            with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_name)
            return

        print("🤖 正在為今日景點貼文生成全新內容...")
        target_cities = "曼谷、清邁、釜山、首爾、新加坡、沖繩、宮古島、福岡、大阪、京都、神戶、東京、宇治、奈良、香港、澳門"
        
        # 3. 核心修改區：強制防護圖文不符
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。你要發一篇 Threads 貼文。\n"
            f"從以下城市中隨機挑選一個：{target_cities}。\n"
            f"挑選該城市中一個真實存在的知名地標、私房秘境或絕美打卡景點、知名夜市或市場（請勿介紹餐廳或美食）。\n"
            f"請你生成以下 6 個欄位的資料，並『嚴格』遵守各欄位的規則：\n"
            f"- caption: 第一人稱發牢騷或表達興奮，結尾拋出引發討論的問題。絕對不要寫出如何抵達或交通方式。150字內。\n"
            f"- image_prompt: (英文咒語) 🚨這非常重要！你必須先用英文具體且詳細描述『該景點的真實樣貌與細節』，然後再將這段風格指令接在後面：'Professional editorial travel photography, full-frame camera quality, shallow depth of field, f/1.4 aperture bokeh, candid professional look, natural light, realistic natural color grading, raw film textures. DO NOT use 8k, masterpiece, cinematic lighting, over-processed HDR, hyper-detailed, perfect composition.'\n"
            f"- comment1: 語氣像回覆朋友，簡單帶出景點名稱和推薦拍照點。\n"
            f"- spot_name: 景點的精準名稱。\n"
            f"- transportation: 詳細的自由行大眾交通方式，例如搭乘哪條地鐵、哪個出口、步行幾分鐘。\n"
            f"- google_maps_keyword: 最容易搜到這個景點的關鍵字。\n\n"
            f"請務必以純 JSON 格式輸出，不要包含 Markdown 標記。"
        )
        
        res = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=task_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.7)
        )
        
        data = json.loads(res.text)
        
        # 4. 強制防護：萬一 AI 偷懶沒寫，強制塞入預設文字，避免 Threads 變成無字天書
        caption = data.get("caption") or "這個景點真的太美了！大家有來過嗎？"
        comment_text = data.get("comment1") or "真的超好拍，推薦給大家！"
        spot_name = data.get("spot_name") or "神秘絕美景點"
        transportation = data.get("transportation") or "交通方式請參考Google Maps"
        google_maps_keyword = data.get("google_maps_keyword") or spot_name
        
        comment2_text = (
            f"📍 景點名稱：{spot_name}\n\n"
            f"🚆 自由行交通攻略：\n{transportation}\n\n"
            f"🗺️ Google Maps 搜尋：{google_maps_keyword}"
        )

        if len(caption) > 480: caption = caption[:475] + "..."
        if len(comment_text) > 480: comment_text = comment_text[:475] + "..."
        if len(comment2_text) > 480: comment2_text = comment2_text[:475] + "..."

        print(f"🎨 最終影像咒語為：{data.get('image_prompt')}")

        image_prompt = data.get("image_prompt", "Professional travel photography...")
        img_res = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=image_prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"], image_config=types.ImageConfig(aspect_ratio="1:1"))
        )
        
        for part in img_res.parts:
            if part.inline_data:
                part.as_image().save(local_img_path)
                break

        # 寫入暫存檔
        with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_name)
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        with open("comment.txt", "w", encoding="utf-8") as f: f.write(comment_text)
        with open("comment2.txt", "w", encoding="utf-8") as f: f.write(comment2_text)

        print("✅ 檔案寫入完成，準備推播至 GitHub。")

    except Exception as e:
        print(f"💥 錯誤：{e}"); sys.exit(1)

if __name__ == "__main__": run()
