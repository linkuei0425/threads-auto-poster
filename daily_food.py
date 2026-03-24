import os
import sys
import time
import re  # 💡 新增正則表達式模組，用來精準抓字
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
        print("🤖 Gemini 正在尋找必吃美食並使用【標籤系統】確保輸出格式...")
        
        target_cities = "曼谷、清邁、釜山、首爾、新加坡、沖繩、宮古島、福岡、大阪、京都、神戶、東京、宇治、奈良、香港、澳門"
        
        # 💡 核心修改區：改用 XML 標籤系統，這是對付 AI 格式跑掉最有效的方法
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
            f"請務必使用特定的標籤包覆你的輸出內容，不要加上任何 Markdown 標題，格式如下：\n"
            f"<caption>主文內容寫這裡</caption>\n"
            f"<prompt>英文咒語寫這裡</prompt>\n"
            f"<comment1>第一則留言寫這裡</comment1>\n"
            f"<comment2>第二則留言寫這裡</comment2>"
        )
        
        res = client.models.generate_content(model='gemini-2.5-flash', contents=task_prompt)
        output_text = res.text
        
        # 💡 使用正則表達式精準提取標籤內的內容
        def extract_content(tag, text):
            match = re.search(f"<{tag}>(.*?)</{tag}>", text, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else ""
            
        caption = extract_content("caption", output_text)
        image_prompt = extract_content("prompt", output_text)
        comment_text = extract_content("comment1", output_text)
        comment2_text = extract_content("comment2", output_text)

        # 💡 終極防呆：如果抓不到東西，印出原始回覆讓我們除錯
        if not comment2_text:
            print("⚠️ 警告：無法抓取第二則留言，AI 原始輸出如下：")
            print(output_text)
        else:
            print("✅ 成功抓取四個區塊！")

        # 💡 字數防呆機制
        if len(caption) > 480: caption = caption[:475] + "..."
        if len(comment_text) > 480: comment_text = comment_text[:475] + "..."
        if len(comment2_text) > 480: comment2_text = comment2_text[:475] + "..."

        # 如果主文或咒語是空的，給個預設值避免報錯
        if not caption: caption = "發生錯誤，無法生成貼文內容"
        if not image_prompt: image_prompt = "Professional gourmet food photography, highly detailed, 8k"
        if not comment_text: comment_text = "📍 餐廳資訊確認中..."
        if not comment2_text: comment2_text = "📍 詳細地址獲取中..."

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
        with open("comment2.txt", "w", encoding="utf-8") as f: f.write(comment2_text)
            
        print(f"👉 檔案寫入完成：主文({len(caption)}字) / 留言1({len(comment_text)}字) / 留言2({len(comment2_text)}字)")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
