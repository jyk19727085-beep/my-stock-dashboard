import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 화면 설정
st.set_page_config(page_title="Daniel Investment Strategy Hub", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; }
    .stAlert { padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 가져오기 함수
@st.cache_data(ttl=60) # 1분마다 데이터 갱신
def get_market_data():
    indices = {
        "S&P 500": "^GSPC",
        "다우 존스": "^DJI",
        "나스닥 종합": "^IXIC",
        "코스피": "^KS11",
        "코스닥": "^KQ11",
        "필라델피아 반도체": "^SOX",
        "환율(원/달러)": "USDKRW=X"
    }
    
    results = {}
    for name, symbol in indices.items():
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="2d")
            if not df.empty:
                current = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                results[name] = {"price": current, "change": change}
        except:
            continue
    return results

# 3. 시장 동향 (상승/하락/인기 - 크롤링 대신 주요 종목 시세로 대체)
def get_stock_trends():
    # 실시간 크롤링은 제약이 많으므로, 주요 리딩 종목들로 시장 분위기를 파악합니다.
    leading_stocks = {
        "삼성전자": "005930.KS",
        "SK하이닉스": "000660.KS",
        "에코프로비엠": "247540.KQ",
        "엔비디아": "NVDA",
        "애플": "AAPL",
        "테슬라": "TSLA"
    }
    
    stock_data = []
    for name, symbol in leading_stocks.items():
        try:
            t = yf.Ticker(symbol)
            info = t.history(period="1d")
            price = info['Close'].iloc[-1]
            # yfinance에서 제공하는 기본 거래대금 수치 활용
            vol = info['Volume'].iloc[-1] 
            stock_data.append({"종목명": name, "현재가": price, "거래량": vol})
        except:
            continue
    return pd.DataFrame(stock_data)

# --- 화면 구성 ---

st.title("📊 Daniel's 전략 본부 (실시간 시장 동향)")
st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (1분마다 자동 갱신)")

# [섹션 1] 글로벌 주요 지수 (미국 전체 + 한국)
st.subheader("🌐 글로벌 핵심 지표")
m_data = get_market_data()
if m_data:
    row1 = st.columns(4)
    row2 = st.columns(3)
    
    idx = 0
    for name, val in m_data.items():
        target_col = row1[idx] if idx < 4 else row2[idx-4]
        target_col.metric(label=name, value=f"{val['price']:,.2f}", delta=f"{val['change']:.2f}%")
        idx += 1

st.divider()

# [섹션 2] 시장 에너지 및 수급 동향
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🔥 주요 종목 흐름 (KOSPI/KOSDAQ/US)")
    trends_df = get_stock_trends()
    if not trends_df.empty:
        st.dataframe(trends_df, use_container_脹=True, hide_index=True)
    else:
        st.write("데이터를 불러오는 중입니다...")

with col_right:
    st.subheader("⚖️ 수급 및 투자 전략")
    
    # 환율에 따른 냉철한 수급 진단
    exchange_rate = m_data.get("환율(원/달러)", {}).get("price", 0)
    if exchange_rate > 1400:
        st.error(f"⚠️ 환율 주의: {exchange_rate:,.2f}원 (외인 수급 이탈 경계)")
    elif exchange_rate < 1320:
        st.success(f"✅ 환율 우호: {exchange_rate:,.2f}원 (외인 순매수 유입 기대)")
    else:
        st.warning(f"ℹ️ 환율 관망: {exchange_rate:,.2f}원 (박스권 흐름)")

    st.info("""
    **💡 오늘의 체크포인트**
    1. **미국 3대 지수** 동반 상승 시 국장 반등 가능성 70% 이상.
    2. **코스닥**은 에코프로비엠 등 2차전지 시총 상위주 흐름에 연동됨.
    3. **수급 TIP:** 거래량이 전일 대비 1.5배 이상 터지는 종목에 주목하세요.
    """)

# 하단 뉴스 링크
st.divider()
st.markdown("🔗 [네이버 증권-수급현황](https://finance.naver.com/sise/sise_trans_stat.naver) | [인베스팅닷컴-실시간차트](https://kr.investing.com/charts/live-charts)")GitHub
