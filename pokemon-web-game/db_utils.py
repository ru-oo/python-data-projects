"""
데이터베이스 유틸리티 함수들
자주 사용되는 데이터베이스 작업을 위한 헬퍼 함수들
"""
import pymysql
from config import DB_CONFIG
from contextlib import contextmanager

@contextmanager
def get_db():
    """MariaDB 연결을 위한 컨텍스트 매니저"""
    conn = pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset=DB_CONFIG['charset'],
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        yield conn
    finally:
        conn.close()

def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    쿼리 실행 헬퍼 함수
    
    Args:
        query: SQL 쿼리문
        params: 쿼리 파라미터 (튜플 또는 리스트)
        fetch_one: 단일 행 반환
        fetch_all: 모든 행 반환
        commit: 커밋 여부 (INSERT, UPDATE, DELETE)
    
    Returns:
        fetch_one이면 dict, fetch_all이면 list of dicts, 
        commit이면 lastrowid 또는 affected rows
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            
            if commit:
                conn.commit()
                # INSERT 쿼리면 lastrowid, 아니면 affected rows
                return cursor.lastrowid if 'INSERT' in query.upper() else cursor.rowcount
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            
            return None

def execute_many(query, params_list):
    """
    여러 행을 한번에 삽입
    
    Args:
        query: SQL 쿼리문
        params_list: 파라미터 리스트의 리스트
    
    Returns:
        affected rows
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount

# 자주 사용되는 쿼리 함수들

def get_user_by_id(user_id):
    """사용자 ID로 사용자 정보 조회"""
    return execute_query(
        'SELECT * FROM users WHERE user_id = %s',
        (user_id,),
        fetch_one=True
    )

def get_user_by_username(username):
    """사용자명으로 사용자 정보 조회"""
    return execute_query(
        'SELECT * FROM users WHERE username = %s',
        (username,),
        fetch_one=True
    )

def create_user(username, money=5000, current_floor=1):
    """새 사용자 생성"""
    return execute_query(
        'INSERT INTO users (username, money, current_floor) VALUES (%s, %s, %s)',
        (username, money, current_floor),
        commit=True
    )

def get_pokemon_info(pokemon_id):
    """포켓몬 정보 조회"""
    return execute_query(
        'SELECT * FROM pokemon_full_info WHERE pokemon_id = %s',
        (pokemon_id,),
        fetch_one=True
    )

def get_user_party(user_id):
    """사용자의 파티 포켓몬 조회"""
    return execute_query('''
        SELECT mp.*, pfi.name_ko, pfi.image_url, pfi.type1, pfi.type2
        FROM my_pokemon mp
        JOIN pokemon_full_info pfi ON mp.pokemon_id = pfi.id
        WHERE mp.user_id = %s AND mp.is_in_party = 1
        ORDER BY mp.slot_position
    ''', (user_id,), fetch_all=True)

def get_user_pc_pokemon(user_id):
    """사용자의 PC 포켓몬 조회"""
    return execute_query('''
        SELECT mp.*, pfi.name_ko, pfi.image_url, pfi.type1, pfi.type2
        FROM my_pokemon mp
        JOIN pokemon_full_info pfi ON mp.pokemon_id = pfi.id
        WHERE mp.user_id = %s AND mp.is_in_party = 0
        ORDER BY mp.slot_id
    ''', (user_id,), fetch_all=True)

def get_user_inventory(user_id):
    """사용자 인벤토리 조회"""
    return execute_query('''
        SELECT i.*, it.name_ko, it.price, it.effect
        FROM inventory i
        JOIN items it ON i.item_id = it.item_id
        WHERE i.user_id = %s
    ''', (user_id,), fetch_all=True)

def update_user_money(user_id, amount):
    """사용자 돈 업데이트"""
    return execute_query(
        'UPDATE users SET money = money + %s WHERE user_id = %s',
        (amount, user_id),
        commit=True
    )

def update_user_floor(user_id, floor):
    """사용자 층 업데이트"""
    return execute_query(
        'UPDATE users SET current_floor = %s WHERE user_id = %s',
        (floor, user_id),
        commit=True
    )

def add_to_inventory(user_id, item_id, count=1):
    """인벤토리에 아이템 추가"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 기존 아이템 확인
            cursor.execute('''
                SELECT * FROM inventory 
                WHERE user_id = %s AND item_id = %s
            ''', (user_id, item_id))
            
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('''
                    UPDATE inventory 
                    SET count = count + %s
                    WHERE user_id = %s AND item_id = %s
                ''', (count, user_id, item_id))
            else:
                cursor.execute('''
                    INSERT INTO inventory (user_id, item_id, count)
                    VALUES (%s, %s, %s)
                ''', (user_id, item_id, count))
            
            conn.commit()
            return cursor.rowcount

def remove_from_inventory(user_id, item_id, count=1):
    """인벤토리에서 아이템 제거""" 
    return execute_query('''
        UPDATE inventory 
        SET count = count - %s
        WHERE user_id = %s AND item_id = %s AND count >= %s
    ''', (count, user_id, item_id, count), commit=True)

def add_pokemon_to_party(user_id, pokemon_id, level, stats):
    """파티에 포켓몬 추가"""
    return execute_query('''
        INSERT INTO my_pokemon 
        (user_id, pokemon_id, level, current_hp, max_hp, attack, defense,
         sp_attack, sp_defense, speed, is_in_party, slot_position, move1_id, move2_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (user_id, pokemon_id, level, stats['current_hp'], stats['max_hp'],
          stats['attack'], stats['defense'], stats['sp_attack'], 
          stats['sp_defense'], stats['speed'], stats['is_in_party'],
          stats['slot_position'], stats.get('move1_id'), stats.get('move2_id')),
    commit=True)

def update_pokemon_hp(slot_id, current_hp):
    """포켓몬 HP 업데이트"""
    return execute_query(
        'UPDATE my_pokemon SET current_hp = %s WHERE slot_id = %s',
        (current_hp, slot_id),
        commit=True
    )

def heal_party_pokemon(user_id):
    """파티 포켓몬 전체 회복"""
    return execute_query(
        'UPDATE my_pokemon SET current_hp = max_hp WHERE user_id = %s AND is_in_party = 1',
        (user_id,),
        commit=True
    )

def update_pokedex(user_id, pokemon_id, is_caught=False, is_seen=True):
    """포켓몬 도감 업데이트"""
    return execute_query('''
        INSERT INTO pokedex_progress (user_id, pokemon_id, is_caught, is_seen)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            is_caught = GREATEST(is_caught, %s),
            is_seen = GREATEST(is_seen, %s)
    ''', (user_id, pokemon_id, is_caught, is_seen, is_caught, is_seen), commit=True)

def get_pokemon_moves(pokemon_id, level):
    """포켓몬이 배울 수 있는 기술 조회"""
    return execute_query('''
        SELECT m.* FROM moves m
        JOIN pokemon_moves pm ON m.move_id = pm.move_id
        WHERE pm.pokemon_id = %s AND pm.learn_level <= %s
        ORDER BY pm.learn_level DESC
        LIMIT 4
    ''', (pokemon_id, level), fetch_all=True)

def get_encounters_by_location(location_id):
    """위치별 야생 포켓몬 조우 정보"""
    return execute_query('''
        SELECT e.*, pfi.*
        FROM encounters e
        JOIN pokemon_full_info pfi ON e.pokemon_id = pfi.id
        WHERE e.location_id = %s
    ''', (location_id,), fetch_all=True)

def get_location_by_floor(floor):
    """층에 해당하는 위치 정보 조회"""
    return execute_query('''
        SELECT * FROM locations 
        WHERE floor_range_start <= %s AND floor_range_end >= %s
        LIMIT 1
    ''', (floor, floor), fetch_one=True)

# 통계 및 분석 함수

def get_user_stats(user_id):
    """사용자 통계 조회"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 기본 정보
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
            
            # 포켓몬 수
            cursor.execute('SELECT COUNT(*) as count FROM my_pokemon WHERE user_id = %s', (user_id,))
            pokemon_count = cursor.fetchone()['count']
            
            # 도감 진행도
            cursor.execute('''
                SELECT 
                    SUM(is_caught) as caught,
                    SUM(is_seen) as seen
                FROM pokedex_progress 
                WHERE user_id = %s
            ''', (user_id,))
            pokedex = cursor.fetchone()
            
            return {
                'user': user,
                'pokemon_count': pokemon_count,
                'caught': pokedex['caught'] or 0,
                'seen': pokedex['seen'] or 0
            }

def check_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
                return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False