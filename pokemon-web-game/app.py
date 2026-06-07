from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pymysql
import random
import secrets
from datetime import datetime
from contextlib import contextmanager
from config import DB_CONFIG, FLASK_SECRET_KEY, FLASK_DEBUG, FLASK_HOST, FLASK_PORT

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# 데이터베이스 연결 컨텍스트 매니저
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
    """쿼리 실행 헬퍼 함수"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            
            if commit:
                conn.commit()
                return cursor.lastrowid if 'INSERT' in query.upper() else cursor.rowcount
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            
            return None

# 필터 추가 (Jinja2 템플릿용)
@app.template_filter('timestamp')
def timestamp_filter(s):
    """현재 시간 반환"""
    return datetime.now().strftime('%H:%M')

# 메인 페이지
@app.route('/')
def index():
    """시작 화면"""
# 1. 스타터 선택 모드인지 먼저 확인합니다.
    choose_mode = session.get('choose_starter', False)

    # 2. [수정] 로그인이 되어 있고, "스타터 선택 모드가 아닐 때만" 메인으로 보냅니다.
    if 'user_id' in session and not choose_mode:
        return redirect(url_for('main'))
    
    starters = []
    
    if choose_mode:
        # 스타터 포켓몬 정보 가져오기
        starters = execute_query(
            'SELECT * FROM pokemon_full_info WHERE id IN (1, 4, 7, 25)',
            fetch_all=True
        )
    
    return render_template('start.html', choose_mode=choose_mode, starters=starters)

@app.route('/new_game', methods=['POST'])
def new_game():
    """새 게임 시작"""
    username = request.form.get('username')
    
    if not username:
        return redirect(url_for('index'))
    
    # 사용자 생성
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO users (username, money, current_floor) VALUES (%s, %s, %s)',
                    (username, 5000, 1)
                )
                user_id = cursor.lastrowid
                
                # 기본 아이템 지급 (몬스터볼)
                cursor.execute(
                    'INSERT INTO inventory (user_id, item_id, count) VALUES (%s, %s, %s)',
                    (user_id, 1, 10)
                )
                
                conn.commit()
        
        session['user_id'] = user_id
        session['username'] = username
        session['choose_starter'] = True
        
        return redirect(url_for('index'))
    except pymysql.IntegrityError:
        # 이미 존재하는 사용자명
        return redirect(url_for('index'))

@app.route('/select_starter', methods=['POST'])
def select_starter():
    """스타터 포켓몬 선택"""
    pokemon_id = int(request.form.get('id'))
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('index'))
    
    # 스타터 포켓몬 정보 가져오기
    pokemon = execute_query(
        'SELECT * FROM pokemon_full_info WHERE id = %s',
        (pokemon_id,),
        fetch_one=True
    )
    
    if not pokemon:
        return redirect(url_for('index'))
    
    # 포켓몬 기술 가져오기
    moves = execute_query(
        '''SELECT m.id FROM moves m
           JOIN pokemon_moves pm ON m.id = pm.move_id
           WHERE pm.pokemon_id = %s AND pm.learn_level <= 5
           ORDER BY pm.learn_level DESC LIMIT 2''',
        (pokemon_id,),
        fetch_all=True
    )
    
    # 스타터 스탯 계산
    level = 5
    max_hp = int(pokemon['hp'] * 1.5)
    attack = int(pokemon['attack'] * 1.2)
    defense = int(pokemon['defense'] * 1.2)
    sp_attack = int(pokemon['sp_attack'] * 1.2)
    sp_defense = int(pokemon['sp_defense'] * 1.2)
    speed = int(pokemon['speed'] * 1.2)
    
    # 파티에 추가
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO my_pokemon 
                (user_id, pokemon_dex_id, level, current_hp, max_hp, attack, defense, 
                 sp_attack, sp_defense, speed, is_in_party, slot_position, move1_id, move2_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (user_id, pokemon_id, level, max_hp, max_hp, attack, defense,
                  sp_attack, sp_defense, speed, 1, 1,
                  moves[0]['id'] if len(moves) > 0 else None,
                  moves[1]['id'] if len(moves) > 1 else None))
            
            # 도감 등록
            cursor.execute('''
                INSERT INTO pokedex_progress (user_id, pokemon_id, is_caught, is_seen)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE is_caught = 1, is_seen = 1
            ''', (user_id, pokemon_id, 1, 1))
            
            conn.commit()
    
    session['choose_starter'] = False
    return redirect(url_for('main'))

@app.route('/main')
def main():
    """메인 메뉴"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    
    # 사용자 정보
    user = execute_query(
        'SELECT * FROM users WHERE user_id = %s',
        (user_id,),
        fetch_one=True
    )
    
    # 파티 포켓몬
    party = execute_query('''
        SELECT mp.*, pfi.name_ko, pfi.image_url, pfi.type1, pfi.type2
        FROM my_pokemon mp
        JOIN pokemon_full_info pfi ON mp.pokemon_id = pfi.id
        WHERE mp.user_id = %s AND mp.is_in_party = 1
        ORDER BY mp.slot_position
    ''', (user_id,), fetch_all=True)
    
    return render_template('main.html', user=user, party=party)

@app.route('/battle')
def battle():
    """배틀 화면"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    
    # 사용자 정보
    user = execute_query(
        'SELECT * FROM users WHERE user_id = %s',
        (user_id,),
        fetch_one=True
    )
    
    # 현재 층에 맞는 위치 찾기
    current_floor = user['current_floor']
    location = execute_query('''
        SELECT * FROM locations 
        WHERE floor_range_start <= %s AND floor_range_end >= %s
        LIMIT 1
    ''', (current_floor, current_floor), fetch_one=True)
    
    if not location:
        location = execute_query('SELECT * FROM locations ORDER BY location_id LIMIT 1', fetch_one=True)
    
    # 야생 포켓몬 조우
    encounters = execute_query('''
        SELECT e.*, pfi.*
        FROM encounters e
        JOIN pokemon_full_info pfi ON e.pokemon_id = pfi.id
        WHERE e.location_id = %s
    ''', (location['location_id'],), fetch_all=True)
    
    if not encounters:
        return redirect(url_for('main'))
    
    # 랜덤 선택
    wild_pokemon = random.choice(encounters)
    wild_level = random.randint(
        wild_pokemon['min_level'] or current_floor,
        wild_pokemon['max_level'] or current_floor + 2
    )
    
    # 내 포켓몬 (첫 번째 파티 멤버)
    my_pokemon = execute_query('''
        SELECT mp.*, pfi.name_ko, pfi.image_url, pfi.type1, pfi.type2
        FROM my_pokemon mp
        JOIN pokemon_full_info pfi ON mp.pokemon_id = pfi.id
        WHERE mp.user_id = %s AND mp.is_in_party = 1
        ORDER BY mp.slot_position
        LIMIT 1
    ''', (user_id,), fetch_one=True)
    
    if not my_pokemon:
        return redirect(url_for('main'))
    
    return render_template('battle.html',
                         user=user,
                         location=location,
                         wild_pokemon=wild_pokemon,
                         wild_level=wild_level,
                         my_pokemon=my_pokemon)

@app.route('/api/battle/action', methods=['POST'])
def battle_action():
    """배틀 액션 처리"""
    data = request.json
    action = data.get('action')
    user_id = session.get('user_id')
    
    if action == 'attack':
        move_id = data.get('move_id')
        my_slot_id = data.get('my_slot_id')
        wild_pokemon_id = data.get('wild_pokemon_id')
        wild_level = data.get('wild_level')
        wild_current_hp = data.get('wild_current_hp')
        
        # 기술 정보
        move = execute_query(
            'SELECT * FROM moves WHERE move_id = %s',
            (move_id,),
            fetch_one=True
        )
        
        # 내 포켓몬 정보
        my_pokemon = execute_query(
            'SELECT * FROM my_pokemon WHERE slot_id = %s',
            (my_slot_id,),
            fetch_one=True
        )
        
        # 야생 포켓몬 정보
        wild_pokemon = execute_query(
            'SELECT * FROM pokemon_full_info WHERE pokemon_id = %s',
            (wild_pokemon_id,),
            fetch_one=True
        )
        
        # 데미지 계산
        if move['category'] == 'physical':
            damage = (my_pokemon['attack'] / (wild_pokemon['defense'] * (1 + wild_level * 0.05))) * move['power'] * 0.4
        elif move['category'] == 'special':
            damage = (my_pokemon['sp_attack'] / (wild_pokemon['sp_defense'] * (1 + wild_level * 0.05))) * move['power'] * 0.4
        else:
            damage = 0
        
        damage = max(1, int(damage * random.uniform(0.85, 1.0)))
        wild_current_hp -= damage
        
        # 야생 포켓몬 기절 확인
        wild_fainted = wild_current_hp <= 0
        
        response_data = {
            'success': True,
            'move_name': move['name_ko'],
            'damage': damage,
            'wild_hp': max(0, wild_current_hp),
            'wild_fainted': wild_fainted
        }
        
        if wild_fainted:
            # 경험치 획득
            exp_gain = int(wild_pokemon['attack'] * wild_level * 0.5)
            money_gain = wild_level * 10
            
            # 업데이트
            with get_db() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        UPDATE my_pokemon 
                        SET exp = exp + %s
                        WHERE slot_id = %s
                    ''', (exp_gain, my_slot_id))
                    
                    cursor.execute('''
                        UPDATE users 
                        SET money = money + %s
                        WHERE user_id = %s
                    ''', (money_gain, user_id))
                    
                    # 레벨업 체크
                    cursor.execute('SELECT exp, level FROM my_pokemon WHERE slot_id = %s', (my_slot_id,))
                    pokemon_data = cursor.fetchone()
                    
                    exp_needed = pokemon_data['level'] * 100
                    leveled_up = False
                    new_level = pokemon_data['level']
                    
                    if pokemon_data['exp'] >= exp_needed:
                        new_level = pokemon_data['level'] + 1
                        leveled_up = True
                        
                        cursor.execute('''
                            UPDATE my_pokemon 
                            SET level = %s, exp = 0,
                                max_hp = max_hp + 5,
                                attack = attack + 2,
                                defense = defense + 2,
                                sp_attack = sp_attack + 2,
                                sp_defense = sp_defense + 2,
                                speed = speed + 2
                            WHERE slot_id = %s
                        ''', (new_level, my_slot_id))
                    
                    # 도감 등록
                    cursor.execute('''
                        INSERT INTO pokedex_progress (user_id, pokemon_id, is_caught, is_seen)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE is_seen = 1
                    ''', (user_id, wild_pokemon_id, 0, 1))
                    
                    conn.commit()
            
            response_data.update({
                'exp_gain': exp_gain,
                'money_gain': money_gain,
                'leveled_up': leveled_up,
                'new_level': new_level
            })
        else:
            # 상대 반격
            counter_damage = int(wild_pokemon['attack'] * (1 + wild_level * 0.05) * 0.3)
            my_hp = max(0, my_pokemon['current_hp'] - counter_damage)
            
            with get_db() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        UPDATE my_pokemon 
                        SET current_hp = %s
                        WHERE slot_id = %s
                    ''', (my_hp, my_slot_id))
                    conn.commit()
            
            response_data.update({
                'counter_damage': counter_damage,
                'my_hp': my_hp
            })
        
        return jsonify(response_data)
    
    elif action == 'catch':
        wild_pokemon_id = data.get('wild_pokemon_id')
        wild_level = data.get('wild_level')
        wild_current_hp = data.get('wild_current_hp')
        wild_max_hp = data.get('wild_max_hp')
        
        # 포획률 계산
        catch_rate = max(10, 100 - (wild_current_hp / wild_max_hp) * 50)
        caught = random.randint(1, 100) <= catch_rate
        
        if caught:
            # 포켓몬 정보
            pokemon = execute_query(
                'SELECT * FROM pokemon_full_info WHERE pokemon_id = %s',
                (wild_pokemon_id,),
                fetch_one=True
            )
            
            # 기술
            moves = execute_query('''
                SELECT m.id FROM moves m
                JOIN pokemon_moves pm ON m.id = pm.move_id
                WHERE pm.pokemon_id = %s AND pm.learn_level <= %s
                ORDER BY pm.learn_level DESC LIMIT 2
            ''', (wild_pokemon_id, wild_level), fetch_all=True)
            
            # 포켓몬 추가
            with get_db() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        INSERT INTO my_pokemon 
                        (user_id, pokemon_id, level, current_hp, max_hp, attack, defense,
                         sp_attack, sp_defense, speed, is_in_party, slot_position, move1_id, move2_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (user_id, wild_pokemon_id, wild_level,
                          int(pokemon['hp'] * (1 + wild_level * 0.05)),
                          int(pokemon['hp'] * (1 + wild_level * 0.05)),
                          int(pokemon['attack'] * (1 + wild_level * 0.05)),
                          int(pokemon['defense'] * (1 + wild_level * 0.05)),
                          int(pokemon['sp_attack'] * (1 + wild_level * 0.05)),
                          int(pokemon['sp_defense'] * (1 + wild_level * 0.05)),
                          int(pokemon['speed'] * (1 + wild_level * 0.05)),
                          0, 99,
                          moves[0]['id'] if len(moves) > 0 else None,
                          moves[1]['id'] if len(moves) > 1 else None))
                    
                    # 도감 등록
                    cursor.execute('''
                        INSERT INTO pokedex_progress (user_id, pokemon_id, is_caught, is_seen)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE is_caught = 1, is_seen = 1
                    ''', (user_id, wild_pokemon_id, 1, 1))
                    
                    # 몬스터볼 소모
                    cursor.execute('''
                        UPDATE inventory 
                        SET count = count - 1 
                        WHERE user_id = %s AND item_id = 1 AND count > 0
                    ''', (user_id,))
                    
                    conn.commit()
        
        return jsonify({
            'success': True,
            'caught': caught,
            'message': '포켓몬을 잡았다!' if caught else '포켓몬이 탈출했다!'
        })
    
    elif action == 'run':
        return jsonify({'success': True, 'run': True})
    
    return jsonify({'success': False})

@app.route('/api/advance_floor', methods=['POST'])
def advance_floor():
    """다음 층으로 이동"""
    user_id = session.get('user_id')
    
    user = execute_query(
        'SELECT current_floor FROM users WHERE user_id = %s',
        (user_id,),
        fetch_one=True
    )
    
    new_floor = user['current_floor'] + 1
    
    # 10층마다 보상
    bonus = 0
    if new_floor % 10 == 0:
        bonus = 1000
        execute_query(
            'UPDATE users SET money = money + %s WHERE user_id = %s',
            (bonus, user_id),
            commit=True
        )
    
    execute_query(
        'UPDATE users SET current_floor = %s WHERE user_id = %s',
        (new_floor, user_id),
        commit=True
    )
    
    return jsonify({'success': True, 'new_floor': new_floor, 'bonus': bonus})

@app.route('/pc')
def pc():
    """PC 화면"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    
    # 파티 포켓몬
    party = execute_query('''
        SELECT mp.*, pfi.name_ko, pfi.image_url, pfi.type1, pfi.type2
        FROM my_pokemon mp
        JOIN pokemon_full_info pfi ON mp.pokemon_id = pfi.id
        WHERE mp.user_id = %s AND mp.is_in_party = 1
        ORDER BY mp.slot_position
    ''', (user_id,), fetch_all=True)
    
    # PC 포켓몬
    pc_pokemon = execute_query('''
        SELECT mp.*, pfi.name_ko, pfi.image_url, pfi.type1, pfi.type2
        FROM my_pokemon mp
        JOIN pokemon_full_info pfi ON mp.pokemon_id = pfi.id
        WHERE mp.user_id = %s AND mp.is_in_party = 0
        ORDER BY mp.slot_id
    ''', (user_id,), fetch_all=True)
    
    return render_template('pc.html', party=party, pc_pokemon=pc_pokemon)

@app.route('/api/swap_pokemon', methods=['POST'])
def swap_pokemon():
    """포켓몬 교체"""
    data = request.json
    slot_id = data.get('slot_id')
    to_party = data.get('to_party')
    user_id = session.get('user_id')
    
    if to_party:
        # 파티 슬롯 수 체크
        party_count = execute_query('''
            SELECT COUNT(*) as count FROM my_pokemon 
            WHERE user_id = %s AND is_in_party = 1
        ''', (user_id,), fetch_one=True)
        
        if party_count['count'] >= 6:
            return jsonify({'success': False, 'message': '파티가 가득 찼습니다!'})
        
        new_position = party_count['count'] + 1
        execute_query('''
            UPDATE my_pokemon 
            SET is_in_party = 1, slot_position = %s
            WHERE slot_id = %s
        ''', (new_position, slot_id), commit=True)
    else:
        execute_query('''
            UPDATE my_pokemon 
            SET is_in_party = 0, slot_position = 99
            WHERE slot_id = %s
        ''', (slot_id,), commit=True)
    
    return jsonify({'success': True})

@app.route('/shop')
def shop():
    """상점"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    
    user = execute_query(
        'SELECT * FROM users WHERE user_id = %s',
        (user_id,),
        fetch_one=True
    )
    
    items = execute_query('SELECT * FROM items', fetch_all=True)
    
    inventory = execute_query('''
        SELECT i.*, it.name_ko, it.price
        FROM inventory i
        JOIN items it ON i.item_id = it.item_id
        WHERE i.user_id = %s
    ''', (user_id,), fetch_all=True)
    
    return render_template('shop.html', user=user, items=items, inventory=inventory)

@app.route('/api/buy_item', methods=['POST'])
def buy_item():
    """아이템 구매"""
    data = request.json
    item_id = data.get('item_id')
    user_id = session.get('user_id')
    
    item = execute_query(
        'SELECT * FROM items WHERE item_id = %s',
        (item_id,),
        fetch_one=True
    )
    
    user = execute_query(
        'SELECT money FROM users WHERE user_id = %s',
        (user_id,),
        fetch_one=True
    )
    
    if user['money'] < item['price']:
        return jsonify({'success': False, 'message': '돈이 부족합니다!'})
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 돈 차감
            cursor.execute(
                'UPDATE users SET money = money - %s WHERE user_id = %s',
                (item['price'], user_id)
            )
            
            # 인벤토리 추가
            cursor.execute('''
                SELECT * FROM inventory 
                WHERE user_id = %s AND item_id = %s
            ''', (user_id, item_id))
            
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('''
                    UPDATE inventory 
                    SET count = count + 1
                    WHERE user_id = %s AND item_id = %s
                ''', (user_id, item_id))
            else:
                cursor.execute('''
                    INSERT INTO inventory (user_id, item_id, count)
                    VALUES (%s, %s, 1)
                ''', (user_id, item_id))
            
            conn.commit()
    
    return jsonify({'success': True})

@app.route('/pokedex')
def pokedex():
    """도감"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    
    # 전체 포켓몬과 진행도
    pokemon_list = execute_query('''
        SELECT pfi.*, 
               COALESCE(pp.is_caught, 0) as is_caught,
               COALESCE(pp.is_seen, 0) as is_seen
        FROM pokemon_full_info pfi
        LEFT JOIN pokedex_progress pp ON pfi.id = pp.pokemon_id 
            AND pp.user_id = %s
        ORDER BY pfi.id
    ''', (user_id,), fetch_all=True)
    
    caught_count = sum(1 for p in pokemon_list if p['is_caught'])
    seen_count = sum(1 for p in pokemon_list if p['is_seen'])
    
    return render_template('pokedex.html', 
                         pokemon_list=pokemon_list,
                         caught_count=caught_count,
                         seen_count=seen_count,
                         total_count=len(pokemon_list))

@app.route('/api/heal_pokemon', methods=['POST'])
def heal_pokemon():
    """포켓몬 회복"""
    user_id = session.get('user_id')
    
    execute_query('''
        UPDATE my_pokemon 
        SET current_hp = max_hp
        WHERE user_id = %s AND is_in_party = 1
    ''', (user_id,), commit=True)
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)