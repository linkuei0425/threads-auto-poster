name: 🍴 中午小編 (深度美食景點文)
on:
  schedule:
    # 台灣時間中午 12:00 (UTC 04:00)
    - cron: '0 4 * * *'
  workflow_dispatch: # 讓你可以隨時手動點擊執行

jobs:
  post:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run food script
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          THREADS_ACCESS_TOKEN: ${{ secrets.THREADS_ACCESS_TOKEN }}
        run: python daily_food.py
