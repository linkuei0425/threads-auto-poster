import os, json
from google import genai
from google.genai import types

def run():
    city = "東京", "曼谷", "清邁", "釜山", "首爾", "新加坡", "沖繩", "宮古島", "福岡", 
            "大阪", "京都", "神戶", "東京", "宇治", "奈良", "香港", "澳門", 
            "河內", "胡志明市", "峴港", "蘇梅島", "普吉島", "芭達雅", "富國島",
            "吉隆坡", "濟州島", "札幌", "峇里島", "雅加達", "馬尼拉", "宿霧", 
            "檳城", "北京", "上海", "廣州", "深圳", "成都"
    if os.path.exists("city.txt"):
        with open("city.txt", "r", encoding="utf-8") as f: city = f.read().strip()
    
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    prompt = f"針對{city}挑選8家餐廳。輸出純JSON格式: {{'caption': '...', 'restaurants': [{'store_name': '...', 'address': '...', 'image_prompt': 'Vertical 9:16 aspect ratio, Phone portrait mode, Raw food photograph, unedited, authentic, shot on iPhone 15 Pro, natural daylight, realistic textures, True-to-life colors, no HDR'}]}}"
    res = client.models.generate_content(model='gemini-2.0-flash', contents=prompt, config=types.GenerateContentConfig(response_mime_type="application/json"))
    data = json.loads(res.text)
    
    with open("caption.txt", "w", encoding="utf-8") as f: f.write(data['caption'])
    img_names = []
    os.makedirs("images/food", exist_ok=True)
    for i, r in enumerate(data['restaurants']):
        img = client.models.generate_content(model='imagen-3.0-generate-002', contents=r['image_prompt'])
        path = f"images/food/food_{i}.jpg"
        img.parts[0].as_image().save(path)
        img_names.append(f"food_{i}.jpg")
        with open(f"comment{i+1}.txt", "w", encoding="utf-8") as f: f.write(f"{r['store_name']}\n{r['address']}")
    with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))

if __name__ == "__main__": run()