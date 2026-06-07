import pandas as pd
import os

# 1. 파일 경로 설정
base_dir = 'C:/KDT/data_project_KDT/burger_dataset'
file_name = '전체_버거_프랜차이즈_통합.csv'
file_path = os.path.join(base_dir, file_name)

# 2. CSV 파일 읽기
if os.path.exists(file_path):
    print(f"파일을 읽어옵니다: {file_path}")
    df = pd.read_csv(file_path)
    
    # 3. '업태 구분명' 컬럼을 모두 '패스트푸드'로 변경
    df['업태 구분명'] = '패스트푸드'
    
    # 4. 같은 파일명으로 덮어쓰기 (저장)
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    
    print("변경 완료! 모든 '업태 구분명'이 '패스트푸드'로 수정되었습니다.")
    print(df[['상호명(통일)', '업태 구분명']].head()) # 결과 확인
else:
    print(f"파일을 찾을 수 없습니다: {file_path}")