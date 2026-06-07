"""
XGBoost를 사용한 Room Type 분류
- 클래스 가중치 적용
- 하이퍼파라미터 튜닝 옵션 포함
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from sklearn.utils.class_weight import compute_class_weight
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("XGBoost Room Type Classification")
print("=" * 80)

# ============================================================================
# 1. 데이터 로드
# ============================================================================
print("\n[1단계] 데이터 로드")
print("-" * 80)

df = pd.read_csv('preprocessed_airbnb_data_final.csv')
print(f"데이터 shape: {df.shape}")

# 특성과 타겟 분리
X = df.drop(['room_type_encoded', 'price'], axis=1)
y = df['room_type_encoded']

print(f"\n특성(X) shape: {X.shape}")
print(f"타겟(y) shape: {y.shape}")

# 클래스 분포
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
# 2. 데이터 분할
# ============================================================================
print("\n[2단계] Train/Test 분할 (Stratified)")
print("-" * 80)

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(f"Train set: {X_train.shape[0]}개")
print(f"Test set:  {X_test.shape[0]}개")

# ============================================================================
# 3. 특성 스케일링
# ============================================================================
print("\n[3단계] 특성 스케일링")
print("-" * 80)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("스케일링 완료!")

# ============================================================================
# 4. 클래스 가중치 계산
# ============================================================================
print("\n[4단계] 클래스 가중치 계산")
print("-" * 80)

# 클래스별 가중치 계산
class_weights = compute_class_weight(
    class_weight='balanced',
    classes=np.unique(y_train),
    y=y_train
)

print("\n계산된 클래스 가중치:")
for cls, weight in zip(np.unique(y_train), class_weights):
    print(f"  클래스 {cls} ({class_names[cls]:20s}): {weight:.4f}")

# 각 샘플의 가중치 생성
sample_weights = np.array([class_weights[y] for y in y_train])

print(f"\n샘플 가중치 생성 완료!")
print(f"  - 평균: {sample_weights.mean():.4f}")
print(f"  - 최소: {sample_weights.min():.4f}")
print(f"  - 최대: {sample_weights.max():.4f}")

# ============================================================================
# 5. XGBoost 모델 학습 (기본 설정)
# ============================================================================
print("\n[5단계] XGBoost 모델 학습 (기본 설정)")
print("=" * 80)

# 기본 XGBoost 모델
xgb_basic = xgb.XGBClassifier(
    objective='multi:softmax',      # 다중 클래스 분류
    num_class=4,                    # 4개 클래스
    n_estimators=100,               # 부스팅 라운드 100번
    max_depth=6,                    # 트리 최대 깊이
    learning_rate=0.1,              # 학습률
    subsample=0.8,                  # 행 샘플링 비율
    colsample_bytree=0.8,           # 열 샘플링 비율
    random_state=42,
    eval_metric='mlogloss',         # 평가 지표
    verbosity=0                     # 로그 출력 안 함
)

print("학습 중 (가중치 적용)...")
xgb_basic.fit(
    X_train_scaled,
    y_train,
    sample_weight=sample_weights,   # ⚖️ 클래스 가중치!
    verbose=False
)

# 예측
y_pred_train_basic = xgb_basic.predict(X_train_scaled)
y_pred_test_basic = xgb_basic.predict(X_test_scaled)

# 평가
train_acc_basic = accuracy_score(y_train, y_pred_train_basic)
test_acc_basic = accuracy_score(y_test, y_pred_test_basic)
f1_macro_basic = f1_score(y_test, y_pred_test_basic, average='macro')
f1_weighted_basic = f1_score(y_test, y_pred_test_basic, average='weighted')

print("\n✅ 학습 완료!")
print(f"\n성능 지표:")
print(f"  Train Accuracy:       {train_acc_basic:.4f}")
print(f"  Test Accuracy:        {test_acc_basic:.4f}")
print(f"  F1-Score (Macro):     {f1_macro_basic:.4f}")
print(f"  F1-Score (Weighted):  {f1_weighted_basic:.4f}")

print(f"\n클래스별 성능:")
print("-" * 80)
print(classification_report(
    y_test, y_pred_test_basic,
    target_names=[class_names[i] for i in sorted(y_test.unique())],
    zero_division=0
))

# ============================================================================
# 6. XGBoost 모델 학습 (최적화 설정)
# ============================================================================
print("\n[6단계] XGBoost 모델 학습 (최적화 설정)")
print("=" * 80)

# 최적화된 XGBoost 모델
xgb_optimized = xgb.XGBClassifier(
    objective='multi:softmax',
    num_class=4,
    n_estimators=200,               # 부스팅 라운드 증가
    max_depth=8,                    # 깊이 증가
    learning_rate=0.05,             # 학습률 낮춤 (과적합 방지)
    subsample=0.7,                  # 샘플링 비율 낮춤
    colsample_bytree=0.7,           # 피처 샘플링 낮춤
    min_child_weight=3,             # 최소 leaf weight
    gamma=0.1,                      # 분할 최소 손실 감소
    reg_alpha=0.1,                  # L1 정규화
    reg_lambda=1.0,                 # L2 정규화
    random_state=42,
    eval_metric='mlogloss',
    verbosity=0
)

print("학습 중 (가중치 + 정규화)...")
xgb_optimized.fit(
    X_train_scaled,
    y_train,
    sample_weight=sample_weights,
    verbose=False
)

# 예측
y_pred_train_opt = xgb_optimized.predict(X_train_scaled)
y_pred_test_opt = xgb_optimized.predict(X_test_scaled)

# 평가
train_acc_opt = accuracy_score(y_train, y_pred_train_opt)
test_acc_opt = accuracy_score(y_test, y_pred_test_opt)
f1_macro_opt = f1_score(y_test, y_pred_test_opt, average='macro')
f1_weighted_opt = f1_score(y_test, y_pred_test_opt, average='weighted')

print("\n✅ 학습 완료!")
print(f"\n성능 지표:")
print(f"  Train Accuracy:       {train_acc_opt:.4f}")
print(f"  Test Accuracy:        {test_acc_opt:.4f}")
print(f"  F1-Score (Macro):     {f1_macro_opt:.4f}")
print(f"  F1-Score (Weighted):  {f1_weighted_opt:.4f}")

print(f"\n클래스별 성능:")
print("-" * 80)
print(classification_report(
    y_test, y_pred_test_opt,
    target_names=[class_names[i] for i in sorted(y_test.unique())],
    zero_division=0
))

# ============================================================================
# 7. 두 모델 비교
# ============================================================================
print("\n[7단계] 기본 vs 최적화 모델 비교")
print("=" * 80)

comparison = pd.DataFrame({
    '모델': ['기본 XGBoost', '최적화 XGBoost'],
    'Train Acc': [train_acc_basic, train_acc_opt],
    'Test Acc': [test_acc_basic, test_acc_opt],
    'F1 (Macro)': [f1_macro_basic, f1_macro_opt],
    'F1 (Weighted)': [f1_weighted_basic, f1_weighted_opt],
    '과적합': [
        train_acc_basic - test_acc_basic,
        train_acc_opt - test_acc_opt
    ]
})

print("\n" + comparison.to_string(index=False))

# 최고 모델 선택
if test_acc_opt > test_acc_basic:
    best_model = xgb_optimized
    best_name = "최적화 XGBoost"
    y_pred_best = y_pred_test_opt
else:
    best_model = xgb_basic
    best_name = "기본 XGBoost"
    y_pred_best = y_pred_test_basic

print(f"\n🏆 최고 성능 모델: {best_name}")

# ============================================================================
# 8. Feature Importance 분석
# ============================================================================
print("\n[8단계] Feature Importance 분석")
print("-" * 80)

# 피처 중요도 추출
feature_importance = best_model.feature_importances_
feature_names = X.columns

# 중요도 순으로 정렬
importance_df = pd.DataFrame({
    'Feature': feature_names,
    'Importance': feature_importance
}).sort_values('Importance', ascending=False)

print("\n피처 중요도 (상위 10개):")
print(importance_df.head(10).to_string(index=False))

# ============================================================================
# 9. 시각화
# ============================================================================
print("\n[9단계] 시각화 생성")
print("-" * 80)

# 그래프 1: Confusion Matrix
fig, axes = plt.subplots(2, 2, figsize=(16, 14))
fig.suptitle('XGBoost Room Type Classification Results', 
             fontsize=16, fontweight='bold')

# 1) Confusion Matrix
ax1 = axes[0, 0]
cm = confusion_matrix(y_test, y_pred_best)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax1,
            xticklabels=[class_names[i] for i in sorted(y_test.unique())],
            yticklabels=[class_names[i] for i in sorted(y_test.unique())])
ax1.set_title(f'Confusion Matrix - {best_name}', fontsize=14, fontweight='bold')
ax1.set_ylabel('Actual', fontsize=12)
ax1.set_xlabel('Predicted', fontsize=12)

# 2) Feature Importance
ax2 = axes[0, 1]
top_n = 12  # 모든 피처
top_features = importance_df.head(top_n)
bars = ax2.barh(range(len(top_features)), top_features['Importance'], color='skyblue')
ax2.set_yticks(range(len(top_features)))
ax2.set_yticklabels(top_features['Feature'])
ax2.set_xlabel('Importance', fontsize=12)
ax2.set_title('Feature Importance (Top 12)', fontsize=14, fontweight='bold')
ax2.invert_yaxis()

# 값 표시
for i, (bar, val) in enumerate(zip(bars, top_features['Importance'])):
    ax2.text(val + 0.001, i, f'{val:.4f}', va='center', fontsize=9)

# 3) 클래스별 F1-Score 비교
ax3 = axes[1, 0]
from sklearn.metrics import precision_recall_fscore_support

precision, recall, f1, support = precision_recall_fscore_support(
    y_test, y_pred_best, 
    labels=sorted(y_test.unique()),
    zero_division=0
)

class_labels = [class_names[i] for i in sorted(y_test.unique())]
x_pos = np.arange(len(class_labels))
width = 0.25

bars1 = ax3.bar(x_pos - width, precision, width, label='Precision', color='skyblue')
bars2 = ax3.bar(x_pos, recall, width, label='Recall', color='lightcoral')
bars3 = ax3.bar(x_pos + width, f1, width, label='F1-Score', color='lightgreen')

ax3.set_xlabel('Room Type', fontsize=12)
ax3.set_ylabel('Score', fontsize=12)
ax3.set_title('Per-Class Performance', fontsize=14, fontweight='bold')
ax3.set_xticks(x_pos)
ax3.set_xticklabels(class_labels, rotation=15, ha='right')
ax3.legend()
ax3.set_ylim(0, 1.1)

# 값 표시
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}', ha='center', va='bottom', fontsize=9)

# 4) 기본 vs 최적화 비교
ax4 = axes[1, 1]
metrics = ['Test Acc', 'F1 (Macro)', 'F1 (Weighted)']
basic_scores = [test_acc_basic, f1_macro_basic, f1_weighted_basic]
opt_scores = [test_acc_opt, f1_macro_opt, f1_weighted_opt]

x_pos2 = np.arange(len(metrics))
width2 = 0.35

bars4_1 = ax4.bar(x_pos2 - width2/2, basic_scores, width2, 
                  label='기본 XGBoost', color='lightblue')
bars4_2 = ax4.bar(x_pos2 + width2/2, opt_scores, width2, 
                  label='최적화 XGBoost', color='orange')

ax4.set_xlabel('Metrics', fontsize=12)
ax4.set_ylabel('Score', fontsize=12)
ax4.set_title('Basic vs Optimized XGBoost', fontsize=14, fontweight='bold')
ax4.set_xticks(x_pos2)
ax4.set_xticklabels(metrics)
ax4.legend()
ax4.set_ylim(0, 1.1)

# 값 표시
for bars in [bars4_1, bars4_2]:
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('/home/claude/xgboost_results.png', dpi=300, bbox_inches='tight')
print("✅ 그래프 저장: /home/claude/xgboost_results.png")

# ============================================================================
# 10. 결과 저장
# ============================================================================
print("\n[10단계] 결과 저장")
print("-" * 80)

# 성능 비교 CSV
comparison.to_csv('/home/claude/xgboost_comparison.csv', index=False)
print("✅ 비교 결과 저장: /home/claude/xgboost_comparison.csv")

# Feature Importance CSV
importance_df.to_csv('/home/claude/xgboost_feature_importance.csv', index=False)
print("✅ 피처 중요도 저장: /home/claude/xgboost_feature_importance.csv")

# 상세 리포트
with open('/home/claude/xgboost_report.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("XGBoost Room Type Classification - 상세 리포트\n")
    f.write("=" * 80 + "\n\n")
    
    f.write("1. 모델 설정\n")
    f.write("-" * 80 + "\n")
    f.write("기본 XGBoost:\n")
    f.write(f"  - n_estimators: 100\n")
    f.write(f"  - max_depth: 6\n")
    f.write(f"  - learning_rate: 0.1\n\n")
    f.write("최적화 XGBoost:\n")
    f.write(f"  - n_estimators: 200\n")
    f.write(f"  - max_depth: 8\n")
    f.write(f"  - learning_rate: 0.05\n")
    f.write(f"  - L1 reg (alpha): 0.1\n")
    f.write(f"  - L2 reg (lambda): 1.0\n\n")
    
    f.write("2. 클래스 가중치\n")
    f.write("-" * 80 + "\n")
    for cls, weight in zip(np.unique(y_train), class_weights):
        f.write(f"  클래스 {cls} ({class_names[cls]:20s}): {weight:.4f}\n")
    f.write("\n")
    
    f.write("3. 성능 비교\n")
    f.write("-" * 80 + "\n")
    f.write(comparison.to_string(index=False))
    f.write("\n\n")
    
    f.write("4. 최고 모델 상세 성능\n")
    f.write("-" * 80 + "\n")
    f.write(f"모델: {best_name}\n\n")
    f.write(classification_report(
        y_test, y_pred_best,
        target_names=[class_names[i] for i in sorted(y_test.unique())],
        zero_division=0
    ))
    f.write("\n")
    
    f.write("5. Feature Importance (Top 10)\n")
    f.write("-" * 80 + "\n")
    f.write(importance_df.head(10).to_string(index=False))
    f.write("\n")

print("✅ 상세 리포트 저장: /home/claude/xgboost_report.txt")

print("\n" + "=" * 80)
print("✅ XGBoost 학습 및 분석 완료!")
print("=" * 80)
print("\n생성된 파일:")
print("  1. xgboost_results.png - 시각화 그래프")
print("  2. xgboost_comparison.csv - 모델 비교")
print("  3. xgboost_feature_importance.csv - 피처 중요도")
print("  4. xgboost_report.txt - 상세 리포트")