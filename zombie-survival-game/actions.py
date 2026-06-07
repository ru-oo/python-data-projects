import sys
import random
import pygame
from config import *

class ActionHandler:
    @staticmethod
    def handle_click(game, aid):
        player = game.player
        sound = game.sound
        effects = game.effects 
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

        if aid == "quit":
            pygame.quit(); sys.exit()
        
        elif aid == "go_guide": game.change_state("GUIDE")
        elif aid == "start_intro": 
            game.change_state("INTRO_GAME")
            game.intro_game.start()
        elif aid == "go_home": game.change_state("HOME")
        elif aid == "go_inventory": 
            sound.play("open")
            game.change_state("INVENTORY")
        
        elif aid in ["go_shop", "go_outside"]:
            success, evt = player.try_consume_energy()
            if not success: 
                game.trigger_shake(5)
                effects.add_text(cx, cy, "행동력 부족!", TXT_WARN)
                return
            
            effects.add_text(800, 100, "-1 Energy", BAR_ENERGY)

            target_state = "SHOP" if aid == "go_shop" else "OUTSIDE"
            
            if evt:
                game.current_event = evt
                game.next_state = target_state
                sound.play("alert")
                effects.trigger_flash(TXT_WARN, 100)
                game.change_state("EVENT_POPUP")
            else:
                game.change_state(target_state)
                if target_state == "OUTSIDE": 
                    if player.weapon_buff:
                        player.weapon_buff = False 
                        game.outdoor_game.state = "SUCCESS" 
                        player.add_log("무기를 사용하여 위협을 손쉽게 제압했습니다!")
                    else:
                        game.outdoor_game.start_game()

        elif aid == "event_confirm":
            if game.current_event:
                money_change = game.current_event['money']
                if money_change != 0:
                    col = TXT_GOLD if money_change > 0 else TXT_WARN
                    prefix = "+" if money_change > 0 else ""
                    effects.add_text(cx, cy - 50, f"{prefix}{money_change} P", col, size=32)

                player.change_money(money_change)
                
                hunger_change = game.current_event.get('hunger', 0)
                mental_change = game.current_event.get('mental', 0)
                energy_change = game.current_event.get('energy', 0)
                
                if hunger_change < 0: effects.add_text(cx, cy, "배고픔 증가", TXT_WARN)
                if mental_change < 0: 
                    effects.add_text(cx, cy+30, "멘탈 붕괴", (200, 50, 200))
                    effects.trigger_flash((100, 0, 0), 150)
                
                player.update_status(hunger_change, 0, mental_change)
                player.energy = max(0, min(player.max_energy, player.energy + energy_change))
                
                evt_type = game.current_event.get('type', 'normal')
                if evt_type == "item_get":
                    item = random.choice(RARE_ITEMS + TRASH_ITEMS)
                    player.inventory.append(item)
                    player.add_log(f"이벤트 획득: {item}")
                    sound.play("success")
                    effects.add_text(cx, cy-80, f"GET: {item}", TXT_SUCCESS)
                elif evt_type == "item_lose":
                    if player.inventory:
                        item = random.choice(player.inventory)
                        player.inventory.remove(item)
                        player.add_log(f"이벤트 소실: {item}")
                        sound.play("fail")
                        effects.add_text(cx, cy-80, f"LOST: {item}", TXT_WARN)

                if game.current_event['money'] < 0 or hunger_change < 0 or mental_change < -10:
                    game.trigger_shake(10)

            game.change_state(game.next_state)
            if game.state == "OUTSIDE": 
                if player.weapon_buff:
                    player.weapon_buff = False
                    game.outdoor_game.state = "SUCCESS"
                    player.add_log("무기를 사용하여 위협을 손쉽게 제압했습니다!")
                else:
                    game.outdoor_game.start_game()
            
        elif aid == "item_get_confirm":
            game.change_state("SHOP")
            
        elif aid == "msg_popup_confirm":
            game.change_state(game.popup_next_state)

        elif aid == "sleep":
            # [수정] 수면 후 생존 여부 확인
            is_survived = player.sleep_and_reset()
            
            if is_survived:
                # 생존 시에만 다음 날 전환 화면으로 이동
                game.change_state("DAY_TRANSITION")
                sound.play("transition")
                # "ZZZ" 텍스트 제거 (Day 화면과 겹침 방지)
            else:
                # 사망 시 화면 전환 안함 -> main loop가 사망 감지 후 RESULT로 이동
                pass
        
        elif aid == "buy_food":
            cost = 800
            if player.discount_active: cost //= 2
            
            if player.money >= cost:
                player.change_money(-cost)
                effects.add_text(cx, cy, f"-{cost} P", TXT_WARN)
                
                item = random.choice(list(FOOD_EFFECTS.keys()))
                game.acquired_item = item
                player.food_bag.append(item)
                
                game.unboxing_timer = 60
                game.unboxing_type = "eats"
                sound.play("open")
            else: 
                player.add_log("잔액 부족")
                game.trigger_shake(5)
                effects.add_text(cx, cy, "돈이 부족합니다!", TXT_WARN)
            
        elif aid == "buy_mental":
            cost = 1000
            if player.discount_active: cost //= 2
            
            if player.money >= cost:
                player.change_money(-cost)
                player.update_status(0, 0, 40)
                effects.add_text(cx, cy, f"-{cost} P", TXT_WARN)
                effects.add_text(cx, cy-40, "멘탈 +40", BAR_MENTAL)
                
                player.add_log("쿠팡플레이 시청: 멘탈이 회복되었습니다.")
                sound.play("success")
                game.show_popup("시청 완료", "쿠팡플레이를 시청하여\n멘탈이 대폭(+40) 회복되었습니다.", next_state="SHOP", style="coupang")
            else: 
                player.add_log("잔액 부족")
                game.trigger_shake(5)
                effects.add_text(cx, cy, "돈이 부족합니다!", TXT_WARN)
            
        elif aid == "sell_all":
            if player.inventory:
                val = sum(2000 if i in RARE_ITEMS else 500 for i in player.inventory)
                player.change_money(val)
                player.inventory = []
                player.add_log(f"판매 완료: +{val}point")
                sound.play("success")
                effects.add_text(cx, cy, f"+{val} Point", TXT_GOLD, size=40)
                effects.trigger_flash(TXT_GOLD, 100)
                
                game.show_popup("정산 완료", f"물품을 모두 판매하여\n{val} 포인트를 획득했습니다.", next_state="SHOP", style="coupang")
            else:
                sound.play("fail")
                game.show_popup("알림", "포인트 교환할 물품이 없습니다.", next_state="SHOP", style="coupang")
                
        elif aid == "outside_reward":
            rand = random.random()
            if rand < 0.2: item = random.choice(EFFECT_ITEMS)
            elif rand < 0.5: item = random.choice(RARE_ITEMS)
            else: item = random.choice(TRASH_ITEMS)
                
            player.inventory.append(item)
            player.add_log(f"파밍 성공: {item}")
            sound.play("success")
            
            effects.add_text(cx, cy, f"획득: {item}", TXT_SUCCESS, size=30)
            effects.trigger_flash(WHITE, 150)
            
            game.change_state("HOME")
            
        elif aid == "outside_fail":
            dmg = random.randint(10, 30)
            player.update_status(-10, -10, -dmg)
            player.add_log(f"도주 중 부상: 체력 -10, 멘탈 -{dmg}")
            sound.play("fail")
            game.trigger_shake(15)
            
            effects.add_text(cx, cy, f"체력 -10", BAR_HP)
            effects.add_text(cx, cy+30, f"멘탈 -{dmg}", (200, 50, 200))
            effects.trigger_flash((200, 0, 0), 200)
            
            game.change_state("HOME")
            
        elif aid.startswith("eat_idx_"):
            idx = int(aid.split("_")[2])
            if idx < len(player.food_bag):
                target_name = player.food_bag[idx]
                player.food_bag.pop(idx) 
                
                eff = FOOD_EFFECTS.get(target_name, {})
                h, t, m = eff.get('hunger', 0), eff.get('thirst', 0), eff.get('mental', 0)
                
                player.update_status(h, t, m)
                player.add_log(f"{target_name} 섭취 완료")
                sound.play("eat")
                
                mx, my = pygame.mouse.get_pos()
                if h > 0: effects.add_text(mx, my-20, f"배고픔 +{h}", BAR_HP)
                if t > 0: effects.add_text(mx, my-45, f"목마름 +{t}", BAR_WATER)
                if m > 0: effects.add_text(mx, my-70, f"멘탈 +{m}", BAR_MENTAL)
                
                msg_lines = []
                if h > 0: msg_lines.append(f"배고픔 해소 +{h}")
                elif h < 0: msg_lines.append(f"배고픔 증가 {h}")
                if t > 0: msg_lines.append(f"목마름 해소 +{t}")
                elif t < 0: msg_lines.append(f"목마름 증가 {t}")
                if m > 0: msg_lines.append(f"멘탈 회복 +{m}")
                elif m < 0: msg_lines.append(f"멘탈 감소 {m}")
                
                full_msg = "\n".join(msg_lines) if msg_lines else "특이한 효과는 없었습니다."
                game.show_popup(f"[{target_name}] 섭취", full_msg, next_state="INVENTORY", style="inventory")
        
        elif aid.startswith("use_idx_"):
            idx = int(aid.split("_")[2])
            if idx < len(player.inventory):
                target = player.inventory[idx]
                
                if player.use_item(target):
                    sound.play("success")
                    mx, my = pygame.mouse.get_pos()
                    effects.add_text(mx, my, "USED!", TXT_SUCCESS)
                    
                    title = f"[{target}] 사용"
                    msg = "효과가 적용되었습니다."
                    if target in ["총", "야구방망이"]:
                        msg = "무기를 장착했습니다.\n다음 외출 시 위협을 자동으로 제압합니다."
                    elif target == "쿠팡 쿠폰":
                        msg = "할인 쿠폰을 적용했습니다.\n오늘 상점 물품이 50% 할인됩니다."
                    elif target in ITEM_EFFECTS:
                        eff = ITEM_EFFECTS[target]
                        lines = []
                        if "desc" in eff: lines.append(eff["desc"])
                        else:
                            if eff.get('energy'): lines.append(f"행동력 회복 +{eff['energy']}")
                            if eff.get('mental'): lines.append(f"멘탈 회복 +{eff['mental']}")
                        if lines: msg = "\n".join(lines)
                    
                    game.show_popup(title, msg, next_state="INVENTORY", style="inventory")
                else:
                    player.add_log("사용할 수 없는 아이템입니다.")
                    game.trigger_shake(5)
    
    # ... (handle_inventory_right_click 유지) ...
    @staticmethod
    def handle_inventory_right_click(game, mouse_pos):
        mx, my = mouse_pos
        cols, slot_sz, gap = 6, 100, 20
        start_x, start_y = 100, 160
        
        items = [{"type":"norm", "obj": i, "idx": idx} for idx, i in enumerate(game.player.inventory)] + \
                [{"type":"food", "obj": f, "idx": idx} for idx, f in enumerate(game.player.food_bag)]
        
        for i, item in enumerate(items):
            row, col = i // cols, i % cols
            x = start_x + col * (slot_sz + gap)
            y = start_y + row * (slot_sz + gap) - game.scroll_y_inventory
            
            rect = pygame.Rect(x, y, slot_sz, slot_sz)
            if 160 <= y <= 560 and rect.collidepoint(mx, my):
                if item['type'] == 'food':
                    ActionHandler.handle_click(game, f"eat_idx_{item['idx']}")
                else:
                    ActionHandler.handle_click(game, f"use_idx_{item['idx']}")
                break