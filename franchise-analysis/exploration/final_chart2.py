import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="프랜차이즈 영향력 분석 (Before & After)",
    page_icon="⚡",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 지표 계산
# -----------------------------------------------------------------------------
@st.cache_data
def load_data(filename):
    df = pd.read_csv(filename)
    df['영업매장수_safe'] = df['영업매장수'].replace(0, 1)
    
    # -------------------------------------------------------------------------
    # 1. 핵심 지표 계산
    # -------------------------------------------------------------------------
    # 1) 업태 밀도 & 시장 점유율
    df['Category_Total_Store'] = df.groupby(['연도', '시도', '업태 구분명'])['영업매장수'].transform('sum')
    df['Category_Density'] = (df['Category_Total_Store'] / df['전체_총인구수']) * 10000
    df['Real_Market_Share_Pct'] = (df['영업매장수'] / df['Category_Total_Store']) * 100
    
    # 2) 소득 지수
    avg_income = df['1인당지역총소득'].mean()
    df['Income_Index'] = df['1인당지역총소득'] / avg_income
    
    # 3) 성장률 & 가중치
    df['Growth_Rate'] = (df['신규매장수'] - df['폐업매장수']) / df['영업매장수_safe']
    growth_factor = (1 + df['Growth_Rate'] * 3).apply(lambda x: max(x, 0.1))
    
    # -------------------------------------------------------------------------
    # 2. 공식 적용 (Final Score)
    # -------------------------------------------------------------------------
    df['Final_Score'] = (
        df['Category_Density'] * df['Real_Market_Share_Pct'] * df['Income_Index'] * growth_factor
    )
    
    return df

try:
    df_all = load_data('franchise_analysis_corrected.csv')
except FileNotFoundError:
    st.error("❌ 'franchise_analysis_corrected.csv' 파일을 찾을 수 없습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바 및 필터링
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 분석 옵션")
years = sorted(df_all['연도'].unique(), reverse=True)
selected_year = st.sidebar.selectbox("연도 선택", years, index=0)
categories = sorted(df_all['업태 구분명'].unique())
selected_category = st.sidebar.selectbox("업태 선택", ["전체 (통합 1위)"] + categories)

df_year = df_all[df_all['연도'] == selected_year].copy()
if selected_category != "전체 (통합 1위)":
    df_year = df_year[df_year['업태 구분명'] == selected_category].copy()

# 영향력 점유율 계산 (Normalization)
region_total_score = df_year.groupby('시도')['Final_Score'].transform('sum')
df_year['Influence_Share_Pct'] = (df_year['Final_Score'] / region_total_score) * 100

# -----------------------------------------------------------------------------
# 4. 데이터 분리 (핵심 로직)
# -----------------------------------------------------------------------------
# [A] 순수 시장점유율 1등 (예: 충북 이디야) -> top_market
top_market = df_year.sort_values(by=['Real_Market_Share_Pct', '영업매장수'], ascending=[False, False])
top_market = top_market.drop_duplicates(subset=['시도'], keep='first')

# [B] 영향력 1등 (예: 충북 투썸) -> top_influence
top_influence = df_year.sort_values(by=['Influence_Share_Pct', '영업매장수'], ascending=[False, False])
top_influence = top_influence.drop_duplicates(subset=['시도'], keep='first')

# 라벨 생성 함수
def create_label(row, col_name, suffix='%'):
    return f"{row['브랜드']}<br>({row[col_name]:.1f}{suffix})"

top_market['Label'] = top_market.apply(lambda x: create_label(x, 'Real_Market_Share_Pct'), axis=1)
top_influence['Label'] = top_influence.apply(lambda x: create_label(x, 'Influence_Share_Pct'), axis=1)

# -----------------------------------------------------------------------------
# 5. 메인 대시보드
# -----------------------------------------------------------------------------
st.title(f"⚡ {selected_year}년 프랜차이즈 1위 분석 (물량 vs 영향력)")
st.markdown("왼쪽은 **현재 매장이 가장 많은 브랜드**, 오른쪽은 **미래 가치와 소득을 포함한 실질적 1위**입니다.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 1. 시장 점유율 1위 (물량)")
    st.caption("공식 적용 전: 단순 매장 수 기준 1위")
    fig_before = px.bar(
        top_market, x='시도', y='Real_Market_Share_Pct', 
        color='브랜드', text='Label',
        hover_data=['업태 구분명'],
        title="지역별 단순 시장 점유율 (%)"
    )
    fig_before.update_traces(textposition='outside', cliponaxis=False)
    fig_before.update_layout(xaxis_title="지역", yaxis_title="시장 점유율 (%)", height=500, margin=dict(t=50))
    st.plotly_chart(fig_before, use_container_width=True)

with col2:
    st.subheader("👑 2. 최종 영향력 1위 (공식)")
    st.caption("공식 적용 후: 밀도 × 점유율 × 소득 × 성장성")
    fig_after = px.bar(
        top_influence, x='시도', y='Influence_Share_Pct', 
        color='브랜드', text='Label',
        hover_data=['업태 구분명', 'Growth_Rate'],
        title="지역별 종합 영향력 점유율 (%)"
    )
    fig_after.update_traces(textposition='outside', cliponaxis=False)
    fig_after.update_layout(xaxis_title="지역", yaxis_title="영향력 점유율 (%)", height=500, margin=dict(t=50))
    st.plotly_chart(fig_after, use_container_width=True)

st.divider()

# -----------------------------------------------------------------------------
# 6. 상세 지표 (수정된 부분)
# -----------------------------------------------------------------------------
st.subheader("🔍 왜 1등이 바뀌었는가? (상세 요인 분석)")
st.markdown("2번 그래프(점유율)는 **물량 1위(기존 강자)**를, 나머지 그래프는 **영향력 1위(신흥 강자)**의 데이터를 보여줍니다.")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("**① 업태 밀도 (시장 규모)**")
    st.caption("해당 지역 업종의 활성화 정도")
    # 업태 밀도: 지역 특성이므로 영향력 1위 데이터 사용 (지역은 같음)
    fig_dens = px.bar(top_influence, x='시도', y='Category_Density', color='Category_Density', color_continuous_scale='Oranges', text_auto='.1f')
    fig_dens.update_layout(showlegend=False, height=250, coloraxis_showscale=False)
    st.plotly_chart(fig_dens, use_container_width=True)

with c2:
    # -------------------------------------------------------------------------
    # [수정 완료] 요청하신 대로 '단순 점유율 1위(top_market)' 데이터 사용
    # -------------------------------------------------------------------------
    st.markdown("**② 시장 점유율 (물량 1위)**")
    st.caption("❗ **단순 매장수 1등 브랜드**의 점유율")
    
    fig_share = px.bar(top_market, x='시도', y='Real_Market_Share_Pct', color='브랜드', text_auto='.1f')
    fig_share.update_layout(showlegend=False, height=250, yaxis_range=[0, 100])
    st.plotly_chart(fig_share, use_container_width=True)

with c3:
    st.markdown("**③ 지역 소득 (구매력)**")
    st.caption("영향력 1위 브랜드가 위치한 지역 소득")
    fig_inc = px.bar(top_influence, x='시도', y='Income_Index', color='Income_Index', color_continuous_scale='Greens', text_auto='.2f')
    fig_inc.add_hline(y=1.0, line_dash="dash", line_color="red")
    fig_inc.update_layout(showlegend=False, height=250, coloraxis_showscale=False)
    st.plotly_chart(fig_inc, use_container_width=True)

with c4:
    st.markdown("**④ 성장성 (역전의 열쇠)**")
    st.caption("🚀 **영향력 1위 브랜드**의 성장률")
    
    colors = ['#2E86C1' if x >= 0 else '#E74C3C' for x in top_influence['Growth_Rate']]
    fig_grow = go.Figure(go.Bar(
        x=top_influence['시도'], y=top_influence['Growth_Rate'],
        marker_color=colors, text=top_influence['Growth_Rate'],
        texttemplate='%{text:.1%}', textposition='outside'
    ))
    g_max = max(top_influence['Growth_Rate'].max(), 0.1)
    g_min = min(top_influence['Growth_Rate'].min(), -0.1)
    st.plotly_chart(fig_grow.update_layout(height=250, yaxis_range=[g_min*1.2, g_max*1.2], showlegend=False), use_container_width=True)

# -----------------------------------------------------------------------------
# 7. 데이터 비교 테이블
# -----------------------------------------------------------------------------
with st.expander("📋 [비교] 물량 1위 vs 영향력 1위 상세 데이터"):
    comp_df = pd.merge(
        top_market[['시도', '브랜드', 'Real_Market_Share_Pct']].rename(columns={'브랜드': '물량 1위', 'Real_Market_Share_Pct': '물량_점유율(%)'}),
        top_influence[['시도', '브랜드', 'Influence_Share_Pct', 'Growth_Rate']].rename(columns={'브랜드': '영향력 1위', 'Influence_Share_Pct': '영향력_점유율(%)', 'Growth_Rate': '영향력_성장률'}),
        on='시도'
    )
    
    comp_df['상태'] = comp_df.apply(lambda x: '⚡ 역전됨' if x['물량 1위'] != x['영향력 1위'] else '-', axis=1)
    
    st.dataframe(
        comp_df.style.format({
            '물량_점유율(%)': '{:.1f}%',
            '영향력_점유율(%)': '{:.1f}%',
            '영향력_성장률': '{:.1%}'
        }).applymap(lambda v: 'background-color: #ffe6e6; font-weight: bold;' if v == '⚡ 역전됨' else '', subset=['상태']),
        use_container_width=True
    )