import pandas as pd
import os

# 1. 합칠 파일들의 경로(이름) 리스트 작성
# 실제 파일명으로 수정해서 사용하세요.
files = [
    "buger.csv",
    "coffie.csv",
    "cp.csv"
]

# 결과를 저장할 파일명
output_filename = "merged_result.csv"

# 데이터프레임을 담을 리스트
dfs = []

print("파일 읽기를 시작합니다...")

for file in files:
    if os.path.exists(file):
        try:
            # CSV 파일 읽기
            # 한글이 깨진다면 encoding='cp949' 또는 'euc-kr'을 시도해보세요.
            df = pd.read_csv(file, encoding='utf-8') 
            dfs.append(df)
            print(f"[성공] {file} 로드 완료 ({len(df)}행)")
        except Exception as e:
            print(f"[오류] {file} 읽기 실패: {e}")
    else:
        print(f"[경고] 파일을 찾을 수 없습니다: {file}")

# 2. 데이터 병합 (위아래로 이어 붙이기)
if dfs:
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # 3. 결과 저장
    merged_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    
    print("-" * 30)
    print(f"병합 완료! 저장된 파일: {output_filename}")
    print(f"전체 데이터 개수: {len(merged_df)}행")
else:
    print("병합할 데이터가 없습니다.")