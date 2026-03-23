import os
import requests
import sys
import time
import base64
from google import genai
from google.genai import types

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
IMGUR_ID = os.getenv("IMGUR_CLIENT_ID") 

def upload_to_imgur(image_path):
    """將本地圖片上傳至 Imgur 並回傳公開網址"""
    print(f"📤 正在上傳圖片至 Imgur: {image_path}...")
    url = "https://api.imgur.com/3/image"
    payload = {}
    
    with open(image_path, 'rb') as image_file:
        payload['image'] = base64.b64encode(image_file.read())
    
    headers = {
        'Authorization': f'Client-ID {IMGUR_ID}'
    }
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        data = response.json()
        imgur_url = data['data']['link']
        print(f"✅ Imgur 上傳成功！網址: {imgur_url}")
        return imgur_url
    except Exception as e:
        print(f"❌ Imgur 上傳失敗: {e}")
        return None

def run():
    try:
        # --- 初始化 ---
        if not GEMINI_KEY or not IMGUR_ID:
            raise Exception("缺少 GEMINI_API_KEY 或 IMGUR_CLIENT_ID 環境變數")
            
        client = genai.Client(api_key=GEMINI_KEY)
        
        # --- A. Gemini 生成專屬城市文案 ---
        print("🤖 Gemini 正在亞洲精選城市中尋找美食...")
        
        target_cities = "曼谷、清邁、釜山、首爾、新加坡、沖繩、宮古島、福岡"
        
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的專業旅遊與美食創作者。任務：\n"
            f"1. 從以下城市中『隨機挑選一個』：{target_cities}。\n"
            f"2. 挑選該城市中一家『真實存在』的在地必吃美食、特色咖啡廳或隱藏版餐廳。\n"
            f"3. 撰寫一段約 400 字的 Threads 貼文（中文）。以第一人稱（Kokko）分享，語氣要像在跟朋友說故事一樣生動、熱情，多用符合情境的 Emoji。\n"
            f"4. 撰寫一段該美食或餐廳氛圍的英文繪圖咒語 (Image Prompt)，要高畫質、有氛圍感。\n"
            f"5. 撰寫一條留言內容，格式為：『📍 店名：XXX \\n📍 所在城市：XXX \\n📍 地址：XXX』。\n"
            f"請嚴格使用 '---' 分隔這三部分（主文---咒語---留言內容）。"
        )
        
        res = client.models.generate_content(model='gemini-2.5-flash', contents=task_prompt)
        parts = res.text.split('---')
        caption = parts[0].strip() if len(parts) > 0 else "無法生成貼文內容"
        image_prompt = parts[1].strip() if len(parts) > 1 else "Professional gourmet food photography"
        comment_text = parts[2].strip() if len(parts) > 2 else "📍 地址資訊確認中..."

        # 💡 重點邏輯：自動偵測曼谷並置入【曼谷通】連結
        if "曼谷" in caption or "曼谷" in comment_text:
            # 記得把下面這行的網址換成你曼谷通的真實連結！
            promo_text = "\n\n🇹🇭 正在規劃泰國行嗎？歡迎使用我的【曼谷通】APP，幫你輕鬆找好吃好玩的！ 👉 https://你的曼谷通網址.com"
            comment_text += promo_text
            print("🇹🇭 偵測到曼谷主題！已自動在留言處加入推廣連結。")

        # --- B. Gemini 生成圖片並儲存 ---
        print(f"🎨 正在繪製：{image_prompt}")
        img_res = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=image_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="1:1")
            )
        )
        
        img_dir = "images/food"
        os.makedirs(img_dir, exist_ok=True)
        local_img_path = f"{img_dir}/food_{int(time.time())}.jpg"
        
        for part in img_res.parts:
            if part.inline_data:
                part.as_image().save(local_img_path)
                break
                
        # --- C. 上傳圖片至 Imgur ---
        imgur_url = upload_to_imgur(local_img_path)
        if not imgur_url:
            raise Exception("圖片上傳 Imgur 失敗，中斷流程")

        # --- D. 寫入暫存檔 (供 Actions 讀取) ---
        with open("imgur_url.txt", "w", encoding="utf-8") as f: f.write(imgur_url)
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        with open("comment.txt", "w", encoding="utf-8") as f: f.write(comment_text)
            
        print(f"✅ Python 任務完成！主文字數：{len(caption)}")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
