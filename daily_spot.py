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

                    # 實際發布
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
        
        print("🤖 系統正在隨機抽取城市與主題...")
        
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
        
        # 擴充為 10 個主題
        themes = [
            "歷史古蹟", "文青巷弄", "自然絕景", "網美打卡", "當地人私房秘境", 
            "浪漫夜景", "購物商圈", "市集或市場或夜市", "特色建築", "藝術展區"
        ]
        
        selected_city = random.choice(target_cities)
        themes_str = "、".join(themes)
        
        print(f"🎯 本次抽中：【{selected_city}】，準備交由 Gemini 生成涵蓋 10 大主題的景點...")
        
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。你要發一篇 Threads 貼文。\n"
            f"1. 請針對【{selected_city}】這個城市，挑選 10 個真實存在知名地標或私房秘境（請勿介紹餐廳或美食）。\n"
            f"這 10 個景點必須『分別對應』以下 10 個不同的主題（每個主題挑選一個景點）：{themes_str}。\n"
            f"請你生成以下 2 個主要的 JSON 欄位資料，並『嚴格』遵守規則：\n"
            f"- caption: (主文) 第一人稱發牢騷或表達興奮，用輕鬆口吻推薦這 10 個景點。結尾拋出引發討論的問題，並呼籲『收藏這篇』和『分享給朋友』。這裡『絕對不要』寫出如何抵達或交通方式。480字內。\n"
            f"  ⚠️【排版與分段要求】：請務必適當分段！段落與段落之間必須使用 '\\n\\n' 換行。例如：先寫一段開場白，換行後列出十個景點的簡單氛圍，換行後再寫結尾互動語。不要把所有字擠在一起！\n"
            f"- spots: (這是一個包含 10 個物件的陣列 Array，每個物件代表一個景點，需包含以下屬性)\n"
            f"  - spot_name: (景點名稱) 景點的精準名稱。\n"
            f"  - spot_theme: (所屬主題) 標明這個景點是對應哪一個主題（例如填入：市集或市場或夜市）。\n"
            f"  - image_prompt: (英文咒語) 為了在『專業攝影的高水準』與『真實、無AI感』之間取得完美平衡，請描述該景點的具體畫面。並且『強制』在開頭或結尾加入以下風格關鍵字：'Professional editorial travel photography, full-frame camera quality, shallow depth of field, f/1.4 aperture bokeh, candid professional look, natural light (e.g., soft golden hour, Moody overcast), realistic natural color grading, raw film textures, slight authentic film grain'. 構圖要精細（例如引導線、三分法），但呈現出的光影和質感必須是自然的真實場景，不要有任何後製過度的痕跡。並且『絕對不要』使用 '8k, masterpiece, cinematic lighting, over-processed HDR, hyper-detailed, perfect composition' 等會增加塑膠感的字眼。尺寸與縱橫比 (Size & Aspect Ratio)：明確指定為「Vertical (9:16) aspect ratio」（垂直 9:16 縱橫比）和「Phone portrait mode」（手機人像模式），以確保生成正確的尺寸。
媒介與真實感 (Medium & Realism)：使用「Raw travel photograph, unedited, authentic」（原始旅遊照片，未修圖，真實），並強調模擬真實相機「iPhone 15 Pro, 35mm equivalent lens」的成相。這能有效打破 AI 過於平滑的塗抹感。
光線與清晰度 (Light & Clarity)：保留了「Clear, crisp, natural daylight」（明亮、清爽、自然的日光）\n"
            f"  - transportation: (交通攻略) 詳細的自由行大眾交通方式，例如搭乘哪條地鐵、哪個出口、步行幾分鐘。越詳細越好。\n"
            f"  - google_maps_keyword: (Google Maps搜尋關鍵字) 最容易搜到這個景點的關鍵字。\n\n"
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
        spots = data.get("spots", [])
        
        if len(spots) < 10:
            print(f"⚠️ 警告：AI 僅生成了 {len(spots)} 個景點。")
            
        if len(caption) > 480: caption = caption[:475] + "..."
        
        # 動態產生最多 10 則留言，每則留言放一個景點
        comment_texts = []
        for i, spot in enumerate(spots):
            spot_name = spot.get("spot_name", "未知景點")
            spot_theme = spot.get("spot_theme", "推薦景點")
            transportation = spot.get("transportation", "未知交通方式")
            google_maps_keyword = spot.get("google_maps_keyword", "未知關鍵字")
            
            c_text = ""
            if i == 0:
                c_text = f"整理好這 {len(spots)} 個地方的交通和搜尋關鍵字給大家啦！快點筆記起來👇\n\n"
            
            c_text += (
                f"✨ {i+1}. [{spot_theme}] {spot_name}\n"
                f"🚆 交通：{transportation}\n"
                f"🗺️ 搜尋：{google_maps_keyword}"
            )
            
            if len(c_text) > 480: c_text = c_text[:475] + "..."
            comment_texts.append(c_text)

        # 將主文與所有交通留言合併，專門給沒有字數限制的 FB / IG 使用
        fb_ig_caption = caption + "\n\n" + "\n\n".join(comment_texts)

        img_dir = "images/SPOT"
        
        if os.path.exists(img_dir) and not os.path.isdir(img_dir):
            os.remove(img_dir)
        os.makedirs(img_dir, exist_ok=True)
        
        img_names = []
        local_img_paths = [] # 追蹤本地圖片路徑供 FB/IG 函數上傳用
        
        for i, spot in enumerate(spots[:10]):
            image_prompt = spot.get("image_prompt")
            if not image_prompt:
                continue
                
            print(f"🎨 正在以專業攝影風格繪製第 {i+1} 個景點 ({spot.get('spot_theme', '未知主題')})...")
            try:
                img_res = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=image_prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio="1:1")
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
                time.sleep(1.5) # 避免 Rate Limit
            except Exception as e:
                print(f"💥 生成第 {i+1} 張圖片時發生錯誤：{e}")
                
        if img_names:
            with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_names[0])
            
        with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        
        # 寫入多達 10 則的留言檔 (保留原本 comment.txt 及 comment2.txt 的命名規律)
        for i, text in enumerate(comment_texts):
            file_name = "comment.txt" if i == 0 else f"comment{i+1}.txt"
            with open(file_name, "w", encoding="utf-8") as f: f.write(text)
            
        print(f"👉 檔案寫入完成：主文({len(caption)}字) / 產出 {len(img_names)} 張圖片")

        # 觸發發文到 FB 與 IG
        post_to_fb_and_ig(fb_ig_caption, local_img_paths)

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
