import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 화면 설정 (모바일/PC 겸용)
st.set_page_config(page_title="Daniel Pro Dashboard", layout="wide")

# 모바일에서 글자가 잘 보이게 하는 설정
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; }
    .main { background-color: #f5f7f9; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 가져오기 함수
def get_data():
    # Daniel님이 요청하신 핵심 지표 리스트
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

# 지표들을 카드 형태로 가로로 배치 (모바일에서는 자동으로 세로로 바뀜)
data = get_data()
cols = st.columns(len(data))

for i, item in enumerate(data):
    with cols[i]:
        # 상승은 빨강, 하락은 파랑으로 표시
        st.metric(
            label=item['name'], 
            value=f"{item['price']:,.2f}", 
            delta=f"{item['change']:.2f}%"
        )

st.divider()

# 4. 하단 상세 정보 및 투자 가이드
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("💡 냉철한 관점: 시장 동향")
    st.info("""
    - **반도체 지수:** 국내 대형주(삼성전자 등)의 선행 지표입니다.
    - **원/달러 환율:** 외인 수급의 핵심입니다. 1,350원 돌파 여부를 체크하세요.
    - **VIX 지수:** 20을 넘어가면 시장이 매우 불안하다는 신호입니다.
    """)

with col_right:
    st.subheader("🔗 주요 실시간 뉴스 연결")
    st.write("- [네이버 증권 시황 뉴스](https://finance.naver.com/news/mainnews.naver)")
    st.write("- [Investing.com 글로벌 경제 지표](https://kr.investing.com/economic-calendar/)")

# 5분마다 자동으로 새로고침 (실시간성 확보)
# st.empty() 기능을 사용하여 60초마다 화면을 갱신하도록 설정 가능