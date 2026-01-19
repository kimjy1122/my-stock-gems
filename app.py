import streamlit as st
from pykrx import stock
import FinanceDataReader as fdr
import pandas_ta as ta
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="Stock Gems", page_icon="💎", layout="wide")
st.title("💎 My Stock Gems Scanner")

rsi_limit = st.sidebar.slider("최소 RSI 강도", 40, 70, 50)
market_type = st.sidebar.selectbox("시장 선택", ["KOSPI", "KOSDAQ"])

@st.cache_data(ttl=3600)
def run_analysis(m_type):
    # 어제 날짜로 데이터 시도 (오늘 데이터가 아직 없을 경우 대비)
    today = datetime.now().strftime("%Y%m%d")
    
    try:
        df_investor = stock.get_market_net_purchase_of_equities_by_ticker(today, today, m_type)
        # 만약 오늘 데이터가 비어있다면 에러 발생시켜 except문으로 이동
        if df_investor.empty or df_investor['외국인'].sum() == 0:
            raise ValueError("No data for today")
    except:
        # 오늘 데이터가 없으면 전일 평일 데이터 가져오기
        target_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        df_investor = stock.get_market_net_purchase_of_equities_by_ticker(target_date, target_date, m_type)

    candidates = df_investor[(df_investor['외국인'] > 0) & (df_investor['기관합계'] > 0)]
    
    gems = []
    for ticker in candidates.index[:20]:
        try:
            df = fdr.DataReader(ticker, (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'))
            if len(df) < 20: continue
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['MA20'] = ta.sma(df['Close'], length=20)
            curr = df.iloc[-1]
            if curr['RSI'] >= rsi_limit and curr['Close'] > curr['MA20']:
                name = stock.get_market_ticker_name(ticker)
                gems.append({"종목명": name, "코드": ticker, "현재가": int(curr['Close']), "RSI": round(curr['RSI'], 1)})
        except: continue
    return pd.DataFrame(gems)

if st.button('🚀 지금 종목 분석 시작'):
    with st.spinner('데이터 분석 중...'):
        result_df = run_analysis(market_type)
        if not result_df.empty:
            st.dataframe(result_df, use_container_width=True)
        else:
            st.warning("조건에 맞는 종목이 없거나 아직 데이터가 업데이트되지 않았습니다.")
