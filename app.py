import streamlit as st
from pykrx import stock
import FinanceDataReader as fdr
import pandas_ta as ta
from datetime import datetime, timedelta
import pandas as pd
import time

st.set_page_config(page_title="Stock Gems", page_icon="💎", layout="wide")
st.title("💎 My Stock Gems Scanner")

rsi_limit = st.sidebar.slider("최소 RSI 강도", 20, 70, 35)
market_type = st.sidebar.selectbox("시장 선택", ["KOSPI", "KOSDAQ"])

@st.cache_data(ttl=600)
def run_analysis(m_type):
    found_df = None
    target_date = None
    
    # 1. 수급 데이터 존재 여부 확인 (최근 15일 탐색)
    for i in range(0, 15):
        check_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            time.sleep(0.1)
            df = stock.get_market_net_purchase_of_equities_by_ticker(check_date, check_date, m_type)
            if not df.empty and df['외국인'].abs().sum() > 0:
                found_df = df
                target_date = check_date
                break
        except:
            continue
    
    # [상태 1] 거래소 데이터 자체가 없는 경우
    if found_df is None:
        return "NO_DATA", None, None

    # 2. 조건 필터링 시작
    candidates = found_df[(found_df['외국인'] > 0) | (found_df['기관합계'] > 0)]
    
    gems = []
    for ticker in candidates.index[:40]:
        try:
            name = stock.get_market_ticker_name(ticker)
            price_df = fdr.DataReader(ticker, (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d'))
            if len(price_df) < 30: continue
            
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
            
    result_df = pd.DataFrame(gems)
    
    # [상태 2] 데이터는 있지만 조건(RSI 등)에 맞는 종목이 없는 경우
    if result_df.empty:
        return "NO_GEMS", target_date, None
        
    # [상태 3] 종목 발견 성공
    return "SUCCESS", target_date, result_df

if st.button('🚀 지금 종목 분석 시작'):
    with st.spinner('데이터를 정밀 분석 중입니다...'):
        status, used_date, final_df = run_analysis(market_type)
        
        if status == "SUCCESS":
            st.success(f"✅ {used_date} 기준 종목 포착 성공!")
            st.dataframe(final_df.sort_values(by="상승에너지(RSI)", ascending=False), use_container_width=True)
            st.balloons()
            
        elif status == "NO_GEMS":
            st.info(f"📅 {used_date} 데이터는 확인되었으나, 설정하신 RSI {rsi_limit} 이상인 종목이 없습니다.")
            st.warning("왼쪽 슬라이더에서 RSI 강도를 낮춰보세요.")
            
        elif status == "NO_DATA":
            st.error("❌ 거래소에서 분석 가능한 최신 데이터를 찾을 수 없습니다.")
            st.info("장 마감 직후에는 데이터 업데이트에 시간이 걸릴 수 있습니다. (보통 17시 이후 안정화)")
