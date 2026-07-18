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
        print("⚠️ 沒有圖片可供發布，略過 FB/IG 發文。")
        return

    fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    page_id = os.getenv("FB_PAGE_ID")
    ig_id = os.getenv("IG_ACCOUNT_ID")

    if not fb_token or not page_id:
        print("⚠️ 未找到 FB Token 或 Page ID。略過 FB/IG 發佈。")
        return

    print("🚀 開始發布至 Facebook 與 Instagram...")
    try:
        fb_media_ids = []
        for img_path in image_paths:
            with open(img_path, "rb") as img:
                upload_url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
                payload = {"published": "false", "access_token": fb_token}
                files = {"source": img}
                up_res = requests.post(upload_url, data=payload, files=files).json()
                if "id" in up_res:
                    fb_media_ids.append(up_res["id"])
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
            
            if ig_id:
                time.sleep(3) 
                ig_media_containers = []
                for m_id in fb_media_ids[:10]:
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
                        time.sleep(1.5)

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
                    else:
                        creation_id = ig_media_containers[0]

                    if creation_id:
                        pub_url = f"https://graph.facebook.com/v19.0/{ig_id}/media_publish"
                        pub_payload = {"creation_id": creation_id, "access_token": fb_token}
                        time.sleep(10)
                        pub_res = requests.post(pub_url, data=pub_payload).json()
                        if "id" in pub_res:
                            print(f"✅ Instagram 發布成功！")
    except Exception as e:
        print(f"💥 FB/IG 發布錯誤：{e}")

def run():
    try:
        if not GEMINI_KEY:
            raise Exception("缺少 GEMINI_API_KEY 環境變數")
            
        client = genai.Client(api_key=GEMINI_KEY)
        
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
        themes = ["歷史古蹟", "文青巷弄", "自然絕景", "網美打卡", "當地人私房秘境", "浪漫夜景", "特色建築", "藝術展區"]
        selected_city = random.choice(target_cities)
        themes_str = "、".join(themes)
        
        print(f"🎯 本次抽中城市：【{selected_city}】，準備寫入 city.txt 給明日的餐廳任務使用...")
        with open("city.txt", "w", encoding="utf-8") as f:
            f.write(selected_city)
        
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。你要發一篇 Threads 貼文。\n"
            f"1. 請針對【{selected_city}】這個城市，挑選 8 個真實存在知名地標或私房秘境（請勿介紹餐廳或美食）。\n"
            f"這 8 個景點必須『分別對應』以下 8 個不同的主題：{themes_str}。\n"
            f"請生成以下 JSON 資料：\n"
            f"- caption: 第一人稱發牢騷或表達興奮，推薦這 8 個景點，要求換行分段。480字內。\n"
            f"- spots: (8 個景點的陣列)\n"
            f"  - spot_name: 景點名稱\n"
            f"  - spot_theme: 所屬主題\n"
            f"  - image_prompt: 為了達到極致的擬真手機攝影質感，『強制』在開頭加入以下關鍵字：'Vertical (9:16) aspect ratio, Phone portrait mode, Raw travel photograph, unedited, authentic, shot on iPhone 15 Pro, 35mm equivalent lens. Clear, crisp, natural daylight. Realistic and imperfect textures, True-to-life colors, no over-saturation, no HDR look.' 描述具體畫面，絕不要使用強調完美或AI生成的字眼。\n"
            f"  - transportation: 詳細交通攻略\n"
            f"  - google_maps_keyword: Google Maps 搜尋關鍵字\n\n"
            f"確保以純 JSON 格式輸出，全中文(image_prompt除外)。"
        )
        
        res = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=task_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.8)
        )
        
        data = json.loads(res.text)
        caption = data.get("caption", "").replace("\\n", "\n") 
        spots = data.get("spots", [])
        
        if len(caption) > 480: caption = caption[:475] + "..."
        
        comment_texts = []
        for i, spot in enumerate(spots):
            c_text = ""
            if i == 0: c_text = f"整理好這 {len(spots)} 個地方的交通和關鍵字啦👇\n\n"
            c_text += f"✨ {i+1}. [{spot.get('spot_theme')}] {spot.get('spot_name')}\n🚆 交通：{spot.get('transportation')}\n🗺️ 搜尋：{spot.get('google_maps_keyword')}"
            comment_texts.append(c_text[:480])

        fb_ig_caption = caption + "\n\n" + "\n\n".join(comment_texts)

        img_dir = "images/SPOT"
        if os.path.exists(img_dir) and not os.path.isdir(img_dir): os.remove(img_dir)
        os.makedirs(img_dir, exist_ok=True)
        # 清除舊照片
        for f in os.listdir(img_dir):
            os.remove(os.path.join(img_dir, f))
            
        img_names, local_img_paths = [], []
        
        for i, spot in enumerate(spots[:8]):
            image_prompt = spot.get("image_prompt")
            print(f"🎨 生成第 {i+1} 張圖片 (手機實拍風格)...")
            try:
                img_res = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=image_prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio="9:16") # 強制直式 9:16
                    )
                )
                
                img_name = f"spot_{int(time.time())}_{i}.jpg"
                local_img_path = f"{img_dir}/{img_name}"
                
                for part in img_res.parts:
                    if part.inline_data:
                        part.as_image().save(local_img_path)
                        img_names.append(img_name)
                        local_img_paths.append(local_img_path)
                        break
                time.sleep(2)
            except Exception as e:
                print(f"💥 生成圖片錯誤：{e}")
                
        with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        
        # 清除舊的 comment*.txt
        for file in os.listdir("."):
            if file.startswith("comment") and file.endswith(".txt"): os.remove(file)
            
        for i, text in enumerate(comment_texts):
            file_name = "comment.txt" if i == 0 else f"comment{i+1}.txt"
            with open(file_name, "w", encoding="utf-8") as f: f.write(text)
            
        print(f"👉 景點腳本完成，準備發佈至 FB/IG...")
        post_to_fb_and_ig(fb_ig_caption, local_img_paths)

    except Exception as e:
        print(f"💥 發生嚴重錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
