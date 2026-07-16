import os
import sys
import time
import json
import random
import requests
from google import genai
from google.genai import types

# --- 設定環境變數 ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FB_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_ID = os.getenv("FB_PAGE_ID")
IG_ID = os.getenv("IG_ACCOUNT_ID")

def post_to_fb_and_ig(text, image_paths):
    """使用 Facebook Graph API 將產生的圖文發布至 FB 與 IG"""
    if not FB_TOKEN or not FB_ID:
        print("⚠️ 未找到 FB Token 或 Page ID，跳過 FB/IG 發布。")
        return

    print("🚀 開始發布至 Facebook 與 Instagram...")
    try:
        # 1. 發布到 Facebook
        print(f"📘 準備發布至 Facebook Page (ID: {FB_ID})")
        fb_media_ids = []
        for img_path in image_paths:
            with open(img_path, "rb") as img:
                upload_url = f"https://graph.facebook.com/v19.0/{FB_ID}/photos"
                payload = {"published": "false", "access_token": FB_TOKEN}
                files = {"source": img}
                up_res = requests.post(upload_url, data=payload, files=files).json()
                if "id" in up_res:
                    fb_media_ids.append(up_res["id"])
                else:
                    print(f"⚠️ FB 圖片上傳失敗: {up_res}")

        if fb_media_ids:
            post_url = f"https://graph.facebook.com/v19.0/{FB_ID}/feed"
            post_payload = {"message": text, "access_token": FB_TOKEN}
            for i, m_id in enumerate(fb_media_ids):
                post_payload[f"attached_media[{i}]"] = f'{{"media_fbid":"{m_id}"}}'
            fb_post_res = requests.post(post_url, data=post_payload).json()
            if "id" in fb_post_res: print(f"✅ Facebook 發布成功！")

            # 2. 發布到 Instagram
            if IG_ID:
                print(f"📸 準備發布至 Instagram (ID: {IG_ID})")
                time.sleep(3) 
                ig_media_containers = []
                for m_id in fb_media_ids[:10]:
                    photo_url_req = f"https://graph.facebook.com/v19.0/{m_id}?fields=images&access_token={FB_TOKEN}"
                    photo_data = requests.get(photo_url_req).json()
                    source_url = photo_data.get("images", [{}])[0].get("source")
                    if source_url:
                        cont_url = f"https://graph.facebook.com/v19.0/{IG_ID}/media"
                        cont_payload = {
                            "image_url": source_url,
                            "is_carousel_item": "true" if len(fb_media_ids) > 1 else "false",
                            "access_token": FB_TOKEN
                        }
                        if len(fb_media_ids) == 1: cont_payload["caption"] = text
                        cont_res = requests.post(cont_url, data=cont_payload).json()
                        if "id" in cont_res: ig_media_containers.append(cont_res["id"])
                        time.sleep(1)

                if ig_media_containers:
                    if len(ig_media_containers) > 1:
                        car_url = f"https://graph.facebook.com/v19.0/{IG_ID}/media"
                        car_payload = {
                            "media_type": "CAROUSEL",
                            "children": ",".join(ig_media_containers),
                            "caption": text,
                            "access_token": FB_TOKEN
                        }
                        creation_id = requests.post(car_url, data=car_payload).json().get("id")
                    else:
                        creation_id = ig_media_containers[0]

                    if creation_id:
                        pub_url = f"https://graph.facebook.com/v19.0/{IG_ID}/media_publish"
                        time.sleep(5)
                        pub_res = requests.post(pub_url, data={"creation_id": creation_id, "access_token": FB_TOKEN}).json()
                        if "id" in pub_res: print(f"✅ Instagram 發布成功！")
    except Exception as e:
        print(f"💥 FB/IG 發布錯誤：{e}")

def run():
    client = genai.Client(api_key=GEMINI_KEY)
    themes = ["歷史古蹟", "文青巷弄", "自然絕景", "網美打卡", "當地人私房秘境", "購物商圈", "浪漫夜景", "特色建築", "傳統市集", "藝術展區"]
    
    # 城市名單 (簡化版)
    target_cities = ["東京", "曼谷", "首爾", "巴黎", "京都", "紐約", "雪梨", "倫敦", "羅馬", "巴塞隆納"]
    selected_city = random.choice(target_cities)
    
    task_prompt = f"針對 {selected_city} 生成 10 個景點，每個景點對應 {', '.join(themes)}。回傳 JSON 格式 (caption, spots: [{spot_name, spot_theme, image_prompt, transportation, google_maps_keyword}])。風格要無AI感，真實旅行攝影。"
    
    res = client.models.generate_content(model='gemini-2.5-flash', contents=task_prompt, config=types.GenerateContentConfig(response_mime_type="application/json"))
    data = json.loads(res.text)
    
    # 處理檔案寫入...
    with open("caption.txt", "w", encoding="utf-8") as f: f.write(data["caption"])
    
    # 圖片生成與儲存邏輯 (保持原有循環)
    img_dir = "images/SPOT"
    os.makedirs(img_dir, exist_ok=True)
    img_names, local_img_paths = [], []
    
    for i, spot in enumerate(data["spots"]):
        img_res = client.models.generate_content(model='gemini-2.5-flash-image', contents=spot["image_prompt"], config=types.GenerateContentConfig(response_modalities=["IMAGE"]))
        local_img_path = f"{img_dir}/spot_{i}.jpg"
        for part in img_res.parts:
            if part.inline_data:
                part.as_image().save(local_img_path)
                img_names.append(f"spot_{i}.jpg")
                local_img_paths.append(local_img_path)
                break
    
    with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))
    
    # 執行 FB/IG 發布
    full_text = f"{data['caption']}\n\n景點資訊整理：\n" + "\n".join([f"{s['spot_name']} ({s['transportation']})" for s in data["spots"]])
    post_to_fb_and_ig(full_text, local_img_paths)

if __name__ == "__main__":
    run()
