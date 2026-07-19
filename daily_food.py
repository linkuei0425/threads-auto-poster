import os, sys, time, json, random
from google import genai
from google.genai import types

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def run():
    try:
        if not GEMINI_KEY: raise Exception("缺少 GEMINI_API_KEY")
        client = genai.Client(api_key=GEMINI_KEY)
        
        # 1. 城市與主題設定
        target_cities = ["曼谷", "清邁", "首爾", "福岡", "大阪", "京都", "東京", "香港"]
        city = random.choice(target_cities)
        if os.path.exists("city.txt"):
            with open("city.txt", "r", encoding="utf-8") as f: city = f.read().strip()
        
        themes = ["在地人推薦街頭小吃", "必吃百年老店", "視覺系網美甜點", "深夜排隊宵夜", "隱藏版巷弄美食"]
        theme = random.choice(themes)
        
        # 2. 核心 Prompt 設定：要求 AI 生成 6 間餐廳與對應欄位
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。請針對【{city}】挑選 6 家符合【{theme}】主題的真實餐廳。\n"
            "輸出純 JSON 格式 (嚴格遵守，不要 Markdown): \n"
            "{{"
            "'caption': 'Threads主文，第一人稱發文，興奮口吻，不寫地址，結尾拋出互動問題。',\n"
            "'restaurants': [{'store_name': '...', 'recommended_food': '...', 'transportation': '...', 'address': '...', 'google_maps_keyword': '...', "
            "'image_prompt': 'Vertical (9:16) aspect ratio, Phone portrait mode, Raw travel photograph, unedited, authentic, shot on iPhone 15 Pro, 35mm equivalent lens, Clear, crisp, natural daylight, Realistic and imperfect, True-to-life colors, no over-saturation, no HDR look. Candid food photography.'}]\n"
            "}}"
        )
        
        res = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=task_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(res.text)
        
        # 3. 處理主文存檔
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(data['caption'])
        
        img_names = []
        os.makedirs("images/food", exist_ok=True)
        
        # 4. 生成 6 家餐廳與圖片 + 6 則留言
        for i, r in enumerate(data['restaurants']):
            print(f"🎨 繪製第 {i+1} 家: {r['store_name']}")
            img = client.models.generate_content(
                model='gemini-2.5-flash-image', 
                contents=r['image_prompt'],
                config=types.GenerateContentConfig(image_config=types.ImageConfig(aspect_ratio="9:16"))
            )
            path = f"images/food/food_{i}.jpg"
            img.parts[0].as_image().save(path)
            img_names.append(f"food_{i}.jpg")
            
            # 建立留言 (comment.txt 為第1則，comment2.txt 為第2則...以此類推)
            file_name = "comment.txt" if i == 0 else f"comment{i+1}.txt"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(f"🍴 {r['store_name']}\n📌 推薦：{r['recommended_food']}\n🚆 交通：{r['transportation']}\n📍 地址：{r['address']}\n🗺️ 搜尋：{r['google_maps_keyword']}")
        
        with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))
        print("🎉 執行完成！生成 6 張圖與 6 則留言。")

    except Exception as e:
        print(f"💥 Error: {e}")
        sys.exit(1)

if __name__ == "__main__": run()