import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="Daniel Alpha System Ver 7.8", layout="wide")
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 22px; font-weight: bold; }
    .stSuccess { background-color: #e6f4ea; border-radius: 10px; padding: 15px; }
    .stWarning { background-color: #fff9e6; border-radius: 10px; padding: 15px; }
    .stError { background-color: #ffe6e6; border-radius: 10px; padding: 15px; }
    .fear-greed-box { background-color: #f0f2f6; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #ddd; }
    .alpha-box { background-color: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 10px; font-family: 'Courier New', Courier, monospace; }
    .momentum-box { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #8a2be2; }
    .broad-box { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .rule-box { background-color: #fffae6; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- 공통 MACD 추세 전환 판별 함수 ---
def check_trend_reversal(df):
    if len(df) < 35: return False
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    is_reversal = (hist.iloc[-1] > 0) and (hist.iloc[-4:-1].min() <= 0)
    return is_reversal

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
            df = t.history(period="6mo") 
            if df.empty or len(df) < 2:
                results.append({"name": name, "error": True})
                continue
            curr = df['Close'].iloc[-1]
            prev = df['Close'].iloc[-2]
            change = ((curr - prev) / prev) * 100
            is_rev = check_trend_reversal(df)
            results.append({"name": name, "price": curr, "change": change, "is_reversal": is_rev, "error": False})
            if name == "VIX 지수": vix_val = curr
        except: 
            results.append({"name": name, "error": True})
    return results, vix_val

# 3. 데이터 엔진 2: 알파 타겟팅 (레버리지 추적)
@st.cache_data(ttl=300)
def get_alpha_data():
    alpha_tickers = {"TQQQ (나스닥 3배)": "TQQQ", "SOXL (반도체 3배)": "SOXL", "UPRO (S&P 3배)": "UPRO", "엔비디아 (NVDA)": "NVDA"}
    results = []
    for name, symbol in alpha_tickers.items():
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="6mo")
            if df.empty or len(df) < 20:
                results.append({"name": name, "error": True})
                continue
            
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
                
            results.append({"name": name, "price": curr_price, "change": change, "rsi": rsi.iloc[-1], "signal": signal, "error": False})
        except: 
            results.append({"name": name, "error": True})
    return results

# 4. 데이터 엔진 3: 한미 주도주 모멘텀 & 추세 전환 스캐너
@st.cache_data(ttl=300)
def get_momentum_top3():
    us_pool = {"NVDA (엔비디아)": "NVDA", "TSLA (테슬라)": "TSLA", "PLTR (팔란티어)": "PLTR", "MSTR (마이크로스트레티지)": "MSTR", "AMD (AMD)": "AMD", "META (메타)": "META", "AVGO (브로드컴)": "AVGO", "TQQQ (나스닥)": "TQQQ", "SOXL (반도체)": "SOXL", "CONL (코인베이스)": "CONL"}
    kr_pool = {"삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "한미반도체": "042700.KS", "알테오젠": "196170.KQ", "에코프로비엠": "247540.KQ", "현대차": "005380.KS", "기아": "000270.KS", "KB금융": "105560.KS", "셀트리온": "068270.KS", "삼양식품": "003230.KS"}
    
    def process_pool(pool):
        results = []
        for name, sym in pool.items():
            try:
                df = yf.Ticker(sym).history(period="6mo")
                if len(df) >= 35:
                    curr_price = df['Close'].iloc[-1]
                    price_5d_ago = df['Close'].iloc[-6]
                    change_5d = ((curr_price - price_5d_ago) / price_5d_ago) * 100
                    
                    is_rev = check_trend_reversal(df)
                    results.append({"name": name, "change_5d": change_5d, "is_reversal": is_rev})
            except: continue
        results.sort(key=lambda x: x['change_5d'], reverse=True)
        return results[:3]
    return process_pool(us_pool), process_pool(kr_pool)

# 5. 데이터 엔진 4: 글로벌 이종 자산 추세 전환 스캐너
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
                df = yf.Ticker(sym).history(period="6mo")
                if len(df) >= 35:
                    is_rev = check_trend_reversal(df)
                    curr_price = df['Close'].iloc[-1]
                    change = ((curr_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                    if is_rev:
                        cat_results.append({"name": name, "change": change})
            except: continue
        results[category] = cat_results
    return results

# --- 화면 출력 시작 ---
st.title("🏛️ Daniel's 연 30% 타겟팅 상황실 (Ver 7.8)")
st.write(f"✅ 네이버 툴 제거 및 글로벌 최적화 툴 적용 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 공포 탐욕 & 페드워치
col_fg, col_fed = st.columns(2)
with col_fg: st.markdown(f"""<a href="https://edition.cnn.com/markets/fear-and-greed" target="_blank" style="text-decoration: none;"><div class="fear-greed-box"><span style="font-size: 16px; color: #555;">CNN Business</span><br><span style="font-size: 24px; color: #000; font-weight: bold;">🔥 공포와 탐욕 지수</span></div></a>""", unsafe_allow_html=True)
with col_fed: st.markdown(f"""<a href="https://www.cmegroup.com/markets/interest-rates/target-rate-probabilities.html" target="_blank" style="text-decoration: none;"><div class="fear-greed-box" style="border-color: #007bff;"><span style="font-size: 16px; color: #555;">CME Group</span><br><span style="font-size: 24px; color: #007bff; font-weight: bold;">🏛️ CME FedWatch 연결</span></div></a>""", unsafe_allow_html=True)

st.divider()

# Alpha 엔진 및 기계적 비중 조절 룰
macro_data, current_vix = get_macro_data()
alpha_data = get_alpha_data()

st.subheader("🚀 Alpha 타겟팅 엔진 & 기계적 자금 관리(Money Management)")

if current_vix >= 30: 
    st.error(f"🚨 **[VIX 경고: {current_vix:.2f}] 극단적 공포.**")
    st.markdown("<div class='rule-box'><b>🔒 모네타의 비중 조절 룰:</b> 주식 비중 20% 이하 축소. 레버리지 신규 진입 절대 금지. 현금 관망.</div>", unsafe_allow_html=True)
elif current_vix >= 20: 
    st.warning(f"⚠️ **[VIX 경계: {current_vix:.2f}] 변동성 확대 구간.**")
    st.markdown("<div class='rule-box'><b>⚖️ 모네타의 비중 조절 룰:</b> 단일 종목 최대 투자 비중 15% 제한. 짧은 익절/손절(-3%) 준수.</div>", unsafe_allow_html=True)
else: 
    st.success(f"✅ **[VIX 안정: {current_vix:.2f}] 시장 안정 구간.**")
    st.markdown("<div class='rule-box'><b>📈 모네타의 비중 조절 룰:</b> 단일 종목 최대 투자 비중 30% 허용. 추세 전환 시그널(🔄) 발생 시 적극 매수 유효.</div>", unsafe_allow_html=True)

st.write("") 

if alpha_data:
    st.markdown("<div class='alpha-box'>", unsafe_allow_html=True)
    cols = st.columns(4)
    for i, item in enumerate(alpha_data):
        with cols[i]:
            if item.get('error'):
                st.metric(label=item['name'], value="통신 지연", delta="재시도 요망")
            else:
                st.metric(label=item['name'], value=f"${item['price']:.2f}", delta=f"{item['change']:.2f}%")
                st.markdown(f"**RSI(14):** {item['rsi']:.1f} / **시그널:** {item['signal']}")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# 글로벌 자산군 추세 전환 스캐너
st.subheader("🌊 글로벌 자산군 추세 전환 포착 (MACD Turnaround)")
st.info("💡 단순히 연속으로 오른 종목이 아니라, **'최근 1~3일 내에 하락세를 끝내고 위로 방향을 튼(추세 전환)'** 자산만 필터링합니다.")

broad_data = get_broad_trend()
cols_broad = st.columns(4)

for i, (category, items) in enumerate(broad_data.items()):
    with cols_broad[i]:
        st.markdown(f"<div class='broad-box'>", unsafe_allow_html=True)
        st.markdown(f"**{category}**")
        if not items:
            st.markdown("<span style='color:gray; font-size:14px;'>현재 추세 전환된 자산 없음 (관망)</span>", unsafe_allow_html=True)
        else:
            for item in items:
                st.markdown(f"🔹 **{item['name']}**<br><span style='color:#8a2be2; font-weight:bold;'>🔄 상승 추세 전환 확인!</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# 한/미 모멘텀 Top 3 스캐너
st.subheader("🔥 주식 모멘텀 스캐너 (5일 누적 상승률 Top 3)")
us_top3, kr_top3 = get_momentum_top3()
col_us, col_kr = st.columns(2)

with col_us:
    st.markdown("<div class='momentum-box'>", unsafe_allow_html=True)
    st.markdown("### 🇺🇸 미국 시장 주도주 Top 3")
    for i, item in enumerate(us_top3):
        rev_mark = " 🔄 **[추세 전환 시작점!]**" if item['is_reversal'] else ""
        st.write(f"**{i+1}. {item['name']}** : `+{item['change_5d']:.2f}%` {rev_mark}")
    st.markdown("</div>", unsafe_allow_html=True)

with col_kr:
    st.markdown("<div class='momentum-box' style='border-left-color: #007bff;'>", unsafe_allow_html=True)
    st.markdown("### 🇰🇷 한국 시장 주도주 Top 3")
    for i, item in enumerate(kr_top3):
        rev_mark = " 🔄 **[추세 전환 시작점!]**" if item['is_reversal'] else ""
        st.write(f"**{i+1}. {item['name']}** : `+{item['change_5d']:.2f}%` {rev_mark}")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# 매크로 레이더
st.subheader("📊 글로벌 매크로 레이더")
rows = [macro_data[i:i+5] for i in range(0, len(macro_data), 5)]
for row in rows:
    cols = st.columns(len(row))
    for i, item in enumerate(row):
        if item.get('error'):
            cols[i].metric(label=item['name'], value="통신 지연", delta="재시도 요망")
        else:
            cols[i].metric(label=item['name'], value=f"{item['price']:,.2f}", delta=f"{item['change']:.2f}%")

st.divider()

# 💡 [핵심 패치 구역] 먹통 네이버 삭제 & 글로벌 메이저 툴 연동
st.subheader("🔍 심층 종목 & 실시간 군중 심리 검색")
st.info("👇 종목명, 티커, 코드를 입력하고 **반드시 [심층 분석 실행] 버튼을 눌러주세요.**")

with st.form(key='search_form'):
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        search_kw = st.text_input("종목명(삼성전자), 티커(NVDA), 종목코드(005930)", label_visibility="collapsed", placeholder="예: 삼성전자, NVDA, 005930")
    with col_btn:
        submit_search = st.form_submit_button("🔍 심층 분석 실행", use_container_width=True)

if submit_search and search_kw:
    search_kw = search_kw.strip()
    encoded_kw = urllib.parse.quote(search_kw)
    
    is_code = search_kw.isdigit() and len(search_kw) == 6
    is_korean = any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in search_kw)
    
    # [수정 사항 1] 네이버페이 증권 제거 -> Investing.com 통합 검색으로 대체 (한국/미국 모두 커버, 에러 없음)
    investing_url = f"https://kr.investing.com/search/?q={encoded_kw}"
    
    # [수정 사항 2] 미국 주식 전용 Finviz 스크리너 추가 (월가 스마트머니 필수 툴)
    finviz_url = f"https://finviz.com/quote.ashx?t={search_kw.upper()}" if not (is_code or is_korean) else "https://finviz.com/"

    if is_code: tv_url = f"https://kr.tradingview.com/chart/?symbol=KRX%3A{search_kw}"
    elif is_korean: tv_url = f"https://kr.tradingview.com/search/?q={encoded_kw}"
    else: tv_url = f"https://kr.tradingview.com/chart/?symbol={search_kw.upper()}"
        
    yahoo_url = f"https://finance.yahoo.com/lookup?s={encoded_kw}"
    google_url = f"https://news.google.com/search?q={encoded_kw}"
    twitter_url = f"https://twitter.com/search?q={encoded_kw}&src=typed_query&f=live"

    st.success(f"**✅ '{search_kw}' 글로벌 심층 분석 파이프라인 가동 완료**")
    
    # 한국 주식도 에러 없이 완벽 지원하는 Investing.com을 최상단 배치
    st.markdown(f"### [📊 **Investing.com** (글로벌 1위 통합 수급/재무/실적)]({investing_url})")
    st.markdown(f"### [📈 **TradingView** (글로벌 차트 바로가기)]({tv_url})")
    
    if not (is_code or is_korean):
        st.markdown(f"### [🇺🇸 **Finviz Screener** (미국주식 공매도/기관 보유량 추적)]({finviz_url})")
        
    st.markdown(f"### [🇺🇸 **Yahoo Finance** (스마트머니 툴 바로가기)]({yahoo_url})")
    st.markdown(f"### [🌐 **구글 뉴스** (실시간 시황 바로가기)]({google_url})")
    st.markdown(f"### [📱 **X(트위터)** (군중 심리/루머 바로가기)]({twitter_url})")
