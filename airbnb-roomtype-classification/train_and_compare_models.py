"""
XGBoost vs Random Forest 비교
- 두 모델 학습 및 비교
- pkl 파일로 저장
- Windows 경로 사용
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, 
    precision_recall_fscore_support
)
from sklearn.utils.class_weight import compute_class_weight
import xgboost as xgb
import pickle
import warnings
warnings.filterwarnings('ignore')

# Windows 경로 설정
DATA_PATH = r'preprocessed_airbnb_data_final.csv'  # 수정 필요
SAVE_DIR = r'models'  # 수정 필요

print("=" * 80)
print("XGBoost vs Random Forest 비교")
print("=" * 80)

# ============================================================================
# 1. 데이터 로드
# ============================================================================
print("\n[1단계] 데이터 로드")
print("-" * 80)

df = pd.read_csv(DATA_PATH)
print(f"✅ 데이터 로드 완료: {df.shape}")

# 특성과 타겟 분리
X = df.drop(['room_type_encoded', 'price'], axis=1)
y = df['room_type_encoded']

print(f"특성(X): {X.shape}")
print(f"타겟(y): {y.shape}")

# 클래스 이름
class_names = {
    0: "Entire home/apt",
    1: "Hotel room",
    2: "Private room",
    3: "Shared room"
}

print("\n클래스 분포:")
for cls in sorted(y.unique()):
    count = (y == cls).sum()
    pct = count / len(y) * 100
    print(f"  {cls}: {class_names[cls]:20s} - {count:5d}개 ({pct:5.2f}%)")

# ============================================================================
# 2. 데이터 분할 및 스케일링
# ============================================================================
print("\n[2단계] 데이터 분할 및 스케일링")
print("-" * 80)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"Train: {X_train.shape[0]}개, Test: {X_test.shape[0]}개")
print("✅ 스케일링 완료")

# ============================================================================
# 3. 클래스 가중치 계산
# ============================================================================
print("\n[3단계] 클래스 가중치 계산")
print("-" * 80)

class_weights = compute_class_weight(
    'balanced',
    classes=np.unique(y_train),
    y=y_train
)

print("계산된 가중치:")
for cls, weight in zip(np.unique(y_train), class_weights):
    print(f"  {cls}: {weight:.4f}")

sample_weights = np.array([class_weights[y] for y in y_train])

# ============================================================================
# 4. Random Forest 학습
# ============================================================================
print("\n[4단계] Random Forest 학습")
print("-" * 80)

rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=12,              # 과적합 방지: 트리 깊이 제한
    min_samples_split=10,      # 과적합 방지: 분할 최소 샘플
    min_samples_leaf=5,        # 과적합 방지: leaf 최소 샘플
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)

print("학습 중...")
rf_model.fit(X_train_scaled, y_train)

y_pred_rf_train = rf_model.predict(X_train_scaled)
y_pred_rf_test = rf_model.predict(X_test_scaled)

rf_train_acc = accuracy_score(y_train, y_pred_rf_train)
rf_test_acc = accuracy_score(y_test, y_pred_rf_test)
rf_f1_macro = f1_score(y_test, y_pred_rf_test, average='macro')
rf_f1_weighted = f1_score(y_test, y_pred_rf_test, average='weighted')

print("✅ Random Forest 학습 완료")
print(f"  Train Acc: {rf_train_acc:.4f}")
print(f"  Test Acc:  {rf_test_acc:.4f}")
print(f"  F1 (Macro): {rf_f1_macro:.4f}")

# ============================================================================
# 5. XGBoost 학습
# ============================================================================
print("\n[5단계] XGBoost 학습")
print("-" * 80)

xgb_model = xgb.XGBClassifier(
    objective='multi:softmax',
    num_class=4,
    n_estimators=200,
    max_depth=8,
    learning_rate=0.05,
    subsample=0.7,
    colsample_bytree=0.7,
    min_child_weight=3,
    gamma=0.1,
    reg_alpha=0.1,
    reg_lambda=1.0,
    random_state=42,
    eval_metric='mlogloss',
    verbosity=0
)

print("학습 중 (가중치 적용)...")
xgb_model.fit(X_train_scaled, y_train, sample_weight=sample_weights)

y_pred_xgb_train = xgb_model.predict(X_train_scaled)
y_pred_xgb_test = xgb_model.predict(X_test_scaled)

xgb_train_acc = accuracy_score(y_train, y_pred_xgb_train)
xgb_test_acc = accuracy_score(y_test, y_pred_xgb_test)
xgb_f1_macro = f1_score(y_test, y_pred_xgb_test, average='macro')
xgb_f1_weighted = f1_score(y_test, y_pred_xgb_test, average='weighted')

print("✅ XGBoost 학습 완료")
print(f"  Train Acc: {xgb_train_acc:.4f}")
print(f"  Test Acc:  {xgb_test_acc:.4f}")
print(f"  F1 (Macro): {xgb_f1_macro:.4f}")

# ============================================================================
# 6. 모델 비교
# ============================================================================
print("\n[6단계] 모델 성능 비교")
print("=" * 80)

comparison_df = pd.DataFrame({
    'Model': ['Random Forest', 'XGBoost'],
    'Train Accuracy': [rf_train_acc, xgb_train_acc],
    'Test Accuracy': [rf_test_acc, xgb_test_acc],
    'F1-Score (Macro)': [rf_f1_macro, xgb_f1_macro],
    'F1-Score (Weighted)': [rf_f1_weighted, xgb_f1_weighted],
    'Overfitting': [
        rf_train_acc - rf_test_acc,
        xgb_train_acc - xgb_test_acc
    ]
})

print("\n" + comparison_df.to_string(index=False))

# 승자 결정
if xgb_test_acc > rf_test_acc:
    print(f"\n🏆 승자: XGBoost ({xgb_test_acc:.4f} > {rf_test_acc:.4f})")
    best_model = xgb_model
    best_name = "XGBoost"
else:
    print(f"\n🏆 승자: Random Forest ({rf_test_acc:.4f} > {xgb_test_acc:.4f})")
    best_model = rf_model
    best_name = "Random Forest"

# ============================================================================
# 7. 시각화
# ============================================================================
print("\n[7단계] 시각화 생성")
print("-" * 80)

fig = plt.figure(figsize=(18, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# 1) 모델 성능 비교 (막대 그래프)
ax1 = fig.add_subplot(gs[0, :2])
metrics = ['Test Accuracy', 'F1 (Macro)', 'F1 (Weighted)']
rf_scores = [rf_test_acc, rf_f1_macro, rf_f1_weighted]
xgb_scores = [xgb_test_acc, xgb_f1_macro, xgb_f1_weighted]

x_pos = np.arange(len(metrics))
width = 0.35

bars1 = ax1.bar(x_pos - width/2, rf_scores, width, label='Random Forest', color='#3498db')
bars2 = ax1.bar(x_pos + width/2, xgb_scores, width, label='XGBoost', color='#e74c3c')

ax1.set_ylabel('Score', fontsize=12, fontweight='bold')
ax1.set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
ax1.set_xticks(x_pos)
ax1.set_xticklabels(metrics, fontsize=11)
ax1.legend(fontsize=11)
ax1.set_ylim(0, 1.1)
ax1.grid(axis='y', alpha=0.3)

# 값 표시
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

# 2) 과적합 비교
ax2 = fig.add_subplot(gs[0, 2])
overfitting = [rf_train_acc - rf_test_acc, xgb_train_acc - xgb_test_acc]
colors_over = ['#3498db', '#e74c3c']
bars_over = ax2.bar(['RF', 'XGB'], overfitting, color=colors_over, alpha=0.7)
ax2.set_ylabel('Train - Test Gap', fontsize=11, fontweight='bold')
ax2.set_title('Overfitting Check', fontsize=12, fontweight='bold')
ax2.axhline(y=0.05, color='orange', linestyle='--', linewidth=2, label='Threshold')
ax2.legend(fontsize=9)
ax2.grid(axis='y', alpha=0.3)

for bar, val in zip(bars_over, overfitting):
    ax2.text(bar.get_x() + bar.get_width()/2., val,
            f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

# 3) Random Forest Confusion Matrix
ax3 = fig.add_subplot(gs[1, 0])
cm_rf = confusion_matrix(y_test, y_pred_rf_test)
sns.heatmap(cm_rf, annot=True, fmt='d', cmap='Blues', ax=ax3,
            xticklabels=[class_names[i][:10] for i in sorted(y_test.unique())],
            yticklabels=[class_names[i][:10] for i in sorted(y_test.unique())],
            cbar_kws={'label': 'Count'})
ax3.set_title('Random Forest\nConfusion Matrix', fontsize=12, fontweight='bold')
ax3.set_ylabel('Actual', fontsize=11)
ax3.set_xlabel('Predicted', fontsize=11)

# 4) XGBoost Confusion Matrix
ax4 = fig.add_subplot(gs[1, 1])
cm_xgb = confusion_matrix(y_test, y_pred_xgb_test)
sns.heatmap(cm_xgb, annot=True, fmt='d', cmap='Reds', ax=ax4,
            xticklabels=[class_names[i][:10] for i in sorted(y_test.unique())],
            yticklabels=[class_names[i][:10] for i in sorted(y_test.unique())],
            cbar_kws={'label': 'Count'})
ax4.set_title('XGBoost\nConfusion Matrix', fontsize=12, fontweight='bold')
ax4.set_ylabel('Actual', fontsize=11)
ax4.set_xlabel('Predicted', fontsize=11)

# 5) 클래스별 F1-Score 비교
ax5 = fig.add_subplot(gs[1, 2])
_, _, f1_rf_class, _ = precision_recall_fscore_support(
    y_test, y_pred_rf_test, labels=sorted(y_test.unique()), zero_division=0
)
_, _, f1_xgb_class, _ = precision_recall_fscore_support(
    y_test, y_pred_xgb_test, labels=sorted(y_test.unique()), zero_division=0
)

class_labels = [class_names[i][:10] for i in sorted(y_test.unique())]
x_pos_class = np.arange(len(class_labels))
width_class = 0.35

bars_rf = ax5.bar(x_pos_class - width_class/2, f1_rf_class, width_class, 
                  label='RF', color='#3498db', alpha=0.8)
bars_xgb = ax5.bar(x_pos_class + width_class/2, f1_xgb_class, width_class, 
                   label='XGB', color='#e74c3c', alpha=0.8)

ax5.set_ylabel('F1-Score', fontsize=11, fontweight='bold')
ax5.set_title('Per-Class F1-Score', fontsize=12, fontweight='bold')
ax5.set_xticks(x_pos_class)
ax5.set_xticklabels(class_labels, rotation=20, ha='right', fontsize=9)
ax5.legend(fontsize=10)
ax5.set_ylim(0, 1.1)
ax5.grid(axis='y', alpha=0.3)

# 6) Feature Importance 비교
ax6 = fig.add_subplot(gs[2, :])
feature_names = X.columns

# Random Forest feature importance
rf_importance = rf_model.feature_importances_
# XGBoost feature importance
xgb_importance = xgb_model.feature_importances_

# 정렬 (XGBoost 기준)
indices = np.argsort(xgb_importance)[::-1]
top_n = 12

x_pos_feat = np.arange(top_n)
width_feat = 0.35

bars_rf_feat = ax6.barh(x_pos_feat + width_feat/2, rf_importance[indices[:top_n]], 
                        width_feat, label='Random Forest', color='#3498db', alpha=0.8)
bars_xgb_feat = ax6.barh(x_pos_feat - width_feat/2, xgb_importance[indices[:top_n]], 
                         width_feat, label='XGBoost', color='#e74c3c', alpha=0.8)

ax6.set_yticks(x_pos_feat)
ax6.set_yticklabels(feature_names[indices[:top_n]], fontsize=10)
ax6.set_xlabel('Importance', fontsize=11, fontweight='bold')
ax6.set_title('Feature Importance Comparison (Top 12)', fontsize=12, fontweight='bold')
ax6.legend(fontsize=10)
ax6.invert_yaxis()
ax6.grid(axis='x', alpha=0.3)

plt.suptitle('XGBoost vs Random Forest - Comprehensive Comparison', 
             fontsize=16, fontweight='bold', y=0.995)

# 저장
comparison_plot_path = SAVE_DIR + r'\model_comparison.png'
plt.savefig(comparison_plot_path, dpi=300, bbox_inches='tight')
print(f"✅ 시각화 저장: {comparison_plot_path}")
plt.close()

# ============================================================================
# 8. 모델 저장 (pkl)
# ============================================================================
print("\n[8단계] 모델 및 데이터 저장")
print("-" * 80)

# 저장할 데이터
model_data = {
    'rf_model': rf_model,
    'xgb_model': xgb_model,
    'scaler': scaler,
    'feature_names': X.columns.tolist(),
    'class_names': class_names,
    'X_test': X_test_scaled,
    'y_test': y_test,
    'y_pred_rf': y_pred_rf_test,
    'y_pred_xgb': y_pred_xgb_test,
    'comparison_df': comparison_df,
    'rf_metrics': {
        'train_acc': rf_train_acc,
        'test_acc': rf_test_acc,
        'f1_macro': rf_f1_macro,
        'f1_weighted': rf_f1_weighted
    },
    'xgb_metrics': {
        'train_acc': xgb_train_acc,
        'test_acc': xgb_test_acc,
        'f1_macro': xgb_f1_macro,
        'f1_weighted': xgb_f1_weighted
    }
}

# pkl 파일로 저장
model_path = SAVE_DIR + r'\room_type_models.pkl'
with open(model_path, 'wb') as f:
    pickle.dump(model_data, f)

print(f"✅ 모델 저장 완료: {model_path}")

# 개별 모델도 저장
rf_path = SAVE_DIR + r'\random_forest_model.pkl'
xgb_path = SAVE_DIR + r'\xgboost_model.pkl'
scaler_path = SAVE_DIR + r'\scaler.pkl'

with open(rf_path, 'wb') as f:
    pickle.dump(rf_model, f)
with open(xgb_path, 'wb') as f:
    pickle.dump(xgb_model, f)
with open(scaler_path, 'wb') as f:
    pickle.dump(scaler, f)

print(f"✅ Random Forest 저장: {rf_path}")
print(f"✅ XGBoost 저장: {xgb_path}")
print(f"✅ Scaler 저장: {scaler_path}")

# ============================================================================
# 9. 결과 요약 저장
# ============================================================================
with open(SAVE_DIR + r'\comparison_results.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("XGBoost vs Random Forest - 비교 결과\n")
    f.write("=" * 80 + "\n\n")
    
    f.write("1. 전체 성능 비교\n")
    f.write("-" * 80 + "\n")
    f.write(comparison_df.to_string(index=False))
    f.write("\n\n")
    
    f.write("2. Random Forest 상세 성능\n")
    f.write("-" * 80 + "\n")
    f.write(classification_report(y_test, y_pred_rf_test,
                                  target_names=[class_names[i] for i in sorted(y_test.unique())],
                                  zero_division=0))
    f.write("\n\n")
    
    f.write("3. XGBoost 상세 성능\n")
    f.write("-" * 80 + "\n")
    f.write(classification_report(y_test, y_pred_xgb_test,
                                  target_names=[class_names[i] for i in sorted(y_test.unique())],
                                  zero_division=0))

print(f"✅ 결과 요약 저장: {SAVE_DIR}\\comparison_results.txt")

print("\n" + "=" * 80)
print("✅ 모든 작업 완료!")
print("=" * 80)
print(f"\n저장된 파일:")
print(f"  1. {model_path}")
print(f"  2. {rf_path}")
print(f"  3. {xgb_path}")
print(f"  4. {scaler_path}")
print(f"  5. {comparison_plot_path}")
print(f"  6. {SAVE_DIR}\\comparison_results.txt")
print(f"\n다음 단계: Streamlit 앱 실행")
print(f"  streamlit run streamlitapp.py")