import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="프랜차이즈 진짜 점유율 분석 대시보드",
    page_icon="📊",
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
    
    # 1) 순성장률 (Growth Rate): (신규 - 폐업) / 전체 매장
    df['Growth_Rate'] = (df['신규매장수'] - df['폐업매장수']) / df['영업매장수_safe']
    
    # 2) 활력 지수 (Health Factor): 1 + 성장률 (최소 0.1)
    df['Health_Factor'] = (1 + df['Growth_Rate']).apply(lambda x: max(x, 0.1))
    
    # 3) 진짜 점유율 점수 (Raw Score)
    df['Raw_Score'] = df['인구1만명당_매장수'] * df['주요4사_내_비중'] * df['Health_Factor']
    
    return df

try:
    df_all = load_data('franchise_analysis_corrected.csv')
except FileNotFoundError:
    st.error("❌ 'franchise_analysis_corrected.csv' 파일을 찾을 수 없습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바 컨트롤 (연도 및 업태 선택)
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 분석 옵션")

# 연도 선택
years = sorted(df_all['연도'].unique(), reverse=True)
selected_year = st.sidebar.selectbox("연도 선택 (Year)", years, index=0)

# 업태 선택 (전체 + 개별 업태)
categories = sorted(df_all['업태 구분명'].unique())
selected_category = st.sidebar.selectbox("업태 선택 (Category)", ["전체 (통합 1위)"] + categories)

# -----------------------------------------------------------------------------
# 4. 데이터 필터링 및 점유율 계산
# -----------------------------------------------------------------------------
# 1) 연도 필터링
df_year = df_all[df_all['연도'] == selected_year].copy()

# 2) 업태 필터링 (선택 시 해당 업태만 남김)
if selected_category != "전체 (통합 1위)":
    df_year = df_year[df_year['업태 구분명'] == selected_category].copy()

# 3) 진짜 점유율 % (True Share Percentage) 계산
# 주의: 업태를 필터링했다면, 그 업태 내에서의 비중이 계산됨 (예: 치킨 시장 내 점유율)
region_total_score = df_year.groupby('시도')['Raw_Score'].transform('sum')
df_year['True_Share_Pct'] = (df_year['Raw_Score'] / region_total_score) * 100

# 4) 시도별 1위 추출
# 점유율 높은 순 -> 매장수 많은 순 정렬
df_year = df_year.sort_values(by=['True_Share_Pct', '영업매장수'], ascending=[False, False])
top_brands = df_year.drop_duplicates(subset=['시도'], keep='first').sort_values(by='True_Share_Pct', ascending=False)

# 5) 시각화용 라벨 생성 (브랜드명 + 성장률)
def create_label(row):
    growth_pct = row['Growth_Rate'] * 100
    icon = "▲" if growth_pct > 0 else ("▼" if growth_pct < 0 else "-")
    return f"{row['브랜드']}<br>({icon}{growth_pct:.1f}%)"

top_brands['Label'] = top_brands.apply(create_label, axis=1)

# -----------------------------------------------------------------------------
# 5. 메인 대시보드 UI
# -----------------------------------------------------------------------------
title_suffix = "통합" if selected_category == "전체 (통합 1위)" else selected_category
st.title(f"🏆 {selected_year}년 {title_suffix} 부문 지역별 1위 브랜드")
st.markdown(f"""
선택하신 **{title_suffix}** 시장에서 **접근성, 지배력, 성장성**을 모두 고려했을 때 가장 강력한 브랜드입니다.
그래프의 숫자는 해당 브랜드의 **성장률(증감률)**을 나타냅니다.
""")

# --- [섹션 1] 메인 차트 ---
st.subheader(f"🗺️ 지역별 1위 브랜드와 성장률")

# 색상 팔레트 설정
fig_main = px.bar(
    top_brands,
    x='시도',
    y='True_Share_Pct',
    color='브랜드',
    text='Label', # 수정됨: 성장률이 포함된 라벨 사용
    hover_data=['업태 구분명', '영업매장수', 'Growth_Rate', '인구1만명당_매장수'],
    height=550
)

fig_main.update_traces(
    textposition='outside', # 막대 위로 텍스트 올리기 (잘 보이게)
    textfont_size=12,
    cliponaxis=False # 텍스트가 차트 밖으로 나가도 잘리지 않게 함
)

# Y축 범위 조정 (텍스트 공간 확보)
y_max = top_brands['True_Share_Pct'].max() * 1.2
fig_main.update_layout(
    xaxis_title="지역",
    yaxis_title="영향력 점유율 (%)",
    yaxis_range=[0, y_max],
    showlegend=True,
    margin=dict(t=50, b=50) # 여백 확보
)
st.plotly_chart(fig_main, use_container_width=True)

# --- [섹션 2] 상세 분석 (3분할 차트) ---
st.divider()
st.subheader(f"📊 {title_suffix} 부문 1위 결정 요인 분석")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 1️⃣ 접근성 (밀도)")
    fig_a = px.bar(top_brands, x='시도', y='인구1만명당_매장수', color='브랜드', text_auto='.2f')
    fig_a.update_layout(showlegend=False, height=300, title="인구 1만명당 매장 수")
    st.plotly_chart(fig_a, use_container_width=True)

with col2:
    st.markdown("#### 2️⃣ 지배력 (점유율)")
    fig_b = px.bar(top_brands, x='시도', y='주요4사_내_비중', color='브랜드', text_auto='.1f')
    fig_b.update_layout(showlegend=False, height=300, title="주요 4사 내 비중 (%)", yaxis_range=[0, 100])
    st.plotly_chart(fig_b, use_container_width=True)

with col3:
    st.markdown("#### 3️⃣ 활력 (성장률)")
    # 색상: 성장(파랑), 감소(빨강)
    colors = ['#2E86C1' if x >= 0 else '#E74C3C' for x in top_brands['Growth_Rate']]
    
    fig_c = go.Figure()
    fig_c.add_trace(go.Bar(
        x=top_brands['시도'],
        y=top_brands['Growth_Rate'],
        marker_color=colors,
        text=top_brands['Growth_Rate'],
        texttemplate='%{text:.1%}',
        textposition='outside' # 막대 밖 표시
    ))
    
    # 성장률 차트 범위 최적화
    g_max = max(top_brands['Growth_Rate'].max(), 0.1)
    g_min = min(top_brands['Growth_Rate'].min(), -0.1)
    
    fig_c.update_layout(
        title="전년 대비 매장 증감률",
        height=300,
        yaxis_tickformat='.0%',
        yaxis_range=[g_min * 1.2, g_max * 1.2],
        showlegend=False
    )
    st.plotly_chart(fig_c, use_container_width=True)

# --- [섹션 3] 데이터 테이블 ---
with st.expander("📋 전체 데이터 표로 보기"):
    st.dataframe(
        top_brands[['시도', '업태 구분명', '브랜드', 'True_Share_Pct', 'Growth_Rate', '영업매장수', '인구1만명당_매장수']]
        .style.format({
            'True_Share_Pct': '{:.1f}%',
            'Growth_Rate': '{:.1%}',
            '인구1만명당_매장수': '{:.4f}개'
        }),
        use_container_width=True
    )