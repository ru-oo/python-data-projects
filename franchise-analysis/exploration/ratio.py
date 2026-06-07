import pandas as pd

# 1. 파일 불러오기
# (파일 경로를 본인 환경에 맞게 수정하세요)
df_franchise = pd.read_csv('franchise_yearly_stats_with_closed.csv')
df_population = pd.read_csv('전체 인구수.csv', encoding='utf-8') # 한글 깨지면 encoding='cp949' 시도

# 2. 인구 데이터 구조 변경 (Pivot 해제)
# 가로로 펼쳐진 지역 컬럼들을 세로로 '녹여서(melt)' 하나의 컬럼으로 만듭니다.
# 결과: [시점, 지역, 인구수] 형태가 됨
id_vars = ['시점']
value_vars = [c for c in df_population.columns if c != '시점' and c != '전국'] # '전국' 제외

df_pop_long = df_population.melt(
    id_vars=id_vars, 
    value_vars=value_vars, 
    var_name='지역_full', 
    value_name='인구수'
)

# 3. 데이터 전처리
# 인구수 숫자로 변환 (결측치 0 처리)
df_pop_long['인구수'] = pd.to_numeric(df_pop_long['인구수'], errors='coerce').fillna(0)

# 지역명 통일 (인구 데이터의 '서울특별시' -> 프랜차이즈 데이터의 '서울')
region_map = {
    '서울특별시': '서울', '부산광역시': '부산', '대구광역시': '대구', '인천광역시': '인천',
    '광주광역시': '광주', '대전광역시': '대전', '울산광역시': '울산', '세종특별자치시': '세종',
    '경기도': '경기', '강원특별자치도': '강원', '충청북도': '충북', '충청남도': '충남',
    '전북특별자치도': '전북', '전라남도': '전남', '경상북도': '경북', '경상남도': '경남',
    '제주특별자치도': '제주'
}
df_pop_long['시도'] = df_pop_long['지역_full'].map(region_map)

# 4. 데이터 합치기 (Merge)
# 두 데이터프레임의 연도와 시도 타입 맞추기
df_franchise['연도'] = df_franchise['연도'].astype(int)
df_pop_long['시점'] = df_pop_long['시점'].astype(int)

merged_df = pd.merge(
    df_franchise,
    df_pop_long[['시점', '시도', '인구수']],
    left_on=['연도', '시도'],
    right_on=['시점', '시도'],
    how='inner' # 교집합 (둘 다 데이터가 있는 경우만)
)

# 5. 인구 1만 명당 매장 수 계산
# 인구수가 0인 경우 나눗셈 에러 방지
merged_df['인구1만명당_매장수'] = merged_df.apply(
    lambda x: (x['영업매장수'] / x['인구수'] * 10000) if x['인구수'] > 0 else 0, axis=1
)

# 6. 보기 좋게 정리 및 저장
final_cols = ['연도', '시도', '업태 구분명', '브랜드', '영업매장수', '인구수', '인구1만명당_매장수']
final_df = merged_df[final_cols]

final_df.to_csv('franchise_population_ratio.csv', index=False, encoding='utf-8-sig')

print("완료! 'franchise_population_ratio.csv' 파일이 생성되었습니다.")
print(final_df.head())