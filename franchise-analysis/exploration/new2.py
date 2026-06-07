import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(layout="wide", page_title="프랜차이즈 지역 제패의 비밀")

st.markdown("""
    <style>
    .main-title { font-size: 2.2rem; font-weight: 800; color: #111827; margin-bottom: 0px; }
    .sub-text { font-size: 1.0rem; color: #6B7280; margin-bottom: 20px; }
    .highlight-box { background-color: #EFF6FF; padding: 20px; border-radius: 12px; border: 1px solid #BFDBFE; margin-bottom: 20px; }
    .metric-card { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🏆 프랜차이즈, 왜 거기서 1등일까?</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-text">데이터로 밝혀내는 지역별 1위 브랜드의 인구학적 성공 요인</div>', unsafe_allow_html=True)

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
    df['1인가구_비중'] = df['1인가구_40세이하_비율'] # 컬럼명 단축
    
    return df

df = load_data()

# ---------------------------------------------------------
# 3. 분석 탭 구성
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["🗺️ 지역별 1등 심층 분석", "📊 브랜드 전체 포지셔닝"])

# =========================================================
# TAB 1: 지역별 1등 심층 분석 (The Core Logic)
# =========================================================
with tab1:
    if df.empty:
        st.error("데이터가 없습니다.")
    else:
        # 1. 지역 선택
        col_sel1, col_sel2 = st.columns([1, 3])
        with col_sel1:
            selected_region = st.selectbox("📍 분석할 지역(시도)을 선택하세요", df['시도'].unique())
        
        # 2. 해당 지역 데이터 추출 및 1등 계산
        region_df = df[df['시도'] == selected_region].sort_values(by='영업매장수', ascending=False)
        if region_df.empty:
            st.warning("해당 지역 데이터가 부족합니다.")
        else:
            winner = region_df.iloc[0]
            runner_up = region_df.iloc[1] if len(region_df) > 1 else None
            
            # --- 1등 강조 섹션 ---
            with st.container():
                st.markdown(f"""
                <div class="highlight-box">
                    <h3 style="margin:0; color:#1E40AF;">🎉 {selected_region}의 지배자는 '<b>{winner['브랜드']}</b>' 입니다.</h3>
                    <p style="margin:5px 0 0 0;">
                        총 <b>{winner['영업매장수']:,}개</b> 매장 운영 중 | 
                        2위({runner_up['브랜드'] if runner_up is not None else '-'}) 대비 
                        <b>{int(winner['영업매장수'] - (runner_up['영업매장수'] if runner_up is not None else 0))}개</b> 더 많음
                    </p>
                </div>
                """, unsafe_allow_html=True)

            # --- 분석 로직: 왜 1등인가? (Why?) ---
            st.subheader(f"🤔 {winner['브랜드']}는 왜 {selected_region}에서 잘될까?")
            
            # (1) 지역의 특징 파악 (전국 평균 대비 Z-Score)
            # 전국 시도별 평균 데이터 계산
            region_stats = df.groupby('시도')[['비율_10대', '비율_2030여성', '비율_4050세대', '1인가구_비중', '1인당지역총소득']].mean()
            
            # 스케일링 (Z-Score)
            scaler = StandardScaler()
            region_scaled = pd.DataFrame(scaler.fit_transform(region_stats), 
                                       columns=region_stats.columns, 
                                       index=region_stats.index)
            
            target_region_score = region_scaled.loc[selected_region]
            
            # (2) 시각화: 지역 특징 vs 브랜드 점유율
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.markdown("#### 1. 지역의 인구학적 DNA")
                st.caption(f"{selected_region}이 전국 평균 대비 어떤 특징을 가졌는지 보여줍니다.")
                
                # 특성 데이터 준비
                traits = {
                    '학생/가족 (10대)': target_region_score['비율_10대'],
                    '트렌드 (2030여성)': target_region_score['비율_2030여성'],
                    '중장년 (4050)': target_region_score['비율_4050세대'],
                    '1인가구 (청년)': target_region_score['1인가구_비중'],
                    '구매력 (소득)': target_region_score['1인당지역총소득']
                }
                
                # 값이 큰 순서대로 정렬하여 Top 3 특징 추출
                sorted_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)
                top_trait = sorted_traits[0][0]
                
                # Bar Chart
                fig_trait = go.Figure()
                colors = ['crimson' if v > 0 else 'gray' for k, v in traits.items()]
                
                fig_trait.add_trace(go.Bar(
                    y=list(traits.keys()),
                    x=list(traits.values()),
                    orientation='h',
                    marker_color=colors,
                    text=[f"{v:.1f}σ" for v in traits.values()],
                    textposition='auto'
                ))
                fig_trait.update_layout(
                    title=f"{selected_region}의 특징 (0=전국평균)",
                    xaxis_title="표준편차 (Z-Score)",
                    height=300,
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                st.plotly_chart(fig_trait, use_container_width=True)
                
            with c2:
                st.markdown(f"#### 2. {winner['브랜드']}의 타겟 적중률")
                st.caption(f"이 브랜드가 전국적으로 어떤 인구층과 친한지 확인합니다.")
                
                # 브랜드의 전국 상관계수 계산
                brand_data = df[df['브랜드'] == winner['브랜드']]
                if len(brand_data) > 3:
                    corrs = {
                        '학생/가족 (10대)': brand_data['인구1만명당_매장수'].corr(brand_data['비율_10대']),
                        '트렌드 (2030여성)': brand_data['인구1만명당_매장수'].corr(brand_data['비율_2030여성']),
                        '중장년 (4050)': brand_data['인구1만명당_매장수'].corr(brand_data['비율_4050세대']),
                        '1인가구 (청년)': brand_data['인구1만명당_매장수'].corr(brand_data['1인가구_비중']),
                        '구매력 (소득)': brand_data['인구1만명당_매장수'].corr(brand_data['1인당지역총소득'])
                    }
                    
                    # 가장 강한 상관관계 찾기
                    sorted_corrs = sorted(corrs.items(), key=lambda x: x[1], reverse=True)
                    best_match = sorted_corrs[0][0]
                    
                    # Radar Chart or Bar Chart for Brand DNA
                    fig_corr = go.Figure()
                    fig_corr.add_trace(go.Bar(
                        x=list(corrs.keys()),
                        y=list(corrs.values()),
                        marker_color='#3B82F6'
                    ))
                    fig_corr.update_layout(
                        title=f"{winner['브랜드']} 입점 성공 요인 (상관계수)",
                        yaxis_title="상관계수 (1에 가까울수록 강력)",
                        height=300,
                        margin=dict(l=0, r=0, t=40, b=0)
                    )
                    st.plotly_chart(fig_corr, use_container_width=True)
                else:
                    st.info("브랜드 데이터가 부족하여 상관관계를 분석할 수 없습니다.")
                    best_match = "분석 불가"

            # --- 결론 도출 (Insight Message) ---
            st.divider()
            
            # 논리적 결론 생성
            match_score = traits.get(best_match, 0)
            
            st.markdown(f"### 💡 데이터 기반 인사이트: {selected_region} X {winner['브랜드']}")
            
            insight_html = f"""
            <ul>
                <li><b>지역 팩트:</b> {selected_region}은 전국 평균보다 <b>'{top_trait}'</b> 성향이 강합니다.</li>
                <li><b>브랜드 팩트:</b> {winner['브랜드']}는 통계적으로 <b>'{best_match}'</b>이(가) 많은 곳에서 매장 수가 늘어납니다.</li>
            </ul>
            """
            st.markdown(insight_html, unsafe_allow_html=True)

            if top_trait == best_match:
                st.success(f"✅ **완벽한 매칭!** {selected_region}의 풍부한 '{top_trait}' 인구가 {winner['브랜드']}의 핵심 타겟과 정확히 일치하여 1등을 차지했습니다.")
            elif traits[best_match] > 0:
                st.info(f"☑️ **유효한 전략.** {selected_region}은 {winner['브랜드']}가 선호하는 '{best_match}' 지표가 평균 이상이므로 경쟁력이 있습니다.")
            else:
                st.warning(f"❓ **의외의 결과.** {selected_region}은 {winner['브랜드']}가 선호하는 '{best_match}' 지표가 낮음에도 1등입니다. 경쟁사 부재나 선점 효과 등 다른 요인이 있을 수 있습니다.")

            # --- 추가: 시장 점유율 파이 차트 ---
            st.markdown("#### 🍰 이 지역 시장 점유율 (Top 5)")
            top5 = region_df.head(5)
            fig_pie = px.pie(top5, values='영업매장수', names='브랜드', hole=0.4,
                             color_discrete_sequence=px.colors.sequential.RdBu)
            fig_pie.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)


# =========================================================
# TAB 2: 브랜드 전체 포지셔닝 (Overview)
# =========================================================
with tab2:
    st.subheader("📊 브랜드별 타겟팅 지도")
    st.caption("가로축은 가족/학생, 세로축은 구매력을 나타냅니다. 브랜드가 어디에 위치하는지 확인하세요.")
    
    # 포지셔닝 맵 데이터 준비 (전체 브랜드 대상)
    brand_stats = []
    for brand in df['브랜드'].unique():
        b_df = df[df['브랜드'] == brand]
        if len(b_df) < 5: continue
        
        # 상관관계 계산
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
            title="브랜드 포지셔닝 맵 (Family vs Income)",
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
        st.error("포지셔닝 맵을 그릴 충분한 데이터가 없습니다.")