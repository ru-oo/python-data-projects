import pygame
import sys
import random
import os

from config import *
from player import Player
from actions import ActionHandler
import ui 
from minigames import IntroRoulette, OutdoorMinigame

# --- 사운드 매니저 ---
class SoundManager:
    def __init__(self):
        self.sounds = {} 
        self.bgm_sounds = {} 
        self.enabled = True
        self.current_bgm_key = None 
        
        # [중요] 변수 초기화
        self.heartbeat_playing = False 
        
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            
            base_dir = os.path.dirname(os.path.abspath(__file__))
            def get_path(filename):
                return os.path.join(base_dir, filename)

            # --- 효과음 로드 ---
            def load_sfx(name, filename):
                full_path = get_path(filename)
                if os.path.exists(full_path):
                    try:
                        self.sounds[name] = pygame.mixer.Sound(full_path)
                        # 볼륨 설정
                        if name == "heartbeat": self.sounds[name].set_volume(0.6)
                        elif name == "step": self.sounds[name].set_volume(0.3)
                        else: self.sounds[name].set_volume(0.4)
                    except: pass
            
            load_sfx("click", "click.wav")
            load_sfx("transition", "whoosh.wav")
            load_sfx("success", "success.wav")
            load_sfx("fail", "fail.wav")
            load_sfx("eat", "eat.wav")
            load_sfx("open", "open.wav")
            load_sfx("alert", "alert.wav")
            load_sfx("day_pass", "day_pass.wav")
            
            # 신규 사운드
            load_sfx("heartbeat", "heartbeat.wav")
            load_sfx("step", "footstep.wav")
            load_sfx("scanner", "scanner.wav") 
            load_sfx("cash", "cash.wav")       
            load_sfx("typing", "typing.wav")   
            
            # --- BGM 로드 ---
            def load_bgm(key, filename):
                full_path = get_path(filename)
                if os.path.exists(full_path):
                    try:
                        snd = pygame.mixer.Sound(full_path)
                        snd.set_volume(0.3)
                        self.bgm_sounds[key] = snd
                    except Exception as e:
                        print(f"BGM 로드 실패 ({filename}): {e}")

            load_bgm("TITLE", "bgm_intro.mp3")
            load_bgm("HOME", "bgm_home.mp3")
            load_bgm("OUTSIDE", "bgm_outside.mp3")
            load_bgm("SHOP", "bgm_shop.mp3")
            
        except Exception as e:
            print(f"사운드 시스템 초기화 실패: {e}")
            self.enabled = False
    
    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()
            
    def play_bgm(self, state):
        if not self.enabled: return
        
        target_key = "HOME"
        if state == "TITLE": target_key = "TITLE"
        elif state == "OUTSIDE": target_key = "OUTSIDE"
        elif state == "SHOP": target_key = "SHOP"
        elif state in ["HOME", "INVENTORY", "DAY_TRANSITION"]: target_key = "HOME"
        else: return 

        if self.current_bgm_key == target_key: return

        if self.current_bgm_key in self.bgm_sounds:
            self.bgm_sounds[self.current_bgm_key].fadeout(1000)
            
        if target_key in self.bgm_sounds:
            self.bgm_sounds[target_key].play(loops=-1, fade_ms=2000)
            self.current_bgm_key = target_key
            
    def stop_bgm(self):
        if self.enabled and self.current_bgm_key in self.bgm_sounds:
            self.bgm_sounds[self.current_bgm_key].stop()
            self.current_bgm_key = None

    # 심장 박동 제어
    def update_heartbeat(self, hp):
        if not self.enabled or "heartbeat" not in self.sounds: return

        # 체력(배고픔/목마름 중 낮은 값)이 30 이하일 때 재생
        if hp <= 30 and hp > 0:
            if not self.heartbeat_playing:
                self.sounds["heartbeat"].play(loops=-1)
                self.heartbeat_playing = True
        else:
            # 30 초과거나 사망(0 이하) 시 정지
            if self.heartbeat_playing:
                self.sounds["heartbeat"].stop()
                self.heartbeat_playing = False

    def stop_heartbeat(self):
        if self.heartbeat_playing and "heartbeat" in self.sounds:
            self.sounds["heartbeat"].stop()
            self.heartbeat_playing = False

# --- 게임 클래스 ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Coupang Survival: Bunker Edition")
        self.clock = pygame.time.Clock()
        
        self.player = Player()
        
        self.sound = SoundManager()
        self.sound.play_bgm("TITLE")
        
        self.effects = ui.EffectManager() 
        self.particles = self.effects.particles 
        
        self.intro_game = IntroRoulette()
        self.outdoor_game = OutdoorMinigame()
        
        self.state = "TITLE"
        self.btns = []
        
        self.scroll_y_inventory = 0
        self.scroll_y_log = 0
        
        self.unboxing_timer = 0
        self.unboxing_type = "eats"
        self.current_event = None
        self.acquired_item = None
        self.next_state = "HOME"
        
        self.fade_alpha = 255
        self.shake_timer = 0
        
        self.popup_info = {"title": "", "msg": "", "style": "default"}
        self.popup_next_state = "HOME"
        self.transition_timer = 0

    def change_state(self, new_state):
        self.state = new_state
        self.fade_alpha = 255 
        
        if new_state == "DAY_TRANSITION":
            self.sound.play("day_pass")
        else:
            self.sound.play("transition")
        
        self.sound.play_bgm(new_state)
        
        # 상태 변경 시 심장 소리 초기화
        if new_state == "RESULT":
            self.sound.stop_heartbeat()
        
        if new_state == "HOME":
            self.scroll_y_log = 99999 
            
        if new_state in ["DAY_TRANSITION", "RESULT", "INTRO_GAME"]:
             self.effects.clear_texts()

    def trigger_shake(self, duration=10):
        self.shake_timer = duration
        self.sound.play("alert")

    def show_popup(self, title, msg, next_state="HOME", style="default"):
        self.popup_info = {"title": title, "msg": msg, "style": style}
        self.popup_next_state = next_state
        self.change_state("MSG_POPUP")

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if self.state == "HOME":
                    if event.key == pygame.K_i: ActionHandler.handle_click(self, "go_inventory")
                    elif event.key == pygame.K_s: ActionHandler.handle_click(self, "go_shop")
                    elif event.key == pygame.K_o: ActionHandler.handle_click(self, "go_outside")
                    
                elif self.state == "INVENTORY":
                    if event.key in [pygame.K_ESCAPE, pygame.K_i]: ActionHandler.handle_click(self, "go_home")
                
                elif self.state == "SHOP":
                    if event.key == pygame.K_ESCAPE: ActionHandler.handle_click(self, "go_home")
                        
                elif self.state in ["EVENT_POPUP", "MSG_POPUP", "ITEM_GET"]:
                    if event.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE]:
                         if self.state == "EVENT_POPUP": ActionHandler.handle_click(self, "event_confirm")
                         elif self.state == "MSG_POPUP": ActionHandler.handle_click(self, "msg_popup_confirm")
                         elif self.state == "ITEM_GET": ActionHandler.handle_click(self, "item_get_confirm")

            if self.state == "INTRO_GAME" and self.intro_game.state == "FINISHED":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.player.apply_roulette_reward(self.intro_game.final_item)
                    self.sound.play("success")
                    self.change_state("DAY_TRANSITION")
            
            elif self.state == "OUTSIDE":
                self.outdoor_game.handle_input(event, self.sound)

            if event.type == pygame.MOUSEWHEEL:
                if self.state == "INVENTORY":
                    self.scroll_y_inventory = max(0, self.scroll_y_inventory - event.y * 30)
                elif self.state == "HOME":
                    mx, my = pygame.mouse.get_pos()
                    log_rect = pygame.Rect(30, SCREEN_HEIGHT - 210, 380, 180)
                    if log_rect.collidepoint(mx, my):
                        self.scroll_y_log -= event.y * 20

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "INVENTORY" and event.button == 3:
                    ActionHandler.handle_inventory_right_click(self, pygame.mouse.get_pos())
                elif event.button == 1:
                    pos = pygame.mouse.get_pos()
                    for btn in self.btns:
                        if btn.is_clicked(pos):
                            self.effects.particles.create(pos, btn.bg_color, count=10, speed_mult=1.2)
                            
                            if "buy_" in btn.action_id:
                                self.sound.play("cash")
                            else:
                                self.sound.play("click")
                                
                            ActionHandler.handle_click(self, btn.action_id)

    def update(self):
        # [수정] 심장 박동 소리 업데이트
        if self.state in ["HOME", "SHOP", "INVENTORY", "OUTSIDE"]:
            # Player 객체에 status나 hp 속성이 없으므로, 배고픔과 목마름 중 낮은 값을 사용
            #
            current_hp = min(self.player.hunger, self.player.thirst)
            self.sound.update_heartbeat(current_hp)
        else:
            self.sound.stop_heartbeat()

        if self.state == "DAY_TRANSITION":
            self.transition_timer += 1
            if self.transition_timer > 100: 
                self.transition_timer = 0
                self.state = "HOME"
                self.sound.play_bgm("HOME")

        if self.state not in ["TITLE", "GUIDE", "INTRO_GAME", "EVENT_POPUP", "ITEM_GET", "MSG_POPUP", "DAY_TRANSITION"] and (not self.player.alive or self.player.game_clear):
            self.state = "RESULT"
            
        if self.state == "INTRO_GAME":
            self.intro_game.update()
        elif self.state == "OUTSIDE":
            self.outdoor_game.update()

            
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 15)
            
        if self.shake_timer > 0:
            self.shake_timer -= 1
            
        self.effects.update()

    def draw(self):
        shake_x, shake_y = 0, 0
        if self.shake_timer > 0:
            shake_x = random.randint(-5, 5)
            shake_y = random.randint(-5, 5)
            
        draw_surf = self.screen.copy()

        self.btns = ui.draw_game_scene(self, draw_surf)
            
        if self.state == "INVENTORY": 
            ui.draw_inventory_tooltips(draw_surf, self)
        if self.unboxing_timer > 0: 
            self.draw_unboxing(draw_surf)
        
        self.effects.draw(draw_surf)
        
        if self.state in ["HOME", "SHOP", "INVENTORY", "OUTSIDE"]:
            self.effects.draw_vignette_overlay(draw_surf, self.player)

        if self.fade_alpha > 0:
            fade_s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade_s.fill(BLACK)
            fade_s.set_alpha(self.fade_alpha)
            draw_surf.blit(fade_s, (0, 0))

        self.screen.blit(draw_surf, (shake_x, shake_y))
        pygame.display.update()
        
    def draw_unboxing(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK); overlay.set_alpha(220)
        surface.blit(overlay, (0,0))
        cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
        offset = random.randint(-5, 5)
        
        if self.unboxing_type == "eats":
            ui.draw_item_icon(surface, "쿠팡이츠 배달통", cx-50+offset, cy-50+offset, 100)
        else:
            ui.draw_item_icon(surface, "쿠팡플레이", cx-50+offset, cy-50+offset, 100)
            
        self.unboxing_timer -= 1
        if self.unboxing_timer == 0:
            color = CP_GREEN if self.unboxing_type == "eats" else TXT_GOLD
            self.particles.create((cx, cy), color, 50, 3.0)
            self.sound.play("success")
            self.state = "ITEM_GET"

if __name__ == "__main__":
    game = Game()
    game.run()