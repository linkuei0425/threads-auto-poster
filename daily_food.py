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
    if not image_paths:
        return

    fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    page_id = os.getenv("FB_PAGE_ID")
    ig_id = os.getenv("IG_ACCOUNT_ID")

    if not fb_token or not page_id:
        print("⚠️ 未找到 FB Token，略過 FB/IG 發佈。")
        return

    print("🚀 餐廳模組 - 開始發布至 FB/IG...")
    try:
        fb_media_ids = []
        for img_path in image_paths:
            with open(img_path, "rb") as img:
                upload_url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
                payload = {"published": "false", "access_token": fb_token}
                files = {"source": img}
                up_res = requests.post(upload_url, data=payload, files=files).json()
                if "id" in up_res: fb_media_ids.append(up_res["id"])

        if fb_media_ids:
            post_url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
            post_payload = {"message": text, "access_token": fb_token}
            for i, m_id in enumerate(fb_media_ids):
                post_payload[f"attached_media[{i}]"] = f'{{"media_fbid":"{m_id}"}}'
            fb_post_res = requests.post(post_url, data=post_payload).json()
            
            if ig_id:
                time.sleep(3) 
                ig_media_containers = []
                for m_id in fb_media_ids[:10]:
                    photo_data = requests.get(f"https://graph.facebook.com/v19.0/{m_id}?fields=images&access_token={fb_token}").json()
                    source_url = photo_data.get("images", [{}])[0].get("source")
                    if source_url:
                        cont_res = requests.post(
                            f"https://graph.facebook.com/v19.0/{ig_id}/media", 
                            data={"image_url": source_url, "is_carousel_item": "true" if len(fb_media_ids) > 1 else "false", "access_token": fb_token}
                        ).json()
                        if "id" in cont_res: ig_media_containers.append(cont_res["id"])
                        time.sleep(1.5)

                if ig_media_containers:
                    if len(ig_media_containers) > 1:
                        car_res = requests.post(
                            f"https://graph.facebook.com/v19.0/{ig_id}/media", 
                            data={"media_type": "CAROUSEL", "children": ",".join(ig_media_containers), "caption": text, "access_token": fb_token}
                        ).json()
                        creation_id = car_res.get("id")
                    else:
                        creation_id = ig_media_containers[0]

                    if creation_id:
                        time.sleep(10)
                        pub_res = requests.post(f"https://graph.facebook.com/v19.0/{ig_id}/media_publish", data={"creation_id": creation_id, "access_token": fb_token}).json()
                        print("✅ FB/IG 多圖發布成功")
    except Exception as e:
        print(f"💥 FB/IG 發布錯誤：{e}")

def run():
    try:
        if not GEMINI_KEY: raise Exception("缺少 GEMINI_API_KEY")
        client = genai.Client(api_key=GEMINI_KEY)
        
        selected_city = "東京"
        if os.path.exists("city.txt"):
            with open("city.txt", "r", encoding="utf-8") as f:
                selected_city = f.read().strip()
                
        print(f"🎯 啟動連動機制！將針對昨天抽中的城市：【{selected_city}】生成 8 間美食！")
        
        themes = ["在地人推薦街頭小吃", "必吃百年老店", "視覺系網美甜點", "深夜排隊宵夜", "隱藏版巷弄美食", "高CP值平價美食", "傳統市場必吃", "在地特色咖啡廳"]
        themes_str = "、".join(themes)
        
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。你要發一篇 Threads 貼文。\n"
            f"1. 請針對【{selected_city}】這個城市，挑選 8 家真實存在的特色美食或隱藏版餐廳。\n"
            f"這 8 家餐廳必須『分別對應』以下 8 個不同的主題：{themes_str}。\n"
            f"請生成以下 JSON 資料：\n"
            f"- caption: 第一人稱發牢騷或表達興奮，推薦這 8 間美食。480字內。\n"
            f"- restaurants: (8 個餐廳的陣列)\n"
            f"  - store_name: 餐廳名稱\n"
            f"  - theme: 餐廳對應主題\n"
            f"  - image_prompt: 『強制』在開頭加入：'Vertical (9:16) aspect ratio, Phone portrait mode, Raw food photograph, unedited, authentic, shot on iPhone 15 Pro, 35mm equivalent lens. Clear, crisp, natural daylight or warm ambient. Realistic and imperfect textures, True-to-life colors, no over-saturation, no HDR look.'\n"
            f"  - address: 真實詳細地址\n"
            f"  - google_maps_keyword: Google Maps 搜尋關鍵字\n\n"
            f"請務必以純 JSON 格式輸出，全中文(image_prompt除外)。"
        )
        
        res = client.models.generate_content(
            model='gemini-2.5-flash', contents=task_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.8)
        )
        
        data = json.loads(res.text)
        caption = data.get("caption", "").replace("\\n", "\n")
        restaurants = data.get("restaurants", [])
        
        comment_texts = []
        for i, r in enumerate(restaurants):
            c_text = ""
            if i == 0: c_text = f"整理好這 {len(restaurants)} 間餐廳的地址和關鍵字啦👇\n\n"
            c_text += f"✨ {i+1}. [{r.get('theme')}] {r.get('store_name')}\n📍 地址：{r.get('address')}\n🗺️ 搜尋：{r.get('google_maps_keyword')}"
            comment_texts.append(c_text[:480])

        fb_ig_caption = caption + "\n\n" + "\n\n".join(comment_texts)

        img_dir = "images/food"
        os.makedirs(img_dir, exist_ok=True)
        img_names, local_img_paths = [], []
        
        for i, r in enumerate(restaurants[:8]):
            print(f"🎨 生成第 {i+1} 張美食圖片 (手機實拍風格)...")
            try:
                img_res = client.models.generate_content(
                    model='gemini-2.5-flash-image', contents=r.get("image_prompt"),
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
                time.sleep(2)
            except Exception as e:
                print(f"💥 生成美食圖片錯誤：{e}")
                
        with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption[:480])
        for i, text in enumerate(comment_texts):
            with open("comment.txt" if i == 0 else f"comment{i+1}.txt", "w", encoding="utf-8") as f: f.write(text)
            
        print("👉 餐廳腳本完成，準備發佈至 FB/IG...")
        post_to_fb_and_ig(fb_ig_caption, local_img_paths)

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
