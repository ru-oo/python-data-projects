"""
데이터베이스 초기화 및 데이터 삽입 스크립트
MariaDB에서 실행하기 위한 스크립트입니다.
"""
import pymysql
from config import DB_CONFIG

def get_connection():
    """데이터베이스 연결"""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset=DB_CONFIG['charset']
    )

def init_tables():
    """테이블 생성 (이미 SQL 파일로 생성되어 있다면 스킵)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 이미 pokemon_full_info 테이블이 있는지 확인
    cursor.execute("""
        SELECT COUNT(*) as cnt 
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_name = 'pokemon_full_info'
    """, (DB_CONFIG['database'],))
    
    result = cursor.fetchone()
    
    if result[0] > 0:
        print("✓ 테이블이 이미 존재합니다.")
    else:
        print("✗ 테이블이 없습니다. SQL 파일을 먼저 import 해주세요.")
        print("  mysql -u root -p pokemon_db < pokemon__1_.sql")
    
    cursor.close()
    conn.close()

def seed_initial_items():
    """초기 아이템 데이터 삽입"""
    conn = get_connection()
    cursor = conn.cursor()
    
    items = [
        (1, '몬스터볼', 'Poke Ball', 'ball', '포켓몬을 잡는 기본 볼', 200, None),
        (2, '슈퍼볼', 'Great Ball', 'ball', '몬스터볼보다 성능이 좋은 볼', 600, None),
        (3, '하이퍼볼', 'Ultra Ball', 'ball', '매우 성능이 좋은 볼', 1200, None),
        (4, '상처약', 'Potion', 'medicine', 'HP를 20 회복한다', 300, None),
        (5, '좋은상처약', 'Super Potion', 'medicine', 'HP를 50 회복한다', 700, None),
    ]
    
    for item in items:
        try:
            cursor.execute('''
                INSERT IGNORE INTO items 
                (item_id, name_ko, name_en, type, effect, price, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', item)
        except Exception as e:
            print(f"아이템 삽입 오류: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✓ 초기 아이템 데이터 삽입 완료")

def seed_initial_encounters():
    """초기 조우 데이터 삽입"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 위치 데이터가 있는지 확인
    cursor.execute("SELECT COUNT(*) as cnt FROM locations")
    location_count = cursor.fetchone()[0]
    
    if location_count == 0:
        # 기본 위치 추가
        cursor.execute('''
            INSERT INTO locations (name_ko, name_en, floor_range_start, floor_range_end)
            VALUES ('숲', 'Forest', 1, 50)
        ''')
        location_id = cursor.lastrowid
        print("✓ 기본 위치 추가됨")
    else:
        cursor.execute("SELECT location_id FROM locations LIMIT 1")
        location_id = cursor.fetchone()[0]
    
    # 조우 데이터 확인
    cursor.execute("SELECT COUNT(*) as cnt FROM encounters")
    encounter_count = cursor.fetchone()[0]
    
    if encounter_count == 0:
        # 야생 포켓몬 조우 설정 (pokemon_id가 실제 DB에 있는지 확인 필요)
        encounters = [
            (location_id, 16, 2, 5, 0.3),   # 구구
            (location_id, 19, 2, 5, 0.3),   # 꼬렛
            (location_id, 10, 2, 4, 0.2),   # 캐터피
            (location_id, 13, 2, 4, 0.2),   # 뿔충이
        ]
        
        for enc in encounters:
            try:
                cursor.execute('''
                    INSERT INTO encounters 
                    (location_id, pokemon_id, min_level, max_level, encounter_rate)
                    VALUES (%s, %s, %s, %s, %s)
                ''', enc)
            except Exception as e:
                print(f"조우 데이터 삽입 오류: {e}")
        
        conn.commit()
        print("✓ 초기 조우 데이터 삽입 완료")
    else:
        print("✓ 조우 데이터가 이미 존재합니다")
    
    cursor.close()
    conn.close()

def verify_database():
    """데이터베이스 상태 확인"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n=== 데이터베이스 상태 확인 ===")
    
    # 테이블 목록
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s
        ORDER BY table_name
    """, (DB_CONFIG['database'],))
    
    tables = cursor.fetchall()
    print(f"\n총 {len(tables)}개의 테이블:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  - {table[0]}: {count} rows")
    
    # 스타터 포켓몬 확인
    cursor.execute("""
        SELECT pokemon_id, name_ko, type1 
        FROM pokemon_full_info 
        WHERE pokemon_id IN (1, 4, 7, 25)
    """)
    starters = cursor.fetchall()
    
    print(f"\n스타터 포켓몬 ({len(starters)}/4):")
    for s in starters:
        print(f"  - #{s[0]} {s[1]} ({s[2]})")
    
    cursor.close()
    conn.close()

def main():
    """메인 실행 함수"""
    print("포켓몬 게임 DB 초기화 시작...\n")
    
    try:
        # 1. 테이블 확인
        init_tables()
        
        # 2. 초기 아이템 데이터
        seed_initial_items()
        
        # 3. 초기 조우 데이터
        seed_initial_encounters()
        
        # 4. 데이터베이스 상태 확인
        verify_database()
        
        print("\n✓ 데이터베이스 초기화 완료!")
        print("\n다음 단계:")
        print("1. .env 파일을 생성하고 데이터베이스 정보를 입력하세요")
        print("2. python app.py 로 서버를 실행하세요")
        
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        print("\n확인사항:")
        print("1. MariaDB 서버가 실행중인지 확인")
        print("2. config.py의 DB_CONFIG 설정이 올바른지 확인")
        print("3. pokemon_db 데이터베이스가 생성되어 있는지 확인")
        print("4. SQL 파일이 import 되어 있는지 확인")

if __name__ == '__main__':
    main()