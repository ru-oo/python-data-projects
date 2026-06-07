import pandas as pd

# 1. 파일 불러오기
df = pd.read_csv('merged_result.csv')

# 2. 날짜 형식 변환
df['허가날짜'] = pd.to_datetime(df['허가날짜'], errors='coerce')
df['폐업날짜'] = pd.to_datetime(df['폐업날짜'], errors='coerce')

# 3. 지역명(시도) 표준화
def get_sido(address):
    if pd.isna(address): return "알수없음"
    sido_raw = str(address).split()[0]
    
    if '서울' in sido_raw: return '서울'
    if '경기' in sido_raw: return '경기'
    if '부산' in sido_raw: return '부산'
    if '대구' in sido_raw: return '대구'
    if '인천' in sido_raw: return '인천'
    if '광주' in sido_raw: return '광주'
    if '대전' in sido_raw: return '대전'
    if '울산' in sido_raw: return '울산'
    if '세종' in sido_raw: return '세종'
    if '강원' in sido_raw: return '강원'
    if '충북' in sido_raw or '충청북도' in sido_raw: return '충북'
    if '충남' in sido_raw or '충청남도' in sido_raw: return '충남'
    if '전북' in sido_raw or '전라북도' in sido_raw: return '전북'
    if '전남' in sido_raw or '전라남도' in sido_raw: return '전남'
    if '경북' in sido_raw or '경상북도' in sido_raw: return '경북'
    if '경남' in sido_raw or '경상남도' in sido_raw: return '경남'
    if '제주' in sido_raw: return '제주'
    return sido_raw

df['시도'] = df['소재지'].apply(get_sido)

# 4. 브랜드명 통일
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
            if keyword in name_clean:
                return brand
    return "기타"

df['브랜드'] = df['상호명'].apply(extract_brand)

# 5. 연도별 통계 집계 (영업 + 신규 + 폐업)
years = range(1992, 2026)
stats_results = []

for year in years:
    target_date = pd.Timestamp(f'{year}-12-31')
    start_date = pd.Timestamp(f'{year}-01-01')
    
    # 영업중 매장 수 (연말 기준)
    active_mask = (df['허가날짜'] <= target_date) & ((df['폐업날짜'] > target_date) | (df['폐업날짜'].isnull()))
    active_counts = df[active_mask].groupby(['시도', '업태 구분명', '브랜드']).size().reset_index(name='영업매장수')
    
    # 폐업 매장 수 (해당 연도 내 폐업)
    closed_mask = (df['폐업날짜'] >= start_date) & (df['폐업날짜'] <= target_date)
    closed_counts = df[closed_mask].groupby(['시도', '업태 구분명', '브랜드']).size().reset_index(name='폐업매장수')
    
    # 신규 매장 수 (해당 연도 내 오픈)
    opened_mask = (df['허가날짜'] >= start_date) & (df['허가날짜'] <= target_date)
    opened_counts = df[opened_mask].groupby(['시도', '업태 구분명', '브랜드']).size().reset_index(name='신규매장수')
    
    # 병합
    merged = pd.merge(active_counts, closed_counts, on=['시도', '업태 구분명', '브랜드'], how='outer')
    merged = pd.merge(merged, opened_counts, on=['시도', '업태 구분명', '브랜드'], how='outer')
    merged['연도'] = year
    merged = merged.fillna(0) # NaN -> 0 처리
    
    stats_results.append(merged)

# 최종 저장
final_stats = pd.concat(stats_results, ignore_index=True)
final_stats = final_stats[final_stats['브랜드'] != '기타']

# 보기 좋게 컬럼 순서 및 타입 정리
cols = ['연도', '시도', '업태 구분명', '브랜드', '영업매장수', '신규매장수', '폐업매장수']
final_stats = final_stats[cols]
for c in ['영업매장수', '신규매장수', '폐업매장수']:
    final_stats[c] = final_stats[c].astype(int)

final_stats.to_csv('franchise_yearly_stats_with_closed.csv', index=False, encoding='utf-8-sig')
print("분석 완료! 파일이 생성되었습니다.")