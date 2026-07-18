import os
import sys
import time
import json
import random
from google import genai
from google.genai import types

# 1. 讀取 Secrets
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
        themes = ["歷史古蹟", "文青巷弄", "自然絕景", "網美打卡", "購物商圈", "傳統市場", "夜市", "當地人私房秘境", "浪漫夜景"]
        
        selected_city = random.choice(target_cities)
        selected_theme = random.choice(themes)
        
        # 💡 [關鍵新增] 將抽中的城市寫入 txt，讓隔天的美食腳本可以讀取連動！
        with open("selected_city.txt", "w", encoding="utf-8") as f:
            f.write(selected_city)
            
        print(f"🎯 本次抽中：【{selected_city}】的【{selected_theme}】。已記錄城市供明日美食腳本連動。")
        
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。你要發一篇社群貼文。\n"
            f"1. 請針對【{selected_city}】這個城市，挑選 3 個符合【{selected_theme}】主題的真實存在知名地標或私房秘境（請勿介紹餐廳或美食）。\n"
            f"請你生成以下 2 個主要的 JSON 欄位資料，並『嚴格』遵守規則：\n"
            f"- caption: (主文) 第一人稱發牢騷或表達興奮，用輕鬆口吻推薦這 3 個景點。結尾拋出引發討論的問題，並呼籲『收藏這篇』和『分享給朋友』。絕對不要寫出交通方式。300字內。段落間請用 '\\n\\n' 換行。\n"
            f"- spots: (這是一個包含 3 個物件的陣列 Array，需包含以下屬性)\n"
            f"  - spot_name: (景點名稱) 景點的精準名稱。\n"
            f"  - transportation: (交通攻略) 詳細的自由行大眾交通方式。\n"
            f"  - google_maps_keyword: (搜尋關鍵字) 最容易搜到這個景點的關鍵字。\n"
            f"  - image_prompt: (美食攝影咒語) 請用英文描述該景點的具體畫面。不需加入器材或風格參數，只要專注描述『景點本身、光影、背景環境』即可。\n\n"
            f"請務必以純 JSON 格式輸出，不要包含任何 Markdown 標記。"
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
        
        comment1_text = "整理好這 3 個地方的交通和搜尋關鍵字給大家啦！快點筆記起來👇\n\n"
        comment2_text = ""
        
        for i, spot in enumerate(spots):
            s_name = spot.get("spot_name", "未知景點")
            s_trans = spot.get("transportation", "未知交通方式")
            s_kw = spot.get("google_maps_keyword", "未知關鍵字")
            
            info = f"✨ {i+1}. {s_name}\n🚆 交通：{s_trans}\n🗺️ 搜尋：{s_kw}\n\n"
            
            if i < 2:
                comment1_text += info
            else:
                comment2_text += info
                
        comment1_text = comment1_text.strip()
        comment2_text = comment2_text.strip()

        img_dir = "images/SPOT"
        if os.path.exists(img_dir) and not os.path.isdir(img_dir):
            os.remove(img_dir)
        os.makedirs(img_dir, exist_ok=True)
        
        # 💡 [關鍵新增] 統一極致真實感直式攝影參數 (符合你的要求)
        core_photography_prompt = (
            ", Vertical (9:16) aspect ratio, Phone portrait mode. "
            "Raw travel photograph, unedited, authentic. "
            "Shot on iPhone 15 Pro, 35mm equivalent lens. "
            "Clear, crisp, natural daylight, similar lighting to image_1.png. "
            "Realistic and imperfect, true-to-life colors, no over-saturation, no HDR look. "
            "DO NOT include AI, CGI, over-processed, flawless, or text elements."
        )
        
        img_names = []
        
        for i, spot in enumerate(spots[:3]):
            base_prompt = spot.get("image_prompt", "Beautiful travel destination")
            full_prompt = base_prompt + core_photography_prompt
            
            print(f"🎨 正在繪製第 {i+1} 個景點 ({spot.get('spot_name')})...")
            try:
                # 💡 [關鍵新增] 強制使用 9:16 縱橫比
                img_res = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=full_prompt,
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
            except Exception as e:
                print(f"💥 生成第 {i+1} 張圖片發生錯誤：{e}")
                
        if img_names:
            with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_names[0])
            with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))
            
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        with open("comment.txt", "w", encoding="utf-8") as f: f.write(comment1_text)
        with open("comment2.txt", "w", encoding="utf-8") as f: f.write(comment2_text)
            
        print(f"👉 檔案寫入完成：產出 {len(img_names)} 張真實直立照片。")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
