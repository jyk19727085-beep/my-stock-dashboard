import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse
import re

# 1. 페이지 설정
st.set_page_config(page_title="Daniel Alpha System Ver 7.2", layout="wide")
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 22px; font-weight: bold; }
    .stSuccess { background-color: #e6f4ea; border-radius: 10px; padding: 15px; }
    .stWarning { background-color: #fff9e6; border-radius: 10px; padding: 15px; }
    .stError { background-color: #ffe6e6; border-radius: 10px; padding: 15px; }
    .fear-greed-box { background-color: #f0f2f6; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #ddd; }
    .alpha-box { background-color: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 10px; font-family: 'Courier New', Courier, monospace; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 엔진 1: 기본 매크로 지표
@st.cache_data(ttl=300)
def get_macro_data():
    tickers = {
        "나스닥 종합": "^IXIC", "S&P 500": "^GSPC", "다우존스": "^DJI",
        "필라 반도체": "^SOX", "러셀 2000": "^RUT", "코스피": "^KS11",
        "코스닥": "^KQ11", "금 (Gold)": "GC=F", "은 (Silver)": "SI=F",
        "구리 (Copper)": "HG=F", "환율": "USDKRW=X", "WTI 원유": "CL=F", "VIX 지수": "^VIX"
    }
    results = []
    vix_val = 20
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="5d")
            if not df.empty:
                curr = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                change = ((curr - prev) / prev) * 100
                is_buy = all(df['Close'].iloc[-i] > df['Close'].iloc[-(i+1)] for i in range(1, 4))
                results.append({"name": name, "price": curr, "change": change, "is_buy": is_buy})
                if name == "VIX 지수": vix_val = curr
        except: continue
    return results, vix_val

# 3. 데이터 엔진 2: 연 30% 알파 타겟팅
@st.cache_data(ttl=300)
def get_alpha_data():
    alpha_tickers = {"TQQQ (나스닥 3배)": "TQQQ", "SOXL (반도체 3배)": "SOXL", "UPRO (S&P 3배)": "UPRO", "엔비디아 (NVDA)": "NVDA"}
    results = []
    for name, symbol in alpha_tickers.items():
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="3mo")
            if len(df) >= 20:
                delta = df['Close'].diff()
                gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
                loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                current_rsi = rsi.iloc[-1]
                
                bb_mid = df['Close'].rolling(window=20).mean()
                bb_std = df['Close'].rolling(window=20).std()
                bb_upper = bb_mid + (bb_std * 2)
                bb_lower = bb_mid - (bb_std * 2)
                
                curr_price = df['Close'].iloc[-1]
                change = ((curr_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                
                signal = "관망 (대기)"
                if current_rsi < 30 and curr_price <= bb_lower.iloc[-1]: signal = "🔥 강력 매수 (과매도)"
                elif current_rsi > 70 and curr_price >= bb_upper.iloc[-1]: signal = "⚠️ 강력 매도 (과매수)"
                    
                results.append({"name": name, "price": curr_price, "change": change, "rsi": current_rsi, "signal": signal})
        except: continue
    return results

# --- 화면 출력 시작 ---
st.title("🏛️ Daniel's 연 30% 타겟팅 상황실 (Ver 7.2)")
st.write(f"✅ 스마트 라우팅 엔진 가동 중: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 공포 탐욕 & 페드워치
col_fg, col_fed = st.columns(2)
with col_fg: st.markdown(f"""<a href="https://edition.cnn.com/markets/fear-and-greed" target="_blank" style="text-decoration: none;"><div class="fear-greed-box"><span style="font-size: 16px; color: #555;">CNN Business</span><br><span style="font-size: 24px; color: #000; font-weight: bold;">🔥 공포와 탐욕 지수</span></div></a>""", unsafe_allow_html=True)
with col_fed: st.markdown(f"""<a href="https://www.cmegroup.com/markets/interest-rates/target-rate-probabilities.html" target="_blank" style="text-decoration: none;"><div class="fear-greed-box" style="border-color: #007bff;"><span style="font-size: 16px; color: #555;">CME Group</span><br><span style="font-size: 24px; color: #007bff; font-weight: bold;">🏛️ CME FedWatch 연결</span></div></a>""", unsafe_allow_html=True)

st.divider()

# Alpha 엔진
macro_data, current_vix = get_macro_data()
alpha_data = get_alpha_data()

st.subheader("🚀 Alpha 타겟팅 엔진 (레버리지 추적기)")
if current_vix >= 30: st.error(f"🚨 **[VIX 경고: {current_vix:.2f}] 극단적 공포. 레버리지 비중 축소 / 현금 관망 필수.**")
elif current_vix >= 20: st.warning(f"⚠️ **[VIX 경계: {current_vix:.2f}] 변동성 확대. 철저한 분할 매매 필수.**")
else: st.success(f"✅ **[VIX 안정: {current_vix:.2f}] 시장 안정. 추세 추종 유효.**")

if alpha_data:
    st.markdown("<div class='alpha-box'>", unsafe_allow_html=True)
    cols = st.columns(4)
    for i, item in enumerate(alpha_data):
        with cols[i]:
            st.metric(label=item['name'], value=f"${item['price']:.2f}", delta=f"{item['change']:.2f}%")
            st.markdown(f"**RSI(14):** {item['rsi']:.1f} / **시그널:** {item['signal']}")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# 매크로 레이더
st.subheader("📊 글로벌 매크로 레이더")
rows = [macro_data[i:i+5] for i in range(0, len(macro_data), 5)]
for row in rows:
    cols = st.columns(len(row))
    for i, item in enumerate(row):
        cols[i].metric(label=item['name'], value=f"{item['price']:,.2f}", delta=f"{item['change']:.2f}%")

st.divider()

# 수급 및 스마트머니
col_trend, col_link = st.columns([1, 1.2])
with col_trend:
    st.subheader("🎯 3일 연속 상승 (추세 포착)")
    idx = 0
    for item in macro_data:
        if item['is_buy']:
            st.success(f"✅ **{item['name']}**")
            idx += 1
    if idx == 0: st.warning("현재 추세 유입 지표 없음")
with col_link:
    st.subheader("🔗 데이터 교차 검증 (스마트 머니)")
    l1, l2 = st.columns(2)
    l1.markdown("### [🐳 WhaleWisdom (13F)](https://whalewisdom.com/)")
    l2.markdown("### [🟢 네이버 증권 수급](https://finance.naver.com/sise/)")

st.divider()

# 💡 [핵심 수정 구간] 모네타의 스마트 라우팅 검색 엔진 (V7.2)
st.subheader("🔍 심층 종목 검색 (스마트 라우팅 탑재)")
st.info("💡 **티커(NVDA), 종목코드(005930), 종목명(삼성전자)** 중 아무거나 입력하셔도 시스템이 자동 분석하여 최적의 링크를 제공합니다.")

search_kw = st.text_input("검색어 입력", placeholder="입력 후 Enter 키를 누르세요")

if search_kw:
    search_kw = search_kw.strip()
    encoded_kw = urllib.parse.quote(search_kw)
    
    # 입력값 형태 분석 (알고리즘)
    is_code = search_kw.isdigit() and len(search_kw) == 6 # 6자리 숫자인가? (한국 종목코드)
    is_korean = any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in search_kw) # 한글이 포함되어 있는가? (한국 종목명)
    
    # 1. 네이버페이 증권 (모든 형태 완벽 지원)
    naver_url = f"https://m.stock.naver.com/search/result/{encoded_kw}"
    
    # 2. 트레이딩뷰 라우팅 (한국/미국 구조 분리)
    if is_code:
        # 종목코드 입력 시 한국 시장(KRX) 강제 지정으로 차트 즉시 오픈
        tv_url = f"https://kr.tradingview.com/chart/?symbol=KRX%3A{search_kw}"
    elif is_korean:
        # 한글 종목명 입력 시 트레이딩뷰 내부 검색 엔진으로 안전하게 연결
        tv_url = f"https://kr.tradingview.com/search/?q={encoded_kw}"
    else:
        # 영어 티커 입력 시 직접 차트 오픈
        tv_url = f"https://kr.tradingview.com/chart/?symbol={search_kw.upper()}"
        
    # 3. 야후 파이낸스 라우팅 (Lookup 엔드포인트 사용으로 에러 원천 차단)
    yahoo_url = f"https://finance.yahoo.com/lookup?s={encoded_kw}"
    
    # 4. 구글 뉴스 라우팅
    google_url = f"https://news.google.com/search?q={encoded_kw}"

    st.markdown(f"**✅ '{search_kw}' 팩트 체크 파이프라인 준비 완료**")
    st.markdown(f"- [🟢 **네이버페이 증권** (국내/해외 수급 및 재무 확인)]({naver_url})")
    st.markdown(f"- [📈 **TradingView** (글로벌 기술적 차트 분석)]({tv_url})")
    st.markdown(f"- [🇺🇸 **Yahoo Finance** (스마트머니 기본 툴 조회)]({yahoo_url})")
    st.markdown(f"- [🌐 **구글 뉴스** (실시간 글로벌 시황 모니터링)]({google_url})")
