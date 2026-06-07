"""
데이터베이스 마이그레이션 및 관리 도구
"""
import pymysql
import sys
from config import DB_CONFIG
from datetime import datetime

def get_connection():
    """데이터베이스 연결"""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset=DB_CONFIG['charset'],
    )

def backup_database(output_file=None):
    """데이터베이스 백업"""
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'backup_{timestamp}.sql'
    
    import subprocess
    
    cmd = [
        'mysqldump',
        '-h', DB_CONFIG['host'],
        '-P', str(DB_CONFIG['port']),
        '-u', DB_CONFIG['user'],
        f"-p{DB_CONFIG['password']}" if DB_CONFIG['password'] else '',
        DB_CONFIG['database']
    ]
    
    try:
        with open(output_file, 'w', encoding='utf8') as f:
            subprocess.run([c for c in cmd if c], stdout=f, check=True)
        print(f"✓ 백업 완료: {output_file}")
        return True
    except Exception as e:
        print(f"✗ 백업 실패: {e}")
        return False

def restore_database(input_file):
    """데이터베이스 복원"""
    import subprocess
    
    if not input_file.endswith('.sql'):
        print("✗ SQL 파일만 복원 가능합니다.")
        return False
    
    cmd = [
        'mysql',
        '-h', DB_CONFIG['host'],
        '-P', str(DB_CONFIG['port']),
        '-u', DB_CONFIG['user'],
        f"-p{DB_CONFIG['password']}" if DB_CONFIG['password'] else '',
        DB_CONFIG['database']
    ]
    
    try:
        with open(input_file, 'r', encoding='utf8') as f:
            subprocess.run([c for c in cmd if c], stdin=f, check=True)
        print(f"✓ 복원 완료: {input_file}")
        return True
    except Exception as e:
        print(f"✗ 복원 실패: {e}")
        return False

def clear_user_data():
    """사용자 데이터 초기화 (게임 데이터는 유지)"""
    response = input("⚠️  모든 사용자 데이터를 삭제하시겠습니까? (yes/no): ")
    if response.lower() != 'yes':
        print("취소되었습니다.")
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 외래키 체크 비활성화
        cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
        
        # 사용자 관련 테이블 초기화
        tables = ['my_pokemon', 'inventory', 'pokedex_progress', 'users']
        
        for table in tables:
            cursor.execute(f'TRUNCATE TABLE {table}')
            print(f"✓ {table} 테이블 초기화 완료")
        
        # 외래키 체크 활성화
        cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
        
        conn.commit()
        print("\n✓ 사용자 데이터 초기화 완료")
    except Exception as e:
        conn.rollback()
        print(f"✗ 초기화 실패: {e}")
    finally:
        cursor.close()
        conn.close()

def show_statistics():
    """데이터베이스 통계 표시"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n=== 데이터베이스 통계 ===\n")
    
    # 테이블별 레코드 수
    cursor.execute("""
        SELECT table_name, table_rows
        FROM information_schema.tables
        WHERE table_schema = %s
        ORDER BY table_name
    """, (DB_CONFIG['database'],))
    
    tables = cursor.fetchall()
    
    print("테이블별 레코드 수:")
    for table in tables:
        print(f"  {table[0]:25s} : {table[1]:>6d} rows")
    
    # 사용자 통계
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM my_pokemon")
    pokemon_count = cursor.fetchone()[0]
    
    print(f"\n사용자 수: {user_count}")
    print(f"총 포켓몬 수: {pokemon_count}")
    
    # 활동 통계
    if user_count > 0:
        cursor.execute("SELECT AVG(current_floor) FROM users")
        avg_floor = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT MAX(current_floor) FROM users")
        max_floor = cursor.fetchone()[0] or 0
        
        print(f"평균 층수: {avg_floor:.1f}")
        print(f"최고 층수: {max_floor}")
    
    cursor.close()
    conn.close()

def optimize_tables():
    """테이블 최적화"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n=== 테이블 최적화 ===\n")
    
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
        ORDER BY table_name
    """, (DB_CONFIG['database'],))
    
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f"OPTIMIZE TABLE {table_name}")
            print(f"✓ {table_name} 최적화 완료")
        except Exception as e:
            print(f"✗ {table_name} 최적화 실패: {e}")
    
    cursor.close()
    conn.close()

def check_integrity():
    """데이터 무결성 확인"""
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    print("\n=== 데이터 무결성 확인 ===\n")
    
    issues = []
    
    # 1. 고아 레코드 확인
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM my_pokemon mp
        LEFT JOIN users u ON mp.user_id = u.user_id
        WHERE u.user_id IS NULL
    """)
    orphan_pokemon = cursor.fetchone()['cnt']
    if orphan_pokemon > 0:
        issues.append(f"고아 포켓몬 레코드: {orphan_pokemon}개")
    
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM inventory i
        LEFT JOIN users u ON i.user_id = u.user_id
        WHERE u.user_id IS NULL
    """)
    orphan_inventory = cursor.fetchone()['cnt']
    if orphan_inventory > 0:
        issues.append(f"고아 인벤토리 레코드: {orphan_inventory}개")
    
    # 2. 잘못된 HP 값
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM my_pokemon
        WHERE current_hp < 0 OR current_hp > max_hp
    """)
    invalid_hp = cursor.fetchone()['cnt']
    if invalid_hp > 0:
        issues.append(f"잘못된 HP 값: {invalid_hp}개")
    
    # 3. 중복 사용자명
    cursor.execute("""
        SELECT username, COUNT(*) as cnt
        FROM users
        GROUP BY username
        HAVING cnt > 1
    """)
    duplicate_users = cursor.fetchall()
    if duplicate_users:
        issues.append(f"중복 사용자명: {len(duplicate_users)}개")
    
    if issues:
        print("발견된 문제:")
        for issue in issues:
            print(f"  ⚠️  {issue}")
    else:
        print("✓ 데이터 무결성 문제 없음")
    
    cursor.close()
    conn.close()

def create_test_user():
    """테스트 사용자 생성"""
    conn = get_connection()
    cursor = conn.cursor()
    
    username = input("테스트 사용자 이름: ")
    
    try:
        cursor.execute(
            "INSERT INTO users (username, money, current_floor) VALUES (%s, %s, %s)",
            (username, 10000, 1)
        )
        user_id = cursor.lastrowid
        
        # 스타터 포켓몬 추가
        cursor.execute(
            "SELECT * FROM pokemon_full_info WHERE pokemon_id = 25"
        )
        pikachu = cursor.fetchone()
        
        if pikachu:
            cursor.execute("""
                INSERT INTO my_pokemon 
                (user_id, pokemon_id, level, current_hp, max_hp, attack, defense,
                 sp_attack, sp_defense, speed, is_in_party, slot_position)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, 25, 10, 60, 60, 70, 50, 60, 60, 110, 1, 1))
        
        # 기본 아이템
        cursor.execute(
            "INSERT INTO inventory (user_id, item_id, count) VALUES (%s, %s, %s)",
            (user_id, 1, 50)
        )
        
        conn.commit()
        print(f"✓ 테스트 사용자 '{username}' 생성 완료 (ID: {user_id})")
    except pymysql.IntegrityError:
        print(f"✗ 사용자 '{username}'이(가) 이미 존재합니다.")
    except Exception as e:
        conn.rollback()
        print(f"✗ 사용자 생성 실패: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    """메인 메뉴"""
    while True:
        print("\n" + "=" * 50)
        print("   데이터베이스 관리 도구")
        print("=" * 50)
        print("\n1. 통계 보기")
        print("2. 백업")
        print("3. 복원")
        print("4. 사용자 데이터 초기화")
        print("5. 테이블 최적화")
        print("6. 데이터 무결성 확인")
        print("7. 테스트 사용자 생성")
        print("0. 종료")
        
        choice = input("\n선택: ")
        
        if choice == '1':
            show_statistics()
        elif choice == '2':
            backup_database()
        elif choice == '3':
            filename = input("복원할 파일명: ")
            restore_database(filename)
        elif choice == '4':
            clear_user_data()
        elif choice == '5':
            optimize_tables()
        elif choice == '6':
            check_integrity()
        elif choice == '7':
            create_test_user()
        elif choice == '0':
            print("종료합니다.")
            break
        else:
            print("잘못된 선택입니다.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n종료합니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        sys.exit(1)