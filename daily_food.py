import os
import sys
import time
import json
import random
import requests
from google import genai
from google.genai import types

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def post_to_fb_and_ig(text, image_paths):
    """使用 Facebook Graph API 將產生的圖文發布至 FB 與 IG"""
    if not image_paths:
        print("⚠️ 沒有圖片可供發布，略過 FB/IG 發文。")
        return

    fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    page_id = os.getenv("FB_PAGE_ID")
    ig_id = os.getenv("IG_ACCOUNT_ID")

    if not fb_token or not page_id:
        print("⚠️ 未找到 FB Token 或 Page ID，請檢查 GitHub Secrets 設定。略過 FB/IG 發佈。")
        return

    print("🚀 開始發布至 Facebook 與 Instagram...")
    try:
        print(f"📘 準備上傳圖片至 Facebook Page (ID: {page_id})")
        fb_media_ids = []
        
        # 上傳所有圖片到 FB 獲取 ID
        for img_path in image_paths:
            with open(img_path, "rb") as img:
                upload_url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
                payload = {"published": "false", "access_token": fb_token}
                files = {"source": img}
                up_res = requests.post(upload_url, data=payload, files=files).json()
                if "id" in up_res:
                    fb_media_ids.append(up_res["id"])
                    print(f"  - 成功上傳 FB 圖片: {up_res['id']}")
                else:
                    print(f"⚠️ FB 圖片上傳失敗: {up_res}")

        # 如果有圖片，則發佈 FB 貼文
        if fb_media_ids:
            post_url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
            post_payload = {"message": text, "access_token": fb_token}
            for i, m_id in enumerate(fb_media_ids):
                post_payload[f"attached_media[{i}]"] = f'{{"media_fbid":"{m_id}"}}'
            
            fb_post_res = requests.post(post_url, data=post_payload).json()
            if "id" in fb_post_res:
                print(f"✅ Facebook 發布成功！(Post ID: {fb_post_res['id']})")
            else:
                print(f"⚠️ Facebook 發布失敗: {fb_post_res}")

            # 接著處理 IG 發佈
            if ig_id:
                print(f"📸 準備發布至 Instagram (ID: {ig_id})")
                time.sleep(3) # 等待 FB 處理圖片
                
                ig_media_containers = []
                for m_id in fb_media_ids[:10]: # IG Carousel 最多 10 張
                    # 先從 FB 取得圖片真實網址
                    photo_url_req = f"https://graph.facebook.com/v19.0/{m_id}?fields=images&access_token={fb_token}"
                    photo_data = requests.get(photo_url_req).json()
                    source_url = photo_data.get("images", [{}])[0].get("source")
                    
                    if source_url:
                        cont_url = f"https://graph.facebook.com/v19.0/{ig_id}/media"
                        cont_payload = {
                            "image_url": source_url,
                            "is_carousel_item": "true" if len(fb_media_ids) > 1 else "false",
                            "access_token": fb_token
                        }
                        # 若只有單圖，需在 container 帶上內文
                        if len(fb_media_ids) == 1: 
                            cont_payload["caption"] = text
                        
                        cont_res = requests.post(cont_url, data=cont_payload).json()
                        if "id" in cont_res:
                            ig_media_containers.append(cont_res["id"])
                            print(f"  - 成功建立 IG 圖片容器: {cont_res['id']}")
                        else:
                            print(f"⚠️ 建立 IG 圖片容器失敗: {cont_res}")
                        time.sleep(1)

                if ig_media_containers:
                    if len(ig_media_containers) > 1:
                        # 多圖情況：建立 Carousel 容器
                        car_url = f"https://graph.facebook.com/v19.0/{ig_id}/media"
                        car_payload = {
                            "media_type": "CAROUSEL",
                            "children": ",".join(ig_media_containers),
                            "caption": text,
                            "access_token": fb_token
                        }
                        car_res = requests.post(car_url, data=car_payload).json()
                        creation_id = car_res.get("id")
                        if not creation_id:
                            print(f"⚠️ 建立 IG Carousel 容器失敗: {car_res}")
                    else:
                        # 單圖情況
                        creation_id = ig_media_containers[0]

                    # 實際發布至 IG
                    if creation_id:
                        pub_url = f"https://graph.facebook.com/v19.0/{ig_id}/media_publish"
                        pub_payload = {"creation_id": creation_id, "access_token": fb_token}
                        print("⏳ 等待 5 秒讓 IG API 準備完成...")
                        time.sleep(5)
                        pub_res = requests.post(pub_url, data=pub_payload).json()
                        if "id" in pub_res:
                            print(f"✅ Instagram 發布成功！(Post ID: {pub_res['id']})")
                        else:
                            print(f"⚠️ Instagram 發布失敗: {pub_res}")
            else:
                 print("⚠️ 未設定 IG_ACCOUNT_ID，跳過 IG 發佈。")
                 
    except Exception as e:
        print(f"💥 FB/IG 發布錯誤：{e}")

def run():
    try:
        if not GEMINI_KEY:
            raise Exception("缺少 GEMINI_API_KEY 環境變數")
            
        client = genai.Client(api_key=GEMINI_KEY)
        
        print("🤖 系統正在準備啟動...")
        
        # 讀取景點腳本留下的城市紀錄 (連動功能)
        selected_city = None
        if os.path.exists("selected_city.txt"):
            try:
                with open("selected_city.txt", "r", encoding="utf-8") as f:
                    selected_city = f.read().strip()
                print(f"📂 成功讀取昨日景點城市紀錄：{selected_city}")
            except Exception as e:
                print(f"⚠️ 讀取 selected_city.txt 發生錯誤: {e}")
                
        # 防呆機制：若無紀錄則隨機抽一個
        if not selected_city:
            target_cities = [
                "曼谷", "清邁", "釜山", "首爾", "新加坡", "沖繩", "宮古島", "福岡", 
                "大阪", "京都", "神戶", "東京", "宇治", "奈良", "香港", "澳門", 
                "河內", "胡志明市", "峴港", "蘇梅島", "普吉島", "芭達雅", "富國島"
            ]
            selected_city = random.choice(target_cities)
            print(f"⚠️ 找不到城市紀錄，改為隨機抽取：{selected_city}")
            
        print(f"🎯 本次連動城市為：【{selected_city}】，準備交由 Gemini 生成 8 間主題美食...")
        
        # 擴充為 8 個主題 (對應 8 餐廳與 8 圖片)
        themes = [
            "在地人推薦街頭小吃", "必吃百年老店", "視覺系網美甜點", "深夜排隊宵夜", 
            "隱藏版巷弄美食", "高CP值平價美食", "人氣網美早午餐", "傳統市場必吃"
        ]
        themes_str = "、".join(themes)
        
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。你要發一篇 Threads 貼文。\n"
            f"1. 請針對【{selected_city}】這個城市，挑選 8 間真實存在特色美食或餐廳。\n"
            f"這 8 間餐廳必須『分別對應』以下 8 個不同的主題（每個主題挑選一間餐廳）：{themes_str}。\n"
            f"請你生成以下 2 個主要的 JSON 欄位資料，並『嚴格』遵守規則：\n"
            f"- caption: (主文) 第一人稱發牢騷或表達興奮，用輕鬆口吻推薦這 8 間美食。結尾拋出引發討論的問題，並呼籲『收藏這篇』。這裡『絕對不要』寫出地址。480字內。\n"
            f"  ⚠️【排版與分段要求】：請務必適當分段！段落與段落之間必須使用 '\\n\\n' 換行。不要把所有字擠在一起！\n"
            f"- foods: (這是一個包含 8 個物件的陣列 Array，每個物件代表一間餐廳，需包含以下屬性)\n"
            f"  - store_name: (店名) 餐廳的精準名稱。\n"
            f"  - food_theme: (所屬主題) 標明這間餐廳是對應哪一個主題。\n"
            f"  - image_prompt: (英文咒語) 為了產生適合手機觀看的真實照片，請使用：'Vertical (9:16) aspect ratio, Phone portrait mode. Raw food photograph, unedited, authentic, shot on iPhone 15 Pro, 35mm equivalent lens. Clear, crisp, natural daylight, true-to-life colors, realistic and imperfect textures, no over-saturation, no HDR look. Describe the specific food and rustic table setting clearly. DO NOT use words like 8k, masterpiece, over-processed.'\n"
            f"  - address: (詳細地址) 餐廳的真實詳細地址。\n"
            f"  - google_maps_keyword: (Google Maps搜尋關鍵字) 最容易搜到這家店的關鍵字。\n"
            f"  - comment_text: (簡介) 簡單帶出店名和必點菜色的介紹，約30字。\n\n"
            f"請務必以純 JSON 格式輸出，不要包含任何 Markdown 標記。並且確保所有輸出內容（除了 image_prompt 外）都必須是全中文。"
        )
        
        res = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=task_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.8 
            )
        )
        
        try:
            data = json.loads(res.text)
        except json.JSONDecodeError:
            print("⚠️ 警告：AI 輸出的不是有效的 JSON！原始輸出如下：")
            print(res.text)
            sys.exit(1)
            
        raw_caption = data.get("caption", "無法生成主文")
        caption = raw_caption.replace("\\n", "\n") 
        foods = data.get("foods", [])
        
        if len(foods) < 8:
            print(f"⚠️ 警告：AI 僅生成了 {len(foods)} 間美食。")
            
        if len(caption) > 480: caption = caption[:475] + "..."
        
        # 動態產生最多 8 則留言，每則留言放一間餐廳
        comment_texts = []
        for i, food in enumerate(foods):
            c_text = (
                f"✨ {i+1}. [{food.get('food_theme')}] {food.get('store_name')}\n"
                f"🍽️ 推薦：{food.get('comment_text')}\n"
                f"📍 地址：{food.get('address')}\n"
                f"🗺️ 搜尋：{food.get('google_maps_keyword')}"
            )
            
            if len(c_text) > 480: c_text = c_text[:475] + "..."
            comment_texts.append(c_text)

        # 將主文與所有資訊留言合併，專門給沒有字數限制的 FB / IG 使用
        fb_ig_caption = caption + "\n\n" + "\n\n".join(comment_texts)

        img_dir = "images/food"
        
        if os.path.exists(img_dir) and not os.path.isdir(img_dir):
            os.remove(img_dir)
        os.makedirs(img_dir, exist_ok=True)
        
        img_names = []
        local_img_paths = []
        
        for i, food in enumerate(foods[:8]):
            image_prompt = food.get("image_prompt")
            if not image_prompt:
                continue
                
            print(f"🎨 正在以真實手機攝影風格繪製第 {i+1} 個美食 ({food.get('food_theme', '未知主題')})...")
            try:
                # 採用 9:16 直式比例
                img_res = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=image_prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio="9:16")
                    )
                )
                
                img_name = f"food_{int(time.time())}_{i}.jpg"
                local_img_path = f"{img_dir}/{img_name}"
                
                for part in img_res.parts:
                    if part.inline_data:
                        part.as_image().save(local_img_path)
                        img_names.append(img_name)
                        local_img_paths.append(local_img_path)
                        break
                time.sleep(1.5)
            except Exception as e:
                print(f"💥 生成第 {i+1} 張圖片時發生錯誤：{e}")
                
        if img_names:
            with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))
            with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
            
            # 寫入多達 8 則的留言檔
            for i, text in enumerate(comment_texts):
                file_name = "comment.txt" if i == 0 else f"comment{i+1}.txt"
                with open(file_name, "w", encoding="utf-8") as f: f.write(text)
                
            print(f"👉 檔案寫入完成：主文({len(caption)}字) / 產出 {len(img_names)} 張圖片")
            
            # 觸發發文到 FB 與 IG
            post_to_fb_and_ig(fb_ig_caption, local_img_paths)
        else:
            print("⚠️ 未能生成任何圖片，程式結束。")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
