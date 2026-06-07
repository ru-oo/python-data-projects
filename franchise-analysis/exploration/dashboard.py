import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px

# ---------------------------------------------------------
# 1. 설정 및 디자인
# ---------------------------------------------------------
st.set_page_config(layout="wide", page_title="프랜차이즈 3D 육각형 분석")

st.markdown("""
    <style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #1E3A8A; text-align: center; margin-bottom: 20px; }
    .sub-header { font-size: 1.2rem; color: #64748B; text-align: center; margin-bottom: 40px; }
    .metric-box {
        background-color: white; border: 1px solid #E2E8F0; border-radius: 10px;
        padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .brand-tag {
        display: inline-block; padding: 2px 8px; border-radius: 4px; 
        color: white; font-weight: bold; font-size: 0.8rem;
    }
    </style>
    <div class="main-header">🏟️ 프랜차이즈 지역 패권 분석</div>
    <div class="sub-header">3D 육각형 지도로 보는 지역별 1등 브랜드와 경쟁 구도</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 데이터 로드
# ---------------------------------------------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('franchise_analysis_major_brands.csv')
    except:
        st.error("데이터 파일을 찾을 수 없습니다.")
        return pd.DataFrame()

    # 좌표 매핑
    coords = {
        '서울': [126.9780, 37.5665], '경기': [127.5183, 37.4138], '부산': [129.0756, 35.1796],
        '대구': [128.6014, 35.8714], '인천': [126.7052, 37.4563], '광주': [126.8526, 35.1595],
        '대전': [127.3845, 36.3504], '울산': [129.3114, 35.5384], '세종': [127.2890, 36.4800],
        '강원': [128.1555, 37.8228], '충북': [127.4914, 36.6350], '충남': [126.6728, 36.6588],
        '전북': [127.1530, 35.7175], '전남': [126.9910, 34.8679], '경북': [128.8889, 36.4919],
        '경남': [128.2132, 35.4606], '제주': [126.5312, 33.4996]
    }
    df['lon'] = df['시도'].map(lambda x: coords.get(x, [0,0])[0])
    df['lat'] = df['시도'].map(lambda x: coords.get(x, [0,0])[1])
    return df

df = load_data()

# 브랜드별 고유 색상 (RGB)
BRAND_COLORS = {
    '스타벅스': [0, 112, 74], '이디야': [37, 47, 127], '투썸플레이스': [213, 0, 55], '빽다방': [255, 232, 0],
    'BBQ': [214, 0, 28], 'BHC': [245, 161, 0], '교촌치킨': [196, 160, 106], '굽네치킨': [218, 41, 28],
    '롯데리아': [227, 6, 19], '맘스터치': [255, 196, 0], '맥도날드': [255, 188, 13], '버거킹': [236, 29, 35],
    '도미노피자': [0, 100, 145], '피자헛': [238, 49, 36], '미스터피자': [255, 0, 0], '청년피자': [0, 0, 0]
}

# ---------------------------------------------------------
# 3. 사이드바 (필터)
# ---------------------------------------------------------
st.sidebar.header("🎛️ 분석 옵션")
year = st.sidebar.slider("연도 선택", int(df['연도'].min()), int(df['연도'].max()), 2023)
category = st.sidebar.selectbox("업태 구분", ["전체"] + list(df['업태 구분명'].unique()))

# ---------------------------------------------------------
# 4. 데이터 가공 (지역별 1등 찾기)
# ---------------------------------------------------------
df_target = df[df['연도'] == year].copy()
if category != "전체":
    df_target = df_target[df_target['업태 구분명'] == category]

# 지역별로 Grouping하여 1등 데이터 추출
map_data = []
for region, group in df_target.groupby('시도'):
    if group.empty: continue
    
    # 1. 매장수 1등 브랜드
    top_count_row = group.loc[group['영업매장수'].idxmax()]
    # 2. 점유율 1등 브랜드 (보통 매장수 1등과 같지만, 데이터 구조상 다를 수도 있음)
    top_share_row = group.loc[group['주요4사_내_비중'].idxmax()]
    
    # 지역 전체 매장 수 합계
    total_stores = group['영업매장수'].sum()
    
    # 색상 결정 (매장수 1등 브랜드 기준)
    brand_color = BRAND_COLORS.get(top_count_row['브랜드'], [128, 128, 128])
    
    map_data.append({
        'region': region,
        'lon': top_count_row['lon'],
        'lat': top_count_row['lat'],
        'total_stores': total_stores,
        'top_count_brand': top_count_row['브랜드'],
        'top_count_val': top_count_row['영업매장수'],
        'top_share_brand': top_share_row['브랜드'],
        'top_share_val': top_share_row['주요4사_내_비중'],
        'color': brand_color
    })

df_map = pd.DataFrame(map_data)

# ---------------------------------------------------------
# 5. 메인 레이아웃 (3D 지도)
# ---------------------------------------------------------
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("🗺️ 지역별 패권 지도 (Hexagon Map)")
    
    if not df_map.empty:
        # PyDeck Layer 설정
        layer = pdk.Layer(
            "ColumnLayer",
            data=df_map,
            get_position=["lon", "lat"],
            get_elevation="total_stores",  # 높이는 해당 지역 전체 규모
            get_fill_color="color",        # 색상은 1등 브랜드
            radius=8000,
            diskResolution=6,              # ⭐ 육각형 모양의 핵심 ⭐
            elevation_scale=50,
            extruded=True,
            pickable=True,
            auto_highlight=True,
        )

        tooltip = {
            "html": """
                <div style="padding:10px; background:rgba(0,0,0,0.8); color:white; border-radius:5px;">
                    <h4 style="margin:0;">{region}</h4>
                    <hr style="margin:5px 0; border-color:gray;">
                    <b>🏆 매장수 1등:</b> {top_count_brand} ({top_count_val}개)<br>
                    <b>📊 점유율 1등:</b> {top_share_brand} ({top_share_val:.1f}%)<br>
                    <br>
                    <span style="font-size:0.8em; color:#ccc;">지역 총 규모: {total_stores}개 매장</span>
                </div>
            """
        }

        view_state = pdk.ViewState(longitude=127.5, latitude=36.0, zoom=6, pitch=50)

        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            map_style='mapbox://styles/mapbox/light-v10'
        )
        st.pydeck_chart(r)
    else:
        st.warning("선택한 조건에 맞는 데이터가 없습니다.")

with col2:
    st.subheader("📊 핵심 요약")
    if not df_map.empty:
        # 전국 1위 (총 매장 수 기준)
        top_nation = df_map.loc[df_map['total_stores'].idxmax()]
        
        st.markdown(f"""
            <div class="metric-box">
                <h4>최대 격전지</h4>
                <h2 style="color:#1E3A8A; margin:0;">{top_nation['region']}</h2>
                <p style="color:gray;">총 {top_nation['total_stores']:,}개 매장</p>
            </div>
            <br>
            <div class="metric-box">
                <h4>{top_nation['region']}의 지배자</h4>
                <h2 style="color:{'rgb(' + str(top_nation['color'][0]) + ',' + str(top_nation['color'][1]) + ',' + str(top_nation['color'][2]) + ')'}; margin:0;">
                    {top_nation['top_count_brand']}
                </h2>
                <p>점유율 {top_nation['top_share_val']:.1f}%</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.info("💡 **지도 가이드**\n\n- **육각형 높이**: 해당 지역의 전체 시장 규모\n- **색상**: 매장 수 1등 브랜드의 고유색")
    else:
        st.write("-")

# ---------------------------------------------------------
# 6. 하단 상세 차트
# ---------------------------------------------------------
st.divider()
st.subheader("📈 상세 점유율 분석")

if not df_target.empty:
    fig_share = px.bar(
        df_target,
        x='시도',
        y='주요4사_내_비중',
        color='브랜드',
        title=f"{year}년 지역별 주요 브랜드 점유율 (100% 기준)",
        color_discrete_map={k: f"rgb({v[0]},{v[1]},{v[2]})" for k, v in BRAND_COLORS.items()}
    )
    st.plotly_chart(fig_share, use_container_width=True)