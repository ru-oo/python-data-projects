import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(layout="wide", page_title="브랜드 성공 요인 분석")

st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: 800; color: #1E3A8A; text-align: center; margin-bottom: 10px; }
    .sub-title { font-size: 1.2rem; color: #555; text-align: center; margin-bottom: 40px; }
    .insight-box { background-color: #f8fafc; padding: 20px; border-radius: 10px; border-left: 5px solid #3b82f6; margin-bottom: 20px; }
    </style>
    <div class="main-title">🎯 브랜드별 '1등의 비밀' 분석</div>
    <div class="sub-title">인구 통계학적 상관관계를 통한 브랜드 포지셔닝 도출</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 데이터 로드 및 전처리
# ---------------------------------------------------------
@st.cache_data
def load_and_calc_corr():
    # 데이터 로드
    try:
        df = pd.read_csv('franchise_analysis_corrected.csv')
    except:
        return pd.DataFrame(), pd.DataFrame()

    # 2023년 데이터 필터링
    df_2023 = df[df['연도'] == 2023].copy()
    
    # 파생변수 생성: 10대 이하 비율 (남+여) -> '가족/학군' 지표
    if '비율_남자_0~19세' in df_2023.columns:
        df_2023['비율_0~19세'] = df_2023['비율_남자_0~19세'] + df_2023['비율_여자_0~19세']
    
    # 분석할 요인 정의
    factors = {
        '비율_0~19세': '가족/학생 (Under 19)',
        '비율_여자_20~39세': '2030 여성 (Trend)',
        '1인가구_40세이하_비율': '청년 1인가구 (Single)',
        '1인당지역총소득': '소득 수준 (Income)'
    }
    
    # 브랜드별 상관계수 계산
    brands = df_2023['브랜드'].unique()
    corr_data = []
    
    for brand in brands:
        df_b = df_2023[df_2023['브랜드'] == brand]
        if len(df_b) < 5: continue # 데이터 부족 제외
        
        row = {'Brand': brand, 'Category': df_b['업태 구분명'].iloc[0]}
        for col, label in factors.items():
            if col in df_b.columns:
                # '인구1만명당_매장수'와 각 요인의 상관계수
                corr = df_b['인구1만명당_매장수'].corr(df_b[col])
                row[label] = corr
        corr_data.append(row)
        
    df_corr = pd.DataFrame(corr_data)
    return df_2023, df_corr

df_raw, df_corr = load_and_calc_corr()

# ---------------------------------------------------------
# 3. 메인: 브랜드 포지셔닝 맵 (핵심 시각화)
# ---------------------------------------------------------
if not df_corr.empty:
    st.subheader("1️⃣ 브랜드 포지셔닝 맵: 누가 누구를 타겟하는가?")
    st.markdown("X축은 **가족/학생(10대)**, Y축은 **젊은 여성(2030)**과의 상관관계입니다. 브랜드가 어디에 위치하는지 보세요.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Scatter Plot
        fig_map = px.scatter(
            df_corr,
            x='가족/학생 (Under 19)',
            y='2030 여성 (Trend)',
            color='Category',
            text='Brand',
            size_max=20,
            hover_data=['소득 수준 (Income)'],
            title="인구 특성에 따른 브랜드 포지셔닝 (2023)",
            height=600
        )
        
        # 기준선 (0,0)
        fig_map.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        fig_map.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        # 사분면 라벨링 (Annotations)
        fig_map.add_annotation(x=0.8, y=0.8, text="🔥 핫플레이스형<br>(스타벅스 구역)", showarrow=False, font=dict(color="red"))
        fig_map.add_annotation(x=0.8, y=-0.5, text="👨‍👩‍👧‍👦 주거밀착형<br>(맘스터치 구역)", showarrow=False, font=dict(color="blue"))
        
        fig_map.update_traces(textposition='top center', marker=dict(size=15, line=dict(width=2, color='DarkSlateGrey')))
        st.plotly_chart(fig_map, use_container_width=True)

    with col2:
        st.markdown("""
        #### 🧭 해석 가이드
        
        **↗️ 1사분면 (우상단)**
        * **트렌드 + 가족 모두 잡음**
        * 대형 프랜차이즈의 이상향
        
        **↖️ 2사분면 (좌상단) - "Trend"**
        * **2030 여성** 집중 공략
        * 오피스, 번화가 상권
        * 대표: **스타벅스, 투썸**
        
        **↘️ 4사분면 (우하단) - "Family"**
        * **10대/가족** 집중 공략
        * 아파트 단지, 학원가 상권
        * 대표: **맘스터치, 롯데리아, BBQ**
        """)

    st.divider()

    # ---------------------------------------------------------
    # 4. 상관관계 히트맵 (전체 요약)
    # ---------------------------------------------------------
    st.subheader("2️⃣ 결정적 요인 분석표 (Correlation Matrix)")
    st.markdown("붉은색(1.0)일수록 해당 요인이 브랜드 입점에 **결정적 영향**을 미친다는 뜻입니다.")
    
    # 히트맵용 데이터 변환
    hm_data = df_corr.set_index('Brand')[['2030 여성 (Trend)', '가족/학생 (Under 19)', '청년 1인가구 (Single)', '소득 수준 (Income)']]
    
    fig_hm = px.imshow(
        hm_data,
        text_auto='.2f',
        aspect="auto",
        color_continuous_scale='RdBu_r', # Red=Positive, Blue=Negative
        origin='lower',
        title="브랜드별 입점 결정 요인 상관계수"
    )
    st.plotly_chart(fig_hm, use_container_width=True)

    st.divider()

    # ---------------------------------------------------------
    # 5. 증거 그래프 (회귀분석)
    # ---------------------------------------------------------
    st.subheader("3️⃣ 증거 확인: 진짜 관계가 있는가?")
    
    c1, c2 = st.columns(2)
    with c1:
        target_brand = st.selectbox("분석할 브랜드 선택", df_corr['Brand'].unique(), index=0)
    with c2:
        target_factor = st.selectbox("확인할 인구 지표 선택", [
            '비율_여자_20~39세', '비율_0~19세', '1인당지역총소득', '1인가구_40세이하_비율'
        ])

    # 선택한 브랜드의 데이터 추출
    df_detail = df_raw[df_raw['브랜드'] == target_brand]
    
    # 상관계수 확인
    corr_val = df_detail['인구1만명당_매장수'].corr(df_detail[target_factor])
    
    fig_reg = px.scatter(
        df_detail,
        x=target_factor,
        y='인구1만명당_매장수',
        hover_data=['시도'],
        trendline='ols', # 회귀선
        title=f"[{target_brand}] 매장 밀도 vs {target_factor} (Corr: {corr_val:.2f})",
        labels={'인구1만명당_매장수': '인구 1만명당 매장 수'}
    )
    st.plotly_chart(fig_reg, use_container_width=True)
    
    if corr_val > 0.5:
        st.success(f"✅ **뚜렷한 양의 상관관계!** {target_brand} 매장은 '{target_factor}'가 높은 지역에 집중되어 있습니다.")
    elif corr_val < -0.5:
        st.error(f"🔻 **음의 상관관계.** {target_brand}는 이 지표가 낮은 지역을 선호합니다.")
    else:
        st.warning(f"⚠️ **관계가 약함.** 이 지표는 {target_brand}의 입점과 큰 관련이 없습니다.")

else:
    st.error("데이터가 없습니다.")