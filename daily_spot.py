import os, sys, time, json, random
from google import genai
from google.genai import types

def run():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    cities = ["曼谷", "清邁", "釜山", "首爾", "新加坡", "沖繩", "宮古島", "福岡", "大阪", "京都", "神戶", "東京", "宇治", "奈良", "香港", "澳門", "河內", "胡志明市", "峴港", "蘇梅島", "普吉島", "芭達雅", "富國島", "吉隆坡", "濟州島", "札幌", "峇里島", "雅加達", "馬尼拉", "宿霧", "檳城", "北京", "上海", "廣州", "深圳", "成都", "新德里", "孟買", "巴黎", "倫敦", "羅馬", "馬德里", "巴塞隆納", "阿姆斯特丹", "柏林", "米蘭", "維也納", "慕尼黑", "威尼斯", "佛羅倫斯", "布拉格", "布達佩斯", "雅典", "蘇黎世", "日內瓦", "哥本哈根", "斯德哥爾摩", "奧斯陸", "赫爾辛基", "里斯本", "波多", "都柏林", "愛丁堡", "布魯塞爾", "法蘭克福", "華沙", "克拉科夫", "尼斯", "里昂", "塞維亞", "瓦倫西亞", "拿坡里", "杜布羅夫尼克", "斯普利特", "薩爾茨堡", "雷克雅維克", "伊斯坦堡", "安塔利亞", "紐約", "洛杉磯", "舊金山", "芝加哥", "拉斯維加斯", "邁阿密", "奧蘭多", "華盛頓特區", "多倫多", "溫哥華", "墨西哥城", "坎昆", "里約熱內盧", "聖保羅", "布宜諾斯艾利斯", "杜拜", "阿布達比", "多哈", "特拉維夫", "開羅", "馬拉喀什", "開普敦", "雪梨", "墨爾本", "奧克蘭"]
    city = random.choice(cities)
    with open("city.txt", "w", encoding="utf-8") as f: f.write(city)
    
    prompt = f"針對{city}挑選8個景點。輸出純JSON格式: {{'caption': '...', 'spots': [{'spot_name': '...', 'transportation': '...', 'image_prompt': 'Vertical 9:16 aspect ratio, Phone portrait mode, Raw travel photograph, unedited, authentic, shot on iPhone 15 Pro, 35mm lens, natural daylight, realistic imperfect textures, True-to-life colors, no HDR'}]}}"
    res = client.models.generate_content(model='gemini-2.0-flash', contents=prompt, config=types.GenerateContentConfig(response_mime_type="application/json"))
    data = json.loads(res.text)
    
    with open("caption.txt", "w", encoding="utf-8") as f: f.write(data['caption'])
    img_names = []
    os.makedirs("images/SPOT", exist_ok=True)
    for i, spot in enumerate(data['spots']):
        img = client.models.generate_content(model='imagen-3.0-generate-002', contents=spot['image_prompt'])
        path = f"images/SPOT/spot_{i}.jpg"
        img.parts[0].as_image().save(path)
        img_names.append(f"spot_{i}.jpg")
        with open(f"comment{i+1}.txt", "w", encoding="utf-8") as f: f.write(f"{spot['spot_name']}\n{spot['transportation']}")
    with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))

if __name__ == "__main__": run()