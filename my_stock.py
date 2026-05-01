import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Daniel Global Macro Dashboard", layout="wide")
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 22px; font-weight: bold; }
    .stAlert { padding: 10px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 가져오기 함수 (실시간 연동)
@st.cache_data(ttl=300) # 5분마다 갱신
def get_macro_data():
    tickers = {
        "S&P 500": "^GSPC", "다우존스": "^DJI", "나스닥 100": "^NDX",
        "러셀 2000": "^RUT", "필라 반도체": "^SOX", "코스피": "^KS11",
        "코스닥": "^KQ11", "환율": "USDKRW=X", "WTI유": "CL=F", "VIX": "^VIX"
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

# 3. 화면 구성
st.title("🌐 Daniel's 글로벌 매크로 상황실")
st.write(f"최종 동기화: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 메인 지수 그리드
data = get_macro_data()
col_idx = st.columns(5)
for i, item in enumerate(data[:5]):
    col_idx[i].metric(label=item['name'], value=f"{item['price']:,.2f}", delta=f"{item['change']:.2f}%")

col_idx2 = st.columns(5)
for i, item in enumerate(data[5:]):
    col_idx2[i].metric(label=item['name'], value=f"{item['price']:,.2f}", delta=f"{item['change']:.2f}%")

st.divider()

# 4. 핵심 매크로 지표 섹션 (Fear & Greed, FedWatch)
col_macro, col_supply = st.columns([1.2, 1])

with col_macro:
    st.subheader("🚨 핵심 시장 심리 & 금리 전망")
    
    # 공포와 탐욕 지수 및 페드워치는 외부 사이트 실시간 연동이 가장 정확합니다.
    st.info("💡 **시장의 심장박동을 확인하세요**")
    
    # 직관적인 버튼형 링크 배치
    st.markdown("""
    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
        <a href="https://edition.cnn.com/markets/fear-and-greed" target="_blank" style="text-decoration: none;">
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; color: black; border: 1px solid #ddd;">
                🔥 <b>공포와 탐욕 지수 (CNN)</b><br>시장의 과열/공포 실시간 확인
            </div>
        </a>
        <a href="https://www.cmegroup.com/markets/interest-rates/target-rate-probabilities.html" target="_blank" style="text-decoration: none;">
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; color: black; border: 1px solid #ddd;">
                🏛️ <b>CME 페드워치 (금리 전망)</b><br>연준의 다음 금리 결정 확률
            </div>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    st.caption("※ 위 지표들은 데이터 보안 정책상 직접 임베딩보다 공식 사이트 실시간 확인이 가장 정확합니다.")

with col_supply:
    st.subheader("🎯 수급 집중 포착 (3일 연속)")
    idx = 0
    for item in data:
        if item['is_buy']:
            st.success(f"✅ **{item['name']}**: 3일 연속 수급 유입 중")
            idx += 1
    if idx == 0:
        st.warning("현재 수급 집중 지수 없음 (보수적 접근)")

st.divider()

# 5. 수급 및 뉴스 연결
st.subheader("🔗 실시간 상세 데이터")
l1, l2, l3 = st.columns(3)
l1.markdown("[📊 코스피/코스닥 수급](https://finance.naver.com/sise/sise_trans_stat.naver)")
l2.markdown("[📰 인베스팅 경제 캘린더](https://kr.investing.com/economic-calendar/)")
l3.markdown("[📺 소셜 미디어 실시간 트렌드](https://trends.google.com/trends/trendingsearches/realtime?geo=KR)")
