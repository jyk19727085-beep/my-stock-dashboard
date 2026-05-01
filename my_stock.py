import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 모바일 최적화 스타일
st.set_page_config(page_title="Daniel Investment Pro", layout="wide")
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 22px; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; height: 50px; background-color: #007bff; color: white; }
    .stSuccess { background-color: #e6f4ea; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 실시간 데이터 호출 함수 (나스닥, 원자재 포함)
@st.cache_data(ttl=300)
def get_final_data():
    tickers = {
        "나스닥 종합": "^IXIC", "S&P 500": "^GSPC", "다우존스": "^DJI",
        "나스닥 100": "^NDX", "필라 반도체": "^SOX", "러셀 2000": "^RUT",
        "코스피": "^KS11", "코스닥": "^KQ11", "금 (Gold)": "GC=F",
        "은 (Silver)": "SI=F", "구리 (Copper)": "HG=F", "환율": "USDKRW=X",
        "WTI 원유": "CL=F", "공포지수(VIX)": "^VIX"
    }
    results = []
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="5d")
            if not df.empty:
                curr = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                change = ((curr - prev) / prev) * 100
                # 3일 연속 종가 상승 여부 분석
                is_3day_buy = all(df['Close'].iloc[-i] > df['Close'].iloc[-(i+1)] for i in range(1, 4))
                results.append({"name": name, "price": curr, "change": change, "is_buy": is_3day_buy})
        except: continue
    return results

# 3. 상단 정보
st.title("🏛️ Daniel's 실시간 투자 상황실")
st.write(f"✅ 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 4. 14대 핵심 지표 배치
data = get_final_data()
rows = [data[i:i+5] for i in range(0, len(data), 5)]
for row in rows:
    cols = st.columns(len(row))
    for i, item in enumerate(row):
        cols[i].metric(label=item['name'], value=f"{item['price']:,.2f}", delta=f"{item['change']:.2f}%")

st.divider()

# 5. CME FedWatch 즉시 연결 & 수급 분석
col_fed, col_trend = st.columns([1, 1])

with col_fed:
    st.subheader("🏛️ 금리 전망 도구")
    # 버튼 클릭 시 CME FedWatch로 즉시 연결되는 링크 설정
    st.markdown("""
        <a href="https://www.cmegroup.com/markets/interest-rates/target-rate-probabilities.html" target="_blank" style="text-decoration: none;">
            <div style="background-color: #007bff; color: white; padding: 15px; text-align: center; border-radius: 10px; font-weight: bold; font-size: 18px;">
                🚀 CME FedWatch 실시간 도구 연결
            </div>
        </a>
        <p style="font-size: 13px; color: gray; margin-top: 10px;">
        ※ 연준의 다음 금리 인상/인하 확률 및 점도표를 즉시 확인하세요.
        </p>
    """, unsafe_allow_html=True)

with col_trend:
    st.subheader("🎯 수급/추세 집중 포착 (3일 연속)")
    idx = 0
    for item in data:
        if item['is_buy']:
            st.success(f"✅ **{item['name']}**")
            idx += 1
    if idx == 0:
        st.warning("현재 3일 연속 상승 지표 없음")

st.divider()

# 6. 보조 지표 링크 (오류 없는 네이버 링크 포함)
l1, l2, l3 = st.columns(3)
with l1: st.markdown("[🔥 공포와 탐욕 지수](https://edition.cnn.com/markets/fear-and-greed)")
with l2: st.markdown("[📊 국내 시장 수급(네이버)](https://finance.naver.com/sise/)")
with l3: st.markdown("[📈 인베스팅 경제 캘린더](https://kr.investing.com/economic-calendar/)")
