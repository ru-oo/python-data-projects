# Airbnb 방 타입 분류 (XGBoost vs Random Forest)

뉴욕 Airbnb 숙소 데이터를 이용해 숙소의 **방 타입(Room Type)** 을 예측하고,
XGBoost와 Random Forest 두 모델의 성능을 비교한 분류 프로젝트입니다.

## 데모

> Streamlit 비교 시각화 앱 실행 화면 스크린샷/GIF는 추후 추가 예정입니다.

## 개요

숙소의 가격·위치·리뷰·가용성 등 특성으로 방 타입을 4개 클래스
(`Entire home/apt`, `Private room`, `Hotel room`, `Shared room`)로 분류합니다.
클래스 불균형이 큰 데이터라 클래스 가중치를 적용했고, 두 트리 기반 모델의
일반화 성능과 과적합 정도를 함께 비교했습니다.

## 핵심 기능

- 캐글 데이터셋 다운로드 및 전처리
- XGBoost / Random Forest 학습 및 성능 비교 (정확도, F1, 과적합도)
- 클래스 가중치 적용으로 소수 클래스 대응
- Streamlit 기반 모델 비교 · 예측 시각화 앱

## 결과

학습/평가 결과는 `models/comparison_results.txt` 에 기록되어 있으며, 핵심 수치는 다음과 같습니다.
(테스트셋 4,112건 기준)

| 모델 | Test Accuracy | F1 (Macro) | F1 (Weighted) | 과적합도 |
|---|---|---|---|---|
| Random Forest | 0.757 | 0.555 | 0.756 | 0.056 |
| XGBoost | 0.767 | 0.565 | 0.768 | 0.091 |

- XGBoost가 정확도·F1에서 근소하게 앞서지만 과적합도는 더 큽니다.
- 다수 클래스(`Entire home/apt`, `Private room`)는 잘 분류하나, 표본이 적은
  `Shared room` 클래스는 두 모델 모두 어려워합니다 (데이터 불균형의 영향).

## 기술 스택

- Python, scikit-learn, XGBoost
- pandas, numpy
- matplotlib, seaborn, plotly (시각화)
- Streamlit (비교 · 예측 앱)
- kagglehub (데이터셋 다운로드)

## 담당 범위 (팀 프로젝트)

- 팀 공동 작업 프로젝트입니다. 데이터 수집·전처리부터 모델 학습·비교, 시각화까지
  팀원들과 함께 진행했습니다.

## 실행 방법

```bash
pip install -r requirements.txt

# 1) 데이터셋 다운로드 (캐글 인증 필요)
python download_dataset.py

# 2) 모델 학습 및 비교
python train_and_compare_models.py

# 3) 비교 시각화 앱 실행
streamlit run streamlit_app.py
```

> 데이터셋과 학습된 모델(`.pkl`)은 용량 문제로 저장소에서 제외되어 있습니다.
> 데이터는 캐글 `vrindakallu/new-york-dataset` 에서 받으며(`download_dataset.py`),
> 모델은 `train_and_compare_models.py` 실행으로 생성됩니다.

## 디렉터리 구조

```
airbnb-roomtype-classification/
├── download_dataset.py            # 캐글 데이터셋 다운로드
├── train_and_compare_models.py    # XGBoost vs RF 학습·비교
├── xgboost_classification.py      # XGBoost 단독 학습 (가중치/튜닝)
├── streamlit_app.py               # 모델 비교·예측 시각화 앱
├── app.py                         # 간단 예측 앱
├── models/                        # 학습 결과 (모델 pkl은 제외, 비교 리포트·차트 포함)
├── output/                        # 분석 차트 이미지
└── requirements.txt
```

## 알려진 한계 / 향후 계획

- 클래스 불균형으로 소수 클래스(`Shared room`, `Hotel room`)의 성능이 낮습니다.
  오버샘플링(SMOTE) 등으로 개선할 여지가 있습니다.
- Streamlit 앱의 모델 경로가 하드코딩되어 있어 환경에 맞게 수정이 필요합니다.
