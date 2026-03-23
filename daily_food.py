# --- A. Gemini 生成文案 ---
        print("🤖 Gemini 正在亞洲精選城市中尋找美食...")
        target_cities = "曼谷、清邁、釜山、首爾、新加坡、沖繩、宮古島、福岡"
        
        # 💡 修改 1：在指令中嚴格限制字數
        task_prompt = (
            f"你是一位經營『Kokko愛旅行』的專業旅遊與美食創作者。任務：\n"
            f"1. 從以下城市中『隨機挑選一個』：{target_cities}。\n"
            f"2. 挑選該城市中一家『真實存在』的在地必吃美食、特色咖啡廳或隱藏版餐廳。\n"
            f"3. 撰寫一段 Threads 貼文主文（中文）。以第一人稱（Kokko）分享，語氣生動熱情。\n"
            f"⚠️ 極度重要：主文字數（含標點符號與Emoji）『絕對不可以超過 350 字』！\n"
            f"4. 撰寫一段該美食或餐廳氛圍的英文繪圖咒語 (Image Prompt)，要高畫質、有氛圍感。\n"
            f"5. 撰寫一條留言內容，格式為：『📍 店名：XXX \\n📍 所在城市：XXX \\n📍 地址：XXX』。\n"
            f"請嚴格使用 '---' 分隔這三部分（主文---咒語---留言內容）。"
        )
        
        res = client.models.generate_content(model='gemini-2.5-flash', contents=task_prompt)
        parts = res.text.split('---')
        caption = parts[0].strip() if len(parts) > 0 else "無法生成貼文內容"
        image_prompt = parts[1].strip() if len(parts) > 1 else "Professional gourmet food photography"
        comment_text = parts[2].strip() if len(parts) > 2 else "📍 地址資訊確認中..."

        # 💡 修改 2：加上 Python 終極防呆機制，超過 480 字直接強制卡掉，保護 API 不出錯
        if len(caption) > 480:
            print(f"⚠️ 警告：生成的字數太長 ({len(caption)} 字)，已觸發自動截斷機制！")
            caption = caption[:475] + "..."

        if "曼谷" in caption or "曼谷" in comment_text:
            promo_text = "\n\n🇹🇭 正在規劃泰國行嗎？歡迎使用我的【曼谷通】APP，幫你輕鬆找好吃好玩的！ 👉 https://你的曼谷通網址.com"
            comment_text += promo_text
