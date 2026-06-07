import pandas as pd
import numpy as np
import re

# ---------------------------------------------------------
# 1. 파일 불러오기
# ---------------------------------------------------------
print("=== [1단계] 파일 로딩 시작 ===")

# (1) 프랜차이즈 데이터
df_franchise = pd.read_csv('merged_result.csv', encoding='utf-8')

# (2) 인구 데이터 (CSV - 인코딩 에러 방지)
try:
    df_pop_old = pd.read_csv('101_DT_1B040M5_20260121105920.csv', encoding='utf-8')
except:
    df_pop_old = pd.read_csv('101_DT_1B040M5_20260121105920.csv', encoding='cp949')

try:
    df_pop_new = pd.read_csv('시군구_성_연령_5세_별_주민등록연앙인구_2023__20260121105622.csv', encoding='utf-8')
except:
    df_pop_new = pd.read_csv('시군구_성_연령_5세_별_주민등록연앙인구_2023__20260121105622.csv', encoding='cp949')

# (3) 1인가구 & 지역내총생산 데이터
df_one = pd.read_excel('1인가구 최종.xlsx')
df_income = pd.read_excel('지역내총생산.xlsx')

# 컬럼명 공백 제거
df_one.columns = [str(c).strip() for c in df_one.columns]
df_income.columns = [str(c).strip() for c in df_income.columns]

# ---------------------------------------------------------
# 2. 공통 함수
# ---------------------------------------------------------
def clean_region(name):
    if pd.isna(name): return "알수없음"
    name = str(name).strip()
    if '서울' in name: return '서울'
    if '경기' in name: return '경기'
    if '부산' in name: return '부산'
    if '대구' in name: return '대구'
    if '인천' in name: return '인천'
    if '광주' in name: return '광주'
    if '대전' in name: return '대전'
    if '울산' in name: return '울산'
    if '세종' in name: return '세종'
    if '강원' in name: return '강원'
    if '충북' in name or '충청북도' in name: return '충북'
    if '충남' in name or '충청남도' in name: return '충남'
    if '전북' in name or '전라북도' in name: return '전북'
    if '전남' in name or '전라남도' in name: return '전남'
    if '경북' in name or '경상북도' in name: return '경북'
    if '경남' in name or '경상남도' in name: return '경남'
    if '제주' in name: return '제주'
    return name

def map_age_group(age):
    if age in ['0 - 4세', '5 - 9세', '10 - 14세', '15 - 19세']: return '0~19세'
    elif age in ['20 - 24세', '25 - 29세', '30 - 34세', '35 - 39세']: return '20~39세'
    elif age in ['40 - 44세', '45 - 49세', '50 - 54세', '55 - 59세']: return '40~59세'
    elif age == '계': return '총인구수'
    else: return '60세이상'

# ---------------------------------------------------------
# 3. 데이터 전처리
# ---------------------------------------------------------

# (A) 인구 (연앙인구)
print("=== [2단계] 인구 데이터 처리 중 ===")
df_old = df_pop_old[(df_pop_old['행정구역(시군구)별'] != '전국') & (df_pop_old['성별'].isin(['남자', '여자']))].copy()
year_cols = [c for c in df_old.columns if '년' in c]
df_old_melt = df_old.melt(id_vars=['행정구역(시군구)별', '연령별', '성별'], value_vars=year_cols, var_name='연도_raw', value_name='인구수')
df_old_melt['연도'] = df_old_melt['연도_raw'].astype(str).str.extract(r'(\d{4})')[0].astype(int)
df_old_melt['시도'] = df_old_melt['행정구역(시군구)별'].apply(clean_region)
df_old_melt = df_old_melt[df_old_melt['연도'] < 2023]

df_new = df_pop_new[df_pop_new['성별'].isin(['남자', '여자'])].copy()
region_cols = [c for c in df_new.columns if c not in ['시점', '연령별', '성별', '전국']]
df_new_melt = df_new.melt(id_vars=['시점', '연령별', '성별'], value_vars=region_cols, var_name='행정구역_raw', value_name='인구수')
df_new_melt.rename(columns={'시점': '연도'}, inplace=True)
df_new_melt['연도'] = df_new_melt['연도'].astype(int)
df_new_melt['시도'] = df_new_melt['행정구역_raw'].apply(clean_region)
df_new_melt = df_new_melt[df_new_melt['연도'] >= 2023]

df_pop_combined = pd.concat([df_old_melt[['연도', '시도', '성별', '연령별', '인구수']], df_new_melt[['연도', '시도', '성별', '연령별', '인구수']]], ignore_index=True)
df_pop_combined['인구수'] = pd.to_numeric(df_pop_combined['인구수'], errors='coerce').fillna(0)
df_pop_combined['연령대'] = df_pop_combined['연령별'].apply(map_age_group)

df_pop_agg = df_pop_combined.groupby(['연도', '시도', '성별', '연령대'])['인구수'].sum().reset_index()
df_pop_wide = df_pop_agg.pivot_table(index=['연도', '시도'], columns=['성별', '연령대'], values='인구수', fill_value=0).reset_index()
df_pop_wide.columns = [f"{c[0]}_{c[1]}" if c[0] not in ['연도', '시도'] else c[0] for c in df_pop_wide.columns]
num_cols = [c for c in df_pop_wide.columns if c not in ['연도', '시도']]
df_pop_wide['전체_총인구수'] = df_pop_wide[num_cols].sum(axis=1)

# 인구수 반올림 (정수)
for col in df_pop_wide.columns:
    if col not in ['연도', '시도']:
        df_pop_wide[col] = df_pop_wide[col].round(0).astype(int)


# (B) 1인 가구 (⭐ 40세 이하로 변경 ⭐)
print("\n=== [3단계] 1인가구 데이터 처리 (40세 이하) ===")

# 1. 컬럼 찾기
region_col = next((c for c in df_one.columns if any(x in str(c) for x in ['시도', '권역', '행정구역', '지역'])), df_one.columns[0])
age_col = next((c for c in df_one.columns if any(x in str(c) for x in ['연령', '나이'])), None)
year_cols_one = [c for c in df_one.columns if re.search(r'\d{4}', str(c))]

# 2. Melt 수행
df_one_melt = df_one.melt(id_vars=[region_col, age_col], value_vars=year_cols_one, var_name='연도_raw', value_name='가구수')

# 3. 데이터 정제
df_one_melt['연도'] = df_one_melt['연도_raw'].astype(str).str.extract(r'(\d{4})')[0].astype(int)
df_one_melt['시도'] = df_one_melt[region_col].apply(clean_region)
df_one_melt['가구수'] = pd.to_numeric(df_one_melt['가구수'], errors='coerce').fillna(0)

# 4. '40세 이하' 추출
# 파일의 '합계'가 실제로는 40세 이하(24세이하 + 25~29 + 30~34 + 35~39)의 총합입니다.
mask_target = df_one_melt[age_col].astype(str).apply(lambda x: any(k in x for k in ['계', '합계', '전체']))
df_one_target = df_one_melt[mask_target].groupby(['연도', '시도'])['가구수'].sum().reset_index()

# 컬럼명 변경 (2030 -> 40세이하)
df_one_target.rename(columns={'가구수': '1인가구수_40세이하'}, inplace=True)
df_one_target['1인가구수_40세이하'] = df_one_target['1인가구수_40세이하'].round(0).astype(int)

# (C) 소득
print("\n=== [4단계] 소득 데이터 처리 ===")
year_cols_inc = [c for c in df_income.columns if str(c).strip().isdigit()]
df_inc_melt = df_income.melt(id_vars=['시도별'], value_vars=year_cols_inc, var_name='연도', value_name='1인당지역총소득')
df_inc_melt['연도'] = df_inc_melt['연도'].astype(int)
df_inc_melt['시도'] = df_inc_melt['시도별'].apply(clean_region)
df_inc_melt['1인당지역총소득'] = pd.to_numeric(df_inc_melt['1인당지역총소득'], errors='coerce').fillna(0)
df_inc_final = df_inc_melt[['연도', '시도', '1인당지역총소득']]

# (D) 프랜차이즈
print("\n=== [5단계] 프랜차이즈 데이터 처리 ===")
df_franchise['허가날짜'] = pd.to_datetime(df_franchise['허가날짜'], errors='coerce')
df_franchise['폐업날짜'] = pd.to_datetime(df_franchise['폐업날짜'], errors='coerce')
df_franchise['시도'] = df_franchise['소재지'].apply(clean_region)

target_brands = {
    '스타벅스': ['스타벅스'], '투썸플레이스': ['투썸'], '이디야': ['이디야'], '빽다방': ['빽다방'],
    '맘스터치': ['맘스터치'], '맥도날드': ['맥도날드'], '버거킹': ['버거킹'], '롯데리아': ['롯데리아'],
    '미스터피자': ['미스터피자'], '도미노피자': ['도미노'], '청년피자': ['청년피자'], '피자헛': ['피자헛'],
    'BBQ': ['BBQ', '비비큐'], 'BHC': ['BHC'], '교촌치킨': ['교촌'], '굽네치킨': ['굽네']
}
def extract_brand(name):
    name_clean = str(name).replace(" ", "").upper()
    for brand, keywords in target_brands.items():
        for keyword in keywords:
            if keyword in name_clean: return brand
    return "기타"
df_franchise['브랜드'] = df_franchise['상호명'].apply(extract_brand)

years = range(2000, 2026)
results = []
for year in years:
    target_date = pd.Timestamp(f'{year}-12-31')
    start_date = pd.Timestamp(f'{year}-01-01')
    
    active_mask = (df_franchise['허가날짜'] <= target_date) & ((df_franchise['폐업날짜'] > target_date) | (df_franchise['폐업날짜'].isnull()))
    new_mask = (df_franchise['허가날짜'] >= start_date) & (df_franchise['허가날짜'] <= target_date)
    closed_mask = (df_franchise['폐업날짜'] >= start_date) & (df_franchise['폐업날짜'] <= target_date)
    
    a_cnt = df_franchise[active_mask].groupby(['시도', '업태 구분명', '브랜드']).size().reset_index(name='영업매장수')
    n_cnt = df_franchise[new_mask].groupby(['시도', '업태 구분명', '브랜드']).size().reset_index(name='신규매장수')
    c_cnt = df_franchise[closed_mask].groupby(['시도', '업태 구분명', '브랜드']).size().reset_index(name='폐업매장수')
    
    merged = pd.merge(a_cnt, n_cnt, on=['시도', '업태 구분명', '브랜드'], how='outer')
    merged = pd.merge(merged, c_cnt, on=['시도', '업태 구분명', '브랜드'], how='outer')
    merged['연도'] = year
    merged = merged.fillna(0)
    results.append(merged)

df_fran_stats = pd.concat(results, ignore_index=True)
df_fran_stats = df_fran_stats[df_fran_stats['브랜드'] != '기타']
for col in ['영업매장수', '신규매장수', '폐업매장수']:
    df_fran_stats[col] = df_fran_stats[col].astype(int)

# ---------------------------------------------------------
# 4. 최종 통합
# ---------------------------------------------------------
print("\n=== [6단계] 최종 병합 및 지표 계산 ===")
# 1. 프랜차이즈 + 인구
final_df = pd.merge(df_fran_stats, df_pop_wide, on=['연도', '시도'], how='left')

# 2. 1인가구 병합 (40세 이하)
final_df = pd.merge(final_df, df_one_target, on=['연도', '시도'], how='left')

# 3. 소득 병합
final_df = pd.merge(final_df, df_inc_final, on=['연도', '시도'], how='left')

# 세종시 등 데이터 정제
final_df = final_df[~((final_df['시도'] == '세종') & ( (final_df['전체_총인구수'].isna()) | (final_df['전체_총인구수'] == 0) ))]

# 브랜드 런칭 연도 필터
launch_years = {
    '맘스터치': 2004, '굽네치킨': 2005, '빽다방': 2006, '청년피자': 2017,
    'BHC': 2004, '이디야': 2001, '투썸플레이스': 2002, '스타벅스': 1999, 'BBQ': 1995
}
for brand, start_year in launch_years.items():
    final_df = final_df[~((final_df['브랜드'] == brand) & (final_df['연도'] < start_year))]

# NaN 채우기
cols_to_fill = ['1인가구수_40세이하', '1인당지역총소득', '전체_총인구수']
for c in cols_to_fill:
    if c in final_df.columns:
        final_df[c] = final_df[c].fillna(0)

# 지표 계산
# (1) 40세이하 1인가구 비율 (전체 인구 대비)
final_df['1인가구_40세이하_비율'] = final_df.apply(lambda x: x['1인가구수_40세이하'] / x['전체_총인구수'] if x['전체_총인구수'] > 0 else 0, axis=1)

# (2) 인구 1만명당 매장수
final_df['인구1만명당_매장수'] = final_df.apply(lambda x: (x['영업매장수'] / x['전체_총인구수'] * 10000) if x['전체_총인구수'] > 0 else 0, axis=1)

# (3) 연령별/성별 인구 비율
age_groups = ['0~19세', '20~39세', '40~59세', '60세이상']
for gender in ['남자', '여자']:
    for age in age_groups:
        col_name = f'{gender}_{age}'
        if col_name in final_df.columns:
            final_df[f'비율_{col_name}'] = final_df.apply(lambda x: x[col_name] / x['전체_총인구수'] if x['전체_총인구수'] > 0 else 0, axis=1)

# ---------------------------------------------------------
# 5. 저장
# ---------------------------------------------------------
final_df.to_csv('franchise_master_analysis_final_fixed.csv', index=False, encoding='utf-8-sig')
print("\n성공! 'franchise_master_analysis_final_fixed.csv' 파일이 생성되었습니다.")