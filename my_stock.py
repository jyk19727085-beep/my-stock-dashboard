import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 화면 설정
st.set_page_config(page_title="Daniel Pro Dashboard", layout="wide")

# 모바일 가독성 설정
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 가져오기 함수
def get_data():
    tickers = {
        "필라델피아 반도체": "^SOX",
        "WTI 원유": "CL=F",
        "환율 (원/달러)": "USDKRW=X",
        "나스닥 100": "^NDX",
        "코스피 지수": "^KS11",
        "공포지수 (VIX)": "^VIX"
    }
    results = []
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="2d")
            if len(df) >= 2:
                current = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                results.append({"name": name, "price": current, "change": change})
        except:
            continue
    return results

# 3. 화면 그리기
st.title("📊 Daniel's 실시간 투자 비서")
st.write(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

data = get_data()
cols = st.columns(len(data))

for i, item in enumerate(data):
    with cols[i]:
        st.metric(label=item['name'], value=f"{item['price']:,.2f}", delta=f"{item['change']:.2f}%")

st.divider()

# 4. 수급 분석 및 뉴스 섹션
col1, col2 = st.columns(2)

with col1:
    st.subheader("💡 냉철한 관점")
    st.info("환율 1,350원 돌파 여부와 VIX 20 돌파 여부를 핵심 지표로 체크하세요.")
    # 링크 형식을 안전하게 수정했습니다
    st.markdown("https://finance.naver.com/")

with col2:
    st.subheader("🔗 주요 지표 뉴스")
    st.markdown("[📊 인베스팅닷컴 경제 캘린더](https://kr.investing.com/economic-calendar/)")
    st.markdown("[📰 네이버 증권 주요뉴스](https://finance.naver.com/news/mainnews.naver)")
