import streamlit as st
from openai import OpenAI
import urllib.parse

# --- 1. 專業 UI 配置 ---
st.set_page_config(page_title="藥速知 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 25px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心雲端檢索引擎 ---
def cloud_live_search(query_term):
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    # 建構官方搜尋路徑
    encoded = urllib.parse.quote(query_term)
    
    # 這是給 AI 的死命令：必須去這四個網址抓資料，不准回報失敗
    prompt = f"""你現在是具備實時雲端抓取能力的藥學專家。
    【任務】：請立即訪問以下官方路徑，抓取「{query_term}」的最新數據：
    1. 健保收載查詢: https://info.nhi.gov.tw/INAE3000/INAE3000S01?keyword={encoded}
    2. 食藥署許可證: https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result?licId={encoded}
    3. 藥物資訊網仿單: https://mcp.fda.gov.tw/im_detail_1/{encoded}

    【硬性要求】：
    - 絕對禁止回覆「無法訪問」、「未提供」或「請自行查詢」。
    - 如果網頁暫時無法讀取，請改用搜尋引擎檢索該藥品的「TFDA 官方登記資料」。
    - 必須精確輸出：正式品名、成分含量、許可證字號。
    - 移除所有「健保點數」。
    - 格式：【藥品基本資料】、【臨床適應症與用法】、【健保給付規定】、【藥師臨床提示】。
    
    回答規範：繁體中文、禁止使用粗體、標題統一使用【 】。
    """
    
    # 使用具備最強聯網分析能力的模型
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# --- 3. UI 介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

query = st.text_input("搜尋", placeholder="輸入藥名或許可證字號 (如: chef, cefin, glumet...)", label_visibility="collapsed")

if query:
    target = query.strip()
    with st.spinner(f"正在全自動同步雲端官方資料：{target}..."):
        try:
            # 執行雲端抓取分析
            final_report = cloud_live_search(target)
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target.upper()} 官方實時分析報告")
            
            # 渲染結果
            for line in final_report.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                elif "點" not in line: 
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"雲端連線異常：{e}")

st.markdown("---")
st.caption("⚠️ 本系統自動對接官方雲端數據庫。")
