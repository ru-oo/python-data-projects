import pandas as pd
import glob
import os
import warnings

# 불필요한 경고 메시지 무시 (openpyxl 스타일 관련 경고)
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# 1. 경로 설정 (스크립트 파일 위치 기준)
# 현재 실행 중인 파이썬 파일(join.py)이 있는 폴더 경로를 가져옵니다.
current_dir = os.path.dirname(os.path.abspath(__file__))

# 데이터가 있는 폴더 경로 설정 (join.py와 같은 폴더 내의 burger_dataset)
input_folder = os.path.join(current_dir, 'burger_dataset')

# 저장할 파일 경로 설정
output_filename = os.path.join(input_folder, '전체_버거_프랜차이즈_통합.csv')

# burger_dataset 폴더 안의 모든 xlsx 파일 찾기
file_pattern = os.path.join(input_folder, '*.xlsx')
all_files = glob.glob(file_pattern)

dfs = []

print(f"데이터 폴더 경로: {input_folder}")
print(f"총 {len(all_files)}개의 엑셀(.xlsx) 파일을 발견했습니다. 병합을 시작합니다...")

for file_path in all_files:
    try:
        # 파일명에 '통합'이 포함된 파일(이미 생성된 결과 파일)은 제외
        if '통합' in os.path.basename(file_path):
            continue
            
        # 2. 엑셀 파일 읽기
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # 3. 데이터 전처리
        
        # [소재지] 도로명 주소 우선 사용, 없으면 지번 주소 사용
        # 컬럼이 아예 없는 경우를 대비해 처리
        addr_road = df['도로명전체주소'] if '도로명전체주소' in df.columns else pd.Series([None]*len(df))
        addr_jibun = df['소재지전체주소'] if '소재지전체주소' in df.columns else pd.Series([None]*len(df))
        
        df['소재지'] = addr_road.fillna(addr_jibun)

        # [좌표] X좌표와 Y좌표를 쉼표로 결합
        if '좌표정보X(EPSG5174)' in df.columns and '좌표정보Y(EPSG5174)' in df.columns:
            df['좌표'] = df.apply(
                lambda row: f"{row['좌표정보X(EPSG5174)']}, {row['좌표정보Y(EPSG5174)']}" 
                if pd.notnull(row['좌표정보X(EPSG5174)']) and pd.notnull(row['좌표정보Y(EPSG5174)']) 
                else None, axis=1
            )
        else:
            df['좌표'] = None

        # 4. 컬럼명 변경 (기존 컬럼명 -> 요청하신 컬럼명)
        rename_map = {
            '사업장명': '상호명(통일)',
            '업태구분명': '업태 구분명',
            '상세영업상태명': '영업중/폐업',
            '인허가일자': '허가날짜',
            '폐업일자': '폐업날짜'
        }
        df.rename(columns=rename_map, inplace=True)

        # 5. 필요한 컬럼만 선택
        final_columns = [
            '상호명(통일)', 
            '업태 구분명', 
            '영업중/폐업', 
            '허가날짜', 
            '폐업날짜', 
            '좌표', 
            '소재지'
        ]
        
        # 실제 데이터프레임에 존재하는 컬럼만 선택 (에러 방지)
        existing_cols = [col for col in final_columns if col in df.columns]
        df_subset = df[existing_cols]
        
        dfs.append(df_subset)

    except Exception as e:
        print(f"파일 처리 중 오류 발생 ({os.path.basename(file_path)}): {e}")

# 6. 전체 병합 및 저장
if dfs:
    result_df = pd.concat(dfs, ignore_index=True)
    
    # 요청하신 컬럼 순서대로 재정렬 (없는 컬럼은 비어있는 상태로 생성됨)
    result_df = result_df.reindex(columns=final_columns)
    
    # CSV 파일로 저장 (utf-8-sig 인코딩 사용)
    result_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    
    print(f"\n성공적으로 병합되었습니다!")
    print(f"저장된 파일 위치: {output_filename}")
    print(f"총 데이터 개수: {len(result_df)}행")
    print(result_df.head()) # 결과 미리보기
else:
    print("병합할 데이터를 찾지 못했습니다.")