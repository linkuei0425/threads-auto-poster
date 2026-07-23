import os
import sys
import time
import json
import random
from google import genai
from google.genai import types

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def run():
    # --- 🛡️ 防噴錢機制開始 🛡️ ---
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "1")
    if run_attempt != "1" and os.path.exists("caption.txt"):
        print(f"♻️ 偵測到這是第 {run_attempt} 次重跑 (Re-run)！")
        print("為了避免噴錢，將直接沿用舊有圖文檔案，跳過 Gemini API。")
        return  # 直接結束 Python 腳本，讓 Actions 繼續拿舊檔案去嘗試發文
    # --- 🛡️ 防噴錢機制結束 🛡️ ---

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
        themes_list = ["必吃在地小吃", "網美打卡咖啡廳", "傳統老店或夜市美食", "高質感特色餐廳", "隱藏版深夜食堂", "人氣排隊甜點"]
        
        # 為了跟景點連戲，讀取由景點腳本保留的 city.txt
        if os.path.exists("city.txt"):
            with open("city.txt", "r", encoding="utf-8") as f: 
                selected_city = f.read().strip()
            print(f"📌 發現保留的 city.txt，繼續使用城市：【{selected_city}】")
        else:
            selected_city = random.choice(target_cities)
            with open("city.txt", "w", encoding="utf-8") as f:
                f.write(selected_city)
            print(f"🎲 抽取新城市並寫入 city.txt：【{selected_city}】")
                
        themes_str = "、".join(themes_list)
        print(f"🎯 本次抽中城市：【{selected_city}】，準備交由 Gemini 生成「綜合多元美食主題」...")
        
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。你要發一篇貼文。\n"
            f"1. 請針對【{selected_city}】這個城市，挑選 6 個『不同類型』的真實存在知名餐廳或在地美食（請勿介紹純景點）。\n"
            f"   💡 【重要】：這 6 間店必須涵蓋多元風格，例如從「{themes_str}」中挑選組合，絕對不要 6 間都是同一種類型，越豐富越好！\n"
            f"請你生成以下 2 個主要的 JSON 欄位資料，並『嚴格』遵守規則：\n"
            f"- caption: (主文) 第一人稱發牢騷或表達興奮或專業美食家，用輕鬆口吻簡單盤點這 6 間店。結尾拋出引發討論的問題，並呼籲『收藏這篇』和『看留言區有詳細資訊』。這裡『絕對不要』寫出地址或營業時間,也不要用副詞。480字內。\n"
            f"  ⚠️【排版與分段要求】：請務必適當分段！段落與段落之間必須使用 '\\n\\n' 換行。不要把所有字擠在一起！\n"
            f"- restaurants: (這是一個包含 6 個物件的陣列 Array，每個物件代表一間店，需包含以下屬性)\n"
            f"  - name: (餐廳名稱) 餐廳的精準名稱。\n"
            f"  - image_prompt: (英文咒語) 請根據該餐廳或招牌菜色的具體畫面撰寫咒語。為了打破 AI 塗抹感並模擬真實手機攝影，『強制』加入以下關鍵字：'Vertical (9:16) aspect ratio, Phone portrait mode, Raw food photograph, unedited, authentic, shot on iPhone 15 Pro, 35mm equivalent lens, Clear, crisp, natural daylight, Realistic and imperfect textures, True-to-life colors, no over-saturation, no HDR look'. 不要使用任何 master piece, 8k 等字眼。\n"
            f"  - info: (地址與營業時間) 詳細的地址、大約的營業時間或必點推薦。越詳細越好。\n"
            f"  - google_maps_keyword: (Google Maps搜尋關鍵字) 最容易搜到這間店的關鍵字。\n\n"
            f"請務必以純 JSON 格式輸出，不要包含任何 Markdown 標記。所有輸出內容（除了 image_prompt 外）必須是全中文。"
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
        
        if len(restaurants) < 6:
            print(f"⚠️ 警告：AI 只有生成 {len(restaurants)} 間餐廳 (預期 6 間)。")

        if len(caption) > 480: caption = caption[:475] + "..."
        
        with open("caption.txt", "w", encoding="utf-8") as f: 
            f.write(caption)
            
        print(f"📝 正在建立留言檔 (每 2 間餐廳合併為 1 則)...")
        # 合併留言邏輯：每 2 間店寫入一個 txt 檔案
        for i in range(0, len(restaurants), 2):
            chunk = restaurants[i:i+2]
            comment_text = ""
            for j, shop in enumerate(chunk):
                idx = i + j + 1
                name = shop.get("name", "未知餐廳")
                info = shop.get("info", "未知資訊")
                keyword = shop.get("google_maps_keyword", "未知關鍵字")
                
                comment_text += f"✨ 美食 {idx}：{name}\n📍 資訊：{info}\n🗺️ 搜尋：{keyword}\n\n"
            
            comment_text = comment_text.strip()
            if len(comment_text) > 480: comment_text = comment_text[:475] + "..."
            
            file_idx = (i // 2) + 1
            with open(f"comment{file_idx}.txt", "w", encoding="utf-8") as f:
                f.write(comment_text)

        # 注意：美食圖片存入 images/food
        img_dir = "images/food"
        if os.path.exists(img_dir) and not os.path.isdir(img_dir):
            os.remove(img_dir)
        os.makedirs(img_dir, exist_ok=True)
        
        img_names = []
        
        for i, shop in enumerate(restaurants):
            image_prompt = shop.get("image_prompt")
            name = shop.get("name", "未知餐廳")
            if not image_prompt:
                print(f"⚠️ {name} 沒有 image_prompt，跳過生圖。")
                continue
                
            print(f"🎨 [{i+1}/{len(restaurants)}] 正在以極致寫實 iPhone 15 Pro 風格繪製：{name}...")
            try:
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
                        break
                        
                time.sleep(5)
                
            except Exception as e:
                print(f"💥 生成 {name} 圖片時發生錯誤：{e}")
                
        if img_names:
            with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_names[0])
            
        with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))
            
        print(f"\n👉 檔案寫入完成：主文({len(caption)}字) / 產出 {len(img_names)} 張圖片")

    except Exception as e:
        print(f"💥 發生嚴重錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
