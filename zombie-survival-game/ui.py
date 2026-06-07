import pygame
import random
import math
import time
from config import *

pygame.font.init()
font_s = get_font(24)
font_m = get_font(28)
font_l = get_font(32)
font_xl = get_font(48)
font_day = get_font(50, True)

# [추가] 플로팅 텍스트 (데미지, 획득 로그 연출용)
class FloatingText:
    def __init__(self, x, y, text, color, size=24, speed=1.5):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.font = get_font(size, bold=True)
        self.alpha = 255
        self.life = 60  # 프레임 수
        self.speed = speed
        self.y_offset = 0

    def update(self):
        self.y_offset += self.speed
        self.life -= 1
        if self.life < 20:
            self.alpha = int(255 * (self.life / 20))

    def draw(self, surface):
        if self.life > 0:
            # 텍스트 그림자
            txt_surf = self.font.render(self.text, True, self.color)
            txt_surf.set_alpha(self.alpha)
            
            shad_surf = self.font.render(self.text, True, BLACK)
            shad_surf.set_alpha(self.alpha)
            
            draw_pos = (self.x - txt_surf.get_width()//2, self.y - self.y_offset)
            surface.blit(shad_surf, (draw_pos[0]+2, draw_pos[1]+2))
            surface.blit(txt_surf, draw_pos)

# [추가] 통합 이펙트 매니저 (파티클, 플로팅 텍스트, 화면 효과 관리)
class EffectManager:
    def __init__(self):
        self.particles = ParticleSystem()
        self.floating_texts = []
        self.flash_alpha = 0
        self.flash_color = (255, 255, 255)
        self.vignette_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.create_vignette()
        
        # [추가] 노이즈 텍스처 미리 생성 (멘탈 붕괴 효과용)
        self.noise_surf = self.create_noise_surface()

    def create_vignette(self):
        # 방사형 그라데이션 (가운데 투명, 가장자리 검정)
        pygame.draw.rect(self.vignette_surf, (0,0,0,0), (0,0,SCREEN_WIDTH, SCREEN_HEIGHT))
        for i in range(100, 0, -10):
            alpha = 2
            pygame.draw.rect(self.vignette_surf, (0,0,0, alpha), (i, i, SCREEN_WIDTH-2*i, SCREEN_HEIGHT-2*i), 100)

    # [추가] 노이즈 텍스처 생성 함수
    def create_noise_surface(self):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        # 화면에 흰색/회색 점들을 무작위로 찍음
        for _ in range(3000): 
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            # 약간 투명한 흰색 점
            color = (200, 200, 200, random.randint(50, 100))
            pygame.draw.rect(surf, color, (x, y, 2, 2))
        return surf

    def clear_texts(self):
        self.floating_texts = []

    def add_text(self, x, y, text, color=WHITE, size=24):
        self.floating_texts.append(FloatingText(x, y, text, color, size))

    def trigger_flash(self, color=(255, 255, 255), intensity=150):
        self.flash_color = color
        self.flash_alpha = intensity

    def update(self):
        # 파티클 업데이트는 main.py 등에서 particles 참조로 처리됨 (호환성 유지)
        self.particles.particles = [p for p in self.particles.particles if p['life'] > 0]
        
        for ft in self.floating_texts[:]:
            ft.update()
            if ft.life <= 0:
                self.floating_texts.remove(ft)
        
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - 10)

    def draw(self, surface):
        # 1. 플로팅 텍스트
        for ft in self.floating_texts:
            ft.draw(surface)
            
        # 2. 화면 플래시
        if self.flash_alpha > 0:
            flash_s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_s.fill(self.flash_color)
            flash_s.set_alpha(self.flash_alpha)
            surface.blit(flash_s, (0, 0))

    # [수정] 체력/멘탈 상태에 따른 특수 효과 그리기
    def draw_vignette_overlay(self, surface, player):
        current_time = pygame.time.get_ticks()
        
        # 1. [Low HP] 붉은 화면 깜빡임 (심장 박동)
        # player.hp가 있으면 사용, 없으면 hunger/thirst로 대체 판정
        hp_val = getattr(player, 'hp', None)
        if hp_val is None: hp_val = min(player.hunger, player.thirst)
        
        if hp_val < 30:
            # 위험할수록 더 빨리 깜빡임
            pulse_speed = 0.005 if hp_val > 15 else 0.01 
            pulse = (math.sin(current_time * pulse_speed) + 1) * 0.5 # 0.0 ~ 1.0
            
            # 위험도 (0.0 ~ 1.0)
            danger_intensity = 1.0 - (max(0, hp_val) / 30)
            
            # 투명도 계산: 위험도 + 깜빡임 효과
            base_alpha = 50 * danger_intensity
            flash_alpha = 100 * danger_intensity * pulse
            final_alpha = int(min(255, base_alpha + flash_alpha))
            
            if final_alpha > 0:
                # 붉은색 테두리
                vig = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.rect(vig, (255, 0, 0, final_alpha), (0,0,SCREEN_WIDTH, SCREEN_HEIGHT), 60) # 두께 60
                
                # 전체적으로 붉은 기운 살짝 추가
                fill_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                fill_surf.fill((255, 0, 0))
                fill_surf.set_alpha(int(final_alpha * 0.3)) # 약하게
                
                surface.blit(vig, (0,0))
                surface.blit(fill_surf, (0,0), special_flags=pygame.BLEND_ADD)

        # 2. [Low Mental] 지직거리는 노이즈 (TV Static)
        if player.mental < 30:
            mental_intensity = 1.0 - (max(0, player.mental) / 30)
            
            # (1) 보라색 테두리 (기존 유지)
            vig_m = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            alpha_m = int(120 * mental_intensity)
            pygame.draw.rect(vig_m, (100, 0, 200, alpha_m), (0,0,SCREEN_WIDTH, SCREEN_HEIGHT), 80)
            surface.blit(vig_m, (0,0))
            
            # (2) 노이즈 효과 (Random Jitter)
            # 노이즈 텍스처를 매 프레임 랜덤한 위치에 그려 '지직'거리는 느낌을 줌
            ox = random.randint(-20, 20)
            oy = random.randint(-20, 20)
            
            noise_copy = self.noise_surf.copy()
            noise_copy.set_alpha(int(180 * mental_intensity)) # 멘탈이 낮을수록 노이즈 진해짐
            
            # 화면보다 조금 큰 영역이 필요하지만 간단히 클리핑 처리됨
            surface.blit(noise_copy, (ox, oy))
            
            # (3) 가끔 화면이 찢어지는 글리치 효과 (매우 낮은 확률)
            if mental_intensity > 0.7 and random.random() < 0.1:
                glitch_h = random.randint(5, 30)
                glitch_y = random.randint(0, SCREEN_HEIGHT - glitch_h)
                offset_x = random.randint(-10, 10)
                
                # 화면의 일부를 잘라서 옆으로 밀어버림
                sub = surface.subsurface(0, glitch_y, SCREEN_WIDTH, glitch_h).copy()
                surface.blit(sub, (offset_x, glitch_y))

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def create(self, pos, color, count=12, speed_mult=1.0):
        for _ in range(count):
            angle = random.uniform(0, 6.28)
            speed = random.uniform(2, 6) * speed_mult
            self.particles.append({
                'x': pos[0], 'y': pos[1],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.randint(30, 60),
                'max_life': 60,
                'color': color,
                'size': random.randint(3, 8)
            })

    def update_and_draw(self, surface):
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vx'] *= 0.95 
            p['vy'] *= 0.95
            p['life'] -= 1
            curr_size = max(0, p['size'] * (p['life'] / p['max_life']))
            if p['life'] <= 0:
                self.particles.remove(p)
            else:
                s = pygame.Surface((int(curr_size*2), int(curr_size*2)), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p['color'], 128), (int(curr_size), int(curr_size)), int(curr_size))
                surface.blit(s, (int(p['x']-curr_size), int(p['y']-curr_size)))

class Button:
    def __init__(self, x, y, w, h, text, color, action_id, text_color=WHITE, style="flat", icon_type=None):
        # ... (기존 초기화 코드 동일) ...
        self.rect = pygame.Rect(x, y, w, h)
        self.x, self.y, self.width, self.height = x, y, w, h
        self.text = text
        self.bg_color = color
        self.action_id = action_id
        self.text_color = text_color
        self.style = style
        self.icon_type = icon_type
        self.is_hovered = False
        
        # [추가] 호버 애니메이션용 변수
        self.hover_anim = 0 

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        # [추가] 호버 애니메이션 계산
        target_anim = 1.0 if self.is_hovered else 0.0
        self.hover_anim += (target_anim - self.hover_anim) * 0.2
        
        # 색상 밝기 계산 (호버 시 부드럽게 밝아짐)
        r, g, b = self.bg_color
        bright_amt = int(30 * self.hover_anim)
        cur_bg = (min(255, r+bright_amt), min(255, g+bright_amt), min(255, b+bright_amt))
        
        # ... (이하 기존 draw 로직에서 self.bg_color 대신 cur_bg 사용) ...
        # (기존 코드가 너무 길어 스타일별 핵심 변경점만 예시로 듭니다)
        
        if self.style == "apocalypse":
            # ... cur_bg 사용 ...
            pass # 기존 로직 유지하되 색상만 cur_bg로
            
            # [기존 코드의 이 부분 대체]
            base_col = cur_bg # self.bg_color 대신 사용
            border_col = APOC_RUST
            if self.is_hovered: border_col = APOC_RUST_BRIGHT
            
            pygame.draw.rect(surface, APOC_METAL_DARK, self.rect, border_radius=4)
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((*base_col, 100))
            surface.blit(overlay, self.rect.topleft)
            # ... 나머지 드로잉 코드 ...
            pygame.draw.rect(surface, border_col, self.rect, 3, border_radius=4)
            # ... (나사 그리기 등 기존 코드 유지) ...
            
            # 텍스트 그리기 (기존 코드 유지)
            if self.text:
                shad_surf = font_l.render(self.text, True, BLACK)
                # 호버 시 텍스트 살짝 위로
                y_offset = -2 if self.is_hovered else 0
                shad_rect = shad_surf.get_rect(center=(self.rect.centerx + 2, self.rect.centery + 2 + y_offset))
                surface.blit(shad_surf, shad_rect)
                
                txt_surf = font_l.render(self.text, True, self.text_color)
                txt_rect = txt_surf.get_rect(center=(self.rect.centerx, self.rect.centery + y_offset))
                surface.blit(txt_surf, txt_rect)

        elif self.style == "flat":
             # Flat 스타일도 cur_bg 사용
            pygame.draw.rect(surface, cur_bg, self.rect, border_radius=8)
            # ... 텍스트 그리기 (위와 동일하게 y_offset 적용하면 좋음) ...
            if self.text:
                txt_surf = font_l.render(self.text, True, self.text_color)
                txt_rect = txt_surf.get_rect(center=self.rect.center)
                surface.blit(txt_surf, txt_rect)

        # ... (나머지 스타일도 cur_bg 적용) ...
        elif self.style == "invisible":
             if self.is_hovered:
                 # ... 기존 로직 ...
                 hover_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                 hover_overlay.fill((*APOC_RUST, 60)) 
                 surface.blit(hover_overlay, self.rect.topleft)
                 pygame.draw.rect(surface, APOC_RUST_BRIGHT, self.rect, 3, border_radius=4)
             if self.text and self.is_hovered:
                 # ... 기존 로직 ...
                 shad_surf = font_l.render(self.text, True, BLACK)
                 shad_rect = shad_surf.get_rect(center=(self.rect.centerx + 2, self.rect.centery + 2))
                 surface.blit(shad_surf, shad_rect)
                 txt_surf = font_l.render(self.text, True, WHITE)
                 txt_rect = txt_surf.get_rect(center=self.rect.center)
                 surface.blit(txt_surf, txt_rect)
        
        else: # Default
            # Default도 cur_bg 적용
            pygame.draw.rect(surface, cur_bg, self.rect, border_radius=5)
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)
            if self.text:
                txt_surf = font_l.render(self.text, True, self.text_color)
                txt_rect = txt_surf.get_rect(center=self.rect.center)
                surface.blit(txt_surf, txt_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

def truncate_text(text, font, max_width):
    if font.size(text)[0] <= max_width:
        return text
    
    for i in range(len(text), 0, -1):
        truncated = text[:i] + "..."
        if font.size(truncated)[0] <= max_width:
            return truncated
    return "..."

def draw_game_scene(game, surface):
    btns = []
    
    if game.state == "SHOP": surface.fill(CP_BG_GRAY)
    elif game.state == "TITLE": surface.fill(BLACK)
    elif game.state == "INTRO_GAME": surface.fill((20, 20, 25))
    elif game.state == "DAY_TRANSITION": surface.fill(BLACK) 
    elif game.state == "OUTSIDE": pass 
    else: surface.fill(BLACK)

    if game.state == "TITLE": btns = draw_title(surface)
    elif game.state == "GUIDE": btns = draw_guide(surface)
    elif game.state == "INTRO_GAME": btns = draw_intro_game(surface, game)
    elif game.state == "HOME": btns = draw_home(surface, game)
    elif game.state == "SHOP": btns = draw_shop(surface, game)
    elif game.state == "INVENTORY": btns = draw_inventory(surface, game)
    elif game.state == "OUTSIDE": btns = draw_outside_scene(surface, game)
    elif game.state == "RESULT": btns = draw_result(surface, game)
    elif game.state == "EVENT_POPUP": btns = draw_event(surface, game)
    elif game.state == "ITEM_GET": btns = draw_item_get(surface, game)
    elif game.state == "MSG_POPUP": btns = draw_msg_popup(surface, game)
    elif game.state == "DAY_TRANSITION": draw_day_transition(surface, game)

    for btn in btns:
        btn.draw(surface)

    return btns

def draw_guide(surface):
    surface.fill(BUNKER_BG)
    doc_rect = pygame.Rect(150, 50, 700, 600)
    pygame.draw.rect(surface, (220, 215, 200), doc_rect) 
    
    surface.blit(font_xl.render("SURVIVAL GUIDE", True, BLACK), (300, 80))
    surface.blit(font_s.render("CONFIDENTIAL", True, CP_RED), (650, 90))
    
    lines = [
        "1. 본인 집에서 30일간 생존하세요.",
        "2. '쿠팡' 시스템으로 식량을 조달하십시오.",
        "3. 돈이 떨어지면 외부 파밍이 필요합니다.",
        "4. 외부에는 감염자들이 가득합니다. (잠입 필수)",
        "5. 멘탈 관리에 실패하면 자살 충동을 느낍니다.",
        "",
        "- 초기 보급품은 룰렛으로 결정됩니다 -"
    ]
    
    start_y = 180
    for i, l in enumerate(lines):
        col = CP_RED if "쿠팡" in l else BLACK
        surface.blit(font_m.render(l, True, col), (200, start_y + i*40))
        
    s = pygame.Surface((200, 100), pygame.SRCALPHA)
    pygame.draw.rect(s, (200, 0, 0, 100), (0,0,200,100), 5)
    text = font_xl.render("APPROVED", True, (200,0,0))
    s.blit(text, (10, 25))
    surface.blit(pygame.transform.rotate(s, -15), (600, 500))

    return [Button(400, 580, 200, 60, "START GAME", CP_BLUE, "start_intro")]

def draw_intro_game(surface, game):
    cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50
    radius = 200
    
    draw_intro_roulette(surface, cx, cy, radius, game.intro_game)
    
    text_y = cy + 280
    
    if game.intro_game.state == "SPINNING":
        msg = "생존물품 탐색 중..."
        col = TXT_WARN 
        if (pygame.time.get_ticks() // 200) % 2 == 0:
            col = (255, 150, 150)
    else:
        idx = game.intro_game.result_idx
        name = game.intro_game.item_names[idx]
        msg = f"[{name}] 획득!"
        col = TXT_GOLD
        
        info_text = "PRESS [SPACE] TO START"
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            info_surf = font_l.render(info_text, True, CP_GREEN)
            info_rect = info_surf.get_rect(center=(cx, text_y + 70))
            
            info_shad = font_l.render(info_text, True, BLACK)
            surface.blit(info_shad, (info_rect.x + 2, info_rect.y + 2))
            surface.blit(info_surf, info_rect)

    t_surf = font_xl.render(msg, True, col)
    t_rect = t_surf.get_rect(center=(cx, text_y))
    
    bg_padding_x = 40
    bg_padding_y = 20
    bg_rect = pygame.Rect(0, 0, t_rect.width + bg_padding_x, t_rect.height + bg_padding_y)
    bg_rect.center = t_rect.center
    
    s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
    s.fill((0, 0, 0, 200))
    pygame.draw.rect(s, (100, 100, 100), s.get_rect(), 2, border_radius=10)
    surface.blit(s, bg_rect.topleft)
    
    surface.blit(t_surf, t_rect)
    
    return []

def draw_day_transition(surface, game):
    day_text = f"DAY {game.player.day}"
    alpha = 255
    
    if game.transition_timer < 20:
        alpha = int(255 * (game.transition_timer / 20))
    elif game.transition_timer > 80:
        alpha = int(255 * ((100 - game.transition_timer) / 20))
    else:
        alpha = 255
        
    text_surf = font_day.render(day_text, True, WHITE)
    text_surf.set_alpha(alpha)
    
    rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    surface.blit(text_surf, rect)
    
    if game.player.day == 1:
        sub = font_m.render("생존이 시작됩니다.", True, TXT_SECONDARY)
    else:
        sub = font_m.render("살아남았습니다.", True, TXT_SECONDARY)
        
    sub.set_alpha(alpha)
    sub_rect = sub.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
    surface.blit(sub, sub_rect)

def draw_home(surface, game):
    draw_room_background(surface)
    player = game.player
    
    # 1. Day 표시
    day_str = f"DAY {player.day}"
    surface.blit(font_day.render(day_str, True, BLACK), (32, 22)) 
    surface.blit(font_day.render(day_str, True, TXT_WARN), (30, 20))
    
    # 2. 상태바
    bar_start_y = 100
    bar_gap = 55
    draw_stat_bar_with_text(surface, "배고픔", player.hunger, 100, 30, bar_start_y, BAR_HP)
    draw_stat_bar_with_text(surface, "목마름", player.thirst, 100, 30, bar_start_y + bar_gap, BAR_WATER)
    draw_stat_bar_with_text(surface, "정신력", player.mental, 100, 30, bar_start_y + bar_gap * 2, BAR_MENTAL)
    
    # 3. 에너지바
    en_x = SCREEN_WIDTH - 230
    surface.blit(font_l.render("ENERGY", True, TXT_SECONDARY), (en_x, 20))
    circle_y = 75 
    for i in range(player.max_energy):
        col = BAR_ENERGY if i < player.energy else (60, 60, 60)
        pygame.draw.circle(surface, (20,20,20), (en_x + 10 + i * 30, circle_y), 12)
        pygame.draw.circle(surface, col, (en_x + 10 + i * 30, circle_y), 10)

    # 4. 생존 일지
    log_h = 180
    panel_w = 380
    log_x = 30
    log_y = SCREEN_HEIGHT - log_h - 30
    
    # 배경 패널
    log_panel = pygame.Surface((panel_w, log_h), pygame.SRCALPHA)
    pygame.draw.rect(log_panel, (0, 0, 0, 160), (0, 0, panel_w, log_h), border_radius=10)
    surface.blit(log_panel, (log_x, log_y))
    
    # 제목
    surface.blit(font_l.render("생존 일지", True, TXT_GOLD), (log_x + 15, log_y + 10)) 
    
    # --- [수정] 스크롤 뷰 시작 위치를 더 아래로 내림 (제목 겹침 방지) ---
    content_y_start = log_y + 55  # 40 -> 55로 수정
    view_h = log_h - 65           # 보여질 높이 조정
    line_h = 28
    
    clip_rect = pygame.Rect(log_x + 15, content_y_start, panel_w - 30, view_h)
    surface.set_clip(clip_rect)
    
    total_content_h = len(player.logs) * line_h
    max_scroll = max(0, total_content_h - view_h)
    game.scroll_y_log = max(0, min(game.scroll_y_log, max_scroll))
    
    start_draw_y = content_y_start - game.scroll_y_log
    text_max_width = panel_w - 40
    
    for i, log in enumerate(player.logs):
        line_y = start_draw_y + i * line_h
        if line_y + line_h < content_y_start or line_y > content_y_start + view_h:
            continue
            
        display_text = f"- {log}"
        display_text = truncate_text(display_text, font_s, text_max_width)
        surface.blit(font_s.render(display_text, True, TXT_PRIMARY), (log_x + 15, line_y))

    surface.set_clip(None)

    return [
        Button(120, 280, 160, 120, "쿠팡 접속", CP_BLUE, "go_shop", style="invisible"),
        Button(500, 600, 80, 60, "가방 열기", (200,150,50), "go_inventory", style="invisible"),
        Button(400, 150, 180, 350, "외출(파밍)", (100,50,50), "go_outside", style="invisible"),
        Button(700, 500, 250, 120, "잠자기", (100,100,200), "sleep", style="invisible"),
    ]

def draw_shop(surface, game):
    draw_coupang_ui_header(surface, game.player.money)
    player = game.player
    
    price_food = 800
    price_mental = 1000
    if player.discount_active:
        price_food //= 2
        price_mental //= 2
    
    panel_w, panel_h = 320, 460
    gap = 60
    total_w = panel_w * 2 + gap
    start_x = (SCREEN_WIDTH - total_w) // 2
    start_y = 150
    
    x1 = start_x
    p1_rect = pygame.Rect(x1, start_y, panel_w, panel_h)
    
    pygame.draw.rect(surface, (200,200,200), p1_rect.move(4, 4), border_radius=12)
    pygame.draw.rect(surface, WHITE, p1_rect, border_radius=12)
    pygame.draw.rect(surface, CP_BORDER, p1_rect, 2, border_radius=12)
    
    pygame.draw.rect(surface, (248, 250, 252), (x1+20, start_y+20, panel_w-40, 180), border_radius=8)
    draw_item_icon(surface, "쿠팡이츠 배달통", x1 + panel_w//2 - 50, start_y + 60, 100)
    
    name_surf = font_l.render("쿠팡 이츠 배달", True, CP_TEXT_BLACK)
    surface.blit(name_surf, name_surf.get_rect(center=(x1 + panel_w//2, start_y + 230)))
    
    price_col = CP_RED if player.money >= price_food else TXT_SECONDARY
    price_surf = font_xl.render(f"{price_food:,} P", True, price_col)
    surface.blit(price_surf, price_surf.get_rect(center=(x1 + panel_w//2, start_y + 275)))
    
    desc_start_y = start_y + 340
    desc_info1 = [("랜덤 음식 획득", CP_TEXT_DARK), ("배고픔/목마름 해결", CP_GREEN)]
    
    for i, (txt, col) in enumerate(desc_info1):
        d_surf = font_s.render(txt, True, col)
        surface.blit(d_surf, d_surf.get_rect(center=(x1 + panel_w//2, desc_start_y + i*25)))

    x2 = start_x + panel_w + gap
    p2_rect = pygame.Rect(x2, start_y, panel_w, panel_h)
    
    pygame.draw.rect(surface, (200,200,200), p2_rect.move(4, 4), border_radius=12)
    pygame.draw.rect(surface, WHITE, p2_rect, border_radius=12)
    pygame.draw.rect(surface, CP_BORDER, p2_rect, 2, border_radius=12)
    
    pygame.draw.rect(surface, (248, 250, 252), (x2+20, start_y+20, panel_w-40, 180), border_radius=8)
    draw_item_icon(surface, "쿠팡플레이", x2 + panel_w//2 - 50, start_y + 60, 100)
    
    name_surf2 = font_l.render("쿠팡플레이 시청", True, CP_TEXT_BLACK)
    surface.blit(name_surf2, name_surf2.get_rect(center=(x2 + panel_w//2, start_y + 230)))
    
    price_col2 = CP_RED if player.money >= price_mental else TXT_SECONDARY
    price_surf2 = font_xl.render(f"{price_mental:,} P", True, price_col2)
    surface.blit(price_surf2, price_surf2.get_rect(center=(x2 + panel_w//2, start_y + 275)))
    
    desc_info2 = [("멘탈 대폭 회복 (+40)", CP_GREEN), ("영화/SNL 무제한", CP_BLUE)]
    
    for i, (txt, col) in enumerate(desc_info2):
        d_surf = font_s.render(txt, True, col)
        surface.blit(d_surf, d_surf.get_rect(center=(x2 + panel_w//2, desc_start_y + i*25)))

    if player.discount_active:
        sale_badge = font_xl.render("SALE !!", True, CP_GREEN)
        rotated_sale = pygame.transform.rotate(sale_badge, 15)
        surface.blit(rotated_sale, (start_x - 30, start_y - 40))

    btn_y = start_y + 400 
    
    return [
        Button(x1+40, btn_y, panel_w-80, 45, "주문하기", CP_BLUE, "buy_food", text_color=WHITE, style="flat"),
        Button(x2+40, btn_y, panel_w-80, 45, "시청하기", CP_BLUE, "buy_mental", text_color=WHITE, style="flat"),
        Button(50, 620, 120, 50, "뒤로가기", (180, 180, 180), "go_home", text_color=BLACK),
        Button(SCREEN_WIDTH-170, 620, 150, 50, "물품 판매", CP_GREEN, "sell_all", text_color=WHITE)
    ]

def draw_inventory(surface, game):
    surface.fill(BUNKER_BG)
    panel_rect = pygame.Rect(50, 50, 900, 600)
    pygame.draw.rect(surface, PANEL_BG, panel_rect, border_radius=15)
    pygame.draw.rect(surface, BORDER_COLOR, panel_rect, 2, border_radius=15)
    surface.blit(font_xl.render("INVENTORY", True, TXT_PRIMARY), (80, 80))
    
    surface.blit(font_m.render("※ 아이템을 우클릭하여 사용/섭취 하세요.", True, TXT_SECONDARY), (500, 95))
    
    cols = 6
    slot_sz, gap = 100, 20
    start_x, start_y = 100, 160
    items = [{"type":"norm", "name":i} for i in game.player.inventory] + \
            [{"type":"food", "name":f} for f in game.player.food_bag]
    btns = []
    view_h = 400
    surface.set_clip(pygame.Rect(80, 160, 840, view_h))
    for i, item in enumerate(items):
        row, col = i // cols, i % cols
        x = start_x + col * (slot_sz + gap)
        y = start_y + row * (slot_sz + gap) - game.scroll_y_inventory
        pygame.draw.rect(surface, (50,50,55), (x, y, slot_sz, slot_sz), border_radius=5)
        draw_item_icon(surface, item['name'], x, y, slot_sz)
                
    surface.set_clip(None)
    btns.append(Button(400, 600, 200, 60, "CLOSE", (100,100,100), "go_home"))
    return btns

def draw_inventory_tooltips(surface, game):
    mx, my = pygame.mouse.get_pos()
    items = [{"name":i} for i in game.player.inventory] + [{"name":f, "food":True} for f in game.player.food_bag]
    cols, slot_sz, gap = 6, 100, 20
    start_x, start_y = 100, 160
    
    for i, item in enumerate(items):
        row, col = i // cols, i % cols
        x = start_x + col * (slot_sz + gap)
        y = start_y + row * (slot_sz + gap) - game.scroll_y_inventory
        
        if 160 <= y <= 560 and pygame.Rect(x, y, slot_sz, slot_sz).collidepoint(mx, my):
            txt = item['name']
            effect_text = ""
            if 'food' in item:
                if txt in FOOD_EFFECTS:
                    eff = FOOD_EFFECTS[txt]
                    effect_text = f"배고픔:{eff['hunger']} 목마름:{eff['thirst']} 멘탈:{eff['mental']}"
            elif txt in ITEM_EFFECTS:
                eff = ITEM_EFFECTS[txt]
                if "desc" in eff:
                    effect_text = eff["desc"]
                else:
                    parts = []
                    if eff.get('energy'): parts.append(f"행동력:{eff['energy']}")
                    if eff.get('mental'): parts.append(f"멘탈:{eff['mental']}")
                    effect_text = " ".join(parts)
            
            if effect_text:
                txt += "\n" + effect_text
            
            txt += "\n[우클릭] 사용/먹기"
            draw_tooltip(surface, txt, mx, my)

def draw_outside_scene(surface, game):
    g = game.outdoor_game
    draw_empty_house(surface)
    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

    if g.state == "INSTRUCTION":
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0,0,0,200), (0,0,SCREEN_WIDTH,SCREEN_HEIGHT))
        surface.blit(overlay, (0,0))
        
        pygame.draw.rect(surface, PANEL_BG, (cx-300, cy-150, 600, 300), border_radius=15)
        pygame.draw.rect(surface, WHITE, (cx-300, cy-150, 600, 300), 2, border_radius=15)
        
        info_surf = font_xl.render(g.info_text, True, TXT_GOLD)
        info_rect = info_surf.get_rect(center=(cx, cy - 60)) 
        surface.blit(info_surf, info_rect)
        
        sub_surf = font_m.render(g.sub_text, True, WHITE)
        sub_rect = sub_surf.get_rect(center=(cx, cy + 10))
        surface.blit(sub_surf, sub_rect)
        
        start_surf = font_l.render("PRESS [SPACE] TO START", True, TXT_WARN)
        start_rect = start_surf.get_rect(center=(cx, cy + 90))
        surface.blit(start_surf, start_rect)
        
        return []

    if g.state == "SUCCESS":
        succ_surf = font_xl.render("MISSION ACCOMPLISHED", True, CP_GREEN)
        succ_rect = succ_surf.get_rect(center=(cx, cy))
        surface.blit(succ_surf, succ_rect)
        return [Button(400, 500, 200, 60, "TAKE LOOT", ACCENT_COLOR, "outside_reward")]
    
    if g.state == "FAILED":
        fail_surf = font_xl.render("DETECTED! RUN!", True, TXT_WARN)
        fail_rect = fail_surf.get_rect(center=(cx, cy))
        surface.blit(fail_surf, fail_rect)
        return [Button(400, 500, 200, 60, "FLEE", (100,0,0), "outside_fail")]

    draw_outside(surface, g) 
    return []

def draw_outside(surface, game):
    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    
    if game.type == "lockpick":
        pygame.draw.circle(surface, (30,30,30), (cx, cy), 100)
        pygame.draw.circle(surface, (100,100,100), (cx, cy), 80, 5)
        start_rad = math.radians(-(game.lock_solution + 20))
        end_rad = math.radians(-(game.lock_solution - 20))
        pygame.draw.arc(surface, TXT_WARN, (cx-80, cy-80, 160, 160), start_rad, end_rad, 15)
        needle_rad = math.radians(game.lock_angle)
        nx = cx + math.cos(needle_rad) * 70
        ny = cy + math.sin(needle_rad) * 70
        pygame.draw.line(surface, WHITE, (cx, cy), (nx, ny), 3)

    elif game.type == "search":
        darkness = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        darkness.fill((0,0,0,240))
        pygame.draw.circle(darkness, (0,0,0,0), (game.search_cursor[0], game.search_cursor[1]), 80)
        surface.blit(darkness, (0,0))
        dist = math.hypot(game.search_cursor[0]-game.search_target[0], game.search_cursor[1]-game.search_target[1])
        if dist < 80:
            pygame.draw.circle(surface, TXT_GOLD, game.search_target, 10)
            
    elif game.type == "breath":
        pygame.draw.rect(surface, (50,50,50), (300, 400, 400, 30), border_radius=15)
        marker_x = 500 + game.breath_val
        color = CP_GREEN if abs(game.breath_val) < 150 else TXT_WARN
        pygame.draw.circle(surface, color, (int(marker_x), 415), 15)
        surface.blit(font_m.render("HOLD BREATH...", True, WHITE), (420, 360))

    elif game.type == "mash":
        pygame.draw.rect(surface, (50,50,50), (300, 400, 400, 40))
        fill = int(400 * (game.mash_count / game.mash_target))
        pygame.draw.rect(surface, TXT_GOLD, (300, 400, fill, 40))
        surface.blit(font_m.render("CLEAR DEBRIS!", True, WHITE), (420, 360))

    elif game.type == "frequency":
        pygame.draw.rect(surface, (10, 30, 10), (200, 200, 600, 300))
        pygame.draw.rect(surface, (50, 100, 50), (200, 200, 600, 300), 2)
        target_y = 350
        points_t = []
        for x in range(600):
            y = target_y + math.sin((x + time.time()*20) * 0.05) * 50
            points_t.append((200+x, y))
        pygame.draw.lines(surface, (0, 200, 0), False, points_t, 2)
        
        current_y = 350 + (game.freq_current - game.freq_target)
        points_c = []
        for x in range(600):
            noise = random.randint(-2, 2)
            y = current_y + math.sin((x + time.time()*20) * 0.05) * 50 + noise
            points_c.append((200+x, y))
        line_col = TXT_GOLD
        if abs(game.freq_current - game.freq_target) < 20: line_col = WHITE
        pygame.draw.lines(surface, line_col, False, points_c, 2)

    elif game.type == "struggle":
        total_w = len(game.struggle_seq) * 80
        start_x = (SCREEN_WIDTH - total_w) // 2
        
        for i, key_name in enumerate(game.struggle_seq):
            bg_col = (50, 50, 50)
            txt_col = TXT_SECONDARY
            
            if i < game.struggle_idx:
                bg_col = (20, 100, 20)
                txt_col = TXT_SUCCESS
            elif i == game.struggle_idx:
                bg_col = (100, 20, 20)
                txt_col = WHITE
            
            cx, cy = start_x + 40, 400
            pygame.draw.circle(surface, bg_col, (cx, cy), 35)
            if i == game.struggle_idx:
                pygame.draw.circle(surface, WHITE, (cx, cy), 35, 2)
            
            symbol = key_name
            if key_name == 'UP': symbol = "상"
            elif key_name == 'DOWN': symbol = "하"
            elif key_name == 'LEFT': symbol = "좌"
            elif key_name == 'RIGHT': symbol = "우"
            
            txt = font_l.render(symbol, True, txt_col)
            surface.blit(txt, txt.get_rect(center=(cx, cy)))
            
            start_x += 80

def draw_item_get(surface, game):
    surface.fill(CP_BG_GRAY)
    
    popup_title = "배달 완료" if game.unboxing_type == "eats" else "로켓배송"
    draw_popup_coupang(surface, popup_title, "") 
    
    cw, ch = 500, 300
    cx, cy = (SCREEN_WIDTH - cw)//2, (SCREEN_HEIGHT - ch)//2 
    
    icon_size = 100
    icon_x = SCREEN_WIDTH // 2 - icon_size // 2
    icon_y = cy + 75
    
    if game.unboxing_type == "eats":
        draw_item_icon(surface, game.acquired_item, icon_x, icon_y, icon_size)
        msg_text = f"[{game.acquired_item}] 도착!"
    else:
        draw_item_icon(surface, "쿠팡플레이", icon_x, icon_y, icon_size)
        msg_text = f"[{game.acquired_item}] 수령!"
        
    text_y = cy + 210
    text_surf = font_l.render(msg_text, True, CP_TEXT_BLACK)
    text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, text_y))
    surface.blit(text_surf, text_rect)

    return [Button(400, 435, 200, 50, "확인", CP_BLUE, "item_get_confirm", text_color=WHITE, style="flat")]

def draw_msg_popup(surface, game):
    style = game.popup_info.get("style", "default")
    
    if style == "coupang":
        surface.fill(CP_BG_GRAY)
        draw_coupang_ui_header(surface, game.player.money)
    elif style == "inventory":
        surface.fill(BUNKER_BG)
        panel_rect = pygame.Rect(50, 50, 900, 600)
        pygame.draw.rect(surface, PANEL_BG, panel_rect, border_radius=15)
        pygame.draw.rect(surface, BORDER_COLOR, panel_rect, 2, border_radius=15)
        surface.blit(font_xl.render("INVENTORY", True, TXT_PRIMARY), (80, 80))
    else:
        draw_room_background(surface)
        
    title = game.popup_info["title"]
    msg = game.popup_info["msg"]
    
    if style == "coupang":
        draw_popup_coupang(surface, title, msg)
        return [Button(400, 435, 200, 50, "확인", CP_BLUE, "msg_popup_confirm", text_color=WHITE, style="flat")]
    else:
        draw_popup_apocalypse(surface, title, msg)
        return [Button(400, 435, 200, 50, "확인", ACCENT_COLOR, "msg_popup_confirm", style="apocalypse")]

def draw_event(surface, game):
    draw_room_background(surface)
    draw_popup_apocalypse(surface, "EVENT", game.current_event['msg'])
    
    return [Button(400, 435, 200, 50, "OK", ACCENT_COLOR, "event_confirm", style="apocalypse")]

def draw_result(surface, game):
    surface.fill(BLACK)
    
    if game.player.game_clear:
        title = "SURVIVED"
        col = CP_GREEN
        msg = "축하합니다! 30일간의 생존에 성공했습니다!"
        sub_msg = "구조대가 도착했습니다."
    else:
        title = "YOU DIED"
        col = TXT_WARN
        msg = game.player.cause_of_death
        sub_msg = ""
        
    title_surf = font_day.render(title, True, col)
    title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 200))
    surface.blit(title_surf, title_rect)
    
    msg_surf = font_m.render(msg, True, WHITE)
    msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH // 2, 300))
    surface.blit(msg_surf, msg_rect)
    
    if sub_msg:
        sub_surf = font_m.render(sub_msg, True, TXT_SECONDARY)
        sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 340))
        surface.blit(sub_surf, sub_rect)
    
    day_info = f"생존 일수: {game.player.day}일"
    day_surf = font_l.render(day_info, True, WHITE)
    day_rect = day_surf.get_rect(center=(SCREEN_WIDTH // 2, 400))
    surface.blit(day_surf, day_rect)
    
    btn_w, btn_h = 200, 60
    btn_x = (SCREEN_WIDTH - btn_w) // 2
    
    return [Button(btn_x, 500, btn_w, btn_h, "EXIT", (100,100,100), "quit")]

def draw_room_background(surface):
    pygame.draw.rect(surface, BUNKER_BG, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
    floor_poly = [(0, 500), (SCREEN_WIDTH, 500), (SCREEN_WIDTH, SCREEN_HEIGHT), (0, SCREEN_HEIGHT)]
    pygame.draw.polygon(surface, BUNKER_FLOOR, floor_poly)
    pygame.draw.line(surface, (20, 15, 10), (0, 500), (SCREEN_WIDTH, 500), 2)

    win_rect = pygame.Rect(700, 100, 200, 250)
    pygame.draw.rect(surface, WINDOW_LIGHT, win_rect)
    pygame.draw.rect(surface, (10, 10, 10), win_rect, 5)
    for i in range(4):
        y = 120 + i * 60
        pygame.draw.rect(surface, WINDOW_BAR, (690, y, 220, 40))
        pygame.draw.circle(surface, (30,20,10), (700, y+20), 3)
        pygame.draw.circle(surface, (30,20,10), (890, y+20), 3)

    desk_rect = pygame.Rect(50, 350, 300, 150)
    pygame.draw.rect(surface, (60, 40, 30), desk_rect)
    pygame.draw.rect(surface, (40, 25, 20), (50, 350, 300, 20))
    pygame.draw.rect(surface, (50, 30, 20), (60, 500, 20, 100))
    pygame.draw.rect(surface, (50, 30, 20), (320, 500, 20, 100))

    monitor_rect = pygame.Rect(120, 280, 160, 100)
    pygame.draw.rect(surface, (20, 20, 20), monitor_rect)
    pygame.draw.rect(surface, (30, 30, 30), (125, 285, 150, 90))
    pygame.draw.rect(surface, CP_BLUE, (130, 290, 140, 80))
    pygame.draw.rect(surface, (10, 10, 10), (190, 380, 20, 20))
    pygame.draw.rect(surface, (20, 20, 20), (170, 400, 60, 10))

    door_rect = pygame.Rect(400, 150, 180, 350)
    pygame.draw.rect(surface, (50, 45, 40), door_rect)
    pygame.draw.rect(surface, (30, 25, 20), door_rect, 5)
    pygame.draw.circle(surface, (200, 180, 50), (560, 320), 5)
    
    paper_rect = pygame.Rect(430, 200, 60, 80)
    pygame.draw.rect(surface, (220, 220, 200), paper_rect)
    pygame.draw.line(surface, (200, 50, 50), (435, 210), (485, 270), 2)

    pygame.draw.polygon(surface, (70, 70, 80), [(700, 550), (950, 550), (980, 650), (670, 650)]) 
    pygame.draw.polygon(surface, (50, 50, 60), [(670, 650), (980, 650), (980, 670), (670, 670)])
    pygame.draw.polygon(surface, (60, 80, 120), [(700, 580), (950, 580), (970, 650), (680, 650)])
    pygame.draw.rect(surface, (200, 200, 210), (720, 530, 100, 40), border_radius=10)

    bag_x, bag_y = 500, 600
    pygame.draw.rect(surface, (100, 70, 40), (bag_x, bag_y, 80, 60), border_radius=10)
    pygame.draw.rect(surface, (80, 50, 30), (bag_x+10, bag_y+30, 60, 25), border_radius=5)
    pygame.draw.rect(surface, (120, 90, 50), (bag_x, bag_y, 80, 20), border_radius=5)
    pygame.draw.rect(surface, (200, 180, 50), (bag_x+35, bag_y+15, 10, 20))

def draw_empty_house(surface):
    surface.fill((15, 15, 20))
    pygame.draw.rect(surface, (25, 25, 30), (100, 400, 250, 150))
    pygame.draw.rect(surface, (30, 30, 35), (700, 200, 200, 400))
    
    moon_light = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(moon_light, (50, 50, 100, 30), [(400, 0), (600, 0), (800, 700), (200, 700)])
    surface.blit(moon_light, (0,0))
    
    pygame.draw.circle(surface, (0,0,0,100), (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 600, 300)

def draw_intro_roulette(surface, cx, cy, radius, game_obj):
    items, names, colors, angle = game_obj.get_draw_info()
    num = len(items)
    arc_angle = 360 / num
    
    pygame.draw.circle(surface, (60, 50, 40), (cx, cy), radius + 12)
    pygame.draw.circle(surface, (40, 30, 20), (cx, cy), radius + 10) 

    for i in range(num):
        start_a = angle + (i * arc_angle)
        
        points = [(cx, cy)]
        steps = 15
        for s in range(steps + 1):
            curr_a = math.radians(start_a + (arc_angle * s / steps))
            px = cx + math.cos(curr_a) * radius
            py = cy + math.sin(curr_a) * radius
            points.append((px, py))
            
        pygame.draw.polygon(surface, colors[i], points)
        pygame.draw.polygon(surface, (30, 20, 10), points, 3)
        
        mid_a = math.radians(start_a + arc_angle/2)
        tx = cx + math.cos(mid_a) * (radius * 0.72)
        ty = cy + math.sin(mid_a) * (radius * 0.72)
        
        text = font_s.render(names[i], True, (10, 5, 5))
        rot_surf = pygame.transform.rotate(text, -math.degrees(mid_a)-90)
        surface.blit(rot_surf, rot_surf.get_rect(center=(tx, ty)))

    tip_y = cy - radius + 15
    
    pygame.draw.polygon(surface, (180, 180, 190), [(cx-10, tip_y-30), (cx+10, tip_y-30), (cx, tip_y+5)])
    pygame.draw.polygon(surface, (200, 0, 0), [(cx-5, tip_y-10), (cx+5, tip_y-10), (cx, tip_y+5)])
    pygame.draw.rect(surface, (50, 40, 30), (cx-6, tip_y-50, 12, 20))

    pygame.draw.circle(surface, (80, 60, 50), (cx, cy), 18)
    pygame.draw.circle(surface, (50, 30, 20), (cx, cy), 18, 3)
    pygame.draw.line(surface, (40, 20, 10), (cx-10, cy), (cx+10, cy), 3)
    pygame.draw.line(surface, (40, 20, 10), (cx, cy-10), (cx, cy+10), 3)

def draw_coupang_ui_header(surface, money):
    pygame.draw.rect(surface, CP_HEADER_WHITE, (0, 0, SCREEN_WIDTH, 120))
    pygame.draw.line(surface, CP_BORDER, (0, 120), (SCREEN_WIDTH, 120), 1)
    surface.blit(font_xl.render("Coupang", True, CP_RED), (50, 35))
    search_rect = pygame.Rect(260, 35, 500, 50)
    pygame.draw.rect(surface, CP_HEADER_WHITE, search_rect, border_radius=4)
    pygame.draw.rect(surface, CP_BLUE, search_rect, 2, border_radius=4)
    surface.blit(font_m.render("생존 물품을 검색하세요", True, (150,150,150)), (280, 47))
    pygame.draw.circle(surface, CP_BLUE, (720, 60), 15, 2)
    m_surf = font_m.render(f"{money:,}point", True, CP_TEXT_BLACK)
    surface.blit(m_surf, (820, 45))

def draw_stat_bar_with_text(surface, label, val, max_val, x, y, col):
    # 컨테이너 높이를 50으로 늘려 넉넉하게 잡음
    container_h = 50
    container = pygame.Surface((300, container_h), pygame.SRCALPHA)
    pygame.draw.rect(container, (0,0,0,150), (0,0,300,container_h), border_radius=10)
    
    # 컨테이너의 수직 중앙 좌표
    cy = container_h // 2
    
    # 1. 라벨 (왼쪽 정렬)
    lbl_surf = font_s.render(label, True, (200,200,200))
    lbl_rect = lbl_surf.get_rect(midleft=(15, cy)) # 왼쪽 여백 15
    container.blit(lbl_surf, lbl_rect)
    
    # 2. 게이지 바 (라벨과 값 사이)
    # "정신력" 등 3글자 고려하여 시작 위치를 110px로 밈
    bar_x = 110
    bar_w = 130
    bar_h = 14
    
    # 배경 바
    bar_bg_rect = pygame.Rect(bar_x, 0, bar_w, bar_h)
    bar_bg_rect.centery = cy
    pygame.draw.rect(container, BAR_BG, bar_bg_rect, border_radius=7)
    
    # 채워진 바
    fill_w = int(bar_w * max(0, min(1, val / max_val)))
    if fill_w > 0:
        bar_fill_rect = pygame.Rect(bar_x, 0, fill_w, bar_h)
        bar_fill_rect.centery = cy
        pygame.draw.rect(container, col, bar_fill_rect, border_radius=7)
        
    # 3. 숫자 값 (바 오른쪽)
    val_surf = font_s.render(f"{int(val)}", True, WHITE)
    # 바 끝(bar_x + bar_w)에서 10px 띄움
    val_rect = val_surf.get_rect(midleft=(bar_x + bar_w + 10, cy))
    container.blit(val_surf, val_rect)
    
    surface.blit(container, (x, y))

def draw_item_icon(surface, item_name, x, y, size):
    icon_type = ITEM_ICONS_MAP.get(item_name, "box")
    cx, cy = x + size//2, y + size//2
    scale = size / 50.0 
    
    pygame.draw.ellipse(surface, (0,0,0,50), (cx-20*scale, cy+15*scale, 40*scale, 10*scale))

    if icon_type == "water":
        pygame.draw.rect(surface, (100, 180, 255), (cx-8*scale, cy-12*scale, 16*scale, 30*scale), border_radius=2)
        pygame.draw.rect(surface, (50, 100, 200), (cx-8*scale, cy-6*scale, 16*scale, 10*scale))
        pygame.draw.rect(surface, (200, 200, 255), (cx-6*scale, cy-16*scale, 12*scale, 4*scale))

    elif icon_type == "soymilk":
        pygame.draw.rect(surface, (220, 210, 180), (cx-10*scale, cy-12*scale, 20*scale, 28*scale), border_radius=2)
        pygame.draw.rect(surface, (100, 120, 80), (cx-5*scale, cy, 10*scale, 10*scale))
        pygame.draw.line(surface, (200, 200, 180), (cx+5*scale, cy-12*scale), (cx+15*scale, cy-20*scale), 2)

    elif icon_type == "bread":
        pygame.draw.rect(surface, (210, 170, 100), (cx-15*scale, cy-12*scale, 30*scale, 26*scale), border_radius=5)
        pygame.draw.rect(surface, (160, 100, 50), (cx-17*scale, cy-12*scale, 34*scale, 26*scale), 2, border_radius=5)
        pygame.draw.circle(surface, (80, 120, 80), (cx-8*scale, cy-5*scale), 4*scale)
        pygame.draw.circle(surface, (80, 120, 80), (cx+8*scale, cy+5*scale), 3*scale)

    elif icon_type == "hamburger":
        pygame.draw.rect(surface, (200, 140, 60), (cx-18*scale, cy+5*scale, 36*scale, 10*scale), border_bottom_left_radius=int(10*scale), border_bottom_right_radius=int(10*scale))
        pygame.draw.rect(surface, (100, 60, 40), (cx-18*scale, cy+2*scale, 36*scale, 6*scale), border_radius=3)
        pygame.draw.polygon(surface, (255, 200, 0), [(cx-16*scale, cy+2*scale), (cx+16*scale, cy+2*scale), (cx, cy+8*scale)])
        pygame.draw.rect(surface, (50, 200, 50), (cx-17*scale, cy-2*scale, 34*scale, 4*scale), border_radius=2)
        pygame.draw.rect(surface, (200, 140, 60), (cx-18*scale, cy-12*scale, 36*scale, 12*scale), border_top_left_radius=int(12*scale), border_top_right_radius=int(12*scale))
        pygame.draw.circle(surface, (240, 220, 180), (cx-5*scale, cy-8*scale), 2*scale)
        pygame.draw.circle(surface, (240, 220, 180), (cx+5*scale, cy-6*scale), 2*scale)

    elif icon_type == "chicken":
        pygame.draw.polygon(surface, (220, 20, 20), [
            (cx-15*scale, cy+15*scale), (cx+15*scale, cy+15*scale),
            (cx+20*scale, cy-5*scale), (cx-20*scale, cy-5*scale)
        ])
        pygame.draw.line(surface, WHITE, (cx, cy+15*scale), (cx, cy-5*scale), int(6*scale))
        chicken_col = (210, 150, 60)
        pygame.draw.circle(surface, chicken_col, (cx-10*scale, cy-8*scale), 8*scale)
        pygame.draw.circle(surface, chicken_col, (cx+5*scale, cy-10*scale), 9*scale)
        pygame.draw.circle(surface, chicken_col, (cx+12*scale, cy-6*scale), 7*scale)

    elif icon_type == "cola":
        pygame.draw.rect(surface, (200, 20, 20), (cx-8*scale, cy-12*scale, 16*scale, 28*scale), border_radius=2)
        pygame.draw.rect(surface, WHITE, (cx-8*scale, cy-2*scale, 16*scale, 4*scale))
        pygame.draw.rect(surface, (150, 150, 150), (cx-6*scale, cy-14*scale, 12*scale, 2*scale))

    elif icon_type == "beer":
        pygame.draw.rect(surface, (255, 200, 0), (cx-10*scale, cy-10*scale, 20*scale, 26*scale))
        pygame.draw.rect(surface, (200, 200, 200), (cx+10*scale, cy-5*scale, 6*scale, 16*scale), 2)
        pygame.draw.circle(surface, WHITE, (cx-6*scale, cy-12*scale), 6*scale)
        pygame.draw.circle(surface, WHITE, (cx, cy-14*scale), 7*scale)
        pygame.draw.circle(surface, WHITE, (cx+6*scale, cy-12*scale), 6*scale)

    elif icon_type == "medkit":
        pygame.draw.rect(surface, (220, 220, 220), (cx-15*scale, cy-12*scale, 30*scale, 24*scale), border_radius=4)
        pygame.draw.rect(surface, (200, 50, 50), (cx-4*scale, cy-8*scale, 8*scale, 16*scale)) 
        pygame.draw.rect(surface, (200, 50, 50), (cx-8*scale, cy-4*scale, 16*scale, 8*scale))

    elif icon_type == "gun":
        pygame.draw.rect(surface, (80, 80, 80), (cx-10*scale, cy-10*scale, 24*scale, 8*scale)) 
        pygame.draw.rect(surface, (50, 40, 30), (cx-10*scale, cy-5*scale, 8*scale, 15*scale)) 

    elif icon_type == "bat":
        pygame.draw.line(surface, (180, 140, 80), (cx-10*scale, cy+10*scale), (cx+15*scale, cy-15*scale), int(6*scale))
        pygame.draw.circle(surface, (50, 40, 30), (cx-12*scale, cy+12*scale), 3*scale) 

    elif icon_type == "battery":
        pygame.draw.rect(surface, (20, 20, 20), (cx-8*scale, cy-12*scale, 16*scale, 24*scale))
        pygame.draw.rect(surface, (220, 180, 50), (cx-8*scale, cy-5*scale, 16*scale, 10*scale)) 
        pygame.draw.rect(surface, (150, 150, 150), (cx-4*scale, cy-14*scale, 8*scale, 2*scale)) 

    elif icon_type == "delivery_bag":
        pygame.draw.rect(surface, CP_GREEN, (cx-15*scale, cy-12*scale, 30*scale, 24*scale), border_radius=3)
        pygame.draw.rect(surface, WHITE, (cx-5*scale, cy-5*scale, 10*scale, 10*scale))

    elif icon_type == "gameboy":
        pygame.draw.rect(surface, (180, 180, 190), (cx-12*scale, cy-18*scale, 24*scale, 36*scale), border_radius=3)
        pygame.draw.rect(surface, (30, 30, 30), (cx-10*scale, cy-15*scale, 20*scale, 15*scale))
        pygame.draw.circle(surface, CP_RED, (cx+6*scale, cy+8*scale), 3*scale)
    
    elif icon_type == "coupon":
        pygame.draw.rect(surface, (255, 215, 0), (cx-18*scale, cy-10*scale, 36*scale, 20*scale), border_radius=3)
        pygame.draw.circle(surface, DARK_BG, (cx-18*scale, cy), 3*scale)
        pygame.draw.circle(surface, DARK_BG, (cx+18*scale, cy), 3*scale)
        pygame.draw.circle(surface, (200, 50, 50), (cx-5*scale, cy-3*scale), 2*scale)
        pygame.draw.circle(surface, (200, 50, 50), (cx+5*scale, cy+3*scale), 2*scale)
        pygame.draw.line(surface, (200, 50, 50), (cx+5*scale, cy-5*scale), (cx-5*scale, cy+5*scale), 2)

    elif icon_type == "play_button":
        pygame.draw.rect(surface, (20, 20, 25), (cx-15*scale, cy-12*scale, 30*scale, 24*scale), border_radius=5)
        pygame.draw.polygon(surface, CP_BLUE, [(cx-3*scale, cy-6*scale), (cx-3*scale, cy+6*scale), (cx+6*scale, cy)])
    
    elif icon_type == "energy_drink":
        pygame.draw.rect(surface, (30, 40, 120), (cx-9*scale, cy-14*scale, 18*scale, 28*scale), border_radius=3)
        pygame.draw.rect(surface, (180, 180, 190), (cx-9*scale, cy-14*scale, 18*scale, 6*scale), border_top_left_radius=3, border_top_right_radius=3)
        
        lightning_points = [
            (cx+3*scale, cy-4*scale), 
            (cx-4*scale, cy+2*scale), 
            (cx+2*scale, cy+2*scale), 
            (cx-3*scale, cy+10*scale)
        ]
        pygame.draw.polygon(surface, (255, 220, 0), lightning_points)
        pygame.draw.polygon(surface, (200, 150, 0), lightning_points, 1)
    
    elif icon_type == "laptop":
        pygame.draw.rect(surface, (200, 200, 200), (cx-16*scale, cy+8*scale, 32*scale, 2*scale))
        pygame.draw.rect(surface, (30, 30, 30), (cx-14*scale, cy-10*scale, 28*scale, 18*scale), border_radius=2)
        pygame.draw.rect(surface, (220, 220, 220), (cx-14*scale, cy-10*scale, 28*scale, 18*scale), 2, border_radius=2)
        pygame.draw.circle(surface, (100, 100, 100), (cx, cy-1), 2*scale)

    elif icon_type == "watch":
        pygame.draw.rect(surface, (180, 160, 100), (cx-6*scale, cy-15*scale, 12*scale, 30*scale), border_radius=2)
        pygame.draw.circle(surface, (255, 215, 0), (cx, cy), 11*scale) 
        pygame.draw.circle(surface, (20, 20, 20), (cx, cy), 9*scale)  
        pygame.draw.line(surface, (255, 255, 255), (cx, cy), (cx+4*scale, cy-4*scale), 2)
        pygame.draw.line(surface, (255, 255, 255), (cx, cy), (cx-2*scale, cy+2*scale), 2)

    elif icon_type == "gold":
        pygame.draw.polygon(surface, (255, 223, 0), [
            (cx-10*scale, cy-5*scale), (cx+5*scale, cy-5*scale), 
            (cx+12*scale, cy+2*scale), (cx-5*scale, cy+2*scale)
        ])
        pygame.draw.polygon(surface, (218, 165, 32), [
            (cx-5*scale, cy+2*scale), (cx+12*scale, cy+2*scale), 
            (cx+12*scale, cy+10*scale), (cx-5*scale, cy+10*scale)
        ])
        pygame.draw.polygon(surface, (184, 134, 11), [
            (cx-10*scale, cy-5*scale), (cx-5*scale, cy+2*scale),
            (cx-5*scale, cy+10*scale), (cx-10*scale, cy+4*scale)
        ])

    elif icon_type == "figure":
        pygame.draw.rect(surface, (50, 50, 60), (cx-10*scale, cy-15*scale, 20*scale, 30*scale), 2)
        pygame.draw.circle(surface, (255, 200, 180), (cx, cy-5*scale), 5*scale)
        pygame.draw.rect(surface, (100, 200, 255), (cx-5*scale, cy, 10*scale, 10*scale))
        pygame.draw.line(surface, (50, 50, 200), (cx-2*scale, cy+10*scale), (cx-2*scale, cy+15*scale), 2)
        pygame.draw.line(surface, (50, 50, 200), (cx+2*scale, cy+10*scale), (cx+2*scale, cy+15*scale), 2)

    elif icon_type == "book":
        pygame.draw.rect(surface, (139, 69, 19), (cx-12*scale, cy-14*scale, 24*scale, 28*scale), border_radius=2)
        pygame.draw.rect(surface, (160, 82, 45), (cx-12*scale, cy-14*scale, 6*scale, 28*scale), border_top_left_radius=2, border_bottom_left_radius=2)
        pygame.draw.rect(surface, (200, 180, 100), (cx-2*scale, cy-8*scale, 10*scale, 2*scale))
        pygame.draw.rect(surface, (200, 180, 100), (cx-2*scale, cy-2*scale, 10*scale, 2*scale))

    elif icon_type == "mouse":
        pygame.draw.ellipse(surface, (80, 80, 80), (cx-10*scale, cy-12*scale, 20*scale, 24*scale))
        pygame.draw.line(surface, (50, 50, 50), (cx-8*scale, cy-4*scale), (cx+8*scale, cy-4*scale), 2)
        pygame.draw.line(surface, (50, 50, 50), (cx, cy-4*scale), (cx, cy-12*scale), 2)
        pygame.draw.arc(surface, (40, 40, 40), (cx-5*scale, cy-20*scale, 20*scale, 20*scale), 0, 3.14, 2)

    elif icon_type == "paper":
        points = [(cx-10*scale, cy-12*scale), (cx+10*scale, cy-12*scale), (cx+10*scale, cy+10*scale), (cx+2*scale, cy+12*scale), (cx-10*scale, cy+8*scale)]
        pygame.draw.polygon(surface, (240, 240, 230), points)
        for i in range(3):
            y_off = i * 6 * scale
            pygame.draw.line(surface, (100, 100, 100), (cx-6*scale, cy-8*scale + y_off), (cx+6*scale, cy-8*scale + y_off), 2)    
    
    else:
        pygame.draw.rect(surface, (160, 130, 90), (cx-15*scale, cy-12*scale, 30*scale, 24*scale))
        pygame.draw.line(surface, (120, 90, 60), (cx, cy-12*scale), (cx, cy+12*scale), 2)

def draw_tooltip(surface, text, x, y):
    lines = text.split('\n')
    w = max(font_s.render(l, True, WHITE).get_width() for l in lines) + 20
    h = len(lines) * 25 + 10
    if x + w > SCREEN_WIDTH: x -= w
    if y + h > SCREEN_HEIGHT: y -= h
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (0,0,0,220), (0,0,w,h), border_radius=5)
    surface.blit(s, (x, y))
    for i, line in enumerate(lines):
        c = TXT_GOLD if i==0 else WHITE
        surface.blit(font_s.render(line, True, c), (x + 10, y + 5 + i * 25))

def draw_popup_coupang(surface, title, msg):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill(BLACK)
    overlay.set_alpha(150)
    surface.blit(overlay, (0, 0))
    
    cw, ch = 520, 320 
    cx, cy = (SCREEN_WIDTH - cw)//2, (SCREEN_HEIGHT - ch)//2
    
    pygame.draw.rect(surface, WHITE, (cx, cy, cw, ch), border_radius=12)
    pygame.draw.rect(surface, (200, 200, 200), (cx, cy, cw, ch), 2, border_radius=12)
    
    t_surf = font_l.render(title, True, CP_TEXT_BLACK)
    t_rect = t_surf.get_rect(center=(cx + cw//2, cy + 50))
    surface.blit(t_surf, t_rect)
    
    if msg:
        lines = msg.split('\n')
        total_h = len(lines) * 30
        start_y = cy + 140 - total_h // 2
        for i, line in enumerate(lines):
            m_surf = font_m.render(line, True, CP_TEXT_DARK)
            m_rect = m_surf.get_rect(center=(cx + cw//2, start_y + i * 30))
            surface.blit(m_surf, m_rect)

def draw_popup_apocalypse(surface, title, msg):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill(BLACK)
    overlay.set_alpha(200) 
    surface.blit(overlay, (0, 0))
    
    cw, ch = 520, 320 
    cx, cy = (SCREEN_WIDTH - cw)//2, (SCREEN_HEIGHT - ch)//2
    
    pygame.draw.rect(surface, (10, 10, 10), (cx+8, cy+8, cw, ch), border_radius=8)
    pygame.draw.rect(surface, APOC_METAL_DARK, (cx, cy, cw, ch), border_radius=8)
    
    header_h = 60
    pygame.draw.rect(surface, APOC_METAL_LIGHT, (cx+4, cy+4, cw-8, header_h), border_top_left_radius=4, border_top_right_radius=4)
    pygame.draw.line(surface, APOC_RUST, (cx+4, cy+header_h+4), (cx+cw-4, cy+header_h+4), 3)
    
    pygame.draw.rect(surface, APOC_RUST, (cx, cy, cw, ch), 4, border_radius=8)
    pygame.draw.rect(surface, (20, 20, 20), (cx+4, cy+4, cw-8, ch-8), 1, border_radius=4)
    
    bolt_r = 5
    bolts = [
        (cx + 15, cy + 15),
        (cx + cw - 15, cy + 15),
        (cx + 15, cy + ch - 15),
        (cx + cw - 15, cy + ch - 15)
    ]
    for bx, by in bolts:
        pygame.draw.circle(surface, APOC_BOLT, (bx, by), bolt_r)
        pygame.draw.circle(surface, (10, 10, 10), (bx, by), bolt_r, 1)
        pygame.draw.line(surface, (30, 30, 30), (bx-3, by), (bx+3, by), 1)

    t_surf = font_l.render(title, True, TXT_WARN)
    t_shad = font_l.render(title, True, BLACK)
    t_rect = t_surf.get_rect(center=(cx + cw//2, cy + 32))
    surface.blit(t_shad, (t_rect.x+2, t_rect.y+2))
    surface.blit(t_surf, t_rect)
    
    if msg:
        lines = msg.split('\n')
        content_center_y = cy + header_h + (ch - header_h) // 2 - 20 
        total_h = len(lines) * 30
        start_y = content_center_y - total_h // 2 
        
        for i, line in enumerate(lines):
            m_surf = font_m.render(line, True, (230, 230, 230))
            m_rect = m_surf.get_rect(center=(cx + cw//2, start_y + i * 30))
            m_shad = font_m.render(line, True, (0, 0, 0))
            surface.blit(m_shad, (m_rect.x+1, m_rect.y+1))
            surface.blit(m_surf, m_rect)

def draw_title(surface):
    surface.fill((25, 28, 32)) 

    for _ in range(50):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        w = random.randint(2, 5)
        h = random.randint(2, 5)
        pygame.draw.rect(surface, (40, 43, 48), (x, y, w, h))

    for _ in range(10): 
        x1 = random.randint(0, SCREEN_WIDTH)
        y1 = random.randint(0, SCREEN_HEIGHT)
        x2 = x1 + random.randint(-50, 50)
        y2 = y1 + random.randint(50, 150)
        pygame.draw.line(surface, (15, 15, 18), (x1, y1), (x2, y2), 2)
        
    fog = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for i in range(5):
        y = 500 + i * 40
        pygame.draw.rect(fog, (10, 10, 12, 10 + i*5), (0, y, SCREEN_WIDTH, 100))
    surface.blit(fog, (0,0))


    title_text = "ZOMBIE SURVIVAL"
    sub_text = "COUPANG EDITION"
    
    t_shad = font_xl.render(title_text, True, (100, 20, 20))
    t_main = font_xl.render(title_text, True, (220, 220, 220))
    
    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 3
    
    surface.blit(t_shad, t_shad.get_rect(center=(center_x + 3, center_y + 3)))
    surface.blit(t_main, t_main.get_rect(center=(center_x, center_y)))
    
    s_main = font_l.render(sub_text, True, (150, 150, 160))
    surface.blit(s_main, s_main.get_rect(center=(center_x, center_y + 60)))
    
    pygame.draw.line(surface, (200, 50, 50), (center_x - 150, center_y + 90), (center_x + 150, center_y + 90), 2)
    
    btn_w, btn_h = 260, 70
    btn_x = (SCREEN_WIDTH - btn_w) // 2
    btn_y = SCREEN_HEIGHT * 3 // 5 + 50
    
    return [Button(btn_x, btn_y, btn_w, btn_h, "START SURVIVAL", (80, 30, 30), "go_guide", text_color=WHITE)]