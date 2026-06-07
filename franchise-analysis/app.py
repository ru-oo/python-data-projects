import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from pyproj import Transformer
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression

# -----------------------------------------------------------------------------
# 1. 페이지 설정 (통합)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="프랜차이즈 통합 분석 시스템",
    page_icon="🚀",
    layout="wide"
)

# [스타일] CSS 추가 (다크모드 완벽 대응)
st.markdown("""
    <style>
    /* 카드 디자인: 다크모드/라이트모드 모두 가독성 확보 */
    .quad_card { 
        flex: 1; padding: 20px; border-radius: 12px; color: white; min-height: 220px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); display: flex; flex-direction: column; margin-bottom: 10px;
    }
    .q_blue { background-color: #2563EB; }   /* 기회 */
    .q_green { background-color: #059669; }  /* 선도 */
    .q_red { background-color: #DC2626; }    /* 과열 */
    .q_gray { background-color: #4B5563; }   /* 열위 */
    
    .card-title { font-size: 1.4rem; font-weight: 800; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 5px; }
    .card-list { font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; }
    .card-desc { font-size: 0.95rem; line-height: 1.5; opacity: 0.95; }
    
    /* 섹션 헤더 디자인 */
    .section-header { 
        font-size: 1.8rem; font-weight: 700; 
        margin-top: 20px; margin-bottom: 20px; 
        border-bottom: 2px solid #888; padding-bottom: 10px; 
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리
# -----------------------------------------------------------------------------
@st.cache_data
def load_raw_data():
    try:
        df = pd.read_csv('franchise_analysis_corrected.csv')
        df['영업매장수_safe'] = df['영업매장수'].replace(0, 1)
        return df
    except FileNotFoundError:
        st.error("❌ 'franchise_analysis_corrected.csv' 파일을 찾을 수 없습니다.")
        return pd.DataFrame()

@st.cache_data
def load_coord_data():
    try:
        df_points = pd.read_csv('merged_result.csv')
        df_points['허가날짜'] = pd.to_datetime(df_points['허가날짜'], errors='coerce')
        df_points['폐업날짜'] = pd.to_datetime(df_points['폐업날짜'], errors='coerce')
        
        def parse_coord(c):
            parts = str(c).replace('"', '').split(',')
            return float(parts[0]), float(parts[1])
        
        coords = df_points['좌표'].dropna().apply(parse_coord)
        if not coords.empty:
            transformer = Transformer.from_crs("epsg:5174", "epsg:4326", always_xy=True)
            lon, lat = transformer.transform([c[0] for c in coords], [c[1] for c in coords])
            
            df_points = df_points.dropna(subset=['좌표']).copy()
            df_points['lon'] = lon
            df_points['lat'] = lat
        return df_points
    except Exception:
        return pd.DataFrame()

# [탭 1 전용] 전처리
def preprocess_for_tab1(df):
    df_stat = df.copy()
    national_income_avg = df_stat['1인당지역총소득'].mean()
    
    df_stat['Category_Total_Store'] = df_stat.groupby(['연도', '시도', '업태 구분명'])['영업매장수'].transform('sum')
    df_stat['Category_Density'] = (df_stat['Category_Total_Store'] / df_stat['전체_총인구수']) * 10000
    df_stat['Real_Market_Share_Pct'] = (df_stat['영업매장수'] / df_stat['Category_Total_Store']) * 100
    df_stat['Income_Index'] = df_stat['1인당지역총소득'] / national_income_avg
    df_stat['Growth_Rate'] = (df_stat['신규매장수'] - df_stat['폐업매장수']) / df_stat['영업매장수_safe']
    
    growth_factor = (1 + df_stat['Growth_Rate'] * 3).apply(lambda x: max(x, 0.1))
    df_stat['Final_Score'] = (
        df_stat['Category_Density'] * df_stat['Real_Market_Share_Pct'] * df_stat['Income_Index'] * growth_factor
    )
    return df_stat, national_income_avg

# [탭 2 전용] 전처리
@st.cache_data
def preprocess_for_tab2_v3(df):
    df_app = df.copy()
    
    df_app['Category_Total'] = df_app.groupby(['연도', '시도', '업태 구분명'])['영업매장수'].transform('sum')
    df_app['Category_Density'] = (df_app['Category_Total'] / df_app['전체_총인구수']) * 10000
    df_app['Real_Market_Share_Pct'] = (df_app['영업매장수'] / df_app['Category_Total']) * 100
    
    avg_income = df_app.groupby('연도')['1인당지역총소득'].transform('mean')
    df_app['Income_Index'] = df_app['1인당지역총소득'] / avg_income
    
    df_app['Growth_Rate'] = (df_app['신규매장수'] - df_app['폐업매장수']) / df_app['영업매장수_safe']
    growth_factor = (1 + df_app['Growth_Rate'] * 3).apply(lambda x: max(x, 0.1))
    
    df_app['Final_Score'] = (
        df_app['Category_Density'] * df_app['Real_Market_Share_Pct'] * df_app['Income_Index'] * growth_factor
    )
    
    region_total = df_app.groupby(['연도', '시도', '업태 구분명'])['Final_Score'].transform('sum').replace(0, 1)
    df_app['Influence_Score'] = (df_app['Final_Score'] / region_total) * 100

    df_app['청년층(2030)'] = (df_app['남자_20~39세'] + df_app['여자_20~39세']) / df_app['전체_총인구수']
    df_app['중장년층(4050)'] = (df_app['남자_40~59세'] + df_app['여자_40~59세']) / df_app['전체_총인구수']
    df_app['노년층(60+)'] = (df_app['남자_60세이상'] + df_app['여자_60세이상']) / df_app['전체_총인구수']
    
    df_app.rename(columns={
        '1인가구_40세이하_비율': '청년1인가구',
        '1인당지역총소득': '지역소득'
    }, inplace=True)
    
    numeric_cols = df_app.select_dtypes(include=[np.number]).columns
    df_app[numeric_cols] = df_app[numeric_cols].fillna(0)
    
    return df_app

# [탭 3 전용] 전처리
def preprocess_for_tab3(df):
    df_t3 = df.copy()
    
    if '비율_남자_20~39세' not in df_t3.columns:
        df_t3['2030대_비율'] = (df_t3['남자_20~39세'] + df_t3['여자_20~39세']) / df_t3['전체_총인구수']
        df_t3['405010대_비율'] = (df_t3['남자_40~59세'] + df_t3['여자_40~59세'] + df_t3['남자_0~19세'] + df_t3['여자_0~19세']) / df_t3['전체_총인구수']
        df_t3['60대이후_비율'] = (df_t3['남자_60세이상'] + df_t3['여자_60세이상']) / df_t3['전체_총인구수']
    else:
        df_t3['2030대_비율'] = df_t3['비율_남자_20~39세'] + df_t3['비율_여자_20~39세']
        df_t3['405010대_비율'] = df_t3[['비율_남자_40~59세', '비율_여자_40~59세', '비율_남자_0~19세', '비율_여자_0~19세']].sum(axis=1)
        df_t3['60대이후_비율'] = df_t3.get('비율_남자_60세이상', 0) + df_t3.get('비율_여자_60세이상', 0)

    df_t3['폐업률'] = (df_t3['폐업매장수'] / df_t3['영업매장수'].replace(0, 1)) * 100

    df_t3['영업매장수_safe'] = df_t3['영업매장수'].replace(0, 1)
    df_t3['Category_Total_Store'] = df_t3.groupby(['연도', '시도', '업태 구분명'])['영업매장수'].transform('sum')
    df_t3['Category_Density'] = (df_t3['Category_Total_Store'] / df_t3['전체_총인구수']) * 10000
    df_t3['Real_Market_Share_Pct'] = (df_t3['영업매장수'] / df_t3['Category_Total_Store']) * 100
    df_t3['Income_Index'] = df_t3['1인당지역총소득'] / df_t3['1인당지역총소득'].mean()
    df_t3['Growth_Rate'] = (df_t3['신규매장수'] - df_t3['폐업매장수']) / df_t3['영업매장수_safe']
    growth_factor = (1 + df_t3['Growth_Rate'] * 3).apply(lambda x: max(x, 0.1))
    
    df_t3['Final_Score_Value'] = df_t3['Category_Density'] * df_t3['Real_Market_Share_Pct'] * df_t3['Income_Index'] * growth_factor
    
    analysis_cols = ['2030대_비율', '405010대_비율', '60대이후_비율', '1인당지역총소득', '1인가구_40세이하_비율', '폐업률']
    valid_cols = [c for c in analysis_cols if c in df_t3.columns]
    
    if valid_cols:
        temp_scaler = MinMaxScaler()
        norm_data = pd.DataFrame(temp_scaler.fit_transform(df_t3[valid_cols].fillna(0)), columns=valid_cols)
        if '폐업률' in norm_data.columns:
            norm_data['폐업률'] = 1.0 - norm_data['폐업률'] 
        df_t3['종합_잠재력_지수'] = norm_data.mean(axis=1) * 100
    else:
        df_t3['종합_잠재력_지수'] = 0

    return df_t3

# 메인 데이터 로드
raw_df = load_raw_data()
coord_df = load_coord_data()

if raw_df.empty:
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바
# -----------------------------------------------------------------------------
st.sidebar.title("🎛️ 분석 옵션")

# 공통 필터
st.sidebar.subheader("1. 공통 설정")
years = sorted(raw_df['연도'].unique(), reverse=True)
selected_year = st.sidebar.selectbox("연도 선택", years, index=0)

categories = sorted(raw_df['업태 구분명'].unique())
selected_category = st.sidebar.selectbox("업태 선택", ["전체 (통합 1위)"] + categories)

st.sidebar.markdown("---")

# 탭 1 옵션
st.sidebar.subheader("2. 지도 옵션 (탭1)")
regions = {
    "전국": {"lat": 36.0, "lon": 127.5, "zoom": 6},
    "서울": {"lat": 37.56, "lon": 126.97, "zoom": 9},  
    "경기": {"lat": 37.41, "lon": 127.51, "zoom": 7.5},
    "대구": {"lat": 35.87, "lon": 128.60, "zoom": 9},
    "부산": {"lat": 35.17, "lon": 129.07, "zoom": 9}
}
selected_region = st.sidebar.selectbox("지도 중심점 이동", list(regions.keys()))

st.sidebar.markdown("---")

# 탭 2 옵션
st.sidebar.subheader("3. 브랜드 옵션 (탭2)")
selected_brand_tab2 = None
if selected_category != "전체 (통합 1위)":
    temp_df = raw_df[(raw_df['연도'] == selected_year) & (raw_df['업태 구분명'] == selected_category)]
    if not temp_df.empty:
        top_brands = temp_df.groupby('브랜드')['영업매장수'].sum().sort_values(ascending=False).head(20).index.tolist()
        selected_brand_tab2 = st.sidebar.selectbox("분석 대상 브랜드", top_brands)
    else:
        st.sidebar.warning("해당 조건의 데이터가 없습니다.")
else:
    st.sidebar.info("구체적인 업태를 선택하면 브랜드 목록이 표시됩니다.")

# -----------------------------------------------------------------------------
# 4. 메인 탭 구성
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 지배력 & 밀도 분석", "🎤 성과 요인 심층 분석", "🎯 시장 기회 매트릭스"])

# =============================================================================
# [TAB 1] 지배력 & 밀도 분석
# =============================================================================
with tab1:
    df_all_stat, income_avg_val = preprocess_for_tab1(raw_df)
    
    df_year = df_all_stat[df_all_stat['연도'] == selected_year].copy()
    if selected_category != "전체 (통합 1위)":
        df_year = df_year[df_year['업태 구분명'] == selected_category].copy()

    region_total_score = df_year.groupby('시도')['Final_Score'].transform('sum')
    df_year['Influence_Share_Pct'] = (df_year['Final_Score'] / region_total_score) * 100

    top_market = df_year.sort_values(by=['Real_Market_Share_Pct'], ascending=False).drop_duplicates('시도')
    top_influence = df_year.sort_values(by=['Influence_Share_Pct'], ascending=False).drop_duplicates('시도')

    target_date = pd.Timestamp(f"{selected_year}-12-31")
    if not coord_df.empty:
        df_map_filtered = coord_df[
            (coord_df['허가날짜'] <= target_date) & 
            ((coord_df['폐업날짜'] > target_date) | (coord_df['폐업날짜'].isnull()))
        ].copy()
        if selected_category != "전체 (통합 1위)":
            df_map_filtered = df_map_filtered[df_map_filtered['업태 구분명'] == selected_category]
    else:
        df_map_filtered = pd.DataFrame()

    st.title(f" {selected_year}년 {selected_category} 점유율 분석")
    st.subheader("지역별 매장 밀집도")
    
    if not df_map_filtered.empty:
        view_info = regions[selected_region]
        view_state = pdk.ViewState(latitude=view_info["lat"], longitude=view_info["lon"], zoom=view_info["zoom"], pitch=45)

        layer = pdk.Layer(
            "HexagonLayer",
            data=df_map_filtered,
            get_position=["lon", "lat"],
            radius=400,
            elevation_scale=30,
            elevation_range=[0, 3000],
            extruded=True,
            pickable=True,
            auto_highlight=True,
            color_range=[[255, 255, 178], [254, 217, 118], [254, 178, 76], [253, 141, 60], [240, 59, 32], [189, 0, 38]]
        )
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "매장 밀집 구역"}))
    else:
        st.warning("지도 데이터가 없거나 필터링된 결과가 없습니다.")

    st.divider()

    st.subheader("1등 분석 지표")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**① 업태 밀도**")
        fig1 = px.bar(top_influence, x='시도', y='Category_Density', color='Category_Density', color_continuous_scale='YlOrBr', height=280, labels={'Category_Density': '업태 밀도'})
        fig1.update_layout(showlegend=False, coloraxis_showscale=False, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        st.markdown("**② 시장 규모 (물량)**")
        fig2 = px.bar(top_market, x='시도', y='Real_Market_Share_Pct', color='브랜드', height=280, labels={'Real_Market_Share_Pct': '시장 점유율(%)'})
        fig2.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig2, use_container_width=True)
    with c3:
        st.markdown("**③ 지역 소득 (구매력)**")
        fig3 = px.bar(top_influence, x='시도', y='1인당지역총소득', color='1인당지역총소득', color_continuous_scale='Greens', height=280, labels={'1인당지역총소득': '지역 소득'})
        fig3.add_hline(y=income_avg_val, line_dash="dash", line_color="#EF4444", annotation_text="전국 평균", annotation_position="top right")
        fig3.update_layout(showlegend=False, coloraxis_showscale=False, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig3, use_container_width=True)
    with c4:
        st.markdown("**④ 성장성**")
        colors = ['#3B82F6' if x >= 0 else '#EF4444' for x in top_influence['Growth_Rate']]
        fig4 = go.Figure(go.Bar(x=top_influence['시도'], y=top_influence['Growth_Rate'], marker_color=colors))
        fig4.update_layout(height=280, showlegend=False, margin=dict(t=10, b=10, l=10, r=10), yaxis_title="성장률")
        st.plotly_chart(fig4, use_container_width=True)

    st.divider()

    brand_colors = {
        "스타벅스": "#00704A", "이디야커피": "#263B96", "메가엠지씨커피": "#FFDD00",
        "컴포즈커피": "#FFCC00", "투썸플레이스": "#D92E36", "파리바게뜨": "#223E90",
        "뚜레쥬르": "#0B4619", "비비큐(BBQ)": "#DE9406", "교촌치킨": "#C49A6C", "BHC": "#F5C251"
    }

    # [수정] 라벨 텍스트 변경 (영향력 -> 점유율)
    top_influence['Label'] = top_influence.apply(lambda x: f"<b>{x['브랜드']}</b><br>{x['Influence_Share_Pct']:.1f}%", axis=1)
    fig_after = px.bar(top_influence, x='시도', y='Influence_Share_Pct', color='브랜드', text='Label', color_discrete_map=brand_colors)
    fig_after.update_traces(textposition='outside', textfont_size=12, cliponaxis=False)
    # [수정] Y축 제목 변경
    fig_after.update_layout(xaxis_title="지역", yaxis_title="점유율 (%)", height=550, yaxis=dict(range=[0, 80], dtick=5), margin=dict(t=100, b=50, l=50, r=50), showlegend=True)
    st.plotly_chart(fig_after, use_container_width=True)

    with st.expander("📋 물량 1위 vs 점유율 1위 데이터 시트"):
        comp_df = pd.merge(
            top_market[['시도', '브랜드', 'Real_Market_Share_Pct']].rename(columns={'브랜드': '물량 1위', 'Real_Market_Share_Pct': '물량 점유율'}),
            top_influence[['시도', '브랜드', 'Influence_Share_Pct', 'Growth_Rate']].rename(columns={'브랜드': '점유율 1위', 'Influence_Share_Pct': '점유율(질적)', 'Growth_Rate': '성장률'}),
            on='시도'
        )
        st.dataframe(comp_df.style.highlight_max(axis=0, subset=['점유율(질적)'], color='#e6f4ea'), use_container_width=True)

# =============================================================================
# [TAB 2] 성과 요인 심층 분석 (수정: 1등 지역 특성 우선 반영 로직 + 점유율 표기)
# =============================================================================
with tab2:
    if selected_category == "전체 (통합 1위)":
        st.warning("⚠️ 분석할 브랜드를 선택하려면 먼저 사이드바에서 '업태'를 선택해주세요.")
    elif selected_brand_tab2 is None:
        st.warning("⚠️ 사이드바에서 분석할 브랜드를 선택해주세요.")
    else:
        df_all_app = preprocess_for_tab2_v3(raw_df)
        df_target = df_all_app[(df_all_app['연도'] == selected_year) & (df_all_app['업태 구분명'] == selected_category)].copy()
        df_brand = df_target[df_target['브랜드'] == selected_brand_tab2].copy()

        if df_brand.empty:
            st.error("선택한 브랜드의 데이터가 없습니다.")
        else:
            analysis_cols = ['청년층(2030)', '중장년층(4050)', '노년층(60+)', '청년1인가구', '지역소득']
            corr_series = df_brand[analysis_cols + ['Influence_Score']].corr()['Influence_Score'].drop('Influence_Score').fillna(0)
            
            # 1. 양의 상관관계(성공 요인) 후보 추출
            positive_candidates = corr_series[corr_series > 0].sort_values(ascending=False).index.tolist()

            # 2. 1등 지역 데이터 추출
            top_region_row = df_brand.sort_values(by='Influence_Score', ascending=False).iloc[0]
            top_region_name = top_region_row['시도']

            # 3. [핵심 로직] 1등 지역이 평균보다 높은 '진짜' 성공 요인 찾기
            strongest_factor = None
            is_positive = False

            if positive_candidates:
                # 후보군 중에서 1등 지역 수치가 평균보다 높은 첫 번째 변수 선택
                for feature in positive_candidates:
                    if top_region_row[feature] > df_brand[feature].mean():
                        strongest_factor = feature
                        is_positive = True
                        break
                
                # 만약 양의 상관관계 변수 중 1등 지역이 잘하는 게 하나도 없다면?
                if strongest_factor is None:
                    strongest_factor = positive_candidates[0]
                    is_positive = True
            else:
                # 양의 상관관계가 아예 없는 경우
                strongest_factor = corr_series.abs().idxmax()
                is_positive = False
            
            st.title(f"🎤 {selected_brand_tab2} 성과 요인 심층 분석")
            st.markdown("""
            이 분석은 **현재의 성과(Where)**를 진단하고, 그 성과를 만들어낸 **핵심 성공 동인(Success Driver)**을 데이터로 증명합니다.
            """)
            st.divider()

            # --- [PART 1] 현황 진단 ---
            st.header("1. 전국 점유율 분포 (현황 진단)")
            col1, col2 = st.columns([1.5, 1])

            with col1:
                # [수정] Influence_Score -> 점유율 로 표기 변경
                fig_map = px.treemap(
                    df_brand, path=['시도'], values='Influence_Score',
                    color='Influence_Score', color_continuous_scale='Reds',
                    title=f"지역별 점유율 현황 ({selected_year})", # [수정] 제목 변경
                    hover_data=['영업매장수'],
                    labels={'Influence_Score': '점유율'} # [수정] 라벨 변경
                )
                fig_map.update_traces(textinfo="label+value+percent root")
                fig_map.update_layout(height=450, margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig_map, use_container_width=True)

            with col2:
                st.subheader("🏆 지역 Top 5")
                top_regions = df_brand.sort_values(by='Influence_Score', ascending=False).head(5)[['시도', 'Influence_Score', '영업매장수']]
                st.dataframe(
                    top_regions.rename(columns={'Influence_Score': '점유율'}).style.format({'점유율': '{:.1f}%', '영업매장수': '{:,}개'})
                    .background_gradient(subset=['점유율'], cmap='Reds'),
                    use_container_width=True, hide_index=True
                )
                st.info("ℹ️ **점유율(Influence Score)이란?** 밀도, 소득, 성장성을 종합하여 브랜드의 '실질적 지배력'을 0~100으로 환산한 지표입니다.")

            st.divider()

            # --- [PART 2] 성공 DNA 분석 ---
            st.header("2. 1등 지역의 성공 DNA (핵심 요인 분석)")
            if not df_brand.empty:
                # 비교를 위한 값 계산
                top_val = top_region_row[strongest_factor]
                avg_val = df_brand[strongest_factor].mean()
                is_higher_than_avg = top_val > avg_val

                st.markdown(f"""
                가장 성과가 좋은 **{top_region_name}** 지역은 어떤 인구 특성을 가지고 있을까요?  
                **상관관계가 높으면서 실제 1등 지역이 보유한 강점**을 분석했습니다.
                """)

                scaler = MinMaxScaler()
                X_factors = df_brand[analysis_cols].fillna(0)
                if len(X_factors) > 0:
                    scaled_vals = scaler.fit_transform(X_factors)
                    df_scaled = pd.DataFrame(scaled_vals, columns=analysis_cols, index=df_brand['시도'])

                    values_top = df_scaled.loc[top_region_name].tolist()
                    values_top += values_top[:1]
                    values_avg = df_scaled.mean().tolist()
                    values_avg += values_avg[:1]
                    categories_radar = analysis_cols + [analysis_cols[0]]

                    c1, c2 = st.columns([1.5, 1])

                    with c1:
                        fig_radar = go.Figure()
                        fig_radar.add_trace(go.Scatterpolar(r=values_avg, theta=categories_radar, fill='toself', name='전국 평균', line_color='gray', opacity=0.3))
                        fig_radar.add_trace(go.Scatterpolar(r=values_top, theta=categories_radar, fill='toself', name=f'1등 지역 ({top_region_name})', line_color='#E74C3C', marker=dict(size=8)))
                        fig_radar.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, 1], showticklabels=False)), 
                            showlegend=True, height=450, title="성공 요인 프로파일",
                            template="streamlit"
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)

                    with c2:
                        if is_positive and is_higher_than_avg:
                            explanation = f"데이터 분석 결과, **{selected_brand_tab2}**는 <b>{strongest_factor}</b> 비율이 높을수록 성과가 좋습니다."
                            key_insight = f"{strongest_factor} 우수 지역"
                            conclusion = f"따라서 <b>{top_region_name}</b> 지역이 1등인 이유는, 브랜드 성공의 핵심인 <b>{strongest_factor}</b> 경쟁력을 완벽하게 갖췄기 때문입니다."
                        elif is_positive and not is_higher_than_avg:
                            explanation = f"일반적으로는 <b>{strongest_factor}</b> 비율이 높을수록 유리하지만, 1등 지역은 예외적인 패턴을 보입니다."
                            key_insight = f"차별화된 성공 ({strongest_factor} 외 요인)"
                            conclusion = f"<b>{top_region_name}</b> 지역은 <b>{strongest_factor}</b> 수치는 낮지만, 압도적인 매장 운영 능력이나 입지 선점으로 1등을 차지한 **아웃라이어(Outlier)**입니다."
                        else:
                            explanation = f"이 브랜드는 <b>{strongest_factor}</b> 비율이 <span style='color:#FF4B4B;'>낮을수록</span> 오히려 성과가 좋은 경향을 보입니다."
                            key_insight = f"{strongest_factor} 최소화 지역"
                            conclusion = f"<b>{top_region_name}</b> 지역은 이러한 성공 패턴에 맞춰 <b>{strongest_factor}</b> 비율이 낮게 유지되고 있어 최적의 성과를 냈습니다."

                        st.markdown(f"""
                        <div style='background-color:#262730; color:white; padding:20px; border-radius:10px; border:1px solid #444;'>
                            <h3 style='color:#FF4B4B; margin-top:0;'>💡 데이터 해석 (Insight)</h3>
                            <p>핵심 변수: <b style='color:#FF4B4B; font-size:1.2em;'>{strongest_factor}</b></p>
                            <hr style='border-color:#555;'>
                            <p>{explanation}</p>
                            <p>{conclusion}</p>
                        </div>
                        """, unsafe_allow_html=True)

            st.divider()

            # --- [PART 3] 근거 검증 ---
            st.header("3. 데이터 검증 (가설 입증)")
            st.markdown(f"핵심 변수 **[{strongest_factor}]**가 실제로 성과를 견인하는지 확인합니다.")

            reg_df = df_brand[[strongest_factor, 'Influence_Score', '시도']].dropna()
            if len(reg_df) > 1:
                X = reg_df[[strongest_factor]]
                y = reg_df['Influence_Score']
                model = LinearRegression()
                model.fit(X, y)
                r2 = model.score(X, y)
                
                x_range = np.linspace(X.min().values[0], X.max().values[0], 100).reshape(-1, 1)
                y_pred = model.predict(x_range)
                
                fig_scatter = px.scatter(
                    reg_df, x=strongest_factor, y='Influence_Score', text='시도', color='시도',
                    labels={strongest_factor: f'{strongest_factor} (성공 요인)', 'Influence_Score': '점유율'}, # [수정] 라벨 변경
                    title=f"[{strongest_factor}]와 점유율의 상관관계"
                )
                fig_scatter.add_trace(go.Scatter(x=x_range.flatten(), y=y_pred, mode='lines', name='성공 추세선', line=dict(color='gray', dash='dash')))
                
                # R2 위치 조정 (오른쪽 아래)
                fig_scatter.add_annotation(
                    x=X.max().values[0], y=y.min(),
                    text=f"R² = {r2:.2f}", showarrow=False, font=dict(size=16, color="red", weight="bold"),
                    align="right", xanchor="right", bgcolor="rgba(255,255,255,0.7)"
                )
                
                fig_scatter.update_traces(textposition='top center', marker=dict(size=12))
                fig_scatter.update_layout(height=500, showlegend=False, template="streamlit")
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                if is_positive and not is_higher_than_avg:
                     st.info(f"ℹ️ **특이 사항 발견**: 전반적인 추세선은 우상향(비례)하지만, 1등 지역인 **{top_region_name}**은 추세선 좌측 상단에 위치한 예외 케이스입니다. 이는 해당 지역이 일반적인 인구 통계 법칙을 뛰어넘는 성과를 내고 있음을 보여줍니다.")
                elif r2 > 0.1:
                    st.success(f"✅ **검증 완료**: 점선(추세선)이 우상향하고 있습니다. 이는 **{strongest_factor}**가 높을수록 브랜드 점유율이 상승한다는 통계적 증거입니다.")
                else:
                    st.warning(f"⚠️ **검증 주의**: {strongest_factor}와의 연관성이 다소 약합니다. 다른 요인(경쟁, 입지)이 더 중요할 수 있습니다.")

# =============================================================================
# [TAB 3] 시장 기회 매트릭스 (다크모드 완벽 대응)
# =============================================================================
with tab3:
    df_stats = preprocess_for_tab3(raw_df)
    
    if not df_stats.empty:
        st.markdown('<div class="section-header">🎯 시장 기회 매트릭스 분석</div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            all_brands = sorted(df_stats['브랜드'].unique())
            target_brand = st.selectbox("분석할 브랜드 선택", all_brands)
        with c2:
            feature_dict = {
                "📊 종합 시장 잠재력 (추천)": "종합_잠재력_지수",
                "👨‍💻 20/30대 남녀 비율": "2030대_비율",
                "👨‍👩‍👧 40/50/10대 남녀 비율": "405010대_비율",
                "👴 60대 이후 남녀 비율": "60대이후_비율",
                "💰 1인당 지역총소득": "1인당지역총소득",
                "🏠 1인가구 40세이하 비율": "1인가구_40세이하_비율"
            }
            selected_label = st.selectbox("비교할 지역 특성 선택", list(feature_dict.keys()))
            target_feature = feature_dict[selected_label]

        # 2025년 데이터가 없다면 가장 최근 연도 사용
        if 2025 in df_stats['연도'].values:
            target_year = 2025
        else:
            target_year = df_stats['연도'].max()
            
        df_analysis = df_stats[(df_stats['연도'] == target_year) & (df_stats['브랜드'] == target_brand)].copy()

        if not df_analysis.empty:
            scaler = MinMaxScaler(feature_range=(0, 100))
            df_analysis['잠재력_점수'] = scaler.fit_transform(df_analysis[[target_feature]])
            df_analysis['실제_점수'] = scaler.fit_transform(df_analysis[['Final_Score_Value']])
            
            def get_market_color(row):
                if row['잠재력_점수'] >= 50 and row['실제_점수'] >= 50: return '#059669' # 선도
                elif row['잠재력_점수'] >= 50 and row['실제_점수'] < 50: return '#2563EB' # 기회
                elif row['잠재력_점수'] < 50 and row['실제_점수'] >= 50: return '#DC2626' # 과열
                else: return '#4B5563' # 열위
            
            df_analysis['점색상'] = df_analysis.apply(get_market_color, axis=1)

            # ---------------------------------------------------------
            # 4. 그래프 시각화 (다크모드 대응 최적화)
            # ---------------------------------------------------------
            fig_quad = px.scatter(
                df_analysis, x='잠재력_점수', y='실제_점수', text='시도',
                color='점색상', color_discrete_map="identity",
                height=750, hover_name='시도'
            )
            
            # 사분면 배경 (기회 시장 강조)
            # 눈부심 방지를 위해 밝은 하늘색 대신 투명도 있는 파란색 사용
            fig_quad.add_shape(
                type="rect", x0=50, y0=-15, x1=115, y1=50,
                fillcolor="rgba(59, 130, 246, 0.15)", # 은은한 파란색 (다크모드 호환)
                opacity=1, layer="below", line_width=0
            )

            # 기준선 (다크모드에서도 잘 보이는 반투명 흰색 점선)
            fig_quad.add_vline(x=50, line_dash="dash", line_color="rgba(255,255,255,0.4)")
            fig_quad.add_hline(y=50, line_dash="dash", line_color="rgba(255,255,255,0.4)")

            # 라벨 스타일 (다크모드에서도 잘 보이도록 밝은 회색)
            label_style = dict(size=18, color="#E5E7EB", family="Malgun Gothic", weight="bold")
            fig_quad.add_annotation(x=-13, y=113, text="🔥 과열 시장", showarrow=False, font=label_style, xanchor="left", yanchor="top")
            fig_quad.add_annotation(x=113, y=113, text="⭐ 선도 시장", showarrow=False, font=label_style, xanchor="right", yanchor="top")
            fig_quad.add_annotation(x=-13, y=-13, text="💤 열위 시장", showarrow=False, font=label_style, xanchor="left", yanchor="bottom")
            fig_quad.add_annotation(x=113, y=-13, text="💎 기회 시장", showarrow=False, font=label_style, xanchor="right", yanchor="bottom")

            # 레이아웃 설정
            fig_quad.update_layout(
                xaxis=dict(title=f"지역 잠재력 점수 ({selected_label})", range=[-15, 115], zeroline=False, color="#E5E7EB"),
                # [수정] Y축 라벨 변경
                yaxis=dict(title="종합 점유율 점수 (Final Score)", range=[-15, 115], zeroline=False, color="#E5E7EB"),
                plot_bgcolor='rgba(0,0,0,0)',  # 차트 배경 투명 (앱 배경색 사용) -> 깜빡임 제거
                paper_bgcolor='rgba(0,0,0,0)', # 외곽 배경 투명
                showlegend=False,
                margin=dict(t=50, b=50, l=50, r=50),
                template="plotly_dark" # 다크모드 기본 템플릿 사용 (안전장치)
            )
            
            # 그리드 라인 설정 (은은한 그리드)
            fig_quad.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
            fig_quad.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
            
            # 점 스타일 및 글자(지역명) 색상 설정
            fig_quad.update_traces(
                mode='markers+text',
                marker=dict(size=18, line=dict(width=1.5, color='white')),
                textposition='top center',
                textfont=dict(
                    color='white',  # 다크모드용 흰색 텍스트
                    size=13,
                    family="Malgun Gothic",
                    weight="bold"
                )
            )
            
            st.plotly_chart(fig_quad, use_container_width=True)
            
            # ---------------------------------------------------------
            # 5. 하단 리포트 (통합 및 스타일 적용)
            # ---------------------------------------------------------
            st.markdown(f"### 📋 {target_brand} 4대 시장 영역별 진단 리포트")
            
            df_analysis['영역'] = df_analysis.apply(
                lambda r: '선도' if r['잠재력_점수']>=50 and r['실제_점수']>=50 else 
                        '기회' if r['잠재력_점수']>=50 and r['실제_점수']<50 else 
                        '과열' if r['잠재력_점수']<50 and r['실제_점수']>=50 else '열위', axis=1
            )

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                list_q = df_analysis[df_analysis['영역']=='기회']['시도'].tolist()
                st.markdown(f'<div class="quad_card q_blue"><div class="card-title">💎 기회 시장</div><div class="card-list">{", ".join(list_q) if list_q else "해당 없음"}</div><div class="card-desc">잠재력은 높으나 브랜드 점유율이 낮은 블루오션입니다.</div></div>', unsafe_allow_html=True)
            with col2:
                list_q = df_analysis[df_analysis['영역']=='선도']['시도'].tolist()
                st.markdown(f'<div class="quad_card q_green"><div class="card-title">⭐ 선도 시장</div><div class="card-list">{", ".join(list_q) if list_q else "해당 없음"}</div><div class="card-desc">점유율과 시장 잠재력이 모두 검증된 핵심 상권입니다.</div></div>', unsafe_allow_html=True)
            with col3:
                list_q = df_analysis[df_analysis['영역']=='과열']['시도'].tolist()
                st.markdown(f'<div class="quad_card q_red"><div class="card-title">🔥 과열 시장</div><div class="card-list">{", ".join(list_q) if list_q else "해당 없음"}</div><div class="card-desc">경쟁이 매우 치열한 레드오션입니다. 추가 진입에 신중해야 합니다.</div></div>', unsafe_allow_html=True)
            with col4:
                list_q = df_analysis[df_analysis['영역']=='열위']['시도'].tolist()
                st.markdown(f'<div class="quad_card q_gray"><div class="card-title">💤 열위 시장</div><div class="card-list">{", ".join(list_q) if list_q else "해당 없음"}</div><div class="card-desc">시장 규모와 브랜드 점유율이 모두 낮은 소외 지역입니다.</div></div>', unsafe_allow_html=True)
    else:
        st.info("데이터가 없습니다.")