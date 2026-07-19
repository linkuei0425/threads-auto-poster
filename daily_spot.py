import os
import sys
import time
import json
import random
from google import genai
from google.genai import types

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

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
        themes = ["歷史古蹟", "文青巷弄", "自然絕景", "購物商圈", "傳統市場或夜市" ,"網美打卡", "當地人私房秘境", "浪漫夜景"]
        
        if os.path.exists("city.txt"):
            with open("city.txt", "r", encoding="utf-8") as f: 
                selected_city = f.read().strip()
            print(f"📌 發現保留的 city.txt，繼續使用城市：【{selected_city}】")
        else:
            selected_city = random.choice(target_cities)
            with open("city.txt", "w", encoding="utf-8") as f:
                f.write(selected_city)
            print(f"🎲 抽取新城市並寫入 city.txt：【{selected_city}】")
                
        selected_theme = random.choice(themes)
        print(f"🎯 本次抽中：【{selected_city}】的【{selected_theme}】，準備交由 Gemini 生成...")
        
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。你要發一篇貼文。\n"
            f"1. 請針對【{selected_city}】這個城市，挑選 10 個符合【{selected_theme}】主題的真實存在知名地標或私房秘境（請勿介紹餐廳或美食）。\n"
            f"請你生成以下 2 個主要的 JSON 欄位資料，並『嚴格』遵守規則：\n"
            f"- caption: (主文) 第一人稱發牢騷或表達興奮或專業旅遊家，用輕鬆口吻簡單盤點這 10 個景點。結尾拋出引發討論的問題，並呼籲『收藏這篇』和『看留言區有詳細交通』。這裡『絕對不要』寫出如何抵達或交通方式,也不要用副詞。480字內。\n"
            f"  ⚠️【排版與分段要求】：請務必適當分段！段落與段落之間必須使用 '\\n\\n' 換行。不要把所有字擠在一起！\n"
            f"- spots: (這是一個包含 10 個物件的陣列 Array，每個物件代表一個景點，需包含以下屬性)\n"
            f"  - spot_name: (景點名稱) 景點的精準名稱。\n"
            f"  - image_prompt: (英文咒語) 請根據該景點具體畫面撰寫咒語。為了打破 AI 塗抹感並模擬真實手機攝影，『強制』加入以下關鍵字：'Vertical (9:16) aspect ratio, Phone portrait mode, Raw travel photograph, unedited, authentic, shot on iPhone 15 Pro, 35mm equivalent lens, Clear, crisp, natural daylight, Realistic and imperfect textures, True-to-life colors, no over-saturation, no HDR look'. 不要使用任何 master piece, 8k 等字眼。\n"
            f"  - transportation: (交通攻略) 詳細的自由行大眾交通方式，例如搭乘哪條地鐵、哪個出口、步行幾分鐘。越詳細越好。\n"
            f"  - google_maps_keyword: (Google Maps搜尋關鍵字) 最容易搜到這個景點的關鍵字。\n\n"
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
        spots = data.get("spots", [])
        
        if len(spots) < 10:
            print(f"⚠️ 警告：AI 只有生成 {len(spots)} 個景點 (預期 10 個)。")

        if len(caption) > 480: caption = caption[:475] + "..."
        
        with open("caption.txt", "w", encoding="utf-8") as f: 
            f.write(caption)
            
        print(f"📝 正在建立 {len(spots)} 則獨立留言檔...")
        for i, spot in enumerate(spots):
            spot_name = spot.get("spot_name", "未知景點")
            transportation = spot.get("transportation", "未知交通方式")
            google_maps_keyword = spot.get("google_maps_keyword", "未知關鍵字")
            
            comment_text = (
                f"✨ 景點 {i+1}：{spot_name}\n"
                f"🚆 交通：{transportation}\n"
                f"🗺️ 搜尋：{google_maps_keyword}"
            )
            
            if len(comment_text) > 480: comment_text = comment_text[:475] + "..."
            
            with open(f"comment{i+1}.txt", "w", encoding="utf-8") as f:
                f.write(comment_text)

        img_dir = "images/SPOT"
        if os.path.exists(img_dir) and not os.path.isdir(img_dir):
            os.remove(img_dir)
        os.makedirs(img_dir, exist_ok=True)
        
        img_names = []
        
        for i, spot in enumerate(spots):
            image_prompt = spot.get("image_prompt")
            spot_name = spot.get("spot_name", "未知景點")
            if not image_prompt:
                print(f"⚠️ {spot_name} 沒有 image_prompt，跳過生圖。")
                continue
                
            print(f"🎨 [{i+1}/{len(spots)}] 正在以極致寫實 iPhone 15 Pro 風格繪製：{spot_name}...")
            try:
                img_res = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=image_prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio="9:16")
                    )
                )
                
                img_name = f"spot_{int(time.time())}_{i}.jpg"
                local_img_path = f"{img_dir}/{img_name}"
                
                for part in img_res.parts:
                    if part.inline_data:
                        part.as_image().save(local_img_path)
                        img_names.append(img_name)
                        break
                        
                time.sleep(5)
                
            except Exception as e:
                print(f"💥 生成 {spot_name} 圖片時發生錯誤：{e}")
                
        if img_names:
            with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_names[0])
            
        with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))
            
        print(f"\n👉 檔案寫入完成：主文({len(caption)}字) / {len(spots)} 個留言檔 / 產出 {len(img_names)} 張圖片")

    except Exception as e:
        print(f"💥 發生嚴重錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
