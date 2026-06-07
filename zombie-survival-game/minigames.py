import random
import time
import math
import pygame
from config import *

class IntroRoulette:
    def __init__(self):
        self.items = [
            "S_TIER", "WEAPON", "MEDKIT", "TECH", 
            "FOOD", "WATER", "TRASH", "BOOM"
        ]
        self.item_names = [
            "특급 보급", "무기 세트", "구급상자", "게임 세트", 
            "식량 박스", "생수 번들", "잡동사니", "꽝!"
        ]
        self.colors = [
            (255, 215, 0),  # Gold
            (200, 50, 50),  # Red
            (50, 200, 50),  # Green
            (50, 100, 200), # Blue
            (200, 150, 50), # Orange
            (100, 200, 255),# Cyan
            (150, 150, 150),# Gray
            (50, 50, 50)    # Black
        ]
        
        self.angle = 0          
        self.velocity = 0       
        self.state = "STOPPED"  
        self.final_item = None
        self.result_idx = 0

    def start(self):
        self.state = "SPINNING"
        self.velocity = random.uniform(25, 40)
        self.angle = 0

    def update(self):
        if self.state == "SPINNING":
            self.angle += self.velocity
            self.velocity *= 0.98 
            
            if self.velocity < 0.1:
                self.state = "FINISHED"
                self.velocity = 0
                normalized_angle = self.angle % 360
                hit_angle = (270 - normalized_angle) % 360
                self.result_idx = int(hit_angle // (360 / len(self.items)))
                self.final_item = self.items[self.result_idx]

    def get_draw_info(self):
        return self.items, self.item_names, self.colors, self.angle

class OutdoorMinigame:
    def __init__(self):
        self.type = None
        self.state = "IDLE" 
        self.timer = 0
        self.info_text = ""
        self.sub_text = ""
        self.time_limit = 5.0
        
        self.lock_angle = 0; self.lock_solution = 0
        self.breath_val = 0; self.breath_vel = 0
        self.search_cursor = [0,0]; self.search_target = [0,0]
        self.mash_count = 0; self.mash_target = 30
        self.freq_target = 0; self.freq_current = 0
        self.struggle_seq = []; self.struggle_idx = 0

    def start_game(self):
        self.type = random.choice(["lockpick", "search", "breath", "mash", "frequency", "struggle"])
        self.state = "INSTRUCTION"
        
        if self.type == "lockpick":
            self.info_text = "잠긴 문 열기"
            self.sub_text = "[SPACE] 바늘이 붉은 구간일 때 누르세요."
            self.lock_angle = 0
            self.lock_solution = random.randint(0, 359)
            
        elif self.type == "search":
            self.info_text = "물건 찾기"
            self.sub_text = "[방향키]로 어둠 속 물건을 찾으세요."
            self.search_cursor = [400, 300]
            self.search_target = [random.randint(100, 700), random.randint(100, 500)]
            
        elif self.type == "breath":
            self.info_text = "숨 참기"
            self.sub_text = "[좌/우 키]로 좀비가 지나갈 때까지 균형을 잡으세요."
            self.breath_val = 0
            self.breath_vel = 0
            
        elif self.type == "mash":
            self.info_text = "장애물 치우기"
            self.sub_text = "[SPACE]를 미친듯이 연타하세요!"
            self.mash_count = 0
            self.mash_target = 40
            
        elif self.type == "frequency":
            self.info_text = "무전기 주파수"
            # [수정] 안내 문구 변경 (좌/우 -> 상/하)
            self.sub_text = "[상/하 키]로 신호를 초록선에 맞추세요."
            self.freq_target = random.randint(100, 500)
            self.freq_current = random.randint(100, 500)
            
        elif self.type == "struggle":
            self.info_text = "좀비 저항!"
            self.sub_text = "화면에 표시되는 방향을 순서대로 입력하세요!"
            self.struggle_seq = [random.choice(['UP', 'DOWN', 'LEFT', 'RIGHT']) for _ in range(6)]
            self.struggle_idx = 0

    def proceed(self):
        self.state = "PLAYING"
        self.timer = time.time()
        
        if self.type == "lockpick": self.time_limit = 5.0
        elif self.type == "search": self.time_limit = 7.0
        elif self.type == "breath": self.time_limit = 5.0
        elif self.type == "mash": self.time_limit = 5.0
        elif self.type == "frequency": self.time_limit = 6.0
        elif self.type == "struggle": self.time_limit = 5.0 # 시간 조금 늘림

    def update(self):
        if self.state != "PLAYING": return
        
        elapsed = time.time() - self.timer
        remain = self.time_limit - elapsed
        
        if remain <= 0:
            if self.type == "breath": self.state = "SUCCESS"
            elif self.type == "frequency":
                if abs(self.freq_current - self.freq_target) < 15: self.state = "SUCCESS"
                else: self.state = "FAILED"
            else: self.state = "FAILED"
            return

        if self.type == "lockpick":
            self.lock_angle = (self.lock_angle + 6) % 360
            
        elif self.type == "search":
            dist = math.hypot(self.search_cursor[0]-self.search_target[0], self.search_cursor[1]-self.search_target[1])
            if dist < 30: self.state = "SUCCESS"
                
        elif self.type == "breath":
            self.breath_vel += random.uniform(-1.5, 1.5)
            self.breath_val += self.breath_vel
            self.breath_vel *= 0.98 
            if abs(self.breath_val) > 150: self.state = "FAILED"
            
        elif self.type == "mash":
            if self.mash_count >= self.mash_target: self.state = "SUCCESS"
            self.mash_count = max(0, self.mash_count - 0.2)

    def handle_input(self, event):
        if self.state == "INSTRUCTION":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.proceed()
            return

        if self.state != "PLAYING": return
        
        if event.type == pygame.KEYDOWN:
            key = event.key
            
            if self.type == "lockpick" and key == pygame.K_SPACE:
                diff = abs(self.lock_angle - self.lock_solution)
                if diff > 180: diff = 360 - diff
                if diff < 25: self.state = "SUCCESS"
                else: self.state = "FAILED"
                
            elif self.type == "search":
                step = 40
                if key == pygame.K_LEFT: self.search_cursor[0] -= step
                elif key == pygame.K_RIGHT: self.search_cursor[0] += step
                elif key == pygame.K_UP: self.search_cursor[1] -= step
                elif key == pygame.K_DOWN: self.search_cursor[1] += step
                
            elif self.type == "breath":
                if key == pygame.K_LEFT: self.breath_vel -= 4
                elif key == pygame.K_RIGHT: self.breath_vel += 4
                
            elif self.type == "mash" and key == pygame.K_SPACE:
                self.mash_count += 3
                
            elif self.type == "struggle":
                target_key = self.struggle_seq[self.struggle_idx]
                correct = False
                if target_key == 'UP' and key == pygame.K_UP: correct = True
                elif target_key == 'DOWN' and key == pygame.K_DOWN: correct = True
                elif target_key == 'LEFT' and key == pygame.K_LEFT: correct = True
                elif target_key == 'RIGHT' and key == pygame.K_RIGHT: correct = True
                
                if correct:
                    self.struggle_idx += 1
                    if self.struggle_idx >= len(self.struggle_seq):
                        self.state = "SUCCESS"
                else:
                    self.state = "FAILED"

        if self.type == "frequency":
            keys = pygame.key.get_pressed()
            # [수정] 상/하 키로 변경
            if keys[pygame.K_UP]: self.freq_current -= 6
            if keys[pygame.K_DOWN]: self.freq_current += 6
            self.freq_current = max(0, min(600, self.freq_current))