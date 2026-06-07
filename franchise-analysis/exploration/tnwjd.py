import pandas as pd

# 1. CSV 파일 불러오기
file_path = 'franchise_analysis_major_brands.csv'
df = pd.read_csv(file_path)

# 2. 미스터피자 중 '치킨'으로 잘못 분류된 데이터 수정
# 조건: 브랜드가 '미스터피자'이고, 업태가 '치킨'인 경우 -> '피자'로 변경
mask = (df['브랜드'] == '미스터피자') & (df['업태 구분명'] == '치킨')
df.loc[mask, '업태 구분명'] = '피자'

# 3. 데이터 중복 처리 (Merge)
# 수정 후, 같은 [시도, 연도, 브랜드, 업태]를 가진 행이 두 개가 될 수 있음
# (예: 충북 2006년에 원래 있던 '미스터피자(피자)' 데이터와 수정된 '미스터피자(치킨->피자)' 데이터)

# 그룹화 기준 컬럼 (Primary Key)
group_cols = ['시도', '연도', '브랜드', '업태 구분명']

# 합산해야 할 컬럼 (매장 수 관련)
sum_cols = ['영업매장수', '신규매장수', '폐업매장수']

# 나머지 컬럼들 (인구수 등 통계 데이터는 합치지 않고 첫 번째 값 유지)
other_cols = [c for c in df.columns if c not in group_cols + sum_cols]

# 집계 방식 정의: 매장 수는 sum, 나머지는 first(첫 번째 값 유지)
agg_dict = {c: 'sum' for c in sum_cols}
for c in other_cols:
    agg_dict[c] = 'first'

# 그룹화하여 데이터 병합
df_corrected = df.groupby(group_cols, as_index=False).agg(agg_dict)

# 4. 컬럼 순서를 원본과 동일하게 맞춤
df_corrected = df_corrected[df.columns]

# 5. 수정된 데이터 저장
output_path = 'franchise_analysis_corrected.csv'
df_corrected.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"수정 완료! '{output_path}' 파일로 저장되었습니다.")