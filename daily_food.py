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
        
        # --- A. 城市連動機制與主題抽取 ---
        print("🤖 系統正在檢查城市連動狀態...")
        
        # 讀取前一天景點腳本留下的城市 (若無則隨機抽取)
        city_file = "selected_city.txt"
        target_cities = ["曼谷", "清邁", "釜山", "首爾", "新加坡", "沖繩", "福岡", "大阪", "京都", "東京", "香港", "澳門"]
        
        if os.path.exists(city_file):
            with open(city_file, "r", encoding="utf-8") as f:
                selected_city = f.read().strip()
            print(f"🔗 成功讀取連動城市：{selected_city}")
        else:
            selected_city = random.choice(target_cities)
            print(f"⚠️ 找不到連動紀錄，隨機抽取城市：{selected_city}")
            
        themes = ["在地人推薦街頭小吃", "必吃百年老店", "視覺系網美甜點", "深夜排隊宵夜", "隱藏版巷弄美食", "高CP值平價美食"]
        selected_theme = random.choice(themes)
        
        print(f"🎯 本次執行：【{selected_city}】的【{selected_theme}】，準備交由 AI 生成 8 間餐廳...")
        
        # --- B. Gemini 生成文案 (8家餐廳) ---
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的創作者。你要發一篇社群貼文。\n"
            f"1. 請針對【{selected_city}】這個城市，挑選 8 家符合【{selected_theme}】主題的真實存在美食或餐廳。\n"
            f"請你生成以下 2 個主要的 JSON 欄位資料，並『嚴格』遵守規則：\n"
            f"- caption: (主文) 第一人稱發牢騷或表達興奮，用輕鬆口吻推薦這 8 家餐廳。結尾拋出引發討論的問題，並呼籲『收藏這篇』。絕對不要在主文寫出地址。300字內。段落間請用 '\\n\\n' 換行。\n"
            f"- restaurants: (這是一個包含 8 個物件的陣列 Array，需包含以下屬性)\n"
            f"  - name: (店名) 餐廳精準名稱。\n"
            f"  - dish: (必點菜色) 推薦一道菜。\n"
            f"  - address: (地址) 餐廳詳細地址。\n"
            f"  - google_maps_keyword: (搜尋關鍵字) 最容易在Google Maps搜到這家店的關鍵字。\n"
            f"  - image_prompt: (美食攝影咒語) 請用英文描述這道菜的畫面。不需加入器材或風格參數，只要專注描述『食物本身、擺盤、背景環境』即可。\n\n"
            f"請務必以純 JSON 格式輸出，不要包含 Markdown 標記。確保除 image_prompt 外皆為繁體中文。"
        )
        
        res = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=task_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.8
            )
        )
        
        data = json.loads(res.text)
        raw_caption = data.get("caption", "無法生成主文")
        caption = raw_caption.replace("\\n", "\n") 
        restaurants = data.get("restaurants", [])
        
        if len(restaurants) < 8:
            print(f"⚠️ 警告：AI 只生成了 {len(restaurants)} 間餐廳。")
            
        # 整理留言 (8家分拆成兩則留言)
        comment1_text = "為大家整理了前 4 家餐廳的詳細資訊👇 快點筆記起來！\n\n"
        comment2_text = "另外 4 家餐廳的詳細資訊在這裡👇 沒吃到會後悔！\n\n"
        
        for i, r in enumerate(restaurants):
            r_name = r.get("name", "未知店名")
            r_dish = r.get("dish", "未知菜色")
            r_addr = r.get("address", "未知地址")
            r_kw = r.get("google_maps_keyword", "未知關鍵字")
            
            info = f"✨ {i+1}. {r_name}\n🍲 必點：{r_dish}\n📍 地址：{r_addr}\n🗺️ 搜尋：{r_kw}\n\n"
            
            if i < 4:
                comment1_text += info
            else:
                comment2_text += info
                
        comment1_text = comment1_text.strip()
        comment2_text = comment2_text.strip()

        # --- C. Gemini 生成圖片 (強制 9:16 真實攝影參數) ---
        img_dir = "images/food"
        if os.path.exists(img_dir) and not os.path.isdir(img_dir):
            os.remove(img_dir)
        os.makedirs(img_dir, exist_ok=True)
        
        # 固定的極致真實感後綴咒語
        core_photography_prompt = (
            ", Vertical (9:16) aspect ratio, Phone portrait mode. "
            "Raw travel photograph, unedited, authentic. "
            "Shot on iPhone 15 Pro, 35mm equivalent lens. "
            "Clear, crisp, natural daylight, similar lighting to image_1.png. "
            "Realistic and imperfect, true-to-life colors, no over-saturation, no HDR look. "
            "DO NOT include AI, CGI, over-processed, flawless, or text elements."
        )
        
        img_names = []
        for i, r in enumerate(restaurants):
            base_prompt = r.get("image_prompt", "Delicious local street food dish")
            full_prompt = base_prompt + core_photography_prompt
            
            print(f"🎨 正在繪製第 {i+1} 家餐廳美食 ({r.get('name')})...")
            try:
                img_res = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=full_prompt,
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
            except Exception as e:
                print(f"💥 生成第 {i+1} 張圖片發生錯誤：{e}")
                
            # 💡 [關鍵修復] 增加緩衝時間，避免連續產 8 張圖被 API 判定為頻繁請求而阻擋
            time.sleep(8)
                
        # --- D. 寫入暫存檔 ---
        if img_names:
            with open("img_name.txt", "w", encoding="utf-8") as f: f.write(img_names[0])
            with open("img_names.txt", "w", encoding="utf-8") as f: f.write(",".join(img_names))
            
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        with open("comment.txt", "w", encoding="utf-8") as f: f.write(comment1_text)
        with open("comment2.txt", "w", encoding="utf-8") as f: f.write(comment2_text)
            
        print(f"👉 檔案寫入完成：成功產出 {len(img_names)} 張真實直立照片。")
    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
