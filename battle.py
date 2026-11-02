import pygame
import random
import sys
import math
from game_data import *

# =====================================================================
# PROJECTILE CLASS (คลาสจัดการกระสุนลูกบอล)
# =====================================================================
class Projectile:
    def __init__(self, x, y, target, damage, color, speed=300):
        self.x, self.y = float(x), float(y)
        self.target = target
        self.damage = damage
        self.color = color
        self.speed = speed
        self.alive = True

    def update(self, dt):
        # ลบกระสุนหากเป้าหมายตายหรือเลือดหมดก่อน
        if not self.target.alive or self.target.hp <= 0:
            self.alive = False
            return

        # คำนวณระยะห่างไปยังเป้าหมาย
        dx, dy = self.target.x - self.x, (self.target.y - 18) - self.y
        dist = math.hypot(dx, dy)
        step = self.speed * dt

        # ตรวจสอบว่ากระสุนถึงเป้าหมายยัง
        if dist <= step + 8:
            self.target.hp -= self.damage
            if self.target.hp <= 0:
                self.target.alive = False
            self.alive = False
        elif dist:
            self.x += dx / dist * step
            self.y += dy / dist * step

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 10)


# =====================================================================
# UNIT CLASS (คลาสตัวละครยูนิตในเกม)
# =====================================================================
class Unit:
    def __init__(self, x, team, unit_id):
        self.x = float(x)
        self.team = team
        self.unit_id = unit_id
        self.data = ALL_UNITS_DATABASE[unit_id]
        self.hp = self.data["hp"] 
        self.max_hp = self.hp
        self.attack_timer = random.uniform(0, 0.4)
        self.speed = self.data["speed"] 
        self.y = 390 + random.randint(-12, 12)
        self.alive = True

    def draw(self):
        unit_img = ASSETS.get(f"unit_{self.unit_id}")
        
        # วาดภาพตัวละครหรือรูปทรงสำรองถ้าไม่มีรูปภาพ
        if unit_img:
            img = unit_img if self.team == "player" else pygame.transform.flip(unit_img, True, False)
            screen.blit(img, (int(self.x - 25), int(self.y - 35)))
        else:
            color = self.data["color"] if self.team == "player" else (205, 75, 83)
            pygame.draw.circle(screen, color, (int(self.x), int(self.y - 23)), 15)
            pygame.draw.rect(screen, color, (int(self.x - 13), int(self.y - 12), 26, 24), border_radius=7)

        # วาดหลอดเลือด (HP Bar) ของยูนิต
        pygame.draw.rect(screen, (65, 65, 65), (int(self.x - 1), int(self.y - 42), 40, 5), border_radius=2)
        hpw = max(0, int(38 * self.hp / self.max_hp))
        pygame.draw.rect(screen, GREEN if self.team == "player" else RED, (int(self.x), int(self.y - 41), hpw, 3), border_radius=2)


# =====================================================================
# STAGE SELECT FUNCTION (หน้าจอเลือกด่าน)
# =====================================================================
def run_stage_select():
    while True:
        screen.fill((40, 45, 60))
        draw_text("เลือกด่านที่ต้องการเล่น", WIDTH // 2, 60, BIG, YELLOW_GOLD, center=True)

        stage_rects = []
        for i, stage in enumerate(STAGES):
            rect = pygame.Rect(200, 130 + i * 120, 600, 95)
            pygame.draw.rect(screen, WHITE, rect, border_radius=12)
            pygame.draw.rect(screen, ORANGE_BORDER, rect, 3, border_radius=12)
            
            draw_text(stage["name"], rect.x + 20, rect.y + 18, FONT, BLACK)
            draw_text(f"รางวัล: gold+{stage['gold_reward']} | ruby+{stage['ruby_reward']}", rect.x + 20, rect.y + 55, SMALL, (80, 140, 60))
            
            play_btn = pygame.Rect(rect.right - 140, rect.centery - 25, 120, 50)
            pygame.draw.rect(screen, GREEN, play_btn, border_radius=10)
            draw_text("Play", play_btn.centerx, play_btn.centery, FONT, WHITE, center=True)
            
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


# =====================================================================
# MAIN BATTLE GAME FUNCTION (ระบบเกมหลักในการต่อสู้)
# =====================================================================
def run_battle_game(stage_data):
    # กำหนดค่าเริ่มต้นของเกม
    player_base, enemy_base = 70, WIDTH - 70
    player_hp, enemy_hp = 500, stage_data["enemy_hp"] #เลือดป้อมเด้อ
    player_max_hp, enemy_max_hp = 500, stage_data["enemy_hp"]
    minerals, production_level = 150, 1
    enemy_spawn_timer = stage_data["spawn_timer"]
    
    units = []
    projectiles = []
    game_over = None
    reward_given = False

    # ดึงค่าตัวละคร 3 ตัวที่ถูกเลือกใช้งาน
    team_units = PLAYER_DATA["loadout"]
    unit_buttons = [pygame.Rect(24 + i * 200, 510, 185, 76) for i in range(3)]
    cooldown_timers = [0.0, 0.0, 0.0]

    upgrade_rect = pygame.Rect(650, 515, 170, 68)
    menu_rect = pygame.Rect(400, 380, 200, 60)

    while True:
        dt = min(clock.tick(60) / 1000.0, 0.05)

        # อัปเดตเวลา Cooldown ของปุ่มตัวละคร
        for i in range(3):
            if cooldown_timers[i] > 0:
                cooldown_timers[i] -= dt

        # จัดการ Event การคลิกเมาส์และปิดเกม
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if game_over: #เกมจบ กดกลับหน้าหลัก
                    if menu_rect.collidepoint(pos):
                        return
                else: 
                    # ตรวจสอบการกดปุ่มปล่อยตัวละครออกไปสู้
                    for i, rect in enumerate(unit_buttons):
                        u_id = team_units[i]
                        if u_id is not None and rect.collidepoint(pos):
                            u_data = ALL_UNITS_DATABASE[u_id]
                            if minerals >= u_data["cost"] and cooldown_timers[i] <= 0: 
                                minerals -= u_data["cost"]
                                units.append(Unit(player_base + 42, "player", u_id))
                                cooldown_timers[i] = u_data["cooldown"]

                    # ตรวจสอบการกดปุ่มอัปเกรดแร่
                    if upgrade_rect.collidepoint(pos):
                        cost = 75 * production_level
                        if minerals >= cost:
                            minerals -= cost
                            production_level += 1

        if not game_over:
            # ระบบผลิตแร่อัตโนมัติ
            production_interval = max(0.65, 2.5 / (1 + (production_level - 1) * 0.65))
            minerals += (25 / production_interval) * dt

            # ระบบเกิดยูนิตฝ่ายศัตรู
            enemy_spawn_timer -= dt
            if enemy_spawn_timer <= 0:
                enemy_spawn_timer = stage_data["spawn_timer"]
                kind = random.choices([5, 6, 7, 8], weights=stage_data["enemy_weights"])[0]
                units.append(Unit(enemy_base - 42, "enemy", kind))

            # อัปเดตการเคลื่อนที่และการโจมตีของยูนิตทั้งหมด
            for unit in units:
                if not unit.alive: 
                    continue
                
                enemies = [u for u in units if u.alive and u.team != unit.team] #ทุกคนที่ไม่ใช่พวกของ unit
                targets = [u for u in enemies if (u.x >= unit.x if unit.team == "player" else u.x <= unit.x)] #เลือกเฉพาะศัตรูที่อยู่ด้านหน้าของตัวละครเรา
                nearest = min(targets, key=lambda u: abs(u.x - unit.x)) if targets else None
                dist = abs(nearest.x - unit.x) if nearest else (enemy_base - unit.x if unit.team == "player" else unit.x - player_base) #ระยะจากเราไปเป้าหมาย หรือ จากเราไปฐานเขา

                
                if dist > unit.data["range"]: #เดิน
                    unit.x += unit.speed * dt * (1 if unit.team == "player" else -1)
                else: #โจมตี
                    unit.attack_timer -= dt
                    if unit.attack_timer <= 0:
                        unit.attack_timer = unit.data["cooldown"]
                        if nearest: #ตีคน
                            proj_color = (0, 200, 255) if unit.team == "player" else (255, 100, 100)
                            projectiles.append(Projectile(unit.x, unit.y - 23, nearest, unit.data["damage"], proj_color))
                        else: #ตีป้อม
                            if unit.team == "player": 
                                enemy_hp -= unit.data["damage"]
                            else: 
                                player_hp -= unit.data["damage"]

            # อัปเดตตำแหน่งกระสุนและกรองเอากระสุนที่ใช้งานอยู่ออก
            for proj in projectiles:
                proj.update(dt)
            projectiles = [p for p in projectiles if p.alive]
            units = [u for u in units if u.alive]

            # ตรวจสอบเงื่อนไขแพ้-ชนะ
            if enemy_hp <= 0:
                game_over = "WIN"
                if not reward_given:
                    PLAYER_DATA["coins"] += stage_data["gold_reward"]
                    PLAYER_DATA["rubies"] += stage_data["ruby_reward"]
                    reward_given = True
            elif player_hp <= 0:
                game_over = "LOSE"

        # วาดพื้นหลังฉากเกม
        bg_img = ASSETS.get(stage_data["bg_key"])
        if bg_img:
            screen.blit(bg_img, (0, 0))
        else:
            screen.fill(SKY)
            pygame.draw.rect(screen, GRASS, (0, 420, WIDTH, 100))

        # วาดฐานทัพ, ยูนิต และกระสุน
        pygame.draw.rect(screen, BLUE, (player_base - 30, 300, 60, 135), border_radius=10)
        pygame.draw.rect(screen, RED, (enemy_base - 30, 300, 60, 135), border_radius=10)

        pygame.draw.rect(screen, (65, 65, 65), (int(player_base - 21), int(275), 40, 5), border_radius=2)
        hpp = max(0, int(38 * player_hp / player_max_hp))
        pygame.draw.rect(screen, GREEN , (int(player_base-20), int(276), hpp, 3), border_radius=2)

        pygame.draw.rect(screen, (65, 65, 65), (int(enemy_base - 21), int(275), 40, 5), border_radius=2)
        hpe = max(0, int(38 * enemy_hp / enemy_max_hp))
        pygame.draw.rect(screen, RED , (int(enemy_base-20), int(276), hpe, 3), border_radius=2)
        
        for unit in units: 
            unit.draw()
        for proj in projectiles: 
            proj.draw()

        # วาด UI แผงควบคุมด้านล่าง (แร่, ปุ่มยูนิต, ปุ่มอัปเกรด)
        pygame.draw.rect(screen, DARK_PANEL, (0, 490, WIDTH, 130))
        draw_text(f"แร่: {int(minerals)}", 450, 20, BIG, YELLOW_GOLD)

        # วาดปุ่มตัวละครพร้อมจัดการสถานะติดคูลดาวน์หรือแร่ไม่พอ
        for i, rect in enumerate(unit_buttons):
            u_id = team_units[i]
            if u_id is not None:
                data = ALL_UNITS_DATABASE[u_id]
                pygame.draw.rect(screen, data["color"], rect, border_radius=9)
                pygame.draw.rect(screen, (255, 255, 255) if ALL_UNITS_DATABASE[u_id]["stars"] == 1 else YELLOW_GOLD, rect, width=2, border_radius=9)

                on_cooldown = cooldown_timers[i] > 0
                not_enough_minerals = minerals < data["cost"]

                # ใส่เอฟเฟกต์สีดำทับปุ่มถ้าไม่สามารถกดได้
                if on_cooldown or not_enough_minerals:
                    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 150))
                    screen.blit(overlay, rect.topleft)

                if on_cooldown:
                    draw_text(f"{cooldown_timers[i]:.1f}s", rect.centerx, rect.centery, FONT, WHITE, center=True)

                draw_text(f"{data['name']}", rect.centerx, rect.centery - 10, FONT, WHITE, center=True)
                draw_text(f"ใช้ {data['cost']} แร่", rect.centerx, rect.centery + 12, SMALL, YELLOW_GOLD, center=True)

        # วาดปุ่มอัปเกรดแร่
        upgrade_cost = 75 * production_level
        pygame.draw.rect(screen, YELLOW_GOLD, upgrade_rect, border_radius=9)
        draw_text(f"อัปเกรดแร่ (Lv.{production_level})", upgrade_rect.centerx, upgrade_rect.centery - 10, FONT, BLACK, center=True)
        draw_text(f"(ใช้ {upgrade_cost} แร่)", upgrade_rect.centerx, upgrade_rect.centery + 12, SMALL, DARK_PANEL, center=True)

        # หน้าต่างแสดงผลเมื่อจบเกม (ชนะ / แพ้)
        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            if game_over == "WIN":
                draw_text("ชนะ!", WIDTH // 2, 220, BIG, YELLOW_GOLD, center=True)
                draw_text(f"ได้รับ: Coin +{stage_data['gold_reward']} | ruby +{stage_data['ruby_reward']}", WIDTH // 2, 280, FONT, WHITE, center=True)
            else:
                draw_text("แพ้!", WIDTH // 2, 230, BIG, RED, center=True)

            pygame.draw.rect(screen, BLUE, menu_rect, border_radius=10)
            draw_text("กลับหน้าหลัก", menu_rect.centerx, menu_rect.centery, FONT, WHITE, center=True)

        pygame.display.flip()