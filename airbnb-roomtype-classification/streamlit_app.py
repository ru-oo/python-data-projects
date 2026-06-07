"""
Streamlit 시각화 앱
XGBoost vs Random Forest 비교 및 예측
"""

import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.metrics import confusion_matrix, classification_report
import warnings
warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="Room Type Classifier",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Windows 경로
MODEL_PATH = r'models\room_type_models.pkl'  # 수정 필요

# ============================================================================
# 모델 로드
# ============================================================================
@st.cache_resource
def load_models():
    """모델 및 데이터 로드"""
    try:
        with open(MODEL_PATH, 'rb') as f:
            data = pickle.load(f)
        return data
    except FileNotFoundError:
        st.error(f"❌ 모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
        st.info("먼저 train_and_compare_models.py를 실행하세요!")
        st.stop()

# 데이터 로드
with st.spinner('모델 로딩 중...'):
    model_data = load_models()

rf_model = model_data['rf_model']
xgb_model = model_data['xgb_model']
scaler = model_data['scaler']
feature_names = model_data['feature_names']
class_names = model_data['class_names']
X_test = model_data['X_test']
y_test = model_data['y_test']
y_pred_rf = model_data['y_pred_rf']
y_pred_xgb = model_data['y_pred_xgb']
comparison_df = model_data['comparison_df']
rf_metrics = model_data['rf_metrics']
xgb_metrics = model_data['xgb_metrics']

# ============================================================================
# 헤더
# ============================================================================
st.markdown('<h1 class="main-header">🏠 Room Type Classifier</h1>', unsafe_allow_html=True)
st.markdown('### XGBoost vs Random Forest 비교 및 예측')
st.markdown('---')

# ============================================================================
# 사이드바 - 모델 선택
# ============================================================================
st.sidebar.header("⚙️ 설정")
selected_model = st.sidebar.selectbox(
    "예측에 사용할 모델 선택",
    ["Random Forest", "XGBoost", "앙상블 (투표)"]
)

st.sidebar.markdown("---")
st.sidebar.header("📊 모델 정보")
st.sidebar.metric("Random Forest Accuracy", f"{rf_metrics['test_acc']:.2%}")
st.sidebar.metric("XGBoost Accuracy", f"{xgb_metrics['test_acc']:.2%}")

# ============================================================================
# 탭 구성
# ============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 모델 비교", 
    "🎯 예측하기", 
    "📈 성능 분석",
    "🔍 Feature Importance"
])

# ============================================================================
# 탭 1: 모델 비교
# ============================================================================
with tab1:
    st.header("📊 모델 성능 비교")
    
    # 성능 지표 비교
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🎯 Test Accuracy",
            f"{max(rf_metrics['test_acc'], xgb_metrics['test_acc']):.2%}",
            delta=f"{abs(rf_metrics['test_acc'] - xgb_metrics['test_acc']):.2%}"
        )
    
    with col2:
        st.metric(
            "📈 F1-Score (Macro)",
            f"{max(rf_metrics['f1_macro'], xgb_metrics['f1_macro']):.3f}",
            delta=f"{abs(rf_metrics['f1_macro'] - xgb_metrics['f1_macro']):.3f}"
        )
    
    with col3:
        winner = "Random Forest" if rf_metrics['test_acc'] > xgb_metrics['test_acc'] else "XGBoost"
        st.metric("🏆 최고 모델", winner)
    
    with col4:
        overfitting_rf = rf_metrics['train_acc'] - rf_metrics['test_acc']
        overfitting_xgb = xgb_metrics['train_acc'] - xgb_metrics['test_acc']
        better_gen = "RF" if overfitting_rf < overfitting_xgb else "XGB"
        st.metric("🎓 일반화", better_gen)
    
    st.markdown("---")
    
    # 비교 테이블
    st.subheader("📋 상세 성능 지표")
    st.dataframe(
        comparison_df.style.highlight_max(axis=0, 
                                         subset=['Test Accuracy', 'F1-Score (Macro)', 'F1-Score (Weighted)'],
                                         color='lightgreen')
                          .highlight_min(axis=0, 
                                        subset=['Overfitting'],
                                        color='lightgreen')
                          .format({
                              'Train Accuracy': '{:.4f}',
                              'Test Accuracy': '{:.4f}',
                              'F1-Score (Macro)': '{:.4f}',
                              'F1-Score (Weighted)': '{:.4f}',
                              'Overfitting': '{:.4f}'
                          }),
        use_container_width=True
    )
    
    st.markdown("---")
    
    # 성능 비교 그래프
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 성능 지표 비교")
        
        fig = go.Figure()
        
        metrics_names = ['Test Accuracy', 'F1 (Macro)', 'F1 (Weighted)']
        rf_scores = [rf_metrics['test_acc'], rf_metrics['f1_macro'], rf_metrics['f1_weighted']]
        xgb_scores = [xgb_metrics['test_acc'], xgb_metrics['f1_macro'], xgb_metrics['f1_weighted']]
        
        fig.add_trace(go.Bar(
            name='Random Forest',
            x=metrics_names,
            y=rf_scores,
            marker_color='#3498db',
            text=[f'{v:.3f}' for v in rf_scores],
            textposition='outside'
        ))
        
        fig.add_trace(go.Bar(
            name='XGBoost',
            x=metrics_names,
            y=xgb_scores,
            marker_color='#e74c3c',
            text=[f'{v:.3f}' for v in xgb_scores],
            textposition='outside'
        ))
        
        fig.update_layout(
            barmode='group',
            yaxis_range=[0, 1.1],
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 과적합 비교")
        
        fig2 = go.Figure()
        
        overfitting_data = [overfitting_rf, overfitting_xgb]
        
        fig2.add_trace(go.Bar(
            x=['Random Forest', 'XGBoost'],
            y=overfitting_data,
            marker_color=['#3498db', '#e74c3c'],
            text=[f'{v:.3f}' for v in overfitting_data],
            textposition='outside'
        ))
        
        fig2.add_hline(y=0.05, line_dash="dash", line_color="orange",
                      annotation_text="Threshold (0.05)")
        
        fig2.update_layout(
            yaxis_title="Train - Test Gap",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig2, use_container_width=True)

# ============================================================================
# 탭 2: 예측하기
# ============================================================================
with tab2:
    st.header("🎯 새로운 데이터 예측")
    
    st.info("💡 숙소 정보를 입력하면 room type을 예측합니다!")
    
    # 입력 폼
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📍 위치 정보")
        latitude = st.number_input("위도 (Latitude)", value=40.75, min_value=40.5, max_value=40.92, step=0.01)
        longitude = st.number_input("경도 (Longitude)", value=-73.98, min_value=-74.25, max_value=-73.70, step=0.01)
        neighbourhood = st.selectbox("자치구", [
            "Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"
        ])
        
    with col2:
        st.subheader("🏠 시설 정보")
        bedrooms = st.number_input("침실 수", value=1, min_value=0, max_value=9, step=1)
        baths = st.number_input("욕실 수", value=1.0, min_value=0.5, max_value=5.0, step=0.5)
        minimum_nights = st.number_input("최소 숙박일", value=30, min_value=1, max_value=365, step=1)
    
    with col3:
        st.subheader("⭐ 리뷰 정보")
        rating = st.slider("평점 (0=없음)", 0.0, 5.0, 4.5, step=0.1)
        number_of_reviews = st.number_input("총 리뷰 수", value=10, min_value=0, max_value=1000, step=1)
        reviews_per_month = st.number_input("월 평균 리뷰", value=1.0, min_value=0.0, max_value=10.0, step=0.1)
        days_since_last_review = st.number_input("마지막 리뷰 경과일", value=400, min_value=0, max_value=3000, step=10)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏢 호스트 정보")
        host_listings = st.number_input("호스트 리스팅 수", value=1, min_value=1, max_value=100, step=1)
    
    with col2:
        st.subheader("📅 가용성")
        availability = st.number_input("연간 이용가능일", value=300, min_value=0, max_value=365, step=1)
    
    # 예측 버튼
    if st.button("🔮 예측하기", type="primary", use_container_width=True):
        # 자치구 인코딩
        neighbourhood_mapping = {
            "Bronx": 0, "Brooklyn": 1, "Manhattan": 2, "Queens": 3, "Staten Island": 4
        }
        neighbourhood_encoded = neighbourhood_mapping[neighbourhood]
        
        # 입력 데이터 생성
        input_data = pd.DataFrame({
            'latitude': [latitude],
            'longitude': [longitude],
            'minimum_nights': [minimum_nights],
            'number_of_reviews': [number_of_reviews],
            'reviews_per_month': [reviews_per_month],
            'calculated_host_listings_count': [host_listings],
            'availability_365': [availability],
            'rating_numeric': [rating],
            'bedrooms_numeric': [bedrooms],
            'baths_numeric': [baths],
            'days_since_last_review': [days_since_last_review],
            'neighbourhood_group_encoded': [neighbourhood_encoded]
        })
        
        # 스케일링
        input_scaled = scaler.transform(input_data)
        
        # 예측
        if selected_model == "Random Forest":
            pred = rf_model.predict(input_scaled)[0]
            pred_proba = rf_model.predict_proba(input_scaled)[0]
        elif selected_model == "XGBoost":
            pred = xgb_model.predict(input_scaled)[0]
            pred_proba = xgb_model.predict_proba(input_scaled)[0]
        else:  # 앙상블
            pred_rf = rf_model.predict(input_scaled)[0]
            pred_xgb = xgb_model.predict(input_scaled)[0]
            
            # 확률 평균
            pred_proba_rf = rf_model.predict_proba(input_scaled)[0]
            pred_proba_xgb = xgb_model.predict_proba(input_scaled)[0]
            pred_proba = (pred_proba_rf + pred_proba_xgb) / 2
            
            # 가장 높은 확률의 클래스
            pred = np.argmax(pred_proba)
        
        # 결과 표시
        st.success(f"### 🎉 예측 결과: **{class_names[pred]}**")
        
        # 확률 표시
        st.subheader("📊 클래스별 확률")
        
        prob_df = pd.DataFrame({
            'Room Type': [class_names[i] for i in range(4)],
            'Probability': pred_proba
        }).sort_values('Probability', ascending=False)
        
        fig_prob = px.bar(
            prob_df,
            x='Probability',
            y='Room Type',
            orientation='h',
            text=[f'{p:.1%}' for p in prob_df['Probability']],
            color='Probability',
            color_continuous_scale='Blues'
        )
        
        fig_prob.update_layout(height=300, showlegend=False)
        fig_prob.update_traces(textposition='outside')
        
        st.plotly_chart(fig_prob, use_container_width=True)

# ============================================================================
# 탭 3: 성능 분석
# ============================================================================
with tab3:
    st.header("📈 모델 성능 상세 분석")
    
    # 모델 선택
    analysis_model = st.selectbox("분석할 모델 선택", ["Random Forest", "XGBoost"])
    
    if analysis_model == "Random Forest":
        y_pred_selected = y_pred_rf
        model_name = "Random Forest"
    else:
        y_pred_selected = y_pred_xgb
        model_name = "XGBoost"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"🎯 {model_name} Confusion Matrix")
        
        cm = confusion_matrix(y_test, y_pred_selected)
        
        fig_cm = go.Figure(data=go.Heatmap(
            z=cm,
            x=[class_names[i] for i in range(4)],
            y=[class_names[i] for i in range(4)],
            colorscale='Blues',
            text=cm,
            texttemplate='%{text}',
            textfont={"size": 16}
        ))
        
        fig_cm.update_layout(
            xaxis_title="Predicted",
            yaxis_title="Actual",
            height=400
        )
        
        st.plotly_chart(fig_cm, use_container_width=True)
    
    with col2:
        st.subheader(f"📊 {model_name} 클래스별 성능")
        
        from sklearn.metrics import precision_recall_fscore_support
        
        precision, recall, f1, support = precision_recall_fscore_support(
            y_test, y_pred_selected, labels=[0, 1, 2, 3], zero_division=0
        )
        
        perf_df = pd.DataFrame({
            'Class': [class_names[i] for i in range(4)],
            'Precision': precision,
            'Recall': recall,
            'F1-Score': f1,
            'Support': support
        })
        
        fig_perf = go.Figure()
        
        fig_perf.add_trace(go.Bar(name='Precision', x=perf_df['Class'], y=perf_df['Precision']))
        fig_perf.add_trace(go.Bar(name='Recall', x=perf_df['Class'], y=perf_df['Recall']))
        fig_perf.add_trace(go.Bar(name='F1-Score', x=perf_df['Class'], y=perf_df['F1-Score']))
        
        fig_perf.update_layout(barmode='group', height=400, yaxis_range=[0, 1.1])
        
        st.plotly_chart(fig_perf, use_container_width=True)
    
    # Classification Report
    st.subheader(f"📋 {model_name} Classification Report")
    
    report = classification_report(
        y_test, y_pred_selected,
        target_names=[class_names[i] for i in range(4)],
        output_dict=True,
        zero_division=0
    )
    
    report_df = pd.DataFrame(report).transpose()
    st.dataframe(
        report_df.style.format("{:.3f}").background_gradient(cmap='YlGnBu'),
        use_container_width=True
    )

# ============================================================================
# 탭 4: Feature Importance
# ============================================================================
with tab4:
    st.header("🔍 Feature Importance 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌲 Random Forest")
        
        rf_importance = pd.DataFrame({
            'Feature': feature_names,
            'Importance': rf_model.feature_importances_
        }).sort_values('Importance', ascending=False)
        
        fig_rf_imp = px.bar(
            rf_importance,
            x='Importance',
            y='Feature',
            orientation='h',
            text=[f'{v:.4f}' for v in rf_importance['Importance']],
            color='Importance',
            color_continuous_scale='Blues'
        )
        
        fig_rf_imp.update_layout(height=500, showlegend=False)
        fig_rf_imp.update_traces(textposition='outside')
        fig_rf_imp.update_yaxes(categoryorder='total ascending')
        
        st.plotly_chart(fig_rf_imp, use_container_width=True)
    
    with col2:
        st.subheader("🚀 XGBoost")
        
        xgb_importance = pd.DataFrame({
            'Feature': feature_names,
            'Importance': xgb_model.feature_importances_
        }).sort_values('Importance', ascending=False)
        
        fig_xgb_imp = px.bar(
            xgb_importance,
            x='Importance',
            y='Feature',
            orientation='h',
            text=[f'{v:.4f}' for v in xgb_importance['Importance']],
            color='Importance',
            color_continuous_scale='Reds'
        )
        
        fig_xgb_imp.update_layout(height=500, showlegend=False)
        fig_xgb_imp.update_traces(textposition='outside')
        fig_xgb_imp.update_yaxes(categoryorder='total ascending')
        
        st.plotly_chart(fig_xgb_imp, use_container_width=True)
    
    # 비교 테이블
    st.subheader("📊 Feature Importance 비교")
    
    comparison_importance = pd.DataFrame({
        'Feature': feature_names,
        'RF Importance': rf_model.feature_importances_,
        'XGB Importance': xgb_model.feature_importances_
    }).sort_values('XGB Importance', ascending=False)
    
    st.dataframe(
        comparison_importance.style.format({
            'RF Importance': '{:.4f}',
            'XGB Importance': '{:.4f}'
        }).background_gradient(subset=['RF Importance', 'XGB Importance'], cmap='YlOrRd'),
        use_container_width=True
    )

# ============================================================================
# 푸터
# ============================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 2rem;'>
    <p>🏠 Room Type Classifier | Built with Streamlit & Machine Learning</p>
    <p>Models: Random Forest & XGBoost with Class Weighting</p>
</div>
""", unsafe_allow_html=True)