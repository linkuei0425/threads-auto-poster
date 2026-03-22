import os
import requests
import google.generativeai as genai

# 1. 讀取金鑰 (從 GitHub Secrets)
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
THREADS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

# 2. 設定 Gemini AI
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def generate_and_post():
    # 叫 Gemini 寫一段旅遊文案
    prompt = "你是一位幽默的旅遊導航員。請為我的網站 https://linkuei0425.github.io/ 寫一段 100 字內的 Threads 貼文介紹曼谷或清邁的隱藏景點，多加點 Emoji。"
    response = model.generate_content(prompt)
    content = response.text
    
    # Threads 發文流程
    base_url = "https://graph.threads.net/v1.0/me"
    
    # A. 建立發文容器
    res = requests.post(f"{base_url}/threads", params={
        'media_type': 'TEXT',
        'text': content,
        'access_token': THREADS_TOKEN
    }).json()
    
    if 'id' in res:
        # B. 正式發布
        publish = requests.post(f"{base_url}/threads_publish", params={
            'creation_id': res['id'],
            'access_token': THREADS_TOKEN
        }).json()
        print(f"✅ 發布成功！貼文 ID: {publish.get('id')}")
    else:
        print(f"❌ 失敗：{res}")

if __name__ == "__main__":
    generate_and_post()
