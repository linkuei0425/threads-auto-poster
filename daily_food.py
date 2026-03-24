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
        
        # --- A. Gemini 生成 Threads 專屬閒聊風文案與雙留言 ---
        print("🤖 Gemini 正在亞洲精選城市中尋找必吃美食，並轉換為 Threads 蓋樓模式...")
        
        target_cities = "曼谷、清邁、釜山、首爾、新加坡、沖繩、宮古島、福岡、大阪、京都、神戶、東京、宇治、奈良、香港、澳門"
        
        # 💡 核心修改區：強制規定輸出格式，換成 '===' 分隔，確保產出 4 個段落
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。你要發一篇 Threads 貼文，必須符合 Threads 隨性、閒聊、強烈情緒的風格。\n"
            f"任務：\n"
            f"1. 從以下城市中隨機挑選一個：{target_cities}。\n"
            f"2. 挑選該城市中一家『真實存在』的特色必吃美食或隱藏版餐廳。\n"
            f"3. 撰寫貼文主文（中文）：第一人稱（Kokko）發牢騷或表達興奮。結尾必須拋出引發討論的問題。絕對不要寫詳細地址。150字以內。\n"
            f"4. 撰寫英文繪圖咒語 (Image Prompt)：專業高畫質美食攝影 (professional gourmet food photography)、令人垂涎欲滴。\n"
            f"5. 撰寫第一則留言：語氣像回覆朋友，簡單帶出店名和必點菜色，例如『這家叫 XXX... 那個（必點菜色）真的必點...』。\n"
            f"6. 撰寫第二則留言：精準店家資訊（包含：店名、詳細地址、Google Maps關鍵字）。排版要乾淨。\n\n"
            f"⚠️ 絕對嚴格的輸出格式規定 ⚠️\n"
            f"請你『完全依照』下方的格式輸出，不要加上任何 Markdown 標題，段落之間必須且只能用 '===' 分隔：\n\n"
            f"(主文內容)\n"
            f"===\n"
            f"(英文咒語內容)\n"
            f"===\n"
            f"(第一則留言內容)\n"
            f"===\n"
            f"(第二則留言內容)"
        )
        
        res = client.models.generate_content(model='gemini-2.5-flash', contents=task_prompt)
        
        # 💡 將分隔符號改為 '==='
        parts = res.text.split('===')
        
        # 💡 增加自動除錯機制：如果 AI 沒有切出 4 個部分，就把 AI 的原始回覆印出來
        if len(parts) < 4:
            print("⚠️ 警告：AI 輸出的格式不正確，原始內容如下：")
            print(res.text)
        
        caption = parts[0].strip() if len(parts) > 0 else "無法生成貼文內容"
        image_prompt = parts[1].strip() if len(parts) > 1 else "Professional gourmet food photography, highly detailed, 8k"
        comment_text = parts[2].strip() if len(parts) > 2 else "📍 餐廳資訊確認中..."
        comment2_text = parts[3].strip() if len(parts) > 3 else "📍 詳細地址獲取中..."

        # 💡 防呆機制：確保字數不會超過 Threads 限制
        if len(caption) > 480:
            print(f"⚠️ 警告：主文字數太長 ({len(caption)} 字)，已觸發自動截斷！")
            caption = caption[:475] + "..."

        if len(comment_text) > 480:
            print(f"⚠️ 警告：第一則留言字數太長 ({len(comment_text)} 字)，已觸發自動截斷！")
            comment_text = comment_text[:475] + "..."

        if len(comment2_text) > 480:
            print(f"⚠️ 警告：第二則留言字數太長 ({len(comment2_text)} 字)，已觸發自動截斷！")
            comment2_text = comment2_text[:475] + "..."

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
        
        # 💡 清空舊檔案避免衝突
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
        with open("comment2.txt", "w", encoding="utf-8") as f: f.write(comment2_text) # 寫入第二則留言
            
        print(f"✅ 美食版任務完成！")
        print(f"👉 主文：{len(caption)}字")
        print(f"👉 留言1：{len(comment_text)}字")
        print(f"👉 留言2：{len(comment2_text)}字")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
