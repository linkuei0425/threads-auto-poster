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
        
        # --- A. Gemini 生成 Threads 專屬閒聊風文案 ---
        print("🤖 Gemini 正在亞洲精選城市中尋找必吃美食並轉換為 Threads 閒聊體...")
        
        target_cities = "曼谷、清邁、釜山、首爾、新加坡、沖繩、宮古島、福岡、大阪、京都、神戶、東京、宇治、奈良、香港、澳門"
        
        # 💡 核心修改區：完全改變 AI 的寫作邏輯，迎合 Threads 演算法
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。你現在要發一篇 Threads 貼文，必須完全符合 Threads 『隨性、閒聊、強烈個人情緒、不套公式』的風格，絕對不要寫成 IG 的精緻行銷文或旅遊書攻略。\n"
            f"任務：\n"
            f"1. 從以下城市中隨機挑選一個：{target_cities}。\n"
            f"2. 挑選該城市中一家『真實存在』且極具特色的必吃美食或隱藏版餐廳。\n"
            f"3. 撰寫一段 Threads 貼文主文（中文）。\n"
            f"   - ⚠️ 絕對禁止：不要用條列式、不要用數字編號、不要寫出詳細地址或營業時間、減少使用 Emoji（最多 2 個）。\n"
            f"   - 💡 寫作風格：用第一人稱（Kokko）發牢騷或表達極度興奮。例如：『為了吃這家排隊排到懷疑人生，但吃到的那一刻真的覺得值了...』或是『到底誰發明這種神仙食物...』。\n"
            f"   - 💡 互動機制：結尾必須拋出一個能引發討論的問題（例如：大家去[城市]必吃的是哪家？有人也吃過這家嗎？）。\n"
            f"   - 字數規定：主文字數越短越好，『絕對不可以超過 150 字』！\n"
            f"4. 撰寫一段該美食或餐廳的英文繪圖咒語 (Image Prompt)，風格為專業高畫質美食攝影 (professional gourmet food photography)、令人垂涎欲滴。\n"
            f"5. 撰寫一條『補充在自己貼文底下』的留言內容。\n"
            f"   - 這裡才公佈店家資訊，但語氣要像是在回覆朋友，不要像機器人表單。\n"
            f"   - 格式參考：『這家叫 XXX，在 OOO 附近。那個（必點菜色）真的必點，口感超讚！想去的話建議（某個時間點）去才不會排到瘋掉～』\n"
            f"請嚴格使用 '---' 分隔這三部分（主文---咒語---留言內容）。"
        )
        
        res = client.models.generate_content(model='gemini-2.5-flash', contents=task_prompt)
        parts = res.text.split('---')
        caption = parts[0].strip() if len(parts) > 0 else "無法生成貼文內容"
        image_prompt = parts[1].strip() if len(parts) > 1 else "Professional gourmet food photography, highly detailed, 8k"
        comment_text = parts[2].strip() if len(parts) > 2 else "📍 餐廳資訊確認中..."

        # 💡 防呆機制維持
        if len(caption) > 480:
            print(f"⚠️ 警告：主文字數太長 ({len(caption)} 字)，已觸發自動截斷！")
            caption = caption[:475] + "..."

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
            
        print(f"✅ 美食版任務完成！主文字數：{len(caption)} / 留言字數：{len(comment_text)}")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
