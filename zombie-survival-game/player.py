from config import *
import random

class Player:
    def __init__(self):
        self.max_day = 30
        self.day = 1
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
        self.logs = ["Day 1: 자취방에서의 생존이 시작되었습니다."]
        
        self.weapon_buff = False
        self.discount_active = False

    def add_log(self, text):
        self.logs.insert(0, text)
        if len(self.logs) > 20: self.logs.pop()

    def change_money(self, amount):
        prev_money = self.money
        self.money += amount
        if self.money < 0:
            self.money = 0
        return self.money != prev_money

    # [수정] 날짜 변경 로직 순서 변경 (상태 반영 -> 생존 체크 -> 날짜 증가)
    def sleep_and_reset(self):
        # 1. 밤사이 배고픔/목마름/멘탈 변화 적용
        self.update_status(-15, -20, 5)
        
        # 2. 상태 변화로 인해 사망했는지 체크
        if not self.alive:
            # 사망했다면 날짜를 증가시키지 않고 False 반환
            return False

        # 3. 생존 확인 후 날짜 증가
        self.day += 1
        if self.day > self.max_day: self.game_clear = True
        
        self.energy = self.max_energy
        self.discount_active = False
        self.logs = [f"Day {self.day}: 새로운 아침이 밝았습니다."]
        
        return True # 생존함

    def update_status(self, hunger=0, thirst=0, mental=0):
        self.hunger = max(0, min(100, self.hunger + hunger))
        self.thirst = max(0, min(100, self.thirst + thirst))
        self.mental = max(0, min(100, self.mental + mental))
        
        if self.mental <= 0:
            self.alive = False
            self.cause_of_death = "절망감에 사로잡혀 삶을 포기했습니다..."
        if self.hunger <= 0:
            self.alive = False
            self.cause_of_death = "굶어 죽었습니다..."
        elif self.thirst <= 0:
            self.alive = False
            self.cause_of_death = "탈수로 쓰러졌습니다..."

    def apply_roulette_reward(self, reward_type):
        if reward_type == "S_TIER":
            items = ["맥북", "롤렉스", "금괴"]
            self.inventory.extend(items)
            self.add_log(f"대박! 특급 보급품을 획득했습니다!")
        elif reward_type == "WEAPON":
            items = ["총", "야구방망이"] 
            self.inventory.extend(items)
            self.add_log(f"호신용 장비 세트를 획득했습니다.")
        elif reward_type == "MEDKIT":
            self.inventory.append("구급상자")
            self.add_log(f"의약품 발견! 구급상자를 획득했습니다.")
        elif reward_type == "TECH":
            items = ["레트로 게임기", "에너지 드링크"] 
            self.inventory.extend(items)
            self.add_log(f"게임 세트를 획득했습니다.")
        elif reward_type == "FOOD":
            items = ["햄버거", "치킨"]
            self.food_bag.extend(items)
            self.add_log(f"식량 박스를 획득했습니다.")
        elif reward_type == "WATER":
            items = ["물", "물", "물"]
            self.food_bag.extend(items)
            self.add_log(f"생수 번들을 획득했습니다.")
        elif reward_type == "TRASH":
            items = ["빈 박스", "찢어진 택배송장"]
            self.inventory.extend(items)
            self.add_log(f"잡동사니를 획득했습니다...")
        elif reward_type == "BOOM":
            self.update_status(0, 0, -10)
            self.add_log(f"꽝! 아무것도 얻지 못해 실망했습니다.")

    def try_consume_energy(self):
        if self.energy <= 0:
            self.add_log("너무 지쳐서 움직일 수 없습니다.")
            return False, None
        
        self.energy -= 1
        if random.random() < 0.5:
            evt = random.choice(RANDOM_EVENTS)
            return True, evt
        return True, None

    def use_item(self, item_name):
        if item_name in self.inventory:
            if item_name in ["총", "야구방망이"]:
                self.inventory.remove(item_name)
                self.weapon_buff = True
                self.add_log(f"[{item_name}] 장착! 다음 외출 시 위협을 제거합니다.")
                return True
            
            elif item_name == "쿠팡 쿠폰":
                self.inventory.remove(item_name)
                self.discount_active = True
                self.add_log("쿠폰 사용! 오늘 상점 물품이 50% 할인됩니다.")
                return True
            
            eff = ITEM_EFFECTS.get(item_name)
            if eff:
                self.inventory.remove(item_name)
                self.update_status(eff.get('hunger',0), eff.get('thirst',0), eff.get('mental',0))
                if eff.get('energy', 0) > 0:
                    self.energy = min(self.max_energy, self.energy + eff['energy'])
                
                self.add_log(f"[{item_name}] 사용 효과 적용됨.")
                return True
                
        return False