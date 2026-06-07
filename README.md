# python-data-projects

KDT 부트캠프 기간에 진행한 데이터 분석 · 머신러닝 · 애플리케이션 프로젝트 모음입니다.
각 폴더는 독립적인 프로젝트이며, 실행 방법과 결과는 폴더별 README에 정리했습니다.

## 프로젝트 목록

| 프로젝트 | 한 줄 요약 | 주요 스택 |
|---|---|---|
| [franchise-analysis](./franchise-analysis) | 공공데이터 기반 프랜차이즈 상권 통합 분석 대시보드 | Streamlit, pandas, pydeck, plotly |
| [airbnb-roomtype-classification](./airbnb-roomtype-classification) | 뉴욕 Airbnb 숙소의 방 타입 분류 (XGBoost vs Random Forest) | XGBoost, scikit-learn, Streamlit |
| [energy-cluster-analysis](./energy-cluster-analysis) | 국가별 발전 믹스 기반 에너지 구조 군집 분석 | scikit-learn (KMeans, PCA) |
| [pokemon-web-game](./pokemon-web-game) | MariaDB를 백엔드로 쓰는 포켓몬 던전 웹게임 | Flask, PyMySQL, MariaDB |
| [zombie-survival-game](./zombie-survival-game) | 벙커 생존 시뮬레이션 게임 (Coupang Survival) | pygame |

## 비고

- 모든 프로젝트는 부트캠프 팀 단위로 진행했으며, 각 README의 **담당 범위** 항목에 본인이 맡은 부분을 명시했습니다.
- 대용량 데이터셋(CSV)과 학습된 모델 파일(`.pkl`)은 저장소 용량을 위해 제외했습니다. 각 프로젝트 README의 데이터 입수 방법을 참고하세요.
