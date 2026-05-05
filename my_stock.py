import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. 페이지 설정 및 KRX 전광판 UI CSS
st.set_page_config(page_title="Daniel Alpha System Ver 8.1", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
    /* 전체 배경: 트레이딩 룸의 심연 (Deep Black & Navy) */
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 0%, #111827 0%, #050505 100%);
        color: #e2e8f0;
    }
    
    /* 텍스트 및 헤더 색상 */
    h1, h2, h3 { color: #ffffff !important; text-shadow: 0 0 5px rgba(255,255,255,0.2); }
    
    /* KRX LED 전광판 카드 스타일 (한국형 빨강/파랑) */
    .krx-board {
        background-color: #0a0a0a;
        border: 2px solid #1f2937;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: inset 0 0 15px rgba(0,0,0,0.8);
        margin-bottom: 15px;
    }
    .krx-title { color: #94a3b8; font-size: 15px; font-weight: bold; margin-bottom: 5px; }
    .krx-price { color: #ffffff; font-size: 26px; font-weight: 900; font-family: 'Courier New', monospace; letter-spacing: -1px; }
    .krx-up { color: #ff3333; text-shadow: 0 0 8px rgba(255, 51, 51, 0.6); font-weight: bold; font-size: 18px; }
    .krx-down { color: #3b82f6; text-shadow: 0 0 8px rgba(59, 130, 246, 0.6); font-weight: bold; font-size: 18px; }
    .krx-flat { color: #94a3b8; font-weight: bold; font-size: 18px; }
    
    /* 기존 박스들 스타일 유지되 더 다크하게 */
    .fear-greed-box { background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 12px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(5px); }
    .momentum-box { background-color: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 12px; border-left: 5px solid #8a2be2; }
    .broad-box { background-color: rgba(255, 255, 255, 0.03); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05); }
    .rule-box { background-color: rgba(245, 158, 11, 0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b; font-size: 14px; color: #e2e8f0; }
    
    /* 동기화 버튼 화려하게 */
    .stButton>button {
        background: linear-gradient(90deg, #1d4ed8 0%, #3b82f6 100%);
        color: white !important;
        font-weight: 900;
        font-size: 18px;
        border-radius: 10px;
        border: none;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
        height: 60px;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #2563eb 0%, #60a5fa 100%);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6);
    }
    
    /* 링크 색상 */
    a { color: #60a5fa !important; text-decoration: none !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- MACD 추세 전환 판별 함수 ---
def check_trend_reversal(df):
    if len(df) < 35: return False
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    is_reversal = (hist.iloc[-1] > 0) and (hist.iloc[-4:-1].min() <= 0)
    return is_reversal

# --- 한국형 LED 전광판 렌더링 함수 ---
def render_krx_board(name, price, change, is_currency=False):
    if change > 0:
        color_class, arrow = "krx-up", "▲"
    elif change < 0:
        color_class, arrow = "krx-down", "▼"
    else:
        color_class, arrow = "krx-flat", "-"
        
    # 환율이나 지수에 따라 소수점 표기 다르게
    price_str = f"{price:,.2f}" if not is_currency else f"{price:,.2f}"
    if name == "비트코인": price_str = f"${price:,.0f}"
        
    html = f"""
    <div class="krx-board">
        <div class="krx-title">{name}</div>
        <div class="krx-price">{price_str}</div>
        <div class="{color_class}">{arrow} {abs(change):.2f}%</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# 2. 데이터 엔진 (캐시 적용)
@st.cache_data(ttl=300)
def get_macro_data():
    tickers = {
        "나스닥 종합": "^IXIC", "S&P 500": "^GSPC", "다우존스": "^DJI",
        "필라 반도체": "^SOX", "러셀 2000": "^RUT", "코스피": "^KS11", "코스닥": "^KQ11", 
        "미 10년물 금리": "^TNX", "비트코인": "BTC-USD", 
        "금 (Gold)": "GC=F", "구리 (Copper)": "HG=F", 
        "원/달러 환율": "USDKRW=X", "엔/달러 환율": "JPY=X", # 핵심 추가: 엔화 리스크 감시
        "WTI 원유": "CL=F", "VIX 지수": "^VIX"
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

@st.cache_data(ttl=300)
def get_alpha_data():
    alpha_tickers = {"TQQQ (나스닥 3배)": "TQQQ", "SOXL (반도체 3배)": "SOXL", "엔비디아 (NVDA)": "NVDA", "MSTR (BTC 프록시)": "MSTR"}
    results = []
    for name, symbol in alpha_tickers.items():
        try:
            df = yf.Ticker(symbol).history(period="6mo")
            if df.empty or len(df) < 20:
                results.append({"name": name, "error": True}); continue
            
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            bb_mid = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            bb_upper = bb_mid + (bb_std * 2)
            bb_lower = bb_mid - (bb_std * 2)
            
            curr = df['Close'].iloc[-1]
            change = ((curr - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
            
            signal = "관망 (대기)"
            if rsi.iloc[-1] < 30 and curr <= bb_lower.iloc[-1]: signal = "🔥 매수 (과매도)"
            elif rsi.iloc[-1] > 70 and curr >= bb_upper.iloc[-1]: signal = "⚠️ 매도 (과매수)"
                
            results.append({"name": name, "price": curr, "change": change, "rsi": rsi.iloc[-1], "signal": signal, "error": False})
        except: results.append({"name": name, "error": True})
    return results

@st.cache_data(ttl=300)
def get_momentum_top3():
    us_pool = {"NVDA (엔비디아)": "NVDA", "TSLA (테슬라)": "TSLA", "PLTR (팔란티어)": "PLTR", "MSTR (마이크로)": "MSTR", "AMD (AMD)": "AMD", "META (메타)": "META", "AVGO (브로드컴)": "AVGO", "TQQQ (나스닥)": "TQQQ", "SOXL (반도체)": "SOXL", "CONL (코인베이스)": "CONL"}
    # 에코프로 추가: 코스닥 유동성 척도
    kr_pool = {"삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "한미반도체": "042700.KS", "알테오젠": "196170.KQ", "에코프로": "086520.KQ", "현대차": "005380.KS", "기아": "000270.KS", "KB금융": "105560.KS", "셀트리온": "068270.KS", "삼양식품": "003230.KS"}
    
    def process_pool(pool):
        results = []
        for name, sym in pool.items():
            try:
                df = yf.Ticker(sym).history(period="6mo")
                if len(df) >= 35:
                    curr = df['Close'].iloc[-1]
                    price_5d = df['Close'].iloc[-6]
                    change_5d = ((curr - price_5d) / price_5d) * 100
                    results.append({"name": name, "change_5d": change_5d, "is_reversal": check_trend_reversal(df)})
            except: continue
        results.sort(key=lambda x: x['change_5d'], reverse=True)
        return results[:3]
    return process_pool(us_pool), process_pool(kr_pool)

@st.cache_data(ttl=300)
def get_broad_trend():
    pools = {
        "🏛️ 채권 (안전자산)": {"미 장기채(TLT)": "TLT", "미 하이일드(HYG)": "HYG"},
        "🚢 해운/운송 (물동량)": {"미국 종합운송(IYT)": "IYT", "한국 해운(HMM)": "011200.KS"},
        "🛢️ 원자재 (인플레이션)": {"달러 인덱스": "DX-Y.NYB", "천연가스": "NG=F"},
        "🌍 타국 증시 (유동성)": {"유럽 STOXX50": "^STOXX50E", "일본 닛케이": "^N225"}
    }
    results = {}
    for category, items in pools.items():
        cat_results = []
        for name, sym in items.items():
            try:
                df = yf.Ticker(sym).history(period="6mo")
                if len(df) >= 35:
                    curr = df['Close'].iloc[-1]
                    change = ((curr - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                    if check_trend_reversal(df): cat_results.append({"name": name, "change": change})
            except: continue
        results[category] = cat_results
    return results


# --- 화면 출력 시작 ---

# 최상단: 타이틀 및 [실시간 100% 동기화 버튼]
col_title, col_sync = st.columns([2.5, 1])
with col_title:
    st.title("🏛️ Daniel's 실시간 투자 상황실 (Ver 8.1)")
    st.markdown(f"<p style='color: #94a3b8;'>✅ KRX LED 전광판 모드 | 최종 업데이트: {datetime.now().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)
with col_sync:
    # 이 버튼을 누르면 캐시가 날아가고 서버에서 즉시 데이터를 다시 끌어옵니다.
    if st.button("🔄 실시간 데이터 강제 갱신", use_container_width=True):
        st.cache_data.clear() # 캐시 강제 삭제
        st.rerun() # 화면 즉시 새로고침

st.divider()

# 공포 탐욕 & 페드워치
col_fg, col_fed = st.columns(2)
with col_fg: st.markdown(f"""<a href="https://edition.cnn.com/markets/fear-and-greed" target="_blank"><div class="fear-greed-box"><span style="font-size: 14px; color: #94a3b8;">CNN Business</span><br><span style="font-size: 22px; color: #ffffff; font-weight: bold;">🔥 공포와 탐욕 지수</span></div></a>""", unsafe_allow_html=True)
with col_fed: st.markdown(f"""<a href="https://www.cmegroup.com/markets/interest-rates/target-rate-probabilities.html" target="_blank"><div class="fear-greed-box" style="border-color: #3b82f6;"><span style="font-size: 14px; color: #94a3b8;">CME Group</span><br><span style="font-size: 22px; color: #3b82f6; font-weight: bold;">🏛️ CME FedWatch 연결</span></div></a>""", unsafe_allow_html=True)

st.divider()

# 데이터 로딩
macro_data, current_vix = get_macro_data()
alpha_data = get_alpha_data()

# KRX 스타일 메인 전광판 (지수 및 매크로)
st.subheader("📊 글로벌 메인 레이더 (KRX LED 전광판 모드)")
st.info("💡 한국 증시 기준 적용: **상승은 붉은색(▲), 하락은 파란색(▼)**으로 표시됩니다. '엔/달러 환율'이 방어선으로 추가되었습니다.")

rows = [macro_data[i:i+4] for i in range(0, len(macro_data), 4)] 
for row in rows:
    cols = st.columns(len(row))
    for i, item in enumerate(row):
        with cols[i]:
            if item.get('error'):
                st.markdown(f"<div class='krx-board'><div class='krx-title'>{item['name']}</div><div class='krx-flat'>통신 지연</div></div>", unsafe_allow_html=True)
            else:
                is_currency = "환율" in item['name']
                render_krx_board(item['name'], item['price'], item['change'], is_currency)

st.divider()

# Alpha 엔진 및 기계적 비중 조절 룰
st.subheader("🚀 Alpha 타겟팅 전광판 & 자금 관리 룰")

if current_vix >= 30: 
    st.markdown("<div class='rule-box' style='background-color: rgba(239, 68, 68, 0.1); border-left-color: #ef4444; color: #fca5a5;'><b>🚨 [VIX 극단적 공포] 모네타 룰:</b> 주식 비중 20% 이하 축소. 레버리지 신규 진입 절대 금지. 현금 관망.</div>", unsafe_allow_html=True)
elif current_vix >= 20: 
    st.markdown("<div class='rule-box'><b>⚠️ [VIX 변동성 확대] 모네타 룰:</b> 단일 종목 최대 비중 15% 제한. 짧은 익절/손절(-3%) 준수.</div>", unsafe_allow_html=True)
else: 
    st.markdown("<div class='rule-box' style='background-color: rgba(16, 185, 129, 0.1); border-left-color: #10b981; color: #6ee7b7;'><b>✅ [VIX 시장 안정] 모네타 룰:</b> 단일 종목 최대 비중 30% 허용. 추세 전환 시그널(🔄) 발생 시 적극 매수.</div>", unsafe_allow_html=True)

st.write("") 

if alpha_data:
    cols = st.columns(4)
    for i, item in enumerate(alpha_data):
        with cols[i]:
            if not item.get('error'):
                # 알파 타겟팅도 전광판 스타일로 적용하되, 하단에 RSI 추가
                color_class = "krx-up" if item['change'] > 0 else "krx-down" if item['change'] < 0 else "krx-flat"
                arrow = "▲" if item['change'] > 0 else "▼" if item['change'] < 0 else "-"
                st.markdown(f"""
                <div class="krx-board" style="border-color: #8a2be2;">
                    <div class="krx-title">{item['name']}</div>
                    <div class="krx-price">${item['price']:.2f}</div>
                    <div class="{color_class}" style="font-size:16px;">{arrow} {abs(item['change']):.2f}%</div>
                    <hr style="margin:10px 0; border-color:#333;">
                    <div style="color:#a3e635; font-size:14px;">RSI: {item['rsi']:.1f} | {item['signal']}</div>
                </div>
                """, unsafe_allow_html=True)

st.divider()

# 글로벌 자산군 추세 전환 스캐너
st.subheader("🌊 글로벌 이종 자산 턴어라운드 (MACD 포착)")
broad_data = get_broad_trend()
cols_broad = st.columns(4)

for i, (category, items) in enumerate(broad_data.items()):
    with cols_broad[i]:
        st.markdown(f"<div class='broad-box'>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:#93c5fd; font-weight:bold;'>{category}</span>", unsafe_allow_html=True)
        if not items:
            st.markdown("<span style='color:#475569; font-size:14px;'>추세 전환 자산 없음</span>", unsafe_allow_html=True)
        else:
            for item in items:
                st.markdown(f"🔹 {item['name']}<br><span style='color:#c084fc; font-size:13px;'>🔄 상승 추세 진입!</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# 한/미 모멘텀 Top 3 스캐너
st.subheader("🔥 주식 모멘텀 스캐너 (5일 누적 상승률 Top 3)")
us_top3, kr_top3 = get_momentum_top3()
col_us, col_kr = st.columns(2)

with col_us:
    st.markdown("<div class='momentum-box'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#ffffff; margin-bottom:15px;'>🇺🇸 미국 주도주 Top 3</h3>", unsafe_allow_html=True)
    for i, item in enumerate(us_top3):
        rev_mark = " 🔄 <span style='color:#c084fc; font-size:13px;'>[턴어라운드]</span>" if item['is_reversal'] else ""
        color = "#ff3333" if item['change_5d'] > 0 else "#3b82f6"
        st.markdown(f"<div style='margin-bottom:8px;'>**{i+1}. {item['name']}** : <span style='color:{color}; font-weight:bold;'>{item['change_5d']:.2f}%</span> {rev_mark}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_kr:
    st.markdown("<div class='momentum-box' style='border-left-color: #3b82f6;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#ffffff; margin-bottom:15px;'>🇰🇷 한국 주도주 Top 3</h3>", unsafe_allow_html=True)
    for i, item in enumerate(kr_top3):
        rev_mark = " 🔄 <span style='color:#c084fc; font-size:13px;'>[턴어라운드]</span>" if item['is_reversal'] else ""
        color = "#ff3333" if item['change_5d'] > 0 else "#3b82f6"
        st.markdown(f"<div style='margin-bottom:8px;'>**{i+1}. {item['name']}** : <span style='color:{color}; font-weight:bold;'>{item['change_5d']:.2f}%</span> {rev_mark}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# 심층 검색 엔진 (폼 형태 유지)
st.subheader("🔍 글로벌 심층 분석 터미널 (원클릭)")
st.info("👇 종목명, 티커, 코드를 입력하고 **[심층 분석 실행]**을 누르십시오.")

with st.form(key='search_form'):
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        search_kw = st.text_input("검색어 입력", label_visibility="collapsed", placeholder="예: 삼성전자, NVDA, 005930")
    with col_btn:
        submit_search = st.form_submit_button("🔍 심층 분석 실행", use_container_width=True)

if submit_search and search_kw:
    search_kw = search_kw.strip()
    encoded_kw = urllib.parse.quote(search_kw)
    
    is_code = search_kw.isdigit() and len(search_kw) == 6
    is_korean = any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in search_kw)
    
    investing_url = f"https://kr.investing.com/search/?q={encoded_kw}"
    finviz_url = f"https://finviz.com/quote.ashx?t={search_kw.upper()}" if not (is_code or is_korean) else "https://finviz.com/"

    if is_code: tv_url = f"https://kr.tradingview.com/chart/?symbol=KRX%3A{search_kw}"
    elif is_korean: tv_url = f"https://kr.tradingview.com/search/?q={encoded_kw}"
    else: tv_url = f"https://kr.tradingview.com/chart/?symbol={search_kw.upper()}"
        
    yahoo_url = f"https://finance.yahoo.com/lookup?s={encoded_kw}"
    google_url = f"https://news.google.com/search?q={encoded_kw}"
    twitter_url = f"https://twitter.com/search?q={encoded_kw}&src=typed_query&f=live"

    st.success(f"**✅ '{search_kw}' 데이터 파이프라인 개방 완료**")
    
    st.markdown(f"### 🔗 [📊 **Investing.com** (글로벌 1위 통합 수급/재무)]({investing_url})")
    st.markdown(f"### 🔗 [📈 **TradingView** (글로벌 차트 바로가기)]({tv_url})")
    if not (is_code or is_korean):
        st.markdown(f"### 🔗 [🇺🇸 **Finviz Screener** (미국주식 공매도/기관 보유량 추적)]({finviz_url})")
    st.markdown(f"### 🔗 [🇺🇸 **Yahoo Finance** (스마트머니 툴 바로가기)]({yahoo_url})")
    st.markdown(f"### 🔗 [🌐 **구글 뉴스** (실시간 시황 바로가기)]({google_url})")
    st.markdown(f"### 🔗 [📱 **X(트위터)** (군중 심리/루머 바로가기)]({twitter_url})")
