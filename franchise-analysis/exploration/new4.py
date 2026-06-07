import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
from pyproj import Transformer

# ---------------------------------------------------------
# 1. 설정 및 디자인
# ---------------------------------------------------------
st.set_page_config(layout="wide", page_title="프랜차이즈 밀도 & 지배력 분석")

st.markdown("""
    <style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #1E3A8A; text-align: center; margin-bottom: 20px; }
    .sub-header { font-size: 1.2rem; color: #64748B; text-align: center; margin-bottom: 40px; }
    .section-title { font-size: 1.5rem; font-weight: 700; color: #111827; margin-top: 40px; margin-bottom: 20px; border-left: 5px solid #1E3A8A; padding-left: 10px; }
    </style>
    <div class="main-header">🗺️ 프랜차이즈 밀도 & 지배력 분석</div>
    <div class="sub-header">3D 밀도 지도, 시장 점유율, 그리고 성장 추이까지 한눈에!</div>
""", unsafe_allow_html=True)

# 브랜드 색상 (RGB Hex)
BRAND_COLORS = {
    '스타벅스': '#00704A', '이디야': '#252F7F', '투썸플레이스': '#D50037', '빽다방': '#FFE800', '메가커피': '#FFD000',
    'BBQ': '#D6001C', 'BHC': '#F5A100', '교촌치킨': '#C4A06A', '굽네치킨': '#DA291C',
    '롯데리아': '#E30613', '맘스터치': '#FFC400', '맥도날드': '#FFBC0D', '버거킹': '#EC1D23',
    '도미노피자': '#006491', '피자헛': '#EE3124', '미스터피자': '#FF0000', '청년피자': '#323232'
}

# ---------------------------------------------------------
# 2. 데이터 로드
# ---------------------------------------------------------
@st.cache_data
def load_data():
    # (1) 개별 매장 데이터 (지도용)
    try:
        df_raw = pd.read_csv('merged_result.csv', encoding='utf-8')
    except:
        try:
            df_raw = pd.read_csv('merged_result.csv', encoding='cp949')
        except:
            st.error("데이터 파일(merged_result.csv)을 찾을 수 없습니다.")
            return pd.DataFrame(), pd.DataFrame()

    df_raw['허가날짜'] = pd.to_datetime(df_raw['허가날짜'], errors='coerce')
    df_raw['폐업날짜'] = pd.to_datetime(df_raw['폐업날짜'], errors='coerce')
    df_raw = df_raw.dropna(subset=['좌표'])

    # 좌표 변환 (EPSG:5174 -> 4326)
    try:
        def parse_coord(c):
            parts = str(c).replace('"', '').split(',')
            return float(parts[0]), float(parts[1])
        
        coords = df_raw['좌표'].apply(parse_coord)
        df_raw['X'] = [c[0] for c in coords]
        df_raw['Y'] = [c[1] for c in coords]

        transformer = Transformer.from_crs("epsg:5174", "epsg:4326", always_xy=True)
        lon, lat = transformer.transform(df_raw['X'].values, df_raw['Y'].values)
        df_raw['lon'] = lon
        df_raw['lat'] = lat
        df_raw = df_raw.dropna(subset=['lon', 'lat'])
    except Exception as e:
        st.error(f"좌표 변환 중 오류 발생: {e}")
        return pd.DataFrame(), pd.DataFrame()

    # (2) 지역 통계 데이터 (그래프용)
    try:
        df_stat = pd.read_csv('franchise_analysis_corrected.csv')
    except:
        st.error("통계 파일(franchise_analysis_corrected.csv)을 찾을 수 없습니다.")
        df_stat = pd.DataFrame()

    return df_raw, df_stat

df_points, df_stats = load_data()

# ---------------------------------------------------------
# 3. 사이드바 컨트롤
# ---------------------------------------------------------
st.sidebar.header("🎛️ 분석 옵션")

min_year = int(df_stats['연도'].min()) if not df_stats.empty else 2000
max_year = int(df_stats['연도'].max()) if not df_stats.empty else 2025

year = st.sidebar.number_input("분석 연도", min_value=min_year, max_value=max_year, value=2023)

if not df_stats.empty:
    cat_list = ["전체"] + sorted(list(df_stats['업태 구분명'].unique()))
    category = st.sidebar.selectbox("업태 구분", cat_list)
else:
    category = "전체"

# 지역 줌 설정
regions = {
    "전국 (전체 보기)": {"lat": 36.0, "lon": 127.5, "zoom": 6.0},
    "서울특별시": {"lat": 37.5665, "lon": 126.9780, "zoom": 10.5},
    "경기도": {"lat": 37.4138, "lon": 127.5183, "zoom": 8.5},
    "부산광역시": {"lat": 35.1796, "lon": 129.0756, "zoom": 10.5},
    "대구광역시": {"lat": 35.8714, "lon": 128.6014, "zoom": 10.5},
    "인천광역시": {"lat": 37.4563, "lon": 126.7052, "zoom": 10.0},
    "광주광역시": {"lat": 35.1595, "lon": 126.8526, "zoom": 10.5},
    "대전광역시": {"lat": 36.3504, "lon": 127.3845, "zoom": 10.5},
    "울산광역시": {"lat": 35.5384, "lon": 129.3114, "zoom": 10.0},
    "세종특별자치시": {"lat": 36.4800, "lon": 127.2890, "zoom": 11.0},
    "강원특별자치도": {"lat": 37.8228, "lon": 128.1555, "zoom": 7.5},
    "충청북도": {"lat": 36.6350, "lon": 127.4914, "zoom": 8.0},
    "충청남도": {"lat": 36.6588, "lon": 126.6728, "zoom": 8.0},
    "전북특별자치도": {"lat": 35.7175, "lon": 127.1530, "zoom": 8.0},
    "전라남도": {"lat": 34.8679, "lon": 126.9910, "zoom": 8.0},
    "경상북도": {"lat": 36.4919, "lon": 128.8889, "zoom": 7.5},
    "경상남도": {"lat": 35.4606, "lon": 128.2132, "zoom": 8.0},
    "제주특별자치도": {"lat": 33.4996, "lon": 126.5312, "zoom": 9.0}
}
selected_region_name = st.sidebar.selectbox("지역 이동 (Zoom)", list(regions.keys()))
view_info = regions[selected_region_name]

# ---------------------------------------------------------
# 4. 데이터 필터링
# ---------------------------------------------------------
# 지도 데이터 필터링
if not df_points.empty:
    target_date = pd.Timestamp(f"{year}-12-31")
    mask = (df_points['허가날짜'] <= target_date) & ((df_points['폐업날짜'] > target_date) | (df_points['폐업날짜'].isnull()))
    df_points_filtered = df_points[mask].copy()
    if category != "전체" and '업태 구분명' in df_points_filtered.columns:
        df_points_filtered = df_points_filtered[df_points_filtered['업태 구분명'] == category]
else:
    df_points_filtered = pd.DataFrame()

# 통계 데이터 필터링 (현재 연도)
if not df_stats.empty:
    df_stats_year = df_stats[df_stats['연도'] == year].copy()
    if category != "전체":
        df_stats_year = df_stats_year[df_stats_year['업태 구분명'] == category]

# ---------------------------------------------------------
# 5. 3D 지도 렌더링
# ---------------------------------------------------------
st.markdown('<div class="section-title">🗺️ 프랜차이즈 밀집도 (3D Hex Map)</div>', unsafe_allow_html=True)

if not df_points_filtered.empty:
    layer = pdk.Layer(
        "HexagonLayer",
        data=df_points_filtered,
        get_position=["lon", "lat"],
        radius=300,
        elevation_scale=30,
        elevation_range=[0, 3000],
        extruded=True,
        pickable=True,
        auto_highlight=True,
        coverage=0.9,
    )
    view_state = pdk.ViewState(longitude=view_info["lon"], latitude=view_info["lat"], zoom=view_info["zoom"], pitch=50, bearing=10)
    
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"html": "<b>매장 수:</b> {elevationValue}개", "style": {"color": "white"}}))
else:
    st.info("지도에 표시할 데이터가 없습니다.")

# ---------------------------------------------------------
# 6. 하단 분석 차트
# ---------------------------------------------------------
st.divider()

if not df_stats.empty:
    # --- Data Processing for Charts ---
    # 1. Dominance Data (1위 브랜드)
    dominance_data = []
    for region, group in df_stats_year.groupby('시도'):
        top_row = group.loc[group['영업매장수'].idxmax()]
        dominance_data.append({
            '지역': region, '1등 브랜드': top_row['브랜드'],
            '매장수': top_row['영업매장수'], '점유율': top_row['주요4사_내_비중'],
            '인구수': top_row['전체_총인구수']
        })
    df_dominance = pd.DataFrame(dominance_data)

    # 2. Density Data (인구 1만명당 총 매장 수)
    density_data = []
    for region, group in df_stats_year.groupby('시도'):
        total_stores = group['영업매장수'].sum()
        population = group['전체_총인구수'].iloc[0]
        density = (total_stores / population) * 10000
        density_data.append({'지역': region, '인구1만명당_매장수': density, '총매장수': total_stores})
    df_density = pd.DataFrame(density_data).sort_values('인구1만명당_매장수', ascending=False)

    # 3. Growth Trend Data (시계열)
    top_brands = df_stats_year.groupby('브랜드')['영업매장수'].sum().nlargest(5).index.tolist()
    
    df_trend = df_stats[df_stats['브랜드'].isin(top_brands)].copy()
    if category != "전체":
        df_trend = df_trend[df_trend['업태 구분명'] == category]
    
    df_trend_agg = df_trend.groupby(['연도', '브랜드'])['영업매장수'].sum().reset_index()


    # --- Layout ---
    col1, col2 = st.columns(2)

    # [Left] 지역별 1위 브랜드
    with col1:
        st.markdown('<div class="section-title">🏆 지역별 시장 점유율 1위</div>', unsafe_allow_html=True)
        if not df_dominance.empty:
            fig_dom = px.bar(
                df_dominance, x='지역', y='점유율', color='1등 브랜드',
                text='1등 브랜드', title=f"{year}년 {category} 1위 브랜드 점유율",
                color_discrete_map=BRAND_COLORS, height=400
            )
            fig_dom.update_traces(textposition='inside')
            st.plotly_chart(fig_dom, use_container_width=True)
        else:
            st.warning("데이터가 없습니다.")

    # [Right] 인구 대비 매장 밀도
    with col2:
        st.markdown('<div class="section-title">📊 지역별 매장 밀도 (포화도)</div>', unsafe_allow_html=True)
        if not df_density.empty:
            fig_den = px.bar(
                df_density, x='지역', y='인구1만명당_매장수',
                color='인구1만명당_매장수', color_continuous_scale='Blues',
                text='인구1만명당_매장수', title=f"인구 1만 명당 {category} 매장 수",
                height=400
            )
            fig_den.update_traces(texttemplate='%{text:.1f}개', textposition='outside')
            fig_den.update_layout(yaxis_title="매장 수 / 1만 명")
            st.plotly_chart(fig_den, use_container_width=True)
        else:
            st.warning("데이터가 없습니다.")

    # --- Bottom: Growth Trend ---
    st.markdown('<div class="section-title">📈 연도별 브랜드 성장 추이</div>', unsafe_allow_html=True)
    if not df_trend_agg.empty:
        fig_trend = px.line(
            df_trend_agg, x='연도', y='영업매장수', color='브랜드',
            markers=True, title=f"주요 {category} 브랜드 성장 그래프 (2000~2025)",
            color_discrete_map=BRAND_COLORS, height=500
        )
        # [수정됨] hover_mode -> hovermode
        fig_trend.update_layout(xaxis=dict(tickmode='linear'), hovermode="x unified")
        st.plotly_chart(fig_trend, use_container_width=True)
        
        with st.expander("💡 그래프 해석 팁"):
            st.markdown("""
            - **상승 곡선**: 공격적으로 매장을 확장하고 있는 브랜드입니다. (성장기)
            - **평탄/하락 곡선**: 시장이 포화되었거나, 구조조정 중인 브랜드일 수 있습니다.
            - **교차점**: 시장의 주도권(1등)이 바뀐 시점을 찾아보세요.
            """)
    else:
        st.info("표시할 시계열 데이터가 부족합니다.")

else:
    st.error("통계 데이터를 불러올 수 없습니다.")