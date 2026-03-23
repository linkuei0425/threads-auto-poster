import os
import sys
import time
from google import genai
from google.genai import types

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def run():
    try:
        if not GEMINI_KEY:
            raise Exception("缺少 GEMINI_API_KEY 環境變數")
            
        client = genai.Client(api_key=GEMINI_KEY)
        
        # --- A. Gemini 生成美食文案與實用資訊 ---
        print("🤖 Gemini 正在亞洲精選城市中尋找必吃美食...")
        
        # 💡 16 大熱門旅遊城市
        target_cities = "曼谷、清邁、釜山、首爾、新加坡、沖繩、宮古島、福岡、大阪、京都、神戶、東京、宇治、奈良、香港、澳門"
        
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的專業旅遊與美食創作者。任務：\n"
            f"1. 從以下城市中『隨機挑選一個』：{target_cities}。\n"
            f"2. 挑選該城市中一家『真實存在』的在地必吃美食、特色咖啡廳或隱藏版餐廳。\n"
            f"3. 撰寫一段 Threads 貼文主文（中文）。以第一人稱（Kokko）分享，描述食物口感細節與現場氛圍，語氣生動熱情，多用符合情境的 Emoji。\n"
            f"⚠️ 排版規定：段落與段落之間『必須空一行』！請多利用短句，絕對不要把文字全部擠成一團！\n"
            f"⚠️ 字數規定：主文字數（含標點符號與Emoji）『絕對不可以超過 350 字』！\n"
            f"4. 撰寫一段該美食或餐廳的英文繪圖咒語 (Image Prompt)，風格必須是專業高畫質美食攝影 (professional gourmet food photography)、令人垂涎欲滴。\n"
            f"5. 撰寫一條給『自由行吃貨』的專屬留言內容。格式為：\n"
            f"『📍 店名：XXX \n"
            f"📍 所在城市：XXX \n"
            f"📍 詳細地址：XXX \n\n"
            f"🤤  Kokko 推薦指南：\n"
            f"[請條列式說明，例如：\n"
            f"✨ 必點推薦：ＯＯＯ（簡述口感）\n"
            f"💡 貼心提醒：建議提早排隊/交通方式/營業時間等]\n"
            f"⚠️ 留言排版規定：推薦指南請務必『條列式分行』撰寫，保持清晰易讀！』\n"
            f"請嚴格使用 '---' 分隔這三部分（主文---咒語---留言內容）。"
        )
        
        res = client.models.generate_content(model='gemini-2.5-flash', contents=task_prompt)
        parts = res.text.split('---')
        caption = parts[0].strip() if len(parts) > 0 else "無法生成貼文內容"
        image_prompt = parts[1].strip() if len(parts) > 1 else "Professional gourmet food photography, highly detailed, 8k"
        comment_text = parts[2].strip() if len(parts) > 2 else "📍 餐廳資訊確認中..."

        # 💡 主文防呆機制：超過 480 字直接強制截斷
        if len(caption) > 480:
            print(f"⚠️ 警告：主文字數太長 ({len(caption)} 字)，已觸發自動截斷！")
            caption = caption[:475] + "..."

        # 💡 留言防呆機制：確保不會超過 Threads 的 500 字上限
        if len(comment_text) > 480:
            print(f"⚠️ 警告：留言字數太長 ({len(comment_text)} 字)，已觸發自動截斷！")
            comment_text = comment_text[:475] + "..."

        # --- B. Gemini 生成圖片並儲存 ---
        print(f"🎨 正在繪製美食：{image_prompt}")
        img_res = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=image_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="1:1")
            )
        )
        
        img_name = f"food_{int(time.time())}.jpg"
        img_dir = "images/food" # 存入美食專屬資料夾
        
        # 💡 終極資料夾防護機制：避免檔案衝突
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
            
        print(f"✅ 美食版任務完成！主文字數：{len(caption)} / 留言字數：{len(comment_text)}")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
