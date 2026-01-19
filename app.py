import streamlit as st
from pykrx import stock
import FinanceDataReader as fdr
import pandas_ta as ta
from datetime import datetime, timedelta
import pandas as pd
import time

st.set_page_config(page_title="Stock Gems", page_icon="💎", layout="wide")
st.title("💎 My Stock Gems Scanner")

# 사이드바 설정 (초기값을 낮춰서 종목이 무조건 보이게 설정)
rsi_limit = st.sidebar.slider("최소 RSI 강도 (낮을수록 많이 검색)", 20, 70, 35)
market_type = st.sidebar.selectbox("시장 선택", ["KOSPI", "KOSDAQ"])

@st.cache_data(ttl=600)
def run_analysis(m_type):
    found_df = None
    target_date = None
    
    # 최근 15일간을 뒤져서 데이터가 '확실히' 있는 날짜를 찾음 (주말/공휴일 완벽 대비)
    for i in range(0, 15):
        check_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            # 수급 데이터를 가져올 때 서버 부하 방지를 위해 살짝 대기
            time.sleep(0.2)
            df = stock.get_market_net_purchase_of_equities_by_ticker(check_date, check_date, m_type)
            
            # 거래량이 있고 외국인 매수 데이터가 존재하는지 확인
            if not df.empty and df['외국인'].abs().sum() > 0:
                found_df = df
                target_date = check_date
                break
        except:
            continue
    
    if found_df is None:
        return pd.DataFrame(), None

    # 조건: 외국인 혹은 기관 중 하나라도 매수 우위인 종목 추출
    candidates = found_df[(found_df['외국인'] > 0) | (found_df['기관합계'] > 0)]
    
    gems = []
    # 분석 속도를 위해 수급 상위 40개 종목 스캔
    for ticker in candidates.index[:40]:
        try:
            name = stock.get_market_ticker_name(ticker)
            # 주가 데이터는 조금 넉넉하게 100일치 가져옴
            price_df = fdr.DataReader(ticker, (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d'))
            if len(price_df) < 30: continue
            
            # 기술적 지표 계산
            price_df['RSI'] = ta.rsi(price_df['Close'], length=14)
            curr = price_df.iloc[-1]
            
            if curr['RSI'] >= rsi_limit:
                gems.append({
                    "종목명": name,
                    "현재가": f"{int(curr['Close']):,}",
                    "상승에너지(RSI)": round(curr['RSI'], 1),
                    "외인매수": found_df.loc[ticker, '외국인'],
                    "기관매수": found_df.loc[ticker, '기관합계']
                })
        except:
            continue
            
    return pd.DataFrame(gems), target_date

if st.button('🚀 지금 종목 분석 시작'):
    with st.spinner('거래소 서버에서 최신 수급 데이터를 탐색 중입니다...'):
        result_df, used_date = run_analysis(market_type)
        
        if not result_df.empty:
            st.success(f"✅ {used_date} 기준 데이터를 찾았습니다! (가장 최근 거래일)")
            st.dataframe(result_df.sort_values(by="상승에너지(RSI)", ascending=False), use_container_width=True)
            st.balloons() # 성공 시 풍선 효과
        else:
            st.error("현재 거래소 데이터 점검 중이거나 조건에 맞는 종목이 없습니다. 30분 뒤에 다시 시도해 주세요.")
