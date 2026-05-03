import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="Daniel Alpha System Ver 7.4", layout="wide")
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 22px; font-weight: bold; }
    .stSuccess { background-color: #e6f4ea; border-radius: 10px; padding: 15px; }
    .stWarning { background-color: #fff9e6; border-radius: 10px; padding: 15px; }
    .stError { background-color: #ffe6e6; border-radius: 10px; padding: 15px; }
    .fear-greed-box { background-color: #f0f2f6; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #ddd; }
    .alpha-box { background-color: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 10px; font-family: 'Courier New', Courier, monospace; }
    .momentum-box { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    .broad-box { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
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
                results.append({"name": name, "price": curr, "change": change})
                if name == "VIX 지수": vix_val = curr
        except: continue
    return results, vix_val

# 3. 데이터 엔진 2: 알파 타겟팅 (레버리지 추적)
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
                
                bb_mid = df['Close'].rolling(window=20).mean()
                bb_std = df['Close'].rolling(window=20).std()
                bb_upper = bb_mid + (bb_std * 2)
                bb_lower = bb_mid - (bb_std * 2)
                
                curr_price = df['Close'].iloc[-1]
                change = ((curr_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                
                signal = "관망 (대기)"
                if rsi.iloc[-1] < 30 and curr_price <= bb_lower.iloc[-1]: signal = "🔥 강력 매수 (과매도)"
                elif rsi.iloc[-1] > 70 and curr_price >= bb_upper.iloc[-1]: signal = "⚠️ 강력 매도 (과매수)"
                    
                results.append({"name": name, "price": curr_price, "change": change, "rsi": rsi.iloc[-1], "signal": signal})
        except: continue
    return results

# 4. 데이터 엔진 3: 한미 주도주 모멘텀 스캐너
@st.cache_data(ttl=300)
def get_momentum_top3():
    us_pool = {"NVDA (엔비디아)": "NVDA", "TSLA (테슬라)": "TSLA", "PLTR (팔란티어)": "PLTR", "MSTR (마이크로스트레티지)": "MSTR", "AMD (AMD)": "AMD", "META (메타)": "META", "AVGO (브로드컴)": "AVGO", "TQQQ (나스닥3배)": "TQQQ", "SOXL (반도체3배)": "SOXL", "CONL (코인베이스2배)": "CONL"}
    kr_pool = {"삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "한미반도체": "042700.KS", "알테오젠": "196170.KQ", "에코프로비엠": "247540.KQ", "현대차": "005380.KS", "기아": "000270.KS", "KB금융": "105560.KS", "셀트리온": "068270.KS", "삼양식품": "003230.KS"}
    
    def process_pool(pool):
        results = []
        for name, sym in pool.items():
            try:
                df = yf.Ticker(sym).history(period="6d")
                if len(df) >= 4:
                    curr_price = df['Close'].iloc[-1]
                    price_3d_ago = df['Close'].iloc[-4]
                    change_3d = ((curr_price - price_3d_ago) / price_3d_ago) * 100
                    is_consec = (df['Close'].iloc[-1] > df['Close'].iloc[-2]) and (df['Close'].iloc[-2] > df['Close'].iloc[-3]) and (df['Close'].iloc[-3] > df['Close'].iloc[-4])
                    results.append({"name": name, "change_3d": change_3d, "is_consec": is_consec})
            except: continue
        results.sort(key=lambda x: x['change_3d'], reverse=True)
        return results[:3]
    return process_pool(us_pool), process_pool(kr_pool)

# 5. 데이터 엔진 4: [신규] 글로벌 이종 자산 연속 상승 스캐너
@st.cache_data(ttl=300)
def get_broad_trend():
    pools = {
        "🏛️ 금리/채권 (돈의 이동)": {"미 10년물 국채금리": "^TNX", "미 장기채(TLT)": "TLT", "미 하이일드(HYG)": "HYG", "KODEX 국고채10년": "148070.KS"},
        "🚢 해운/운송 (물동량)": {"미국 종합운송(IYT)": "IYT", "글로벌 해운(ZIM)": "ZIM", "한국 해운(HMM)": "011200.KS"},
        "🛢️ 환율/원자재 (매크로)": {"달러 인덱스": "DX-Y.NYB", "천연가스": "NG=F", "우라늄(URA)": "URA", "비트코인": "BTC-USD"},
        "🌍 글로벌 증시 (자본 흐름)": {"유럽 STOXX50": "^STOXX50E", "일본 닛케이": "^N225", "인도 Nifty50": "^NSEI", "대만 가권": "^TWII"}
    }
    results = {}
    for category, items in pools.items():
        cat_results = []
        for name, sym in items.items():
            try:
                df = yf.Ticker(sym).history(period="10d")
                if len(df) >= 2:
                    streak = 0
                    for i in range(1, len(df)):
                        if df['Close'].iloc[-i] > df['Close'].iloc[-(i+1)]:
                            streak += 1
                        else:
                            break
                    curr_price = df['Close'].iloc[-1]
                    change = ((curr_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                    
                    if streak >= 3: # 3일 이상 연속 상승 중인 지수만 추출
                        cat_results.append({"name": name, "streak": streak, "change": change})
            except: continue
        cat_results.sort(key=lambda x: x['streak'], reverse=True)
        results[category] = cat_results
    return results

# --- 화면 출력 시작 ---
st.title("🏛️ Daniel's 연 30% 타겟팅 상황실 (Ver 7.4)")
st.write(f"✅ 글로벌 이종 자산 스캐너 가동 중: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 공포 탐욕 & 페드워치
col_fg, col_fed = st.columns(2)
with col_fg: st.markdown(f"""<a href="https://edition.cnn.com/markets/fear-and-greed" target="_blank" style="text-decoration: none;"><div class="fear-greed-box"><span style="font-size: 16px; color: #555;">CNN Business</span><br><span style="font-size: 24px; color: #000; font-weight: bold;">🔥 공포와 탐욕 지수</span></div></a>""", unsafe_allow_html=True)
with col_fed: st.markdown(f"""<a href="https://www.cmegroup.com/markets/interest-rates/target-rate-probabilities.html" target="_blank" style="text-decoration: none;"><div class="fear-greed-box" style="border-color: #007bff;"><span style="font-size: 16px; color: #555;">CME Group</span><br><span style="font-size: 24px; color: #007bff; font-weight: bold;">🏛️ CME FedWatch 연결</span></div></a>""", unsafe_allow_html=True)

st.divider()

# Alpha 엔진
macro_data, current_vix = get_macro_data()
alpha_data = get_alpha_data()

st.subheader("🚀 Alpha 타겟팅 엔진 (레버리지 추적)")
if current_vix >= 30: st.error(f"🚨 **[VIX 경고: {current_vix:.2f}] 극단적 공포. 레버리지 비중 축소 / 현금 관망 필수.**")
elif current_vix >= 20: st.warning(f"⚠️ **[VIX 경계: {current_vix:.2f}] 변동성 확대. 철저한 분할 매매 필수.**")
else: st.success(f"✅ **[VIX 안정: {current_vix:.2f}] 시장 안정. 추세 추종 유효.**")

if alpha_data:
    st.markdown("<div class='alpha-box'>", unsafe_allow_html=True)
    cols = st.columns(4)
    for i, item in enumerate(alpha_data):
        with cols[i]:
            st.metric(label=item['name'], value=f"${item['price']:.2f}", delta=f"{item['change']:.2f}% (1일)")
            st.markdown(f"**RSI(14):** {item['rsi']:.1f} / **시그널:** {item['signal']}")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# 💡 [핵심 신규 추가] 이종 자산 스캐너
st.subheader("🌊 글로벌 자산군 연속 상승 스캐너 (Intermarket Analysis)")
st.info("💡 채권, 운송, 원자재 등 다양한 자산군에서 **'현재 3거래일 이상 연속 상승 중'**인 지수만 실시간으로 필터링합니다.")

broad_data = get_broad_trend()
cols_broad = st.columns(4)

for i, (category, items) in enumerate(broad_data.items()):
    with cols_broad[i]:
        st.markdown(f"<div class='broad-box'>", unsafe_allow_html=True)
        st.markdown(f"**{category}**")
        if not items:
            st.markdown("<span style='color:gray; font-size:14px;'>현재 3일 연속 상승 중인 지수 없음</span>", unsafe_allow_html=True)
        else:
            for item in items:
                st.markdown(f"🔹 **{item['name']}**<br><span style='color:#d62728; font-weight:bold;'>{item['streak']}일 연속 상승</span> (오늘 {item['change']:.2f}%)", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# 한/미 모멘텀 Top 3 스캐너
st.subheader("🔥 주식 모멘텀 스캐너 (3일 누적 상승률 Top 3)")
us_top3, kr_top3 = get_momentum_top3()
col_us, col_kr = st.columns(2)

with col_us:
    st.markdown("<div class='momentum-box'>", unsafe_allow_html=True)
    st.markdown("### 🇺🇸 미국 시장 주도주 Top 3")
    for i, item in enumerate(us_top3):
        consec_mark = "📈 (3일 연속 우상향)" if item['is_consec'] else ""
        st.write(f"**{i+1}. {item['name']}** : `+{item['change_3d']:.2f}%` {consec_mark}")
    st.markdown("</div>", unsafe_allow_html=True)

with col_kr:
    st.markdown("<div class='momentum-box' style='border-left-color: #007bff;'>", unsafe_allow_html=True)
    st.markdown("### 🇰🇷 한국 시장 주도주 Top 3")
    for i, item in enumerate(kr_top3):
        consec_mark = "📈 (3일 연속 우상향)" if item['is_consec'] else ""
        st.write(f"**{i+1}. {item['name']}** : `+{item['change_3d']:.2f}%` {consec_mark}")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# 심층 검색 엔진 (스마트 라우팅)
st.subheader("🔍 심층 종목 검색 (스마트 라우팅 탑재)")
search_kw = st.text_input("종목명(삼성전자), 티커(NVDA), 종목코드(005930) 중 입력", placeholder="입력 후 Enter 키를 누르세요")

if search_kw:
    search_kw = search_kw.strip()
    encoded_kw = urllib.parse.quote(search_kw)
    
    is_code = search_kw.isdigit() and len(search_kw) == 6
    is_korean = any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in search_kw)
    
    naver_url = f"https://m.stock.naver.com/search/result/{encoded_kw}"
    if is_code: tv_url = f"https://kr.tradingview.com/chart/?symbol=KRX%3A{search_kw}"
    elif is_korean: tv_url = f"https://kr.tradingview.com/search/?q={encoded_kw}"
    else: tv_url = f"https://kr.tradingview.com/chart/?symbol={search_kw.upper()}"
        
    yahoo_url = f"https://finance.yahoo.com/lookup?s={encoded_kw}"
    google_url = f"https://news.google.com/search?q={encoded_kw}"

    st.markdown(f"**✅ '{search_kw}' 팩트 체크 파이프라인 준비 완료**")
    st.markdown(f"- [🟢 **네이버페이 증권** (국내/해외 수급 및 재무 확인)]({naver_url})")
    st.markdown(f"- [📈 **TradingView** (글로벌 기술적 차트 분석)]({tv_url})")
    st.markdown(f"- [🇺🇸 **Yahoo Finance** (스마트머니 기본 툴 조회)]({yahoo_url})")
    st.markdown(f"- [🌐 **구글 뉴스** (실시간 글로벌 시황 모니터링)]({google_url})")
