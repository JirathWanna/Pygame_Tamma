import pygame
import random
import sys
from game_data import *

# Stage Select Screen
# ==========================================
def run_stage_select():
    while True:
        screen.fill((40, 45, 60))
        draw_text("🗺️ เลือกด่านที่ต้องการเล่น", WIDTH//2, 60, BIG, YELLOW_GOLD, center=True)

        stage_rects = []
        for i, stage in enumerate(STAGES):
            rect = pygame.Rect(200, 130 + i * 120, 600, 95)
            pygame.draw.rect(screen, WHITE, rect, border_radius=12)
            pygame.draw.rect(screen, ORANGE_BORDER, rect, 3, border_radius=12)
            
            draw_text(stage["name"], rect.x + 20, rect.y + 18, FONT, BLACK)
            draw_text(f"รางวัล: 🪙+{stage['gold_reward']} | 💎+{stage['ruby_reward']}", rect.x + 20, rect.y + 55, SMALL, (80, 140, 60))
            
            play_btn = pygame.Rect(rect.right - 140, rect.centery - 25, 120, 50)
            pygame.draw.rect(screen, GREEN, play_btn, border_radius=10)
            draw_text("เข้าเล่น ⚔️", play_btn.centerx, play_btn.centery, FONT, WHITE, center=True)
            
            stage_rects.append((play_btn, stage))

        back_rect = pygame.Rect(50, 40, 120, 45)
        pygame.draw.rect(screen, RED_TAG, back_rect, border_radius=10)
        draw_text("‹ กลับ", back_rect.centerx, back_rect.centery, FONT, WHITE, center=True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(event.pos):
                    return
                for btn, stage in stage_rects:
                    if btn.collidepoint(event.pos):
                        run_battle_game(stage)

        pygame.display.flip()
        clock.tick(60)

# ==========================================
# Main Battle Game (เกมหลัก)
# ==========================================
class Unit:
    def __init__(self, x, team, unit_id):
        self.x = float(x)
        self.team = team
        self.unit_id = unit_id
        self.data = ALL_UNITS_DATABASE[unit_id]
        self.hp = 100 if team == "player" else 85
        self.max_hp = self.hp
        self.attack_timer = random.uniform(0, 0.4)
        self.speed = 27 if team == "player" else 23
        self.y = 390 + random.randint(-12, 12)
        self.alive = True

    def draw(self):
        unit_img = ASSETS.get(f"unit_{self.unit_id}")
        if unit_img:
            img = unit_img if self.team == "player" else pygame.transform.flip(unit_img, True, False)
            screen.blit(img, (int(self.x - 25), int(self.y - 35)))
        else:
            color = self.data["color"] if self.team == "player" else (205, 75, 83)
            pygame.draw.circle(screen, color, (int(self.x), int(self.y - 23)), 15)
            pygame.draw.rect(screen, color, (int(self.x - 13), int(self.y - 12), 26, 24), border_radius=7)

        pygame.draw.rect(screen, (65, 65, 65), (int(self.x - 20), int(self.y - 42), 40, 5), border_radius=2)
        hpw = max(0, int(38 * self.hp / self.max_hp))
        pygame.draw.rect(screen, GREEN if self.team == "player" else RED, (int(self.x - 19), int(self.y - 41), hpw, 3), border_radius=2)

def run_battle_game(stage_data):
    player_base, enemy_base = 70, WIDTH - 70
    player_hp, enemy_hp = 500, stage_data["enemy_hp"]
    minerals, production_level = 100, 1
    production_timer = 0.0
    enemy_spawn_timer = stage_data["spawn_timer"]
    
    units = []
    game_over = None
    reward_given = False

    # โหลดตัวละครในทีม 3 ตัวมาสร้างปุ่ม
    team_units = PLAYER_DATA["loadout"]
    unit_buttons = [pygame.Rect(24 + i * 200, 510, 185, 76) for i in range(3)]
    
    # พารามิเตอร์ Cooldown ของปุ่มส่งตัวละคร
    cooldown_timers = [0.0, 0.0, 0.0]

    upgrade_rect = pygame.Rect(650, 515, 170, 68)
    menu_rect = pygame.Rect(400, 380, 200, 60)

    while True:
        dt = min(clock.tick(60) / 1000.0, 0.05)

        # อัปเดต Cooldown
        for i in range(3):
            if cooldown_timers[i] > 0:
                cooldown_timers[i] -= dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if game_over:
                    if menu_rect.collidepoint(pos):
                        return
                else:
                    # กดที่ปุ่มตัวละครเพื่อส่งทันที
                    for i, rect in enumerate(unit_buttons):
                        u_id = team_units[i]
                        if u_id is not None and rect.collidepoint(pos):
                            u_data = ALL_UNITS_DATABASE[u_id]
                            if minerals >= u_data["cost"] and cooldown_timers[i] <= 0:
                                minerals -= u_data["cost"]
                                units.append(Unit(player_base + 42, "player", u_id))
                                cooldown_timers[i] = u_data["cooldown"] # เริ่มนับ Cooldown

                    # ปุ่มอัปเกรดแร่
                    if upgrade_rect.collidepoint(pos):
                        cost = 75 * production_level
                        if minerals >= cost:
                            minerals -= cost
                            production_level += 1

        if not game_over:
            production_timer += dt
            if production_timer >= max(0.65, 2.5 / (1 + (production_level - 1) * 0.65)):
                production_timer = 0.0
                minerals += 50

            enemy_spawn_timer -= dt
            if enemy_spawn_timer <= 0:
                enemy_spawn_timer = stage_data["spawn_timer"]
                kind = random.choices([0, 1, 2], weights=stage_data["enemy_weights"])[0]
                units.append(Unit(enemy_base - 42, "enemy", kind))

            for unit in units:
                if not unit.alive: continue
                enemies = [u for u in units if u.alive and u.team != unit.team]
                targets = [u for u in enemies if (u.x >= unit.x if unit.team == "player" else u.x <= unit.x)]
                nearest = min(targets, key=lambda u: abs(u.x - unit.x)) if targets else None
                dist = abs(nearest.x - unit.x) if nearest else (enemy_base - unit.x if unit.team == "player" else unit.x - player_base)

                if dist > unit.data["range"]:
                    unit.x += unit.speed * dt * (1 if unit.team == "player" else -1)
                else:
                    unit.attack_timer -= dt
                    if unit.attack_timer <= 0:
                        unit.attack_timer = unit.data["cooldown"]
                        if nearest:
                            nearest.hp -= unit.data["damage"]
                            if nearest.hp <= 0: nearest.alive = False
                        else:
                            if unit.team == "player": enemy_hp -= unit.data["damage"]
                            else: player_hp -= unit.data["damage"]

            units = [u for u in units if u.alive]

            if enemy_hp <= 0:
                game_over = "WIN"
                if not reward_given:
                    PLAYER_DATA["coins"] += stage_data["gold_reward"]
                    PLAYER_DATA["rubies"] += stage_data["ruby_reward"]
                    reward_given = True
            elif player_hp <= 0:
                game_over = "LOSE"

        # Background
        bg_img = ASSETS.get(stage_data["bg_key"])
        if bg_img:
            screen.blit(bg_img, (0, 0))
        else:
            screen.fill(SKY)
            pygame.draw.rect(screen, GRASS, (0, 420, WIDTH, 100))

        # Bases & Units
        pygame.draw.rect(screen, BLUE, (player_base - 30, 300, 60, 135), border_radius=10)
        pygame.draw.rect(screen, RED, (enemy_base - 30, 300, 60, 135), border_radius=10)
        for unit in units: unit.draw()

        # UI Panel ด้านล่าง
        pygame.draw.rect(screen, DARK_PANEL, (0, 490, WIDTH, 130))
        draw_text(f"แร่: {minerals}", 450, 20, BIG, YELLOW_GOLD)

        # วาดปุ่มส่งตัวละครทันทีพร้อม Cooldown Overlay
        for i, rect in enumerate(unit_buttons):
            u_id = team_units[i]
            if u_id is not None:
                data = ALL_UNITS_DATABASE[u_id]
                pygame.draw.rect(screen, data["color"], rect, border_radius=9)
                draw_text(f"{data['name']}", rect.centerx, rect.centery - 10, FONT, WHITE, center=True)
                draw_text(f"ใช้ {data['cost']} แร่", rect.centerx, rect.centery + 12, SMALL, YELLOW_GOLD, center=True)
                
                # แสดงแอนิเมชัน Cooldown สีเทา
                if cooldown_timers[i] > 0:
                    cd_ratio = cooldown_timers[i] / data["cooldown"]
                    cd_rect = pygame.Rect(rect.x, rect.y, rect.width, int(rect.height * cd_ratio))
                    s = pygame.Surface((rect.width, int(rect.height * cd_ratio)), pygame.SRCALPHA)
                    s.fill((0, 0, 0, 160))
                    screen.blit(s, (rect.x, rect.y))
                    draw_text(f"{cooldown_timers[i]:.1f}s", rect.centerx, rect.centery, FONT, WHITE, center=True)

        # ปุ่มอัปเกรดแร่พร้อมบอกราคา
        upgrade_cost = 75 * production_level
        pygame.draw.rect(screen, YELLOW_GOLD, upgrade_rect, border_radius=9)
        draw_text(f"อัปเกรดแร่", upgrade_rect.centerx, upgrade_rect.centery - 10, FONT, BLACK, center=True)
        draw_text(f"(ใช้ {upgrade_cost} แร่)", upgrade_rect.centerx, upgrade_rect.centery + 12, SMALL, DARK_PANEL, center=True)

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            if game_over == "WIN":
                draw_text("🏆 ชนะแล้ว!", WIDTH//2, 220, BIG, YELLOW_GOLD, center=True)
                draw_text(f"ได้รับ: 🪙 +{stage_data['gold_reward']} | 💎 +{stage_data['ruby_reward']}", WIDTH//2, 280, FONT, WHITE, center=True)
            else:
                draw_text("💀 แพ้แล้ว!", WIDTH//2, 230, BIG, RED, center=True)

            pygame.draw.rect(screen, BLUE, menu_rect, border_radius=10)
            draw_text("กลับหน้าหลัก", menu_rect.centerx, menu_rect.centery, FONT, WHITE, center=True)

        pygame.display.flip()
