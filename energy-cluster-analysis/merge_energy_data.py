import pandas as pd
import os

# 1. 분할된 파일 불러오기
# (파일 경로는 실제 저장한 위치에 맞춰 수정해주세요)
file_paths = [
    'energy-data-kor1.csv',
    'ml_ready_energy_data.csv',
    'global_energy3.csv'
]

# 파일 존재 여부 확인 후 읽기
dfs = []
for path in file_paths:
    if os.path.exists(path):
        dfs.append(pd.read_csv(path))
    else:
        print(f"오류: '{path}' 파일을 찾을 수 없습니다.")

# 2. 데이터프레임 합치기 (Concatenation)
# axis=1 : 옆으로(칼럼 방향으로) 합친다는 뜻입니다.
# axis=0 : 위아래로(행 방향으로) 합칠 때 사용합니다.
if len(dfs) == 3:
    # 모든 파일의 행(Row) 개수가 같은지 검증 (필수)
    if len(dfs[0]) == len(dfs[1]) == len(dfs[2]):
        df_merged = pd.concat(dfs, axis=1)
        
        print("--- 병합 완료 ---")
        print(f"총 행(Row) 수: {df_merged.shape[0]}")
        print(f"총 칼럼(Column) 수: {df_merged.shape[1]}")
        
        # 합쳐진 데이터 확인 (처음 5행)
        print("\n[상위 5행 미리보기]")
        print(df_merged.head())
        
        # 3. 합친 파일 저장하기
        df_merged.to_csv('global_energy_merged.csv', index=False)
        print("\n'global_energy_merged.csv' 파일로 저장이 완료되었습니다.")
        
    else:
        print("오류: 세 파일의 행(Row) 개수가 다릅니다. 데이터가 손상되었거나 순서가 섞였을 수 있습니다.")
else:
    print("오류: 3개의 파일을 모두 불러오지 못했습니다.")