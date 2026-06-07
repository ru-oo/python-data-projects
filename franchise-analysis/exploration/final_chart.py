import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="프랜차이즈 정밀 점유율 분석",
    page_icon="🎯",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리
# -----------------------------------------------------------------------------
@st.cache_data
def load_data(filename):
    df = pd.read_csv(filename)
    
    # 0으로 나누기 방지
    df['영업매장수_safe'] = df['영업매장수'].replace(0, 1)
    
    # -------------------------------------------------------------------------
    # [수정 완료] 연도별/지역별/업태별 진짜 총합 계산
    # 반드시 '연도'를 포함해야 해당 해의 총합이 구해집니다.
    # -------------------------------------------------------------------------
    df['Real_Category_Total'] = df.groupby(['연도', '시도', '업태 구분명'])['영업매장수'].transform('sum')
    
    # 1) 진짜 시장 점유율 (%) 계산 (이젠 합치면 100%가 됩니다!)
    df['Real_Market_Share_Pct'] = (df['영업매장수'] / df['Real_Category_Total']) * 100
    
    # 2) 성장률 & 활력 지수
    df['Growth_Rate'] = (df['신규매장수'] - df['폐업매장수']) / df['영업매장수_safe']
    df['Health_Factor'] = (1 + df['Growth_Rate']).apply(lambda x: max(x, 0.1))
    
    # 3) 최종 영향력 점수 (Raw Score)
    # 공식: 밀도 * 시장점유율(%) * 성장성
    df['Final_Score'] = df['인구1만명당_매장수'] * df['Real_Market_Share_Pct'] * df['Health_Factor']
    
    return df

try:
    df_all = load_data('franchise_analysis_corrected.csv')
except FileNotFoundError:
    st.error("❌ 'franchise_analysis_corrected.csv' 파일을 찾을 수 없습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바 컨트롤
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 분석 옵션")
years = sorted(df_all['연도'].unique(), reverse=True)
selected_year = st.sidebar.selectbox("연도 선택", years, index=0)

categories = sorted(df_all['업태 구분명'].unique())
selected_category = st.sidebar.selectbox("업태 선택", ["전체 (통합 1위)"] + categories)

# -----------------------------------------------------------------------------
# 4. 데이터 필터링 및 랭킹 산정
# -----------------------------------------------------------------------------
df_year = df_all[df_all['연도'] == selected_year].copy()

if selected_category != "전체 (통합 1위)":
    df_year = df_year[df_year['업태 구분명'] == selected_category].copy()

# 시각화용 점유율(Influence Share) 계산 
# (지역 내 1등 브랜드가 전체 영향력에서 차지하는 비중)
region_total_score = df_year.groupby('시도')['Final_Score'].transform('sum')
df_year['Influence_Share_Pct'] = (df_year['Final_Score'] / region_total_score) * 100

# 1위 추출 (영향력 점수 높은 순)
df_year = df_year.sort_values(by=['Influence_Share_Pct', '영업매장수'], ascending=[False, False])
top_brands = df_year.drop_duplicates(subset=['시도'], keep='first').sort_values(by='Influence_Share_Pct', ascending=False)

# 라벨 생성
def create_label(row):
    growth_pct = row['Growth_Rate'] * 100
    icon = "▲" if growth_pct > 0 else ("▼" if growth_pct < 0 else "-")
    return f"{row['브랜드']}<br>({icon}{growth_pct:.1f}%)"

top_brands['Label'] = top_brands.apply(create_label, axis=1)

# -----------------------------------------------------------------------------
# 5. 메인 대시보드
# -----------------------------------------------------------------------------
st.title(f"🎯 {selected_year}년 지역별 1위 브랜드 (정밀 점유율 반영)")
st.markdown("""
**수정 사항 반영됨**: 이제 시장 점유율 분모가 **해당 연도**의 매장 수 합계로 정확히 계산됩니다.
* **공식**: `밀도` × `시장점유율(%)` × `성장성`
* **시장점유율(%)**: 해당 연도, 해당 지역, 해당 업태 내에서의 실제 매장 비중
""")

# [메인 차트]
st.subheader("🗺️ 지역별 영향력 1위 현황")
st.caption("지역 내 프랜차이즈 영향력 총량 중 1위 브랜드가 차지하는 비중")
fig_main = px.bar(
    top_brands, x='시도', y='Influence_Share_Pct', 
    color='브랜드', text='Label',
    hover_data=['업태 구분명', 'Real_Market_Share_Pct', 'Growth_Rate'],
    height=600
)
fig_main.update_traces(textposition='outside', textfont_size=13, cliponaxis=False)
fig_main.update_layout(
    xaxis_title="지역", yaxis_title="종합 영향력 점유율 (%)",
    yaxis_range=[0, top_brands['Influence_Share_Pct'].max() * 1.25],
    margin=dict(t=60)
)
st.plotly_chart(fig_main, use_container_width=True)

# [상세 지표 분석]
st.divider()
st.subheader("📊 1위 결정 요인 정밀 분석")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**1️⃣ 접근성 (밀도)**")
    st.caption("인구 1만명당 매장 수")
    st.plotly_chart(px.bar(top_brands, x='시도', y='인구1만명당_매장수', color='브랜드', text_auto='.2f').update_layout(showlegend=False, height=300), use_container_width=True)

with c2:
    st.markdown("**2️⃣ 시장 점유율 (Market Share)**")
    st.caption("실제 업태 내 매장 점유율 (정상 반영됨)")
    # 점유율을 %로 표시
    fig_share = px.bar(top_brands, x='시도', y='Real_Market_Share_Pct', color='브랜드')
    fig_share.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
    fig_share.update_layout(showlegend=False, height=300, yaxis_range=[0, 100])
    st.plotly_chart(fig_share, use_container_width=True)

with c3:
    st.markdown("**3️⃣ 활력 (성장률)**")
    st.caption("전년 대비 매장 증감률")
    colors = ['#2E86C1' if x >= 0 else '#E74C3C' for x in top_brands['Growth_Rate']]
    fig_c = go.Figure(go.Bar(
        x=top_brands['시도'], y=top_brands['Growth_Rate'],
        marker_color=colors, text=top_brands['Growth_Rate'],
        texttemplate='%{text:.1%}', textposition='outside'
    ))
    g_max = max(top_brands['Growth_Rate'].max(), 0.1)
    g_min = min(top_brands['Growth_Rate'].min(), -0.1)
    st.plotly_chart(fig_c.update_layout(height=300, yaxis_range=[g_min*1.2, g_max*1.2], showlegend=False), use_container_width=True)

# [데이터 테이블]
with st.expander("📋 데이터 상세 보기 (수치 검증용)"):
    st.dataframe(
        top_brands[['시도', '업태 구분명', '브랜드', 'Influence_Share_Pct', 'Real_Market_Share_Pct', 'Growth_Rate', '영업매장수', 'Real_Category_Total']]
        .rename(columns={'Real_Market_Share_Pct': '실제점유율(%)', 'Real_Category_Total': '연도별_업태총매장수'})
        .style.format({'Influence_Share_Pct': '{:.1f}%', '실제점유율(%)': '{:.1f}%', 'Growth_Rate': '{:.1%}'}),
        use_container_width=True
    )