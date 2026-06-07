import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
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
        base_dir = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(os.path.join(base_dir, 'franchise_analysis_corrected.csv'))
        df['영업매장수_safe'] = df['영업매장수'].replace(0, 1)
        return df
    except FileNotFoundError:
        st.error("❌ 'franchise_analysis_corrected.csv' 파일을 찾을 수 없습니다.")
        return pd.DataFrame()

@st.cache_data
def load_coord_data():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        df_points = pd.read_csv(os.path.join(base_dir, 'merged_result.csv'))
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
def preprocess_for_tab2(df):
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
    
    # 점유율(Influence_Score) 계산
    region_total = df_app.groupby(['연도', '시도'])['Final_Score'].transform('sum').replace(0, 1)
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
    
    region_total = df_t3.groupby(['연도', '시도'])['Final_Score_Value'].transform('sum').replace(0, 1)
    df_t3['Influence_Score'] = (df_t3['Final_Score_Value'] / region_total) * 100
    
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
st.sidebar.subheader("2. 지도 옵션 (탭2)")
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
st.sidebar.subheader("3. 브랜드 옵션 (탭3)")
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
# [수정] 탭 구성 변경: '프로젝트 개요' 탭 추가
tab0, tab1, tab2, tab3 = st.tabs(["📑 프로젝트 개요", "📊 지배력 & 밀도 분석", "🎤 점유율 요인 심층 분석", "🎯 시장 기회 매트릭스"])

# =============================================================================
# [TAB 0] 프로젝트 개요 (수정됨: 디자인 개선 & 라이트모드 가독성 확보)
# =============================================================================
with tab0:
    st.title("Franchise's Ranking Analysis")
    st.markdown("### 🍔 프랜차이즈 순위 및 시장 분석 프로젝트")
    
    st.divider()

    # --- 1. 프로젝트 개요 (Introduction) ---
    st.subheader("프로젝트 개요 (Introduction)")
    try:
        st.image(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ppt_intro.png"), caption="프로젝트 배경 및 개요", use_container_width=True)
    except:
        st.info("👋 'ppt_intro.png' 이미지를 폴더에 추가하면 이곳에 표시됩니다.")
        st.markdown("""
        본 프로젝트는 **공공 데이터**와 **공간 데이터**를 활용하여 대한민국 주요 프랜차이즈 시장의 **경쟁 현황**을 시각화하고, 
        지역별 **성공 요인**을 분석하여 예비 창업자와 기업에게 실질적인 **시장 기회(Insight)**를 제공하는 것을 목적으로 합니다.
        """)

    # --- 2. 분석 대상 (Targets) ---
    st.subheader("🎯 분석 대상 (Targets)")
    st.markdown("본 프로젝트에서 분석한 **업종별 프랜차이즈 브랜드** 현황입니다.")
    
    # 데이터셋 내 모든 유니크 브랜드 추출
    all_brands_in_data = sorted(raw_df['브랜드'].unique())
    
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.markdown("#### 🍔 버거")
        st.write("- 맥도날드\n- 롯데리아\n- 버거킹\n- 맘스터치")
    with t2:
        st.markdown("#### ☕ 카페")
        st.write("- 스타벅스\n- 이디야커피\n- 빽다방\n- 투썸플레이스")
    with t3:
        st.markdown("#### 🍗 치킨")
        st.write("- BBQ\n- BHC\n- 교촌치킨\n- 굽네치킨")
    with t4:
        st.markdown("#### 🍕 피자")
        st.write("- 도미노피자\n- 피자헛\n- 미스터피자\n- 청년피자")
    
    with st.expander("🔍 조사된 모든 프랜차이즈 명단 보기"):
        brand_cols = st.columns(5)
        for i, brand in enumerate(all_brands_in_data):
            brand_cols[i % 5].write(f"• {brand}")

    st.divider()
    
    # --- 3. 팀원 소개 & 분석 프로세스 (수직 배치 & 가독성 개선) ---
    st.subheader("👥 팀원 소개 (Team)")
    # 배경색을 rgba(128, 128, 128, 0.1)로 설정하여 라이트/다크 모드 모두에서 텍스트가 잘 보이도록 함
    st.markdown("""
    <div style='background-color: rgba(128, 128, 128, 0.1); padding:20px; border-radius:10px; border:1px solid rgba(128, 128, 128, 0.2); margin-bottom:20px;'>
        <h4 style='margin-top:0; color:#FF4B4B;'>Member</h4>
        <p style='font-size:1.35rem; line-height:1.6;'>
            <b>- 김세현</b> : 데이터 수집 및 전처리, 점유율 도출 및 스트림릿 구현<br>
            <b>- 송승민</b> : 데이터 수집 및 전처리, 시장 기회 도출, 시각화<br>
            <b>- 장현근</b> : 데이터 수집 및 전처리, 상관 관계 분석, 시각화<br>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🛠️ 분석 프로세스 (Process)")
    st.markdown("""
    <div style='background-color: rgba(128, 128, 128, 0.1); padding:20px; border-radius:10px; border:1px solid rgba(128, 128, 128, 0.2);'>
        <p style='font-size:1.25rem; margin-bottom:8px;'><b>STEP 1. 개요 </b> : 프로젝트 개요 설명 및 데이터 소개</p>
        <p style='font-size:1.25rem; margin-bottom:8px;'><b>STEP 2. 서론 </b> : 지역별 브랜드 지배력 분석</p>
        <p style='font-size:1.25rem; margin-bottom:8px;'><b>STEP 3. 본론 </b> :  핵심 성공 요인(인구, 소득 등) 상관관계 분석</p>
        <p style='font-size:1.25rem; margin-bottom:0px;'><b>STEP 4. 결론 </b> : 데이터 기반 시장 기회 매트릭스 도출 및 전략 제언</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # --- 4. 데이터 구축 (이미지 -> 설명 카드 -> 데이터프레임 순서) ---
    st.subheader("📊 데이터 구축 및 활용 데이터셋 (Data)")
    
    # 1. 이미지
    try:
        st.image(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ppt_data.png"), caption="Data Sources & Preprocessing Flow", use_container_width=True)
    except:
        st.info("👋 'ppt_data.png' 이미지를 추가하면 데이터 구축 장표가 표시됩니다.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. 설명 카드 (색상 테마 적용: 파랑/초록/빨강 - 투명도 적용으로 가독성 확보)
    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown("""
        <div style='background-color: rgba(37, 99, 235, 0.1); padding:15px; border-radius:10px; border:1px solid rgba(37, 99, 235, 0.2); min-height:120px;'>
            <h5 style='margin-top:0; color:#2563EB;'>🇰🇷 KOSIS (국가통계포털)</h5>
            <p style='font-size:0.9rem;'>행정구역별 인구 통계<br>1인당 지역 총소득 데이터</p>
        </div>
        """, unsafe_allow_html=True)
    with d2:
        st.markdown("""
        <div style='background-color: rgba(5, 150, 105, 0.1); padding:15px; border-radius:10px; border:1px solid rgba(5, 150, 105, 0.2); min-height:120px;'>
            <h5 style='margin-top:0; color:#059669;'>📂 공공데이터포털</h5>
            <p style='font-size:0.9rem;'>행정 구역 및 상권 정보<br>ㅤ</p>
        </div>
        """, unsafe_allow_html=True)
    with d3:
        st.markdown("""
        <div style='background-color: rgba(220, 38, 38, 0.1); padding:15px; border-radius:10px; border:1px solid rgba(220, 38, 38, 0.2); min-height:120px;'>
            <h5 style='margin-top:0; color:#DC2626;'>🏢 LOCALDATA (지방행정)</h5>
            <p style='font-size:0.9rem;'>프랜차이즈 인허가 현황<br>개업 및 폐업 이력 정보</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. 데이터프레임
    st.markdown("#### 📋 분석 데이터셋 샘플 (DataFrame)")
    st.markdown("분석에 활용된 통합 데이터셋의 상위 10개 행입니다.")
    st.dataframe(raw_df.head(10), use_container_width=True)
# =============================================================================
# [TAB 1] 지배력 & 밀도 분석 (수정됨: 시장 규모 점유율 계산 로직 개선)
# =============================================================================
with tab1:
    df_all_stat, income_avg_val = preprocess_for_tab1(raw_df)
    
    df_year = df_all_stat[df_all_stat['연도'] == selected_year].copy()
    if selected_category != "전체 (통합 1위)":
        df_year = df_year[df_year['업태 구분명'] == selected_category].copy()

    # [핵심 수정] 시장 점유율(Real_Market_Share_Pct) 재계산 로직 추가
    # 기존: 해당 브랜드의 '업종 내' 점유율 (예: 맘스터치 / 전체 버거 매장 수)
    # 변경: 현재 선택된 '전체 범위' 내 점유율 (예: 맘스터치 / (버거+치킨+카페+피자) 전체 매장 수)
    # -> 이렇게 해야 '전체' 선택 시 업종을 불문하고 진짜 매장이 가장 많은 브랜드가 1위로 나옴.
    
    current_scope_total = df_year.groupby('시도')['영업매장수'].transform('sum')
    df_year['Real_Market_Share_Pct'] = (df_year['영업매장수'] / current_scope_total) * 100

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
    st.subheader("지역별 매장 밀집도 (3D Heatmap)")
    
    if not df_map_filtered.empty:
        view_info = regions[selected_region]
        
        view_state = pdk.ViewState(
            latitude=view_info["lat"],
            longitude=view_info["lon"],
            zoom=view_info["zoom"],
            pitch=55,   
            bearing=30  
        )

        layer = pdk.Layer(
            "HexagonLayer",
            data=df_map_filtered,
            get_position=["lon", "lat"],
            radius=400,
            coverage=0.88,        
            elevation_scale=40,
            elevation_range=[0, 3000],
            extruded=True,
            pickable=True,
            auto_highlight=True,
            color_range = [
                [37, 52, 148],
                [44, 127, 184],
                [65, 182, 196],
                [127, 205, 187],
                [199, 233, 180],
                [255, 255, 204]
            ],
            material={
                "ambient": 0.8,
                "diffuse": 0.9,
                "shininess": 150,
                "specularColor": [255, 255, 230]
            },
            transitions={'elevationScale': 1000}
        )
        
        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style=pdk.map_styles.CARTO_DARK, 
            tooltip={
                "html": """
                    <div style='background: rgba(20, 20, 30, 0.9); color: white; padding: 12px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.2); box-shadow: 0 4px 6px rgba(0,0,0,0.3);'>
                        <span style='font-size: 0.9em; color: #aaa;'>매장 밀집도</span><br/>
                        <span style='font-size: 1.5em; font-weight: bold; color: #FFDD00;'>{elevationValue}개</span>
                        <span style='font-size: 0.9em;'> 점포 추정</span>
                    </div>
                """
            }
        )
        st.pydeck_chart(deck, use_container_width=True, key="pdk_hex_map")
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
        # [수정] 위에서 재계산한 Real_Market_Share_Pct가 반영됨
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

    def format_label_with_arrow(row):
        brand = row['브랜드']
        share = row['Influence_Share_Pct']
        growth = row['Growth_Rate'] * 100
        
        if growth > 0:
            growth_str = f"<span style='color:#EF4444'>▲ +{growth:.1f}%</span>"
        elif growth < 0:
            growth_str = f"<span style='color:#3B82F6'>▼ {abs(growth):.1f}%</span>"
        else:
            growth_str = f"<span style='color:gray'>- 0.0%</span>"
            
        return f"<b>{brand}</b><br>{share:.1f}%<br>{growth_str}"

    top_influence['Label'] = top_influence.apply(format_label_with_arrow, axis=1)
    
    fig_after = px.bar(top_influence, x='시도', y='Influence_Share_Pct', color='브랜드', text='Label', color_discrete_map=brand_colors)
    fig_after.update_traces(textposition='outside', textfont_size=12, cliponaxis=False)
    fig_after.update_layout(xaxis_title="지역", yaxis_title="영향력 점유율 (%)", height=550, yaxis=dict(range=[0, 80], dtick=5), margin=dict(t=100, b=50, l=50, r=50), showlegend=True)
    st.plotly_chart(fig_after, use_container_width=True)

    with st.expander("📋 물량 1위 vs 영향력 1위 데이터 시트"):
        comp_df = pd.merge(
            top_market[['시도', '브랜드', 'Real_Market_Share_Pct']].rename(columns={'브랜드': '물량 1위', 'Real_Market_Share_Pct': '물량 점유율'}),
            top_influence[['시도', '브랜드', 'Influence_Share_Pct', 'Growth_Rate']].rename(columns={'브랜드': '영향력 1위', 'Influence_Share_Pct': '영향력 점유율', 'Growth_Rate': '성장률'}),
            on='시도'
        )
        st.dataframe(comp_df.style.highlight_max(axis=0, subset=['영향력 점유율'], color='#e6f4ea'), use_container_width=True)

# =============================================================================
# [TAB 2] 성과 요인 심층 분석 (수정됨: 1등 지역 특성 우선 반영 로직)
# =============================================================================
with tab2:
    if selected_category == "전체 (통합 1위)":
        st.warning("⚠️ 분석할 브랜드를 선택하려면 먼저 사이드바에서 '업태'를 선택해주세요.")
    elif selected_brand_tab2 is None:
        st.warning("⚠️ 사이드바에서 분석할 브랜드를 선택해주세요.")
    else:
        df_all_app = preprocess_for_tab2(raw_df)
        df_target = df_all_app[(df_all_app['연도'] == selected_year) & (df_all_app['업태 구분명'] == selected_category)].copy()
        df_brand = df_target[df_target['브랜드'] == selected_brand_tab2].copy()

        if df_brand.empty:
            st.error("선택한 브랜드의 데이터가 없습니다.")
        else:
            analysis_cols = ['청년층(2030)', '중장년층(4050)', '노년층(60+)', '청년1인가구', '지역소득']
            
            # [수정] 성공 요인 도출 로직 개선
            # 기존: 단순 전국 상관계수 1위 -> 문제점: 1등 지역(울산)의 특성(소득)이 묻힘
            # 개선: '1등 지역'에서 '전국 평균' 대비 가장 두드러지는(Gap이 큰) 요인을 선정
            
            if not df_brand.empty:
                # 1. 1등 지역 찾기
                top_region_row = df_brand.sort_values(by='Influence_Score', ascending=False).iloc[0]
                top_region_name = top_region_row['시도']
                
                # 2. 데이터 정규화 (MinMax) - 변수 간 스케일 맞춤
                scaler = MinMaxScaler()
                X = df_brand[analysis_cols].fillna(0)
                X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=analysis_cols, index=df_brand['시도'])
                
                # 3. 1등 지역의 정규화된 값 가져오기
                top_region_vals = X_scaled.loc[top_region_name]
                
                # 4. 가장 높은 점수를 기록한 요인을 '핵심 성공 요인'으로 선정
                # (예: 울산은 소득 점수가 1.0(최대)에 가까우므로 '지역소득'이 선정됨)
                strongest_factor = top_region_vals.idxmax()
                
                # 상관계수도 참고용으로 계산 (양/음 관계 파악)
                corr_val = df_brand[strongest_factor].corr(df_brand['Influence_Score'])
                is_positive = corr_val > 0
            
            st.title(f"🎤 {selected_brand_tab2} 점유율 요인 심층 분석")
            st.markdown("""
            이 분석은 **현재의 점유율**을 진단하고, 그 성과를 만들어낸 **핵심 점유율 동인**을 데이터로 증명합니다.
            """)
            st.divider()

            # --- [PART 1] 현황 진단 ---
            st.header("1. 전국 점유율 분포")
            col1, col2 = st.columns([1.5, 1])

            with col1:
                fig_map = px.treemap(
                    df_brand, path=['시도'], values='Influence_Score',
                    color='Influence_Score', color_continuous_scale='Reds',
                    title=f"지역별 점유율 현황 ({selected_year})",
                    labels={'Influence_Score': '점유율'} 
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

            st.divider()

            # --- [PART 2] 성공 DNA 분석 ---
            st.header("2. 1등 점유율 지역의 성공 핵심 요인 분석")
            
            st.markdown(f"""
            가장 점유율이 높은 **{top_region_name}** 지역은 어떤 인구 특성을 가지고 있을까요?  
            **1등 지역이 전국 평균 대비 가장 압도적인 우위를 보이는 특성**을 분석했습니다.
            """)

            # 레이더 차트 데이터 준비
            values_top = X_scaled.loc[top_region_name].tolist()
            values_top += values_top[:1]
            values_avg = X_scaled.mean().tolist()
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
                # 텍스트 로직 수정
                explanation = f"<b>{top_region_name}</b>은(는) 다른 지역보다 <br><b style='color:#FF4B4B; font-size:1.1em;'>{strongest_factor}</b> 수치가 월등히 높습니다."
                key_insight = f"{strongest_factor} 우위 지역"

                st.markdown(f"""
                <div style='background-color:#262730; color:white; padding:20px; border-radius:10px; border:1px solid #444;'>
                    <h3 style='color:#FF4B4B; margin-top:0;'>💡 데이터 해석 (Insight)</h3>
                    <p>분석 결과, <b>{selected_brand_tab2}</b>의 1등 지역({top_region_name})을 만든 핵심 요인은 
                    <b style='color:#FF4B4B; font-size:1.2em;'>{strongest_factor}</b> 입니다.</p>
                    <hr style='border-color:#555;'>
                    <p>{explanation}</p>
                    <p>따라서 이 브랜드는 <b>{key_insight}</b>에서 최고의 성과를 낼 가능성이 높습니다.</p>
                </div>
                """, unsafe_allow_html=True)

            st.divider()

            # --- [PART 3] 근거 검증 ---
            st.header("3. 데이터 검증 (가설 입증)")
            st.markdown(f"핵심 변수 {strongest_factor}가 실제로 점유율을 견인하는지 확인합니다.")

            reg_df = df_brand[[strongest_factor, 'Influence_Score', '시도']].dropna()
            if len(reg_df) > 1:
                X_reg = reg_df[[strongest_factor]]
                y_reg = reg_df['Influence_Score']
                model = LinearRegression()
                model.fit(X_reg, y_reg)
                r2 = model.score(X_reg, y_reg)
                
                x_range = np.linspace(X_reg.min().values[0], X_reg.max().values[0], 100).reshape(-1, 1)
                y_pred = model.predict(x_range)
                
                fig_scatter = px.scatter(
                    reg_df, x=strongest_factor, y='Influence_Score', text='시도', color='시도',
                    labels={strongest_factor: f'{strongest_factor} (성공 요인)', 'Influence_Score': '점유율'},
                    title=f"{strongest_factor}와 점유율의 상관 관계"
                )
                fig_scatter.add_trace(go.Scatter(x=x_range.flatten(), y=y_pred, mode='lines', name='추세선', line=dict(color='gray', dash='dash')))
                
                fig_scatter.add_annotation(
                    x=X_reg.max().values[0], y=y_reg.min(),
                    text=f"R² = {r2:.2f}", showarrow=False, font=dict(size=16, color="red", weight="bold"),
                    align="right", xanchor="right", bgcolor="rgba(255,255,255,0.7)"
                )
                
                fig_scatter.update_traces(textposition='top center', marker=dict(size=12))
                fig_scatter.update_layout(height=500, showlegend=False, template="streamlit")
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                # 검증 메시지도 수정
                if is_positive:
                    st.success(f"✅ **검증 완료**: {top_region_name}의 높은 **{strongest_factor}** 특성이 브랜드 점유율 상승에 긍정적인 영향을 미치고 있음을 확인했습니다.")
                else:
                    st.info(f"ℹ️ **참고**: {strongest_factor}는 {top_region_name}만의 독특한 성공 요인으로 보입니다. (전국적인 상관관계보다는 해당 지역 특화 요인)")

# =============================================================================
# [TAB 3] 시장 기회 매트릭스 (다크/라이트 모드 호환성 개선)
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
            
            # [수정됨] Influence_Score(점유율)로 정규화
            df_analysis['실제_점수'] = scaler.fit_transform(df_analysis[['Influence_Score']])
            
            def get_market_color(row):
                if row['잠재력_점수'] >= 50 and row['실제_점수'] >= 50: return '#059669' # 선도
                elif row['잠재력_점수'] >= 50 and row['실제_점수'] < 50: return '#2563EB' # 기회
                elif row['잠재력_점수'] < 50 and row['실제_점수'] >= 50: return '#DC2626' # 과열
                else: return '#4B5563' # 열위
            
            df_analysis['점색상'] = df_analysis.apply(get_market_color, axis=1)

            # ---------------------------------------------------------
            # 4. 그래프 시각화 (호환성 개선)
            # ---------------------------------------------------------
            fig_quad = px.scatter(
                df_analysis, x='잠재력_점수', y='실제_점수', text='시도',
                color='점색상', color_discrete_map="identity",
                height=750, hover_name='시도'
            )
            
            # [수정] 사분면 배경: 투명도를 조절하여 다크/라이트 모두에서 은은하게 보이도록 설정
            fig_quad.add_shape(
                type="rect", x0=50, y0=-15, x1=115, y1=50,
                fillcolor="rgba(59, 130, 246, 0.1)", # 매우 연한 파란색
                opacity=1, layer="below", line_width=0
            )

            # [수정] 기준선: 완전 흰색 대신 '중립적인 회색' 점선 사용
            neutral_line_color = "rgba(128, 128, 128, 0.5)" 
            fig_quad.add_vline(x=50, line_dash="dash", line_color=neutral_line_color)
            fig_quad.add_hline(y=50, line_dash="dash", line_color=neutral_line_color)

            # [수정] 라벨 스타일: 색상 지정을 제거하여 테마에 따라 자동 반전되도록 함
            # 글자 크기만 키우고 색상은 시스템에 맡김
            label_font = dict(size=18, weight="bold") 
            
            fig_quad.add_annotation(x=-13, y=113, text="🔥 과열 시장", showarrow=False, font=label_font, xanchor="left", yanchor="top")
            fig_quad.add_annotation(x=113, y=113, text="⭐ 선도 시장", showarrow=False, font=label_font, xanchor="right", yanchor="top")
            fig_quad.add_annotation(x=-13, y=-13, text="💤 열위 시장", showarrow=False, font=label_font, xanchor="left", yanchor="bottom")
            fig_quad.add_annotation(x=113, y=-13, text="💎 기회 시장", showarrow=False, font=label_font, xanchor="right", yanchor="bottom")

            # [수정] 레이아웃 설정: 
            # 1. template="plotly_dark" 제거 (자동 테마 적용을 위해)
            # 2. 축 색상, 그리드 색상 강제 지정 제거
            fig_quad.update_layout(
                xaxis=dict(title=f"지역 잠재력 점수 ({selected_label})", range=[-15, 115], zeroline=False),
                yaxis=dict(title="종합 영향력 점유율 (Influence Score)", range=[-15, 115], zeroline=False),
                plot_bgcolor='rgba(0,0,0,0)',  # 투명 배경
                paper_bgcolor='rgba(0,0,0,0)', # 투명 배경
                showlegend=False,
                margin=dict(t=50, b=50, l=50, r=50),
                # template="streamlit" # Streamlit 기본 템플릿 사용 (명시하지 않아도 됨)
            )
            
            # [수정] 그리드 라인: 강제 흰색 제거 -> 시스템 기본값(회색조) 사용
            fig_quad.update_xaxes(showgrid=True, gridwidth=1)
            fig_quad.update_yaxes(showgrid=True, gridwidth=1)
            
            # [수정] 점 스타일: 텍스트 색상 강제(white) 제거 -> 테마에 따름
            # 테두리(line) 색상도 제거하여 깔끔하게 표현
            fig_quad.update_traces(
                mode='markers+text',
                marker=dict(size=18, line=dict(width=1, color='rgba(0,0,0,0.2)')), # 테두리는 연한 그림자처럼 처리
                textposition='top center',
                textfont=dict(
                    size=13,
                    # family="Malgun Gothic",
                    weight="bold"
                    # color='white'  <-- 이 부분을 제거해야 라이트 모드에서 글씨가 보입니다.
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
                st.markdown(f'<div class="quad_card q_blue"><div class="card-title">💎 기회 시장</div><div class="card-list">{", ".join(list_q) if list_q else "해당 없음"}</div><div class="card-desc">잠재력은 높으나 브랜드 영향력이 낮은 블루오션입니다.</div></div>', unsafe_allow_html=True)
            with col2:
                list_q = df_analysis[df_analysis['영역']=='선도']['시도'].tolist()
                st.markdown(f'<div class="quad_card q_green"><div class="card-title">⭐ 선도 시장</div><div class="card-list">{", ".join(list_q) if list_q else "해당 없음"}</div><div class="card-desc">영향력과 시장 잠재력이 모두 검증된 핵심 상권입니다.</div></div>', unsafe_allow_html=True)
            with col3:
                list_q = df_analysis[df_analysis['영역']=='과열']['시도'].tolist()
                st.markdown(f'<div class="quad_card q_red"><div class="card-title">🔥 과열 시장</div><div class="card-list">{", ".join(list_q) if list_q else "해당 없음"}</div><div class="card-desc">경쟁이 매우 치열한 레드오션입니다. 추가 진입에 신중해야 합니다.</div></div>', unsafe_allow_html=True)
            with col4:
                list_q = df_analysis[df_analysis['영역']=='열위']['시도'].tolist()
                st.markdown(f'<div class="quad_card q_gray"><div class="card-title">💤 열위 시장</div><div class="card-list">{", ".join(list_q) if list_q else "해당 없음"}</div><div class="card-desc">시장 규모와 브랜드 영향력이 모두 낮은 소외 지역입니다.</div></div>', unsafe_allow_html=True)
    else:
        st.info("데이터가 없습니다.")