import os
import sys
import time
import json
import random
import shutil
from google import genai
from google.genai import types

# 1. 讀取 Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def run():
    try:
        if not GEMINI_KEY:
            raise Exception("缺少 GEMINI_API_KEY 環境變數")
            
        client = genai.Client(api_key=GEMINI_KEY)
        
        # --- A. 隨機抽取地區與主題 ---
        print("🤖 系統正在隨機抽取伴手禮產地與商品主題...")
        
        regions = ["日本東京", "日本大阪", "韓國首爾", "泰國曼谷", "台灣", "香港", "新加坡", "澳洲", "法國巴黎", "德國"]
        themes = ["美妝保養神物", "當地人氣零食", "實用居家小物", "特色飲料與茶包", "在地必買伴手禮", "藥妝店掃貨清單", "超市必買尋寶"]
        
        selected_region = random.choice(regions)
        selected_theme = random.choice(themes)
        
        print(f"🎯 本次抽中：【{selected_region}】的【{selected_theme}】，準備交由 Gemini 生成...")
        
        # --- B. 指示 AI 生成 Threads 文案與 5 個商品的生圖咒語 ---
        task_prompt = (
            f"你是一位經驗豐富的『旅遊達人』。你要在 Threads 發布一篇 5 張圖片的多圖輪播(Carousel)貼文。\n"
            f"請針對【{selected_region}】這個地區，挑選 5 個符合【{selected_theme}】主題的真實熱門伴手禮或必買好物。\n"
            f"請生成以下 JSON 格式的資料，『嚴格』遵守規則且全中文（除 image_prompt 外）：\n"
            f"- caption: (主貼文) 以旅遊達人的熱情口吻，詳細介紹這 5 種商品的特色與為什麼必買。文末『必須』加上明確的行動呼籲(CTA)：邀請讀者「收藏這篇文章」、「轉發給準備去旅遊的朋友」並「將這些好物列入未來的旅遊伴手禮清單」。(字數約 350-450 字)\n"
            f"- comment1: (第一則留言) 詳細說明第 1 到第 3 項商品「具體在哪裡能買到」(例如特定連鎖超市、免稅店、藥妝店名)，以及相關的「購買建議」(例如買什麼口味最保險、要注意什麼標籤)。\n"
            f"- comment2: (第二則留言) 詳細說明第 4 到第 5 項商品「在哪裡能買到」，並補充整體的「購買建議」(例如哪家店容易有折扣、退稅門檻、或是購買時的避坑指南)。\n"
            f"- products: 一個陣列(Array)，必須剛好包含 5 個物件，每個物件只有一個屬性 `image_prompt`。\n"
            f"  - image_prompt: (英文咒語) 為了產生高質感的商品照，請描述該單一商品的具體畫面。強制加入：'Professional commercial product photography, well-lit, sharp focus, high-end magazine style, appealing composition, clean background, realistic texture'. 絕對不要用 '8k, masterpiece' 等過度塑膠感的字眼。\n"
            f"請務必只輸出純 JSON 格式，不要包含任何 Markdown 標記 (例如 ```json)。"
        )
        
        # 呼叫 Gemini 2.5 Flash 生成文字內容
        res = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=task_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.8
            )
        )
        
        try:
            data = json.loads(res.text.strip())
        except json.JSONDecodeError:
            print("⚠️ 警告：AI 輸出的不是有效的 JSON！原始輸出如下：")
            print(res.text)
            sys.exit(1)
            
        caption = data.get("caption", "無法生成主文")
        comment_text = data.get("comment1", "購買地點資訊整理中...")
        comment2_text = data.get("comment2", "更多購買建議整理中...")
        products = data.get("products", [])
        
        if len(products) != 5:
            print(f"⚠️ 警告：AI 沒有產生剛好 5 個商品，而是 {len(products)} 個。腳本仍將嘗試執行...")

        # Threads 字數限制保護 (單篇上限 500 字)
        if len(caption) > 490: caption = caption[:485] + "..."
        if len(comment_text) > 490: comment_text = comment_text[:485] + "..."
        if len(comment2_text) > 490: comment2_text = comment2_text[:485] + "..."

        print("\n--- 📝 文案產出預覽 ---")
        print(f"[主文 {len(caption)}字]:\n{caption}\n")
        print(f"[留言一 {len(comment_text)}字]:\n{comment_text}\n")
        print(f"[留言二 {len(comment2_text)}字]:\n{comment2_text}\n")

        # --- C. 迴圈呼叫生圖模型 5 次 ---
        img_dir = "images/GIFT"
        # 清空舊資料夾，避免舊圖殘留被一起推上 GitHub
        if os.path.exists(img_dir):
            shutil.rmtree(img_dir)
        os.makedirs(img_dir, exist_ok=True)
        
        saved_image_names = []
        
        for idx, item in enumerate(products[:5]):
            prompt = item.get("image_prompt", "Professional commercial product photography, neutral background")
            print(f"🎨 正在繪製第 {idx+1} 張商品照...")
            
            try:
                img_res = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio="1:1")
                    )
                )
                
                img_name = f"gift_{int(time.time())}_{idx}.jpg"
                local_img_path = f"{img_dir}/{img_name}"
                
                for part in img_res.parts:
                    if part.inline_data:
                        part.as_image().save(local_img_path)
                        saved_image_names.append(img_name)
                        break
                        
                # 避免請求過於頻繁
                time.sleep(3)
                
            except Exception as img_err:
                print(f"❌ 第 {idx+1} 張圖生成失敗: {img_err}")
                continue
                
        # --- D. 寫入暫存檔供 GitHub Actions 使用 ---
        # 將圖片檔名列表寫入檔案，每行一個
        with open("img_names.txt", "w", encoding="utf-8") as f:
            for name in saved_image_names:
                f.write(name + "\n")
                
        with open("caption.txt", "w", encoding="utf-8") as f: f.write(caption)
        with open("comment.txt", "w", encoding="utf-8") as f: f.write(comment_text)
        with open("comment2.txt", "w", encoding="utf-8") as f: f.write(comment2_text)
            
        print(f"👉 檔案寫入完成！共成功產生 {len(saved_image_names)} 張商品照。準備交由 GitHub Actions 發布。")

    except Exception as e:
        print(f"💥 發生錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run()