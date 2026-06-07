import pandas as pd

# 데이터 로드
df = pd.read_csv('franchise_master_analysis_final_fixed.csv')

# 1. 합계 구하기 (로직은 동일)
df['주요4사_총매장수'] = df.groupby(['연도', '시도', '업태 구분명'])['영업매장수'].transform('sum')
df['시도별_주요브랜드_총합'] = df.groupby(['연도', '시도'])['영업매장수'].transform('sum')

# 2. 비율 구하기 (용어 변경)
# "점유율" 대신 "비중(Relative Share)"이라는 표현 사용
df['주요4사_내_비중'] = df.apply(lambda x: (x['영업매장수'] / x['주요4사_총매장수'] * 100) if x['주요4사_총매장수'] > 0 else 0, axis=1)

# 3. 분석 신뢰도를 높이는 파생 변수 추가
# (예: 인구 대비 주요 브랜드 집중도 - 이 지역이 메이저 브랜드 선호도가 높은가?)
df['인구1만명당_주요4사_매장수'] = df.apply(lambda x: (x['주요4사_총매장수'] / x['전체_총인구수'] * 10000) if x['전체_총인구수'] > 0 else 0, axis=1)

# 저장
df.to_csv('franchise_analysis_major_brands.csv', index=False, encoding='utf-8-sig')
print("완료: 컬럼명을 명확히 변경하여 저장했습니다.")