import streamlit as st
import requests
import pandas as pd

def search_tfda_drug(keyword):
    # 使用食藥署西藥、醫療器材、化妝品許可證查詢 API (範例網址)
    # 這是公開資料，不需要讀取您的私人雲端
    url = "https://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&sectorId=1&dataTypeCode=01"
    
    try:
        # 在實際開發中，通常會下載這個 JSON/CSV 到本地端做比對
        # 這裡演示如何過濾關鍵字
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # 關鍵：使用「包含」邏輯搜尋，不分大小寫
            results = [item for item in data if keyword.upper() in str(item.get('中文品名', '')).upper() 
                       or keyword.upper() in str(item.get('英文品名', '')).upper()]
            return results
    except:
        return None

# UI 介面
st.title("💊 藥速知 MedQuick (官方數據連線版)")

query = st.text_input("輸入藥品關鍵字", placeholder="例如: ACETAL, TOPCEF...")

if query:
    target = query.strip().upper()
    with st.spinner(f'正在向食藥署/健保局資料庫請求數據...'):
        res = search_tfda_drug(target)
        
        if res:
            st.success(f"找到 {len(res)} 筆符合的官方品項")
            st.dataframe(pd.DataFrame(res)) # 直接顯示官方表格資料
        else:
            st.error(f"官方資料庫中查無「{target}」。請確認名稱是否完整（例如：CHEF 是否為特定商品名之縮寫）。")
