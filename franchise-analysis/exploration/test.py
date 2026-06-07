import streamlit as st
import pandas as pd
import io

# 페이지 설정 (넓게 보기)
st.set_page_config(page_title="공공데이터 뷰어", layout="wide")

st.title("📊 공공데이터 CSV 뷰어")
st.markdown("인코딩 문제(cp949/utf-8) 걱정 없이 파일을 업로드해보세요.")

# 파일 업로더 생성
uploaded_file = st.file_uploader("CSV 파일을 여기에 드래그하거나 선택하세요", type=['csv'])

# 데이터 로딩 함수 (캐싱 적용으로 속도 향상)
@st.cache_data
def load_data(file):
    # 시도할 인코딩 목록
    encodings = ['cp949', 'utf-8', 'euc-kr', 'utf-8-sig']
    
    for enc in encodings:
        try:
            # 파일 포인터 위치 초기화 (중요: 여러 번 읽을 때 필요)
            file.seek(0)
            
            # 읽기 시도 (에러 나는 줄은 건너뛰기 옵션 적용)
            df = pd.read_csv(file, encoding=enc, on_bad_lines='skip')
            return df, enc # 성공하면 데이터프레임과 인코딩 방식 반환
        except UnicodeDecodeError:
            continue # 인코딩 안 맞으면 다음으로 넘어감
        except Exception as e:
            # 다른 에러가 나면 멈추지 않고 계속 시도해볼 수도 있지만, 일단 패스
            continue
            
    return None, None # 모든 시도 실패 시

if uploaded_file is not None:
    with st.spinner('파일을 분석하고 있습니다...'):
        df, success_enc = load_data(uploaded_file)

    if df is not None:
            st.success("데이터 로드 완료!")

            # ---------------------------------------------------------
            # 1. 검색 기능 만들기 (가장 중요!)
            # ---------------------------------------------------------
            st.subheader("🔍 브랜드 검색하기")
            
            # 텍스트 입력창 만들기
            keyword = st.text_input("찾고 싶은 브랜드 이름을 입력하세요 (예: 스타벅스, 이디야)", value="스타벅스")

            if keyword:
                # '상호명' 컬럼에서 입력한 글자가 포함된 행만 뽑아내기
                # na=False: 상호명이 비어있는 데이터는 에러 안 나게 제외
                search_result = df[df['상호명'].astype(str).str.contains(keyword, na=False)]
                
                st.write(f"**'{keyword}'** 검색 결과: 총 **{len(search_result):,}**개가 발견되었습니다.")
                
                # 결과 보여주기 (상호명, 지점명, 시군구명, 주소 등 주요 정보만)
                cols_to_view = ['상호명', '지점명', '상권업종대분류명', '상권업종중분류명', '시도명', '시군구명', '도로명주소']
                valid_cols = [c for c in cols_to_view if c in search_result.columns]
                
                st.dataframe(search_result[valid_cols])
            
            # ---------------------------------------------------------
            # 2. 전체 데이터 통계 (참고용)
            # ---------------------------------------------------------
            with st.expander("전체 데이터 요약 보기"):
                st.write(f"전체 데이터 개수: {len(df):,}개")
                # 업종대분류(음식, 소매 등)가 몇 개씩 있는지 세어보기
                if '상권업종중분류명' in df.columns:
                    st.write(df['상권업종중분류명'].value_counts())

    else:
        st.error("❌ 파일을 읽을 수 없습니다. 파일이 손상되었거나 지원하지 않는 형식일 수 있습니다.")