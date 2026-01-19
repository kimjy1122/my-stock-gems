import streamlit as st
from pykrx import stock
import FinanceDataReader as fdr
import pandas_ta as ta
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="Stock Gems", page_icon="💎", layout="wide")
st.title("💎 My Stock Gems Scanner")

# 사이드바: 기준을 조금 더 완화 (RSI 40부터)
rsi_limit = st.sidebar.slider("최소 RSI 강도", 30, 70, 40)
market_type = st.sidebar.selectbox("시장 선택", ["KOSPI", "KOSDAQ"])

@st.cache_data(ttl=600) # 10분마다 갱신
def run_analysis(m_type):
    found_df = None
    target_date = None
    
    # 최근 10일간을 뒤져서 데이터가 있는 가장 최근 날짜를 찾음
    for i in range(0, 10):
        check_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = stock.get_market_net_purchase_of_equities_by_ticker(check_date, check_date, m_type)
            # 외국인이나 기관 매수 합계가 0이 아니면 데이터가 있는 것으로 간주
            if not df.empty and (abs(df['외국인'].sum()) > 0):
                found_df = df
                target_date = check_date
                break
        except:
            continue
    
    if found_df is None:
        return pd.DataFrame(), None

    # 조건 완화: 외인 '또는' 기관 매수 (둘 다 양수일 때 우선순위)
    candidates = found_df[(found_df['외국인'] > 0) | (found_df['기관합계'] > 0)]
    
    gems = []
    # 상위 30개 종목 스캔
    for ticker in candidates.index[:30]:
        try:
            name = stock.get_market_ticker_name(ticker)
            price_df = fdr.DataReader(ticker, (datetime.now() - timedelta(days=50)).strftime('%Y-%m-%d'))
            if len(price_df) < 20: continue
            
            price_df['RSI'] = ta.rsi(price_df['Close'], length=14)
            curr = price_df.iloc[-1]
            
            if curr['RSI'] >= rsi_limit:
                gems.append({
                    "종목명": name,
                    "현재가": int(curr['Close']),
                    "RSI(강도)": round(curr['RSI'], 1),
                    "외인매수": found_df.loc[ticker, '외국인'],
                    "기관매수": found_df.loc[ticker, '기관합계']
                })
        except:
            continue
            
    return pd.DataFrame(gems), target_date

if st.button('🚀 지금 종목 분석 시작'):
    with st.spinner('거래소에서 데이터를 불러오는 중...'):
        result_df, used_date = run_analysis(market_type)
        
        if not result_df.empty:
            st.success(f"✅ {used_date} 기준 데이터를 찾았습니다!")
            st.dataframe(result_df.sort_values(by="RSI(강도)", ascending=False), use_container_width=True)
        else:
            st.error("❌ 현재 분석 가능한 데이터가 없습니다. 잠시 후(오후 6시 이후) 다시 시도해 주세요.")
