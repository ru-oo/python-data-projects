import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(layout="wide", page_title="프랜차이즈 성공 전략 분석")

st.markdown("""
    <style>
    .main-title { font-size: 2.2rem; font-weight: 800; color: #111827; margin-bottom: 0px; }
    .sub-text { font-size: 1.0rem; color: #6B7280; margin-bottom: 20px; }
    .highlight-box { background-color: #EFF6FF; padding: 20px; border-radius: 12px; border: 1px solid #BFDBFE; margin-bottom: 20px; }
    .vs-box { background-color: #FFF7ED; padding: 15px; border-radius: 10px; border: 1px solid #FFEDD5; text-align: center; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🏆 프랜차이즈, 이길 수밖에 없는 이유</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-text">지역별 1등의 비밀 & 라이벌 브랜드 전격 비교</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 데이터 로드 및 전처리
# ---------------------------------------------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('franchise_analysis_corrected.csv')
    except:
        st.error("CSV 파일을 찾을 수 없습니다.")
        return pd.DataFrame()

    # 2023년 데이터 기준
    df = df[df['연도'] == 2023].copy()
    
    # 핵심 파생변수 생성
    df['비율_10대'] = df['비율_남자_0~19세'] + df['비율_여자_0~19세']
    df['비율_2030여성'] = df['비율_여자_20~39세']
    df['비율_4050세대'] = df['비율_남자_40~59세'] + df['비율_여자_40~59세']
    df['1인가구_비중'] = df['1인가구_40세이하_비율'] 
    
    return df

df = load_data()

# ---------------------------------------------------------
# 3. 분석 탭 구성
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🗺️ 지역별 1등 분석", "⚔️ 라이벌 전격 비교", "📊 전체 포지셔닝 맵"])

# =========================================================
# TAB 1: 지역별 1등 심층 분석 (업태 필터 추가)
# =========================================================
with tab1:
    if df.empty:
        st.error("데이터가 없습니다.")
    else:
        # 1. 필터링 (지역 & 업태)
        c1, c2 = st.columns([1, 1])
        with c1:
            selected_region = st.selectbox("📍 지역(시도) 선택", df['시도'].unique())
        with c2:
            # 업태 목록 추출 (전체 포함)
            categories = ['전체'] + sorted(df['업태 구분명'].unique().tolist())
            selected_category = st.selectbox("🏢 업태(카테고리) 선택", categories)
        
        # 2. 데이터 필터링
        filtered_df = df[df['시도'] == selected_region].copy()
        if selected_category != '전체':
            filtered_df = filtered_df[filtered_df['업태 구분명'] == selected_category]
            
        # 3. 순위 계산
        ranked_df = filtered_df.sort_values(by='영업매장수', ascending=False)
        
        if ranked_df.empty:
            st.warning("조건에 맞는 브랜드가 없습니다.")
        else:
            winner = ranked_df.iloc[0]
            runner_up = ranked_df.iloc[1] if len(ranked_df) > 1 else None
            
            # --- 1등 강조 섹션 ---
            st.markdown(f"""
            <div class="highlight-box">
                <h3 style="margin:0; color:#1E40AF;">
                    🎉 {selected_region} <span style='color:#EF4444;'>{selected_category}</span> 분야 1위는 '<b>{winner['브랜드']}</b>'
                </h3>
                <p style="margin:5px 0 0 0;">
                    점유 매장: <b>{winner['영업매장수']:,}개</b> 
                    {f"(2위 {runner_up['브랜드']} 대비 +{int(winner['영업매장수'] - runner_up['영업매장수'])}개)" if runner_up is not None else ""}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # --- 분석 로직 (기존 로직 유지) ---
            # (1) 지역 특징 Z-Score
            region_stats = df.groupby('시도')[['비율_10대', '비율_2030여성', '비율_4050세대', '1인가구_비중', '1인당지역총소득']].mean()
            scaler = StandardScaler()
            region_scaled = pd.DataFrame(scaler.fit_transform(region_stats), columns=region_stats.columns, index=region_stats.index)
            target_region_score = region_scaled.loc[selected_region]
            
            # (2) 브랜드 상관관계 (전국 기준)
            brand_data = df[df['브랜드'] == winner['브랜드']]
            
            if len(brand_data) > 3:
                corrs = {
                    '가족친화 (10대)': brand_data['인구1만명당_매장수'].corr(brand_data['비율_10대']),
                    '트렌드 (2030여성)': brand_data['인구1만명당_매장수'].corr(brand_data['비율_2030여성']),
                    '중장년 (4050)': brand_data['인구1만명당_매장수'].corr(brand_data['비율_4050세대']),
                    '1인가구 (청년)': brand_data['인구1만명당_매장수'].corr(brand_data['1인가구_비중']),
                    '구매력 (소득)': brand_data['인구1만명당_매장수'].corr(brand_data['1인당지역총소득'])
                }
                
                # 시각화 (지역 특징 vs 브랜드 성향)
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    # 지역 특징 시각화
                    traits = {
                        '가족친화 (10대)': target_region_score['비율_10대'],
                        '트렌드 (2030여성)': target_region_score['비율_2030여성'],
                        '중장년 (4050)': target_region_score['비율_4050세대'],
                        '1인가구 (청년)': target_region_score['1인가구_비중'],
                        '구매력 (소득)': target_region_score['1인당지역총소득']
                    }
                    fig_trait = go.Figure()
                    colors = ['crimson' if v > 0 else 'gray' for k, v in traits.items()]
                    fig_trait.add_trace(go.Bar(y=list(traits.keys()), x=list(traits.values()), orientation='h', marker_color=colors))
                    fig_trait.update_layout(title=f"{selected_region} 인구 특징 (Z-Score)", height=300, margin=dict(t=30,b=0))
                    st.plotly_chart(fig_trait, use_container_width=True)
                    
                with col_g2:
                    # 브랜드 성향 시각화
                    fig_corr = go.Figure()
                    fig_corr.add_trace(go.Bar(x=list(corrs.keys()), y=list(corrs.values()), marker_color='#3B82F6'))
                    fig_corr.update_layout(title=f"{winner['브랜드']}의 입점 성공 요인", height=300, margin=dict(t=30,b=0))
                    st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.info("데이터가 부족하여 상세 분석을 생략합니다.")


# =========================================================
# TAB 2: 라이벌 전격 비교 (Brand vs Brand)
# =========================================================
with tab2:
    st.subheader("⚔️ 브랜드 vs 브랜드: 누가 더 우세한가?")
    
    # 선택 UI
    rc1, rc2, rc3 = st.columns([1, 1, 1])
    with rc1:
        comp_cat = st.selectbox("업태 선택", sorted(df['업태 구분명'].unique()), key='comp_cat')
    
    # 해당 업태의 브랜드만 필터링
    cat_brands = sorted(df[df['업태 구분명'] == comp_cat]['브랜드'].unique())
    
    with rc2:
        brand_a = st.selectbox("브랜드 A (기준)", cat_brands, index=0)
    with rc3:
        # Brand A가 아닌 것 중 선택되도록
        brand_b_options = [b for b in cat_brands if b != brand_a]
        brand_b = st.selectbox("브랜드 B (비교)", brand_b_options, index=0 if brand_b_options else 0)

    if brand_a and brand_b:
        # 데이터 준비
        df_a = df[df['브랜드'] == brand_a]
        df_b = df[df['브랜드'] == brand_b]
        
        # 1. 핵심 지표 비교 (Metrics)
        m1, m2, m3, m4 = st.columns(4)
        total_a = df_a['영업매장수'].sum()
        total_b = df_b['영업매장수'].sum()
        
        new_a = df_a['신규매장수'].sum()
        new_b = df_b['신규매장수'].sum()
        
        m1.metric(f"{brand_a} 총 매장", f"{total_a:,}", delta=int(total_a - total_b))
        m2.metric(f"{brand_b} 총 매장", f"{total_b:,}", delta=int(total_b - total_a))
        m3.metric(f"{brand_a} 신규 오픈", f"{new_a:,}", delta=int(new_a - new_b), delta_color="off")
        m4.metric(f"{brand_b} 신규 오픈", f"{new_b:,}", delta=int(new_b - new_a), delta_color="off")
        
        st.divider()
        
        # 2. DNA 레이더 차트 (성향 비교)
        c_radar, c_bar = st.columns([1, 1])
        
        with c_radar:
            st.markdown("#### 🧬 브랜드 DNA 비교 (타겟 성향)")
            
            def get_corrs(sub_df):
                if len(sub_df) < 3: return [0,0,0,0,0]
                return [
                    sub_df['인구1만명당_매장수'].corr(sub_df['비율_10대']),
                    sub_df['인구1만명당_매장수'].corr(sub_df['비율_2030여성']),
                    sub_df['인구1만명당_매장수'].corr(sub_df['1인가구_비중']),
                    sub_df['인구1만명당_매장수'].corr(sub_df['비율_4050세대']),
                    sub_df['인구1만명당_매장수'].corr(sub_df['1인당지역총소득'])
                ]
            
            categories_radar = ['가족친화(10대)', '트렌드(2030여)', '1인가구(청년)', '중장년(4050)', '구매력(소득)']
            val_a = get_corrs(df_a)
            val_b = get_corrs(df_b)
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=val_a, theta=categories_radar, fill='toself', name=brand_a, line_color='#1E40AF'))
            fig_radar.add_trace(go.Scatterpolar(r=val_b, theta=categories_radar, fill='toself', name=brand_b, line_color='#EF4444'))
            
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[-0.5, 1])), showlegend=True, height=400)
            st.plotly_chart(fig_radar, use_container_width=True)
            
        with c_bar:
            st.markdown(f"#### 🗺️ 지역별 매장 수 대결")
            # 시도별 매장 수 병합
            merge_df = pd.merge(
                df_a[['시도', '영업매장수']].rename(columns={'영업매장수': brand_a}),
                df_b[['시도', '영업매장수']].rename(columns={'영업매장수': brand_b}),
                on='시도', how='outer'
            ).fillna(0)
            
            # 그래프
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(name=brand_a, x=merge_df['시도'], y=merge_df[brand_a], marker_color='#1E40AF'))
            fig_comp.add_trace(go.Bar(name=brand_b, x=merge_df['시도'], y=merge_df[brand_b], marker_color='#EF4444'))
            fig_comp.update_layout(barmode='group', height=400)
            st.plotly_chart(fig_comp, use_container_width=True)


# =========================================================
# TAB 3: 브랜드 전체 포지셔닝 (Overview)
# =========================================================
with tab3:
    st.subheader("📊 브랜드 포지셔닝 맵")
    
    # 업태 필터 추가
    all_cats = ['전체'] + sorted(df['업태 구분명'].unique().tolist())
    pos_cat = st.selectbox("표시할 업태 선택", all_cats, key='pos_cat')
    
    # 포지셔닝 맵 데이터 준비
    brand_stats = []
    
    target_df = df if pos_cat == '전체' else df[df['업태 구분명'] == pos_cat]
    
    for brand in target_df['브랜드'].unique():
        b_df = df[df['브랜드'] == brand] # 전체 데이터에서 계산해야 상관계수 정확
        if len(b_df) < 5: continue
        
        corr_family = b_df['인구1만명당_매장수'].corr(b_df['비율_10대'])
        corr_income = b_df['인구1만명당_매장수'].corr(b_df['1인당지역총소득'])
        
        brand_stats.append({
            '브랜드': brand,
            '업종': b_df['업태 구분명'].iloc[0],
            '가족친화도': corr_family,
            '고소득친화도': corr_income,
            '총매장수': b_df['영업매장수'].sum()
        })
    
    df_pos = pd.DataFrame(brand_stats)
    
    if not df_pos.empty:
        fig_pos = px.scatter(
            df_pos,
            x='가족친화도',
            y='고소득친화도',
            color='업종',
            size='총매장수',
            text='브랜드',
            hover_data=['브랜드'],
            title=f"포지셔닝 맵 ({pos_cat})",
            size_max=40,
            height=600
        )
        # 사분면 가이드
        fig_pos.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.3)
        fig_pos.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.3)
        fig_pos.add_annotation(x=0.5, y=0.5, text="💎 부촌/학군<br>(Premium Family)", showarrow=False, font=dict(color="blue"))
        fig_pos.add_annotation(x=-0.5, y=0.5, text="💼 오피스/번화가<br>(Premium Single)", showarrow=False, font=dict(color="red"))
        fig_pos.add_annotation(x=0.5, y=-0.5, text="🏠 주거밀집/가성비<br>(Budget Family)", showarrow=False, font=dict(color="green"))
        
        fig_pos.update_traces(textposition='top center')
        st.plotly_chart(fig_pos, use_container_width=True)
    else:
        st.error("데이터가 부족합니다.")