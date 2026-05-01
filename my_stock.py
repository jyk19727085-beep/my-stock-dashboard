import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 모바일 가독성 최적화
st.set_page_config(page_title="Daniel Macro & Commodity", layout="wide")
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 20px; font-weight: bold; }
    .stSuccess { background-color: #e6f4ea; border-radius: 10px; padding: 15px; }
    .stInfo { border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 호출 함수 (나스닥 종합 및 원자재 추가)
@st.cache_data(ttl=300)
def get_extended_data():
    tickers = {
        "나스닥 종합": "^IXIC", "S&P 500": "^GSPC", "다우존스": "^DJI",
        "필라 반도체": "^SOX", "러셀 2000": "^RUT", "코스피": "^KS11",
        "코스닥": "^KQ11", "금 (Gold)": "GC=F", "은 (Silver)": "SI=F",
        "구리 (Copper)": "HG=F", "환율": "USDKRW=X", "WTI유": "CL=F", "VIX": "^VIX"
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

# 3. 화면 타이틀
st.title("🏛️ Daniel's 글로벌 매크로 & 원자재 상황실")
st.write(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 4. 주요 지수 및 원자재 메트릭 (3줄 배치)
all_data = get_extended_data()
rows = [all_data[i:i+5] for i in range(0, len(all_data), 5)]

for row in rows:
    cols = st.columns(len(row))
    for i, item in enumerate(row):
        cols[i].metric(label=item['name'], value=f"{item['price']:,.2f}", delta=f"{item['change']:.2f}%")

st.divider()

# 5. 매크로 심층 분석 섹션 (CME 페드워치 세분화)
col_fed, col_trend = st.columns([1.2, 1])

with col_fed:
    st.subheader("🏛️ CME FedWatch 지수 리스트")
    st.write("연준의 금리 결정을 예측하는 핵심 지표들입니다.")
    
    # 페드워치의 주요 지표 종류를 설명과 함께 배치
    with st.expander("📌 CME FedWatch 주요 확인 지수 종류"):
        st.markdown("""
        *   **Target Rate Probabilities:** 다음 FOMC 회의에서의 금리 동결/인상/인하 확률
        *   **Historical View:** 시간에 따른 금리 예측치의 변화 추이
        *   **Dot Plot:** 연준 위원들의 향후 금리 전망 점도표
        *   **Treasury Yields:** 국채 수익률 곡선과의 비교 데이터
        """)
    
    st.markdown("""
    <a href="https://www.cmegroup.com/markets/interest-rates/target-rate-probabilities.html" target="_blank">
        <button style="width:100%; padding:10px; background-color:#007bff; color:white; border:none; border-radius:5px; cursor:pointer;">
            🚀 실시간 CME FedWatch 도구 바로가기
        </button>
    </a>
    """, unsafe_allow_html=True)

with col_trend:
    st.subheader("🎯 3일 연속 수급 유입 (추세)")
    idx = 0
    for item in all_data:
        if item['is_buy']:
            st.success(f"✅ **{item['name']}**")
            idx += 1
    if idx == 0: st.warning("현재 3일 연속 상승 지표 없음")

st.divider()

# 6. 공포 탐욕 및 수급 링크
st.subheader("🔗 전략 보조 지표")
l1, l2, l3 = st.columns(3)
with l1: st.markdown("[🔥 공포와 탐욕 지수](https://edition.cnn.com/markets/fear-and-greed)")
with l2: st.markdown("[📊 국내 시장 수급 (네이버)](https://finance.naver.com/sise/sise_trans_stat.naver)")
with l3: st.markdown("[📈 인베스팅 경제 캘린더](https://kr.investing.com/economic-calendar/)")
