import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import warnings
warnings.filterwarnings('ignore')

# 데이터 로드
df = pd.read_csv('energy_data_merged_kor.csv')

print("데이터 형태:", df.shape)
print("\n컬럼 목록:")
print(df.columns.tolist())
print("\n데이터 샘플:")
print(df.head())

# 발전 믹스 관련 Feature 선택 (비율 기반)
power_mix_features = [
    '화석연료_발전_비중',
    '가스_발전_비중', 
    '수력_발전_비중',
    '저탄소_발전_비중',
    '바이오연료_발전_비중',
    '석탄_발전_비중'
]

# 결측치 확인
print("\n결측치 확인:")
print(df[power_mix_features].isnull().sum())

# 결측치 처리 (0으로 채우기)
df_clean = df.copy()
for col in power_mix_features:
    df_clean[col] = df_clean[col].fillna(0)

# Feature 데이터 추출
X = df_clean[power_mix_features].values

print("\n특성 데이터 형태:", X.shape)
print("특성 통계:")
print(pd.DataFrame(X, columns=power_mix_features).describe())

# 데이터 정규화
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("\n정규화 후 데이터 샘플:")
print(X_scaled[:5])

# PCA 적용 (95% 분산 설명)
pca = PCA(n_components=0.95)
X_pca = pca.fit_transform(X_scaled)

print(f"\nPCA 결과:")
print(f"원본 차원: {X_scaled.shape[1]}")
print(f"축소 차원: {X_pca.shape[1]}")
print(f"설명된 분산 비율: {pca.explained_variance_ratio_}")
print(f"누적 설명 분산: {pca.explained_variance_ratio_.sum():.4f}")

# 최적 클러스터 수 찾기 (Elbow Method)
inertias = []
silhouette_scores = []
K_range = range(2, 11)

from sklearn.metrics import silhouette_score

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(X_pca)
    inertias.append(kmeans.inertia_)
    silhouette_scores.append(silhouette_score(X_pca, kmeans.labels_))

# Elbow 그래프 저장
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

ax1.plot(K_range, inertias, 'bo-')
ax1.set_xlabel('Number of Clusters (k)', fontsize=12)
ax1.set_ylabel('Inertia', fontsize=12)
ax1.set_title('Elbow Method', fontsize=14)
ax1.grid(True)

ax2.plot(K_range, silhouette_scores, 'ro-')
ax2.set_xlabel('Number of Clusters (k)', fontsize=12)
ax2.set_ylabel('Silhouette Score', fontsize=12)
ax2.set_title('Silhouette Score', fontsize=14)
ax2.grid(True)

plt.tight_layout()
plt.savefig('elbow_analysis.png', dpi=300, bbox_inches='tight')
print("\nElbow 분석 그래프 저장 완료: elbow_analysis.png")

# 최적 클러스터 수 선택 (여기서는 4개로 설정)
optimal_k = 4
print(f"\n선택된 클러스터 수: {optimal_k}")

# 최종 K-Means 모델 학습
kmeans_final = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
clusters = kmeans_final.fit_predict(X_pca)

df_clean['cluster'] = clusters

print(f"\n클러스터별 데이터 분포:")
print(df_clean['cluster'].value_counts().sort_index())

# 클러스터별 특성 분석
print("\n클러스터별 발전 믹스 평균:")
cluster_profiles = df_clean.groupby('cluster')[power_mix_features].mean()
print(cluster_profiles)

# 클러스터 시각화
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
axes = axes.ravel()

for idx, feature in enumerate(power_mix_features):
    ax = axes[idx]
    cluster_profiles[feature].plot(kind='bar', ax=ax, color='steelblue')
    ax.set_title(f'{feature} by Cluster', fontsize=12)
    ax.set_xlabel('Cluster', fontsize=10)
    ax.set_ylabel('Average Value (%)', fontsize=10)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('cluster_profiles.png', dpi=300, bbox_inches='tight')
print("\n클러스터 프로파일 그래프 저장 완료: cluster_profiles.png")

# PCA 시각화 (2D)
if X_pca.shape[1] >= 2:
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=clusters, 
                         cmap='viridis', alpha=0.6, s=50)
    plt.colorbar(scatter, label='Cluster')
    plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)', fontsize=12)
    plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)', fontsize=12)
    plt.title('Clusters in PCA Space', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.savefig('pca_clusters.png', dpi=300, bbox_inches='tight')
    print("PCA 클러스터 시각화 저장 완료: pca_clusters.png")

# 클러스터 이름 부여
cluster_names = {
    0: "High Fossil Fuel",
    1: "Balanced Mix",
    2: "Low Carbon Dominant",
    3: "Coal Intensive"
}

# 각 클러스터의 특징 분석
print("\n===== 클러스터 특성 분석 =====")
for cluster_id in sorted(df_clean['cluster'].unique()):
    print(f"\n클러스터 {cluster_id}:")
    cluster_data = df_clean[df_clean['cluster'] == cluster_id]
    print(f"데이터 수: {len(cluster_data)}")
    print("평균 발전 믹스:")
    for feature in power_mix_features:
        mean_val = cluster_data[feature].mean()
        print(f"  {feature}: {mean_val:.2f}%")

# 모델 및 전처리 객체 저장
models = {
    'scaler': scaler,
    'pca': pca,
    'kmeans': kmeans_final,
    'feature_names': power_mix_features,
    'cluster_names': cluster_names,
    'optimal_k': optimal_k
}

with open('clustering_models.pkl', 'wb') as f:
    pickle.dump(models, f)

print("\n모델 저장 완료: clustering_models.pkl")

# 샘플 예측을 위한 함수 테스트
def predict_cluster(input_data, models):
    """
    입력된 발전 믹스 데이터로 클러스터 예측
    
    input_data: dict with keys matching power_mix_features
    """
    # 입력 데이터를 배열로 변환
    X_input = np.array([[
        input_data['화석연료_발전_비중'],
        input_data['가스_발전_비중'],
        input_data['수력_발전_비중'],
        input_data['저탄소_발전_비중'],
        input_data['바이오연료_발전_비중'],
        input_data['석탄_발전_비중']
    ]])
    
    # 정규화
    X_scaled = models['scaler'].transform(X_input)
    
    # PCA 변환
    X_pca = models['pca'].transform(X_scaled)
    
    # 클러스터 예측
    cluster = models['kmeans'].predict(X_pca)[0]
    
    return cluster

# 테스트
test_input = {
    '화석연료_발전_비중': 80.0,
    '가스_발전_비중': 40.0,
    '수력_발전_비중': 10.0,
    '저탄소_발전_비중': 15.0,
    '바이오연료_발전_비중': 2.0,
    '석탄_발전_비중': 25.0
}

predicted_cluster = predict_cluster(test_input, models)
print(f"\n테스트 예측 결과: 클러스터 {predicted_cluster}")

print("\n전체 파이프라인 완료!")