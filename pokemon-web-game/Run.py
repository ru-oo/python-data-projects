#!/usr/bin/env python3
"""
포켓몬 게임 서버 실행 스크립트
"""
import sys
import os

def check_environment():
    """환경 설정 확인"""
    print("=== 환경 확인 중 ===\n")
    
    # .env 파일 확인
    if not os.path.exists('.env'):
        print("⚠️  .env 파일이 없습니다!")
        print("   .env.example 파일을 복사하여 .env 파일을 만들고")
        print("   데이터베이스 정보를 입력해주세요.\n")
        response = input("계속하시겠습니까? (y/n): ")
        if response.lower() != 'y':
            print("종료합니다.")
            sys.exit(0)
    
    # 패키지 확인
    try:
        import flask
        import pymysql
        import dotenv
        print("✓ 필요한 패키지가 모두 설치되어 있습니다.\n")
    except ImportError as e:
        print(f"✗ 패키지 설치 필요: {e}")
        print("   pip install -r requirements.txt 를 실행하세요.\n")
        sys.exit(1)
    
    # 데이터베이스 연결 확인
    try:
        from db_utils import check_database_connection
        if check_database_connection():
            print("✓ 데이터베이스 연결 성공!\n")
        else:
            print("✗ 데이터베이스 연결 실패")
            print("   config.py의 설정을 확인하거나")
            print("   MariaDB 서버가 실행중인지 확인하세요.\n")
            response = input("계속하시겠습니까? (y/n): ")
            if response.lower() != 'y':
                sys.exit(1)
    except Exception as e:
        print(f"✗ 데이터베이스 확인 중 오류: {e}\n")
        response = input("계속하시겠습니까? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("     포켓몬 DS 웹 게임 - MariaDB 버전")
    print("=" * 50)
    print()
    
    check_environment()
    
    print("=== 서버 시작 ===\n")
    
    try:
        from app import app
        from config import FLASK_DEBUG, FLASK_HOST, FLASK_PORT
        
        print(f"서버 주소: http://{FLASK_HOST}:{FLASK_PORT}")
        print("종료하려면 Ctrl+C를 누르세요.\n")
        
        app.run(
            debug=FLASK_DEBUG,
            host=FLASK_HOST,
            port=FLASK_PORT
        )
    except KeyboardInterrupt:
        print("\n\n서버를 종료합니다.")
    except Exception as e:
        print(f"\n서버 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()