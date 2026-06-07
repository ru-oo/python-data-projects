import random

# --- [게임 데이터] real_final/config.py 및 player.py 기반 ---

# 1. 음식 효과
FOOD_EFFECTS = {
    "물": {"hunger": 0, "thirst": 20, "mental": 5},
    "상한 두유": {"hunger": 10, "thirst": 10, "mental": -10},
    "상한 빵": {"hunger": 10, "thirst": -5, "mental": -10},
    "햄버거": {"hunger": 20, "thirst": 0, "mental": 5},
    "치킨": {"hunger": 30, "thirst": -5, "mental": 10},
    "콜라": {"hunger": 0, "thirst": 30, "mental": 5},
    "맥주": {"hunger": 0, "thirst": 20, "mental": 50}
}

# 2. 신규 아이템 효과 (real_final 업데이트)
# 총, 야구방망이, 쿠팡 쿠폰은 특수 로직으로 처리
ITEM_EFFECTS = {
    "구급상자": {"energy": 1, "hunger": 0, "thirst": 0, "mental": 10},
    "레트로 게임기": {"energy": 0, "hunger": 0, "thirst": 0, "mental": 25},
    "건전지": {"energy": 1, "hunger": 0, "thirst": 0, "mental": 0},
    "생존 가이드북": {"energy": 0, "hunger": 0, "thirst": 0, "mental": 15},
}

# 3. 아이템 분류
EFFECT_ITEMS = ["총", "야구방망이", "구급상자", "생존 가이드북", "건전지", "레트로 게임기", "쿠팡 쿠폰"]
RARE_ITEMS = ["맥북", "롤렉스", "금괴", "한정판 피규어"]
TRASH_ITEMS = ["빈 박스", "고장난 마우스", "찢어진 택배송장"]

# 4. 인트로 보상 (업데이트됨)
INTRO_REWARDS = {
    "S_TIER": (["맥북", "롤렉스", "금괴"], "inventory"),
    "WEAPON": (["총", "야구방망이"], "inventory"), # 변경됨
    "MEDKIT": (["구급상자"], "inventory"),         # 변경됨 (아이템 지급)
    "TECH": (["레트로 게임기", "건전지"], "inventory"),
    "FOOD": (["햄버거", "치킨"], "food"),
    "WATER": (["물", "물", "물"], "food"),
    "TRASH": (["빈 박스", "찢어진 택배송장"], "inventory"),
    "BOOM": (None, "damage") 
}

# 5. 랜덤 이벤트
RANDOM_EVENTS = [
    {"type": "normal", "msg": "[해킹]", "money": -1000, "hunger": 0, "energy": 0, "mental": -15},
    {"type": "normal", "msg": "[습격]", "money": 0, "hunger": -20, "energy": 0, "mental": -20},
    {"type": "normal", "msg": "[수신]", "money": 0, "hunger": 0, "energy": 0, "mental": 20},
    {"type": "normal", "msg": "[재난]", "money": -500, "hunger": -5, "energy": -1, "mental": -10},
    {"type": "normal", "msg": "[발견]", "money": 500, "hunger": 0, "energy": 0, "mental": 10},
    {"type": "normal", "msg": "[고통]", "money": 0, "hunger": 0, "energy": -1, "mental": -10},
    {"type": "normal", "msg": "[부패]", "money": 0, "hunger": 0, "energy": 0, "mental": -10},
    {"type": "normal", "msg": "[공포]", "money": 0, "hunger": 0, "energy": 0, "mental": -25},
    {"type": "item_get", "msg": "[행운]", "money": 0, "hunger": 0, "energy": 0, "mental": 10},
    {"type": "normal", "msg": "[보상]", "money": 300, "hunger": 0, "energy": 0, "mental": 5},
    {"type": "normal", "msg": "[추억]", "money": 0, "hunger": 0, "energy": 0, "mental": 15},
    {"type": "normal", "msg": "[생활]", "money": 0, "hunger": 0, "energy": 0, "mental": 10},
    {"type": "normal", "msg": "[정전]", "money": 0, "hunger": 0, "energy": 0, "mental": -20},
    {"type": "normal", "msg": "[파손]", "money": -300, "hunger": -5, "energy": -1, "mental": -5},
    {"type": "item_lose", "msg": "[손실]", "money": 0, "hunger": 0, "energy": 0, "mental": -10}
]

class SurvivorBot:
    def __init__(self, skill_level=0.8, verbose=False):
        self.day = 1
        self.max_day = 30
        self.money = 1500
        self.hunger = 80
        self.thirst = 80
        self.mental = 100
        self.inventory = []
        self.food_bag = []
        self.alive = True
        self.game_clear = False
        self.cause_of_death = ""
        self.max_energy = 3
        self.energy = 3
        
        # [신규] 상태 변수
        self.weapon_buff = False    # 무기 장착 여부
        self.discount_active = False # 쿠폰 사용 여부
        
        self.skill_level = skill_level
        self.verbose = verbose
        self.logs = []

    def log(self, text):
        if self.verbose:
            print(f"[Day {self.day}] {text}")

    def update_status(self, h, t, m):
        self.hunger = max(0, min(100, self.hunger + h))
        self.thirst = max(0, min(100, self.thirst + t))
        self.mental = max(0, min(100, self.mental + m))
        
        if self.hunger <= 0: self.die("굶어 죽음")
        elif self.thirst <= 0: self.die("탈수")
        elif self.mental <= 0: self.die("자살")

    def die(self, cause):
        self.alive = False
        self.cause_of_death = cause
        self.log(f"💀 사망: {cause}")

    # --- 행동 로직 ---

    def action_start_roulette(self):
        """게임 시작 시 룰렛 (업데이트된 보상)"""
        keys = list(INTRO_REWARDS.keys())
        choice = random.choice(keys)
        reward_items, reward_type = INTRO_REWARDS[choice]
        
        self.log(f"🎲 룰렛 결과: {choice}")
        
        if choice == "BOOM":
            self.update_status(0, 0, -10)
        elif reward_type == "inventory":
            self.inventory.extend(reward_items)
        elif reward_type == "food":
            self.food_bag.extend(reward_items)

    def action_use_utility_item(self):
        """상황에 맞는 아이템 사용 (전략적 AI)"""
        used = False
        
        # 1. 쇼핑 전 쿠폰 사용 (돈이 있고 상태가 나쁠 때)
        if "쿠팡 쿠폰" in self.inventory and not self.discount_active:
            if self.money >= 400 and (self.hunger < 60 or self.mental < 60):
                self.inventory.remove("쿠팡 쿠폰")
                self.discount_active = True
                self.log("🎫 쿠폰 사용: 오늘 50% 할인!")
                used = True
        
        # 2. 외출 전 무기 장착 (행동력이 있을 때 안전 확보)
        if self.energy > 0 and not self.weapon_buff:
            for w in ["총", "야구방망이"]:
                if w in self.inventory:
                    self.inventory.remove(w)
                    self.weapon_buff = True
                    self.log(f"🔫 {w} 장착: 파밍 100% 성공 보장")
                    used = True
                    break
                    
        # 3. 소모품 사용 (상태가 낮을 때)
        # 리스트 복사본으로 순회하며 삭제
        for item in list(self.inventory): 
            if item not in ITEM_EFFECTS: continue
            
            eff = ITEM_EFFECTS[item]
            should_use = False
            
            # 사용 조건 판단
            if item == "구급상자" and (self.mental < 40 or self.hunger < 50): should_use = True
            elif item == "레트로 게임기" and self.mental < 50: should_use = True
            elif item == "생존 가이드북" and self.mental < 60: should_use = True
            elif item == "건전지" and self.energy < 2: should_use = True # 행동력 회복
            
            if should_use:
                self.inventory.remove(item)
                self.update_status(eff.get('hunger',0), eff.get('thirst',0), eff.get('mental',0))
                if eff.get('energy', 0) > 0:
                    self.energy = min(3, self.energy + eff['energy'])
                self.log(f"💊 {item} 사용: 상태 회복")
                used = True
                
        return used

    def action_eat(self):
        if not self.food_bag: return False
        
        best_food = None
        max_utility = -999
        
        for food in self.food_bag:
            eff = FOOD_EFFECTS.get(food, {})
            h_gain = min(100 - self.hunger, eff.get('hunger', 0))
            t_gain = min(100 - self.thirst, eff.get('thirst', 0))
            m_gain = min(100 - self.mental, eff.get('mental', 0))
            utility = h_gain + t_gain * 1.5 + m_gain
            
            if utility > max_utility:
                max_utility = utility
                best_food = food
        
        if best_food:
            self.food_bag.remove(best_food)
            eff = FOOD_EFFECTS[best_food]
            self.update_status(eff['hunger'], eff['thirst'], eff['mental'])
            self.log(f"🍔 섭취: {best_food} (H:{self.hunger} T:{self.thirst} M:{self.mental})")
            return True
        return False

    def action_shop(self):
        # [할인 적용]
        price_food = 400 if self.discount_active else 800
        price_mental = 500 if self.discount_active else 1000
        
        # 멘탈 케어 (게임기 구매)
        if self.mental < 40 and self.money >= price_mental:
            self.money -= price_mental
            self.update_status(0, 0, 40)
            self.inventory.append("레트로 게임기")
            self.log(f"🛒 쇼핑: 멘탈 케어 (-{price_mental}원)")
            return True
            
        # 식량 구매
        if (len(self.food_bag) < 2 or self.hunger < 50) and self.money >= price_food:
            self.money -= price_food
            item = random.choice(list(FOOD_EFFECTS.keys()))
            self.food_bag.append(item)
            self.log(f"🛒 쇼핑: 식량 박스 [{item}] (-{price_food}원)")
            return True
            
        return False

    def action_outside(self):
        if self.energy <= 0: return False
        
        self.energy -= 1
        self.log("🏃 외출 시도...")
        
        # 1. 이벤트 (50%)
        if random.random() < 0.5:
            evt = random.choice(RANDOM_EVENTS)
            self.money = max(0, self.money + evt['money'])
            self.update_status(evt.get('hunger', 0), 0, evt.get('mental', 0))
            self.log(f"⚡ 이벤트: {evt['msg']}")
            
            if evt['type'] == 'item_get':
                item = random.choice(RARE_ITEMS + TRASH_ITEMS)
                self.inventory.append(item)
            elif evt['type'] == 'item_lose' and self.inventory:
                self.inventory.pop(random.randint(0, len(self.inventory)-1))
        
        # 2. 파밍 (무기 버프 체크)
        else:
            if self.weapon_buff:
                success = True
                self.weapon_buff = False # 버프 소모
                self.log("🔫 무기 사용! 위협 제압 및 자동 파밍 성공")
            else:
                success = random.random() < self.skill_level
                if not success:
                    dmg = random.randint(10, 30)
                    self.update_status(-10, -10, -dmg)
                    self.log(f"💢 파밍 실패! 부상 (M-{dmg})")

            # 전리품 획득 (변경된 확률 적용)
            if success:
                rand = random.random()
                if rand < 0.2: # 20% 기능성 아이템
                    item = random.choice(EFFECT_ITEMS)
                elif rand < 0.5: # 30% 고가 아이템
                    item = random.choice(RARE_ITEMS)
                else: # 50% 잡동사니
                    item = random.choice(TRASH_ITEMS)
                
                self.inventory.append(item)
                self.log(f"🎁 파밍 성공: [{item}] 획득")

        return True

    def action_sell(self):
        if not self.inventory: return False
        
        sold_val = 0
        kept_items = []
        
        for item in self.inventory:
            # 기능성 아이템은 웬만하면 보존 (단, 너무 많으면 판매)
            if item in EFFECT_ITEMS:
                # 무기나 구급상자는 1개만 유지하고 팔기 (간단한 로직)
                if item in kept_items:
                    sold_val += 100
                else:
                    kept_items.append(item)
            else:
                # 판매 (레어 1500원, 일반 100원)
                val = 1500 if item in RARE_ITEMS else 100
                sold_val += val
                
        self.inventory = kept_items
        self.money += sold_val
        if sold_val > 0:
            self.log(f"💰 아이템 판매 (+{sold_val}원)")
        return sold_val > 0

    def run_day_cycle(self):
        """하루 일과"""
        if self.day == 1: self.action_start_roulette()

        while self.energy > 0 and self.alive:
            acted = False
            
            # 1. 생존 (먹기)
            if self.hunger < 40 or self.thirst < 40:
                if self.action_eat(): acted = True
            
            # 2. 아이템 사용 (회복/준비)
            if not acted:
                if self.action_use_utility_item(): acted = True
                
            # 3. 판매 (돈 부족/인벤 가득)
            if not acted and (self.money < 800 or len(self.inventory) >= 5):
                if self.action_sell(): acted = True
                
            # 4. 쇼핑 (돈 충분 시)
            if not acted:
                if self.action_shop(): acted = True
                
            # 5. 외출 (상태 양호 시)
            if not acted and self.hunger > 30 and self.thirst > 30 and self.mental > 30:
                if self.action_outside(): acted = True
                
            if not acted: break # 할 일 없으면 휴식

        # 밤: 수면 및 초기화
        if self.alive:
            self.update_status(-15, -20, 5)
            self.energy = 3
            self.discount_active = False # 쿠폰 효과 종료
            
            if self.day >= self.max_day and self.alive:
                self.game_clear = True
            else:
                self.day += 1

# --- 시뮬레이션 실행 ---
def run_simulation(count=1000, skill=0.8):
    stats = {"success": 0, "fail": 0, "days": 0}
    
    print(f"🔄 시뮬레이션 {count}회 실행 (Skill: {skill*100}%)...")
    for _ in range(count):
        bot = SurvivorBot(skill_level=skill)
        while bot.alive and not bot.game_clear:
            bot.run_day_cycle()
            
        stats["days"] += bot.day
        if bot.game_clear: stats["success"] += 1
        else: stats["fail"] += 1
        
    avg_days = stats["days"] / count
    win_rate = (stats["success"] / count) * 100
    print(f"결과: 승률 {win_rate:.1f}% | 평균 생존 {avg_days:.1f}일")

if __name__ == "__main__":
    # 1회 상세 테스트
    print("=== 👀 1회 상세 플레이 ===")
    test_bot = SurvivorBot(verbose=True)
    while test_bot.alive and not test_bot.game_clear:
        test_bot.run_day_cycle()
    
    print("\n=== 📊 대규모 통계 ===")
    run_simulation(1000, 0.5) # 초보
    run_simulation(1000, 0.9) # 고수