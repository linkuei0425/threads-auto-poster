import os
import sys
import time
import json
import random
import requests
from google import genai
from google.genai import types

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

            if ig_id:
                print(f"📸 準備發布至 Instagram (ID: {ig_id})")
                time.sleep(3) # 等待 FB 處理圖片
                
                ig_media_containers = []
                for m_id in fb_media_ids[:10]: # IG Carousel 最多 10 張
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
                        if len(fb_media_ids) == 1: cont_payload["caption"] = text
                        
                        cont_res = requests.post(cont_url, data=cont_payload).json()
                        if "id" in cont_res:
                            ig_media_containers.append(cont_res["id"])
                            print(f"  - 成功建立 IG 圖片容器: {cont_res['id']}")
                        else:
                            print(f"⚠️ 建立 IG 圖片容器失敗: {cont_res}")
                        time.sleep(1)

                if ig_media_containers:
                    if len(ig_media_containers) > 1:
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
                        creation_id = ig_media_containers[0]

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
        
        print("🤖 系統正在準備生成美食主題...")
        
        target_cities = [
            "曼谷", "清邁", "釜山", "首爾", "新加坡", "沖繩", "宮古島", "福岡", 
            "大阪", "京都", "神戶", "東京", "宇治", "奈良", "香港", "澳門", 
            "河內", "胡志明市", "峴港", "蘇梅島", "普吉島", "芭達雅", "富國島",
            "吉隆坡", "濟州島", "札幌", "峇里島", "雅加達", "馬尼拉", "宿霧", 
            "檳城", "北京", "上海", "廣州", "深圳", "成都", "新德里", "孟買",
            "巴黎", "倫敦", "羅馬", "馬德里", "巴塞隆納", "阿姆斯特丹", "柏林", 
            "米蘭", "維也納", "慕尼黑", "威尼斯", "佛羅倫斯", "布拉格", "布達佩斯", 
            "雅典", "蘇黎世", "日內瓦", "哥本哈根", "斯德哥爾摩", "奧斯陸", "赫爾辛基", 
            "里斯本", "波多", "都柏林", "愛丁堡", "布魯塞爾", "法蘭克福", "華沙", 
            "克拉科夫", "尼斯", "里昂", "塞維亞", "瓦倫西亞", "拿坡里", "杜布羅夫尼克", 
            "斯普利特", "薩爾茨堡", "雷克雅維克", "伊斯坦堡", "安塔利亞", "紐約", 
            "洛杉磯", "舊金山", "芝加哥", "拉斯維加斯", "邁阿密", "奧蘭多", "華盛頓特區", 
            "多倫多", "溫哥華", "墨西哥城", "坎昆", "里約熱內盧", "聖保羅", 
            "布宜諾斯艾利斯", "杜拜", "阿布達比", "多哈", "特拉維夫", "開羅", 
            "馬拉喀什", "開普敦", "雪梨", "墨爾本", "奧克蘭"
        ]
        
        themes = [
            "在地人推薦街頭小吃", "必吃百年老店", "視覺系網美甜點", "深夜排隊宵夜", 
            "隱藏版巷弄美食", "高CP值平價美食", "傳統道地家常菜", "超人氣排隊名店"
        ]
        
        if os.path.exists("selected_city.txt"):
            with open("selected_city.txt", "r", encoding="utf-8") as f:
                selected_city = f.read().strip()
            print(f"📥 城市連動成功！接續昨日景點，本日為您介紹：【{selected_city}】的美食")
        else:
            selected_city = random.choice(target_cities)
            print(f"🎲 未找到昨日紀錄，隨機抽取城市：【{selected_city}】")
            
        themes_str = "、".join(themes)
        
        print(f"🎯 準備交由 Gemini 生成 8 間不同主題的餐廳...")
        
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。你要發一篇 Threads 貼文。\n"
            f"1. 請針對【{selected_city}】這個城市，挑選 8 間真實存在、有名的特色美食或餐廳。\n"
            f"這 8 間餐廳必須『分別對應』以下 8 個不同的主題（每個主題挑選一間）：{themes_str}。\n"
            f"請你生成以下 2 個主要的 JSON 欄位資料，並『嚴格』遵守規則：\n"
            f"- caption: (主文) 第一人稱發牢騷或表達興奮，用輕鬆口吻推薦這 8 間必吃餐廳。結尾拋出引發討論的問題，並呼籲『收藏這篇』和『分享給朋友』。這裡『絕對不要』寫出地址或詳細店名。480字內。\n"
            f"  ⚠️【排版與分段要求】：請務必適當分段！段落與段落之間必須使用 '\\n\\n' 換行。不要把所有字擠在一起！\n"
            f"- restaurants: (這是一個包含 8 個物件的陣列 Array，每個物件代表一間餐廳，需包含以下屬性)\n"
            f"  - store_name: (店名) 餐廳的精準名稱。\n"
            f"  - theme: (所屬主題) 標明這家店是對應哪一個主題（例如填入：深夜排隊宵夜）。\n"
            f"  - must_order: (必點菜色) 推薦的一道必點菜色。\n"
            f"  - image_prompt: (英文咒語) 請撰寫一個具體且專業的英文美食攝影咒語。為了確保真實無AI感，『強制』加入以下風格關鍵字：'Vertical (9:16) aspect ratio, Phone portrait mode, Raw food photograph, unedited, authentic, shot on iPhone 15 Pro, 35mm equivalent lens, Clear, crisp, natural daylight, similar lighting to image_1.png, Realistic and imperfect textures, True-to-life colors, no over-saturation, no HDR look'. 背景需呈現簡單、自然的餐桌或餐廳環境，並自然模糊。嚴禁使用：AI, CGI, render, perfect, flawless, 8k, highly detailed, over-processed HDR。\n"
            f"  - address: (詳細地址) 餐廳的真實詳細地址。\n"
            f"  - google_maps_keyword: (Google Maps搜尋關鍵字) 最容易搜到這家店的關鍵字。\n\n"
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
        restaurants = data.get("restaurants", [])
        
        if len(restaurants) < 8:
            print(f"⚠️ 警告：AI 僅生成了 {len(restaurants)} 間餐廳。")
            
        if len(caption) > 480: caption = caption[:475] + "..."
        
        comment_texts = []
        for i, r in enumerate(restaurants):
            store_name = r.get("store_name", "未知店名")
            theme = r.get("theme", "推薦美食")
            must_order = r.get("must_order", "未知")
            address = r.get("address", "未知地址")
            google_maps_keyword = r.get("google_maps_keyword", "未知關鍵字")
            
            c_text = ""
            if i == 0:
                c_text = f"整理好這 {len(restaurants)} 間必吃美食的地址和搜尋關鍵字啦！吃貨們快點筆記起來👇\n\n"
            
            c_text += (
                f"✨ {i+1}. [{theme}] {store_name}\n"
                f"🍽️ 必點：{must_order}\n"
                f"📍 地址：{address}\n"
                f"🗺️ 搜尋：{google_maps_keyword}"
            )
            
            if len(c_text) > 480: c_text = c_text[:475] + "..."
            comment_texts.append(c_text)

        fb_ig_caption = caption + "\n\n" + "\n\n".join(comment_texts)

        img_dir = "images/food"
        
        if os.path.exists(img_dir) and not os.path.isdir(img_dir):
            os.remove(img_dir)
        os.makedirs(img_dir, exist_ok=True)
        
        img_names = []
        local_img_paths = []
        
        for i, r in enumerate(restaurants[:8]):
            image_prompt = r.get("image_prompt")
            if not image_prompt:
                continue
                
            print(f"🎨 正在以真實手機攝影風格繪製第 {i+1} 間餐廳 ({r.get('theme', '未知主題')})...")
            try:
                img_res = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=image_prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        # 💡 確保美食圖片也是直立的 9:16
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
                time.sleep(1.5) # 避免 Rate Limit
            except Exception as e:
                print(f"💥 生成第 {i+1} 張圖片時發生錯誤：{e}")
                
        if img_names:
            with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_names[0])
            
        with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        
        for i, text in enumerate(comment_texts):
            file_name = "comment.txt" if i == 0 else f"comment{i+1}.txt"
            with open(file_name, "w", encoding="utf-8") as f: f.write(text)
            
        print(f"👉 檔案寫入完成：主文({len(caption)}字) / 產出 {len(img_names)} 張圖片")

        post_to_fb_and_ig(fb_ig_caption, local_img_paths)

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()