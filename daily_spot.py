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

# 2. 設定 FB & IG 發文 Token
FB_IG_TOKEN = "EAAPh5v5diIEBRZC0yZB7duqOn3pMK6EOi4swY011hFWMF2QJdmgMOPrBSvYZApeUkwE1R7uZA99GRUQmVi03ZA9cLmSB95nhzfLixvalTZBWU3wZBgIjfuc01QDwAj8R1dte339ZCI8ZBUj5S30YvpwpCV6EPhAMof8uAgfhhRnxOIBrseQt5YmDZBhZAAZBEtY8sQZDZD"

def post_to_fb_and_ig(text, image_paths):
    """使用 Facebook Graph API 將產生的圖文發布至 FB 與 IG"""
    if not image_paths:
        print("⚠️ 沒有圖片可供發布，略過 FB/IG 發文。")
        return

    print("🚀 開始發布至 Facebook 與 Instagram...")
    try:
        # 1. 取得 Page ID 和 IG Account ID
        me_url = f"https://graph.facebook.com/v19.0/me?fields=id,instagram_business_account&access_token={FB_IG_TOKEN}"
        me_res = requests.get(me_url).json()
        page_id = me_res.get("id")
        ig_id = me_res.get("instagram_business_account", {}).get("id")

        if not page_id:
            print("⚠️ 無法取得 Facebook Page ID，請確認 Token 權限。")
            return

        # 發布到 Facebook
        print(f"📘 準備發布至 Facebook Page (ID: {page_id})")
        fb_media_ids = []
        for img_path in image_paths:
            with open(img_path, "rb") as img:
                upload_url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
                payload = {
                    "published": "false", # 先上傳為未發布的相片
                    "access_token": FB_IG_TOKEN
                }
                files = {"source": img}
                up_res = requests.post(upload_url, data=payload, files=files).json()
                if "id" in up_res:
                    fb_media_ids.append(up_res["id"])
                else:
                    print(f"⚠️ FB 圖片上傳失敗: {up_res}")

        if fb_media_ids:
            # 將上傳的相片綁定成一篇貼文
            post_url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
            post_payload = {
                "message": text,
                "access_token": FB_IG_TOKEN
            }
            for i, m_id in enumerate(fb_media_ids):
                post_payload[f"attached_media[{i}]"] = f'{{"media_fbid":"{m_id}"}}'
            
            fb_post_res = requests.post(post_url, data=post_payload).json()
            if "id" in fb_post_res:
                print(f"✅ Facebook 發布成功！Post ID: {fb_post_res['id']}")
            else:
                print(f"⚠️ Facebook 發布失敗: {fb_post_res}")

            # 發布到 Instagram
            if ig_id:
                print(f"📸 準備發布至 Instagram (ID: {ig_id})")
                time.sleep(3) # 等待 FB 圖片在 CDN 上準備好
                
                ig_media_containers = []
                # IG 最多支援 10 張圖片的 Carousel
                for m_id in fb_media_ids[:10]:
                    photo_url_req = f"https://graph.facebook.com/v19.0/{m_id}?fields=images&access_token={FB_IG_TOKEN}"
                    photo_data = requests.get(photo_url_req).json()
                    
                    images = photo_data.get("images", [])
                    if images:
                        source_url = images[0]["source"] # 取得最大解析度的直接網址
                        ig_cont_url = f"https://graph.facebook.com/v19.0/{ig_id}/media"
                        cont_payload = {
                            "image_url": source_url,
                            "is_carousel_item": "true" if len(fb_media_ids) > 1 else "false",
                            "access_token": FB_IG_TOKEN
                        }
                        # 單圖才在 item 層級設定 caption
                        if len(fb_media_ids) == 1:
                            cont_payload["caption"] = text
                        
                        cont_res = requests.post(ig_cont_url, data=cont_payload).json()
                        if "id" in cont_res:
                            ig_media_containers.append(cont_res["id"])
                            print(f"  - IG 容器 {cont_res['id']} 建立成功")
                        else:
                            print(f"⚠️ IG 圖片容器建立失敗: {cont_res}")
                        time.sleep(1)

                if ig_media_containers:
                    if len(ig_media_containers) > 1:
                        print("  - 建立 IG Carousel 輪播容器...")
                        car_url = f"https://graph.facebook.com/v19.0/{ig_id}/media"
                        car_payload = {
                            "media_type": "CAROUSEL",
                            "children": ",".join(ig_media_containers),
                            "caption": text,
                            "access_token": FB_IG_TOKEN
                        }
                        car_res = requests.post(car_url, data=car_payload).json()
                        creation_id = car_res.get("id")
                    else:
                        creation_id = ig_media_containers[0]

                    if creation_id:
                        print(f"  - 發布 IG 貼文 (Creation ID: {creation_id})...")
                        pub_url = f"https://graph.facebook.com/v19.0/{ig_id}/media_publish"
                        pub_payload = {
                            "creation_id": creation_id,
                            "access_token": FB_IG_TOKEN
                        }
                        time.sleep(5) # API 需要時間準備好輪播容器
                        pub_res = requests.post(pub_url, data=pub_payload).json()
                        if "id" in pub_res:
                            print(f"✅ Instagram 發布成功！IG Post ID: {pub_res['id']}")
                        else:
                            print(f"⚠️ Instagram 發布失敗: {pub_res}")
            else:
                print("⚠️ 此 Token 未綁定 Instagram Business Account，跳過 IG 發布。")
                
    except Exception as e:
        print(f"💥 FB/IG 發布過程中發生錯誤：{e}")


def run():
    try:
        if not GEMINI_KEY:
            raise Exception("缺少 GEMINI_API_KEY 環境變數")
            
        client = genai.Client(api_key=GEMINI_KEY)
        
        # --- A. Gemini 生成 Threads 專屬閒聊風文案與 10 留言 ---
        print("🤖 系統正在隨機抽取城市與主題...")
        
        target_cities = [
            "曼谷", "清邁", "釜山", "首爾", "新加坡", "沖繩", "宮古島", "福岡", 
            "大阪", "京都", "神戶", "東京", "宇治", "奈良", "香港", "澳門", 
            "河內", "胡志明市", "峴港", "蘇梅島", "普吉島", "芭達雅", "富國島",
            "吉隆坡", "濟州島", "札幌", "峇里島", "雅加達", "馬尼拉", "宿霧", 
            "檳城", "北京", "上海", "廣州", "深圳", "成都", "雲南", "新德里", "孟買",
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
        
        # 擴展至 10 個主題
        themes = ["歷史古蹟", "文青巷弄", "自然絕景", "網美打卡", "當地人私房秘境", "購物商圈", "浪漫夜景", "特色建築", "傳統市集", "藝術展區"]
        
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
            f"  - spot_theme: (所屬主題) 標明這個景點是對應哪一個主題（例如填入：文青巷弄）。\n"
            f"  - image_prompt: (英文咒語) 為了徹底消除「AI塑膠感」與「過度精緻感」，請描述該景點具體畫面，並『強制』加入以下風格關鍵字：'Shot on iPhone 15 camera roll, authentic everyday travel snapshot, unedited raw photo, Kodak Portra 400 film aesthetic, natural mundane lighting, slight motion blur, documentary photography, amateur casual framing, realistic imperfections, natural film grain, life-like textures'. 畫面不要太完美、不要刻意對稱，可以帶點路人、電線桿等真實街景雜物。並且『絕對禁止』使用 '8k, masterpiece, cinematic lighting, epic, hyper-detailed, HDR, perfect composition, professional, studio lighting' 等催生AI感的字眼。\n"
            f"  - transportation: (交通攻略) 超簡短大眾交通方式，例如「地鐵某站出口步行3分」。請務必精簡在15個字以內以免超過留言字數限制。\n"
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
            print("⚠️ 警告：AI 輸出的不是有效的 JSON！")
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

        # --- B. Gemini 生成圖片並儲存 ---
        img_dir = "images/SPOT"
        if os.path.exists(img_dir) and not os.path.isdir(img_dir):
            os.remove(img_dir)
        os.makedirs(img_dir, exist_ok=True)
        
        img_names = []
        local_img_paths = [] # 用於給 FB 和 IG API 抓取圖片路徑
        
        for i, spot in enumerate(spots[:10]):
            image_prompt = spot.get("image_prompt")
            if not image_prompt: continue
                
            print(f"🎨 正在以無修圖真實風格繪製第 {i+1} 個景點 ({spot.get('spot_theme', '未知主題')})...")
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
                
                # 避免連續呼叫 API 造成 Rate Limit
                time.sleep(1.5)
            except Exception as e:
                print(f"💥 生成圖片時發生錯誤：{e}")
                
        # --- C. 寫入暫存檔 (供後續 Threads 發文或其他用途) ---
        if img_names:
            with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_names[0])
            
        with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        
        # 寫入多達 10 則的留言檔 (保留原本 comment.txt 及 comment2.txt 的命名規律)
        for i, text in enumerate(comment_texts):
            file_name = "comment.txt" if i == 0 else f"comment{i+1}.txt"
            with open(file_name, "w", encoding="utf-8") as f: f.write(text)
            
        # 寫入給 FB 和 IG 的合併版文案
        with open("fb_ig_caption.txt", "w", encoding="utf-8") as f: f.write(fb_ig_caption)
            
        print(f"👉 檔案寫入完成：主文({len(caption)}字) / 產出 {len(img_names)} 張圖片")

        # --- D. 呼叫自動發布至 FB 與 IG ---
        post_to_fb_and_ig(fb_ig_caption, local_img_paths)

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
