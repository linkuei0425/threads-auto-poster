import os, sys, json, random
from google import genai
from google.genai import types

def run():
    # 強制設定 API Key 檢查
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is missing!")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    cities = ["曼谷", "清邁", "釜山", "首爾", "新加坡", "沖繩", "福岡", "大阪", "京都", "東京", "香港", "澳門", "巴黎", "倫敦", "紐約", "雪梨"]
    city = random.choice(cities)
    
    # 寫入城市供餐廳腳本使用
    with open("city.txt", "w", encoding="utf-8") as f:
        f.write(city)
        
    print(f"Generating spots for: {city}")
    
    prompt = f"針對{city}挑選8個景點。輸出純JSON格式: {{'caption': '...', 'spots': [{'spot_name': '...', 'transportation': '...', 'image_prompt': 'Vertical 9:16 aspect ratio, Phone portrait mode, Raw travel photograph, unedited, authentic, shot on iPhone 15 Pro, 35mm lens, natural daylight, realistic imperfect textures, True-to-life colors, no HDR'}]}}"
    
    try:
        res = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt, 
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(res.text)
        
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(data['caption'])
        
        img_names = []
        os.makedirs("images/SPOT", exist_ok=True)
        
        for i, spot in enumerate(data['spots']):
            print(f"Generating image for: {spot['spot_name']}")
            img = client.models.generate_content(model='imagen-3.0-generate-002', contents=spot['image_prompt'])
            path = f"images/SPOT/spot_{i}.jpg"
            img.parts[0].as_image().save(path)
            img_names.append(f"spot_{i}.jpg")
            
            with open(f"comment{i+1}.txt", "w", encoding="utf-8") as f:
                f.write(f"{spot['spot_name']}\n{spot['transportation']}")
                
        with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))
        print("Success!")
        
    except Exception as e:
        print(f"Error during execution: {e}")
        sys.exit(1)

if __name__ == "__main__": run()