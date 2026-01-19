import streamlit as st
from pykrx import stock
import FinanceDataReader as fdr
import pandas_ta as ta
from datetime import datetime, timedelta
import pandas as pd

# 앱 설정
st.set_page_config(page_title="Stock Gems", page_icon="💎", layout="wide")
st.title("💎 My Stock Gems Scanner")

# 사이드바 설정
rsi_limit = st.sidebar.slider("최소 RSI 강도 (높을수록 강한 상승)", 40, 70, 50)
market_type = st.sidebar.selectbox("시장 선택", ["KOSPI", "KOSDAQ"])

@st.cache_data(ttl=3600)
def run_analysis(m_type):
    # 최근 5일 중 데이터가 있는 날을 자동으로 탐색
    found_data = False
    for i in range(0, 10):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df_investor = stock.get_market_net_purchase_of_equities_by_ticker(target_date, target_date, m_type)
            if not df_investor.empty and df_investor['외국인'].sum() != 0:
                found_data = True
                break
        except:
            continue
    
    if not found_data:
        return pd.DataFrame() # 데이터를 아예 못 찾으면 빈 결과 반환

    # 외국인/기관 동반 매수 종목 필터링
    candidates = df_investor[(df_investor['외국인'] > 0) & (df_investor['기관합계'] > 0)]
    
    gems = []
    # 분석 속도를 위해 상위 20개 종목만 정밀 스캔
    for ticker in candidates.index[:20]:
        try:
            # 60일치 주가 데이터
            df = fdr.DataReader(ticker, (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'))
            if len(df) < 25: continue
            
            # 지표 계산
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['MA20'] = ta.sma(df['Close'], length=20)
            
            curr = df.iloc[-1]
            # 조건: RSI가 설정값 이상이고 20일 이동평균선 위에 있을 때
            if curr['RSI'] >= rsi_limit and curr['Close'] > curr['MA20']:
                name = stock.get_market_ticker_name(ticker)
                gems.append({
                    "종목명": name,
                    "현재가": f"{int(curr['Close']):,}",
                    "상승에너지(RSI)": round(curr['RSI'], 1),
                    "외인매수": f"{int(df_investor.loc[ticker, '외국인']):,}",
                    "기관매수": f"{int(df_investor.loc[ticker, '기관합계']):,}"
                })
        except:
            continue
    return pd.DataFrame(gems)

# 실행 버튼
if st.button('🚀 지금 종목 분석 시작'):
    with st.spinner('최근 거래일 데이터를 찾는 중...'):
        result_df = run_analysis(market_type)
        
        if not result_df.empty:
            st.success("조건에 맞는 종목을 찾았습니다!")
            st.dataframe(result_df, use_container_width=True)
            st.info("💡 종목명과 현재가를 확인하고 HTS/MTS에서 차트를 점검해보세요.")
        else:
            st.warning("분석 가능한 데이터를 찾지 못했거나 조건에 맞는 종목이 없습니다. 잠시 후 다시 시도해주세요.")
