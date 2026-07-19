import os, sys, time, json, random
from google import genai
from google.genai import types

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def run():
    try:
        if not GEMINI_KEY: raise Exception("缺少 GEMINI_API_KEY")
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
        
        if os.path.exists("city.txt"):
            with open("city.txt", "r", encoding="utf-8") as f: 
                city = f.read().strip()
            print(f"🔗 從 city.txt 讀取到城市：【{city}】 (與景點同步)")
        else:
            city = random.choice(target_cities)
            print(f"🎲 未找到 city.txt，隨機抽選城市：【{city}】")

        themes = ["在地人推薦街頭小吃", "必吃百年老店", "視覺系網美甜點", "深夜排隊宵夜", "隱藏版巷弄美食"]
        theme = random.choice(themes)
        print(f"🎯 本次餐廳主題抽中：【{theme}】")
        
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。請針對【{city}】挑選 6 家符合【{theme}】主題的真實餐廳或小吃攤。\n"
            "輸出純 JSON 格式 (嚴格遵守，不要 Markdown): \n"
            "{{"
            "'caption': 'Threads主文，第一人稱發文，興奮口吻，不寫地址，結尾拋出互動問題。',\n"
            "'restaurants': [{'store_name': '...', 'recommended_food': '...', 'transportation': '...', 'address': '...', 'google_maps_keyword': '...', "
            "'image_prompt': 'Vertical (9:16) aspect ratio, Phone portrait mode, Raw travel photograph, unedited, authentic, shot on iPhone 15 Pro, 35mm equivalent lens, Clear, crisp, natural daylight, Realistic and imperfect, True-to-life colors, no over-saturation, no HDR look. Candid food photography.'}]\n"
            "}}"
        )
        
        print("🤖 正在交由 Gemini 生成餐廳內容...")
        res = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=task_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(res.text)
        
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(data['caption'])
        
        img_names = []
        img_dir = "images/food"
        os.makedirs(img_dir, exist_ok=True)
        
        for i, r in enumerate(data['restaurants']):
            store_name = r.get('store_name', '未知餐廳')
            print(f"🎨 [{i+1}/6] 正在以極致寫實風格繪製：{store_name}...")
            
            try:
                img = client.models.generate_content(
                    model='gemini-2.5-flash-image', 
                    contents=r['image_prompt'],
                    config=types.GenerateContentConfig(image_config=types.ImageConfig(aspect_ratio="9:16"))
                )
                
                img_name = f"food_{int(time.time())}_{i}.jpg"
                path = f"{img_dir}/{img_name}"
                img.parts[0].as_image().save(path)
                img_names.append(img_name)
                
            except Exception as e:
                print(f"💥 生成 {store_name} 圖片時發生錯誤：{e}")
                continue

            with open(f"comment{i+1}.txt", "w", encoding="utf-8") as f:
                f.write(f"🍴 {store_name}\n📌 推薦：{r.get('recommended_food', '無')}\n🚆 交通：{r.get('transportation', '無')}\n📍 地址：{r.get('address', '無')}\n🗺️ 搜尋：{r.get('google_maps_keyword', '無')}")
            
            time.sleep(5)
            
        with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))
        print(f"🎉 執行完成！生成 {len(img_names)} 張圖與對應留言。")

        if os.path.exists("city.txt"):
            os.remove("city.txt")
            print("🧹 已清除 city.txt，準備下一次的新城市抽籤！")

    except Exception as e:
        print(f"💥 Error: {e}")
        sys.exit(1)

if __name__ == "__main__": 
    run()
