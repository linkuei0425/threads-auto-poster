# 這裡不需要手動列 FOOD_TOPICS 了，讓 Gemini 自己發揮
def generate_ai_content(client):
    # 這是給 Gemini 的「終極任務」
    task_prompt = """
    任務：
    1. 隨機從世界各地的名菜、街頭小吃或甜點中挑選一個主題。
    2. 為這個美食寫一段 80 字內的 Threads 活潑貼文（中文）。
    3. 為這個美食寫一段專業的「英文 AI 繪圖提示詞」(Image Prompt)。
       - 要求：電影感、專業食物攝影、4k、極致細節、柔和光影。
    
    請務必用 '---' 這個符號分隔貼文與英文提示詞。
    """

    print("🤖 Gemini 正在思考今天吃什麼並撰寫咒語...")
    response = client.models.generate_content(
        model='gemini-2.0-flash', # 使用你剛解鎖的最強 2.0
        contents=task_prompt
    )
    
    # 拆分結果
    content_parts = response.text.split('---')
    caption = content_parts[0].strip()
    image_prompt = content_parts[1].strip() if len(content_parts) > 1 else "Gourmet food photography"
    
    return caption, image_prompt
