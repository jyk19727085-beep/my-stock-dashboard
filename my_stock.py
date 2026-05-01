import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Daniel Ultimate Dashboard", layout="wide")
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 22px; font-weight: bold; }
    .stSuccess { background-color: #e6f4ea; border-radius: 10px; padding: 15px; }
    .stWarning { background-color: #fff9e6; border-radius: 10px; padding: 15px; }
    .fear-greed-box { background-color: #f0f2f6; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# 2. 실시간 데이터 호출 함수
@st.cache_data(ttl=300)
def get_all_market_data():
    tickers = {
        "나스닥 종합": "^IXIC", "S&P 500": "^GSPC", "다우존스": "^DJI",
        "나스닥 100": "^NDX", "필라 반도체": "^SOX", "러셀 2000": "^RUT",
        "코스피": "^KS11", "코스닥": "^KQ11", "금 (Gold)": "GC=F",
        "은 (Silver)": "SI=F", "구리 (Copper)": "HG=F", "환율": "USDKRW=X",
        "WTI 원유": "CL=F", "VIX 지수": "^VIX"
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
                is_3day_buy = all(df['Close'].iloc[-i] > df['Close'].iloc[-(i+1)] for i in range(1, 4))
                results.append({"name": name, "price": curr, "change": change, "is_buy": is_3day_buy})
        except: continue
    return results

# 3. 타이틀 및 업데이트 정보
st.title("🏛️ Daniel's 실시간 투자 상황실 (Ver 4.0)")
st.write(f"✅ 최신 동기화: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 4. 공포와 탐욕 지수 & CME 페드워치 상단 배치
st.subheader("🚨 핵심 시장 심리 & 금리 전망")
col_fg, col_fed = st.columns(2)

with col_fg:
    st.markdown(f"""
        <a href="https://edition.cnn.com/markets/fear-and-greed" target="_blank" style="text-decoration: none;">
            <div class="fear-greed-box">
                <span style="font-size: 16px; color: #555;">CNN Business</span><br>
                <span style="font-size: 24px; color: #000; font-weight: bold;">🔥 공포와 탐욕 지수 확인</span><br>
                <span style="font-size: 14px; color: #888;">(현재 시장의 과열/공포 상태 실시간 이동)</span>
            </div>
        </a>
    """, unsafe_allow_html=True)

with col_fed:
    st.markdown(f"""
        <a href="https://www.cmegroup.com/markets/interest-rates/target-rate-probabilities.html" target="_blank" style="text-decoration: none;">
            <div class="fear-greed-box" style="border-color: #007bff;">
                <span style="font-size: 16px; color: #555;">CME Group</span><br>
                <span style="font-size: 24px; color: #007bff; font-weight: bold;">🏛️ CME FedWatch 연결</span><br>
                <span style="font-size: 14px; color: #888;">(다음 FOMC 금리 인상/인하 확률 확인)</span>
            </div>
        </a>
    """, unsafe_allow_html=True)

st.divider()

# 5. 14대 핵심 지수 그리드
st.subheader("📊 글로벌 주요 지표 & 원자재")
data = get_all_market_data()
rows = [data[i:i+5] for i in range(0, len(data), 5)]
for row in rows:
    cols = st.columns(len(row))
    for i, item in enumerate(row):
        cols[i].metric(label=item['name'], value=f"{item['price']:,.2f}", delta=f"{item['change']:.2f}%")

st.divider()

# 6. 수급 분석 및 보조 지표
col_trend, col_link = st.columns([1, 1.2])

with col_trend:
    st.subheader("🎯 3일 연속 수급 유입")
    idx = 0
    for item in data:
        if item['is_buy']:
            st.success(f"✅ **{item['name']}**")
            idx += 1
    if idx == 0: st.warning("현재 3일 연속 상승 지표 없음")

with col_link:
    st.subheader("🔗 전략 보조 링크")
    l1, l2 = st.columns(2)
    # 오류 수정된 네이버 증권 링크
    l1.markdown("### [📊 국내 수급(네이버)](https://finance.naver.com/sise/)")
    l2.markdown("### [📈 경제 캘린더](https://kr.investing.com/economic-calendar/)")
