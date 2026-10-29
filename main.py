import pygame
import random
import math
import sys
from game_data import *
from team import run_team_screen
from battle import run_stage_select

# Gacha System Logic & Animation
# ==========================================
def draw_gacha_animation(pull_count):
    # อนิเมชั่นสุ่มตัวละคร
    start_time = pygame.time.get_ticks()
    duration = 2000 # 2 วินาที
    
    results = []
    # กำหนดเรทสุ่ม: 1 ดาว (70%), 2 ดาว (30%)
    for _ in range(pull_count):
        rand = random.random()
        if rand < 0.70:
            chosen = random.choice([u for u in ALL_UNITS_DATABASE if u["stars"] == 1])
        else:
            chosen = random.choice([u for u in ALL_UNITS_DATABASE if u["stars"] == 2])
        results.append(chosen)
        if chosen["id"] not in PLAYER_DATA["inventory"]:
            PLAYER_DATA["inventory"].append(chosen["id"])

    while pygame.time.get_ticks() - start_time < duration:
        screen.fill(BLACK)
        elapsed = (pygame.time.get_ticks() - start_time) / 1000.0
        
        # วาดวงเวทเอฟเฟกต์หมุน
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        radius = int(80 + math.sin(elapsed * 10) * 20)
        pygame.draw.circle(screen, YELLOW_GOLD, (center_x, center_y), radius, 4)
        pygame.draw.circle(screen, PURPLE, (center_x, center_y), radius + 30, 2)
        
        draw_text("🔮 กำลังสุ่มอัญเชิญเรนเจอร์...", center_x, center_y + 160, BIG, YELLOW_GOLD, center=True)
        
        pygame.display.flip()
        clock.tick(60)

    return results

# ==========================================
# Main Lobby Screen
# ==========================================
def main_lobby():
    active_tab = None
    gacha_result = None  # สำหรับแสดงหน้าสรุปผลสุ่ม

    while True:
        if ASSETS["bg_lobby"]:
            screen.blit(ASSETS["bg_lobby"], (0, 0))
        else:
            screen.fill(SKY)
            pygame.draw.rect(screen, (220, 150, 40), (0, 260, WIDTH, 360))

        draw_top_bar()

        # ปุ่มสเตจหลัก
        stage_btn_rect = pygame.Rect(380, 140, 240, 130)
        if ASSETS["btn_stage"]:
            screen.blit(ASSETS["btn_stage"], (380, 140))
        else:
            pygame.draw.rect(screen, (90, 85, 80), stage_btn_rect, border_radius=20)
            pygame.draw.rect(screen, ORANGE_BORDER, stage_btn_rect, 5, border_radius=20)
            draw_text("สเตจหลัก", stage_btn_rect.centerx, stage_btn_rect.centery, BIG, YELLOW_GOLD, center=True)

        # วาดตัวละครใน Loadout ปัจจุบันยืนโชว์
        pedestal_x = [280, 500, 720]
        for i, slot_unit_id in enumerate(PLAYER_DATA["loadout"]):
            x = pedestal_x[i]
            y = 380
            pygame.draw.ellipse(screen, (120, 200, 240), (x - 45, y, 90, 25))
            if slot_unit_id is not None:
                unit_data = ALL_UNITS_DATABASE[slot_unit_id]
                unit_img = ASSETS.get(f"unit_{slot_unit_id}")
                if unit_img:
                    screen.blit(unit_img, (x - 25, y - 45))
                else:
                    pygame.draw.circle(screen, unit_data["color"], (x, y - 20), 20)

        nav_buttons = draw_bottom_navigation(active_tab)

        # Popup สำหรับ Tabs
        if active_tab:
            pop_rect = pygame.Rect(120, 90, 760, 400)
            pygame.draw.rect(screen, WHITE, pop_rect, border_radius=15)
            pygame.draw.rect(screen, ORANGE_BORDER, pop_rect, 4, border_radius=15)
            
            close_btn = pygame.Rect(pop_rect.right - 45, pop_rect.top + 10, 35, 35)
            pygame.draw.rect(screen, RED, close_btn, border_radius=8)
            draw_text("X", close_btn.centerx, close_btn.centery, FONT, WHITE, center=True)

            # --- TAB 2: กาชา (GACHA) ---
            if active_tab == "GACHA":
                draw_text("🎰 สุ่มอัญเชิญเรนเจอร์ (Gacha)", pop_rect.centerx, pop_rect.top + 30, BIG, BLACK, center=True)
                draw_text("โอกาสได้รับ: ⭐1 ดาว (70%) | ⭐2 ดาว (30%)", pop_rect.centerx, pop_rect.top + 75, FONT, (80, 80, 80), center=True)

                gacha_1_btn = pygame.Rect(pop_rect.centerx - 220, pop_rect.top + 200, 180, 70)
                pygame.draw.rect(screen, GREEN if PLAYER_DATA["rubies"] >= 10 else (180, 180, 180), gacha_1_btn, border_radius=12)
                draw_text("สุ่ม 1 ครั้ง", gacha_1_btn.centerx, gacha_1_btn.centery - 12, FONT, WHITE, center=True)
                draw_text("💎 10", gacha_1_btn.centerx, gacha_1_btn.centery + 15, FONT, YELLOW_GOLD, center=True)

                gacha_10_btn = pygame.Rect(pop_rect.centerx + 40, pop_rect.top + 200, 180, 70)
                pygame.draw.rect(screen, PURPLE if PLAYER_DATA["rubies"] >= 100 else (180, 180, 180), gacha_10_btn, border_radius=12)
                draw_text("สุ่ม 10 ครั้ง", gacha_10_btn.centerx, gacha_10_btn.centery - 12, FONT, WHITE, center=True)
                draw_text("💎 100", gacha_10_btn.centerx, gacha_10_btn.centery + 15, FONT, YELLOW_GOLD, center=True)

            # --- TAB 3: อัปเกรด (UPGRADE) ---
            elif active_tab == "UPGRADE":
                draw_text("⚡ อัปเกรดพลังโจมตีเรนเจอร์", pop_rect.centerx, pop_rect.top + 30, BIG, BLACK, center=True)
                for idx, u_id in enumerate(PLAYER_DATA["inventory"]):
                    u = ALL_UNITS_DATABASE[u_id]
                    y_pos = pop_rect.top + 90 + idx * 75
                    draw_text(f"{u['name']} (★{u['stars']}) - Atk: {u['damage']}", pop_rect.left + 50, y_pos, FONT, BLACK)
                    
                    up_btn = pygame.Rect(pop_rect.right - 220, y_pos - 5, 160, 40)
                    pygame.draw.rect(screen, YELLOW_GOLD if PLAYER_DATA["coins"] >= 200 else (180, 180, 180), up_btn, border_radius=8)
                    draw_text("อัปแรง (+2) 🪙200", up_btn.centerx, up_btn.centery, SMALL, BLACK, center=True)

        # Popup สรุปผลการสุ่มกาชา
        if gacha_result:
            res_rect = pygame.Rect(200, 120, 600, 380)
            pygame.draw.rect(screen, WHITE, res_rect, border_radius=15)
            pygame.draw.rect(screen, YELLOW_GOLD, res_rect, 4, border_radius=15)
            
            draw_text("🎉 ยินดีด้วย! คุณได้รับ:", res_rect.centerx, res_rect.top + 25, BIG, BLACK, center=True)
            
            # วาดการ์ดแสดงผล
            for i, res in enumerate(gacha_result[:10]): # แสดงไม่เกิน 10 ตัว
                row = i // 5
                col = i % 5
                cx = res_rect.left + 50 + col * 105
                cy = res_rect.top + 80 + row * 110
                
                c_rect = pygame.Rect(cx, cy, 90, 95)
                pygame.draw.rect(screen, (240, 245, 250), c_rect, border_radius=8)
                draw_text(res["name"], c_rect.centerx, c_rect.top + 15, SMALL, BLACK, center=True)
                draw_text("★" * res["stars"], c_rect.centerx, c_rect.top + 40, SMALL, ORANGE_BORDER, center=True)

            close_res_btn = pygame.Rect(res_rect.centerx - 80, res_rect.bottom - 55, 160, 42)
            pygame.draw.rect(screen, GREEN, close_res_btn, border_radius=10)
            draw_text("ตกลง", close_res_btn.centerx, close_res_btn.centery, FONT, WHITE, center=True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                if gacha_result:
                    close_res_btn = pygame.Rect(420, 445, 160, 42)
                    if close_res_btn.collidepoint(pos):
                        gacha_result = None
                elif active_tab:
                    close_btn = pygame.Rect(835, 100, 35, 35)
                    if close_btn.collidepoint(pos):
                        active_tab = None
                    
                    elif active_tab == "GACHA":
                        g1 = pygame.Rect(260, 290, 180, 70)
                        g10 = pygame.Rect(520, 290, 180, 70)
                        if g1.collidepoint(pos) and PLAYER_DATA["rubies"] >= 10:
                            PLAYER_DATA["rubies"] -= 10
                            gacha_result = draw_gacha_animation(1)
                        elif g10.collidepoint(pos) and PLAYER_DATA["rubies"] >= 100:
                            PLAYER_DATA["rubies"] -= 100
                            gacha_result = draw_gacha_animation(10)

                    elif active_tab == "UPGRADE":
                        for idx, u_id in enumerate(PLAYER_DATA["inventory"]):
                            up_btn = pygame.Rect(660, 175 + idx * 75, 160, 40)
                            if up_btn.collidepoint(pos) and PLAYER_DATA["coins"] >= 200:
                                PLAYER_DATA["coins"] -= 200
                                ALL_UNITS_DATABASE[u_id]["damage"] += 2
                else:
                    if stage_btn_rect.collidepoint(pos):
                        run_stage_select()
                    for rect, item_id in nav_buttons:
                        if rect.collidepoint(pos):
                            if item_id == "TEAM":
                                run_team_screen()      # เปลี่ยนไปหน้า team screen
                            else:
                                active_tab = item_id

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main_lobby()