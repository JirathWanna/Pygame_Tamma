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
# UNIT CLASSES 
# =====================================================================
class Unit:
    """คลาสแม่: เก็บคุณสมบัติและพฤติกรรมพื้นฐานที่ทุกยูนิตใช้ร่วมกัน"""

    team = None
    direction = 0
    hp_color = WHITE
    projectile_color = WHITE
    flip_image = False

    def __init__(self, x, unit_id):
        self.x = float(x)
        self.unit_id = unit_id
        self.data = ALL_UNITS_DATABASE[unit_id]

        self.hp = self.data["hp"]
        self.max_hp = self.hp
        self.attack_timer = random.uniform(0, 0.4)
        self.speed = self.data["speed"]
        self.y = 390 + random.randint(-12, 12)
        self.alive = True

    def move(self, dt):
        """เคลื่อนที่ตามทิศทางที่คลาสลูกกำหนด"""
        self.x += self.speed * dt * self.direction

    def draw(self):
        unit_img = ASSETS.get(f"unit_{self.unit_id}")

        # วาดภาพตัวละคร หรือใช้รูปทรงสำรองถ้าไม่มีรูป
        if unit_img:
            img = pygame.transform.flip(unit_img, True, False) if self.flip_image else unit_img
            screen.blit(img, (int(self.x - 25), int(self.y - 35)))
        else:
            color = self.data["color"] if self.team == "player" else (205, 75, 83)
            pygame.draw.circle(screen, color, (int(self.x), int(self.y - 23)), 15)
            pygame.draw.rect(screen, color, (int(self.x - 13), int(self.y - 12), 26, 24), border_radius=7)

        # วาดหลอดเลือด (HP Bar) ของยูนิต
        pygame.draw.rect(screen, (65, 65, 65), (int(self.x - 1), int(self.y - 42), 40, 5), border_radius=2)
        hpw = max(0, int(38 * self.hp / self.max_hp))
        pygame.draw.rect(screen, self.hp_color, (int(self.x), int(self.y - 41), hpw, 3), border_radius=2)

class PlayerUnit(Unit):
    """คลาสลูกของยูนิตฝ่ายผู้เล่น"""
    team = "player"
    direction = 1
    hp_color = GREEN
    projectile_color = (0, 200, 255)
    flip_image = False

class EnemyUnit(Unit):
    """คลาสลูกของยูนิตฝ่ายศัตรู"""
    team = "enemy"
    direction = -1
    hp_color = RED
    projectile_color = (255, 100, 100)
    flip_image = True

# =====================================================================
# GAME CLASS 
# =====================================================================
class Game:
    def __init__(self, stage_data):
        self.stage_data = stage_data
        
        # ตำแหน่งและสถานะป้อม
        self.player_base = 70
        self.enemy_base = WIDTH - 70
        self.player_hp = 500
        self.player_max_hp = 500
        self.enemy_hp = stage_data["enemy_hp"]
        self.enemy_max_hp = stage_data["enemy_hp"]

        # ระบบแร่และทรัพยากร
        self.minerals = 150
        self.production_level = 1
        self.max_minerals = 150

        # ตัวจัดการเวลาและศัตรู
        self.enemy_spawn_timer = stage_data["spawn_timer"]
        
        # รายการยูนิตและกระสุน
        self.units = []
        self.projectiles = []

        # สถานะเกม
        self.game_over = None
        self.reward_given = False
        self.paused = False

        # ข้อมูลตัวละครและการกดปุ่ม
        self.team_units = PLAYER_DATA["loadout"]
        self.unit_buttons = [pygame.Rect(24 + i * 200, 510, 185, 76) for i in range(3)]
        self.cooldown_timers = [0.0, 0.0, 0.0]

        # ปุ่ม UI ต่างๆ
        self.upgrade_rect = pygame.Rect(650, 515, 170, 68)
        self.menu_rect = pygame.Rect(400, 380, 200, 60)
        self.pause_rect = pygame.Rect(WIDTH - 125, 20, 100, 42)
        self.resume_rect = pygame.Rect(WIDTH // 2 - 110, 270, 220, 48)
        self.restart_rect = pygame.Rect(WIDTH // 2 - 110, 330, 220, 48)
        self.pause_home_rect = pygame.Rect(WIDTH // 2 - 110, 390, 220, 48)

    def handle_events(self):
        """จัดการ Event การคลิกเมาส์และปิดเกม"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if self.game_over:
                    if self.menu_rect.collidepoint(pos):
                        return "EXIT"
                elif self.paused:
                    if self.resume_rect.collidepoint(pos):
                        self.paused = False
                    elif self.restart_rect.collidepoint(pos):
                        return "RESTART"
                    elif self.pause_home_rect.collidepoint(pos):
                        return "EXIT"
                elif self.pause_rect.collidepoint(pos):
                    self.paused = True
                else:
                    # ตรวจสอบการกดปุ่มปล่อยตัวละคร
                    for i, rect in enumerate(self.unit_buttons):
                        u_id = self.team_units[i]
                        if rect.collidepoint(pos):
                            u_data = ALL_UNITS_DATABASE[u_id]
                            if self.minerals >= u_data["cost"] and self.cooldown_timers[i] <= 0:
                                self.minerals -= u_data["cost"]
                                self.units.append(PlayerUnit(self.player_base + 42, u_id))
                                self.cooldown_timers[i] = u_data["cooldown"]

                    # ตรวจสอบการกดปุ่มอัปเกรดแร่
                    if self.upgrade_rect.collidepoint(pos):
                        cost = 75 * self.production_level
                        if self.minerals >= cost:
                            self.minerals -= cost
                            self.production_level += 1
                            self.max_minerals += 100
        return None

    def update(self, dt):
        """อัปเดตการต่อสู้ การเคลื่อนที่ แร่ และเงื่อนไขแพ้ชนะ"""
        if self.game_over or self.paused:
            return

        # อัปเดตเวลา Cooldown ของปุ่มตัวละคร
        for i in range(3):
            if self.cooldown_timers[i] > 0:
                self.cooldown_timers[i] = max(0, self.cooldown_timers[i] - dt)

        # ระบบผลิตแร่อัตโนมัติ
        production_interval = max(0.65, 2.5 / (1 + (self.production_level - 1) * 0.65))
        self.minerals = min(self.max_minerals, self.minerals + (25 / production_interval) * dt)

        # ระบบเกิดยูนิตฝ่ายศัตรู
        self.enemy_spawn_timer -= dt
        if self.enemy_spawn_timer <= 0:
            self.enemy_spawn_timer = self.stage_data["spawn_timer"]
            kind = random.choices([5, 6, 7, 8], weights=self.stage_data["enemy_weights"])[0]
            self.units.append(EnemyUnit(self.enemy_base - 42, kind))

        # อัปเดตการเคลื่อนที่และการโจมตีของยูนิตทั้งหมด
        for unit in self.units:
            if not unit.alive:
                continue
            
            enemies = [u for u in self.units if u.alive and u.team != unit.team]
            targets = [u for u in enemies if (u.x >= unit.x if unit.team == "player" else u.x <= unit.x)]
            nearest = min(targets, key=lambda u: abs(u.x - unit.x)) if targets else None
            dist = abs(nearest.x - unit.x) if nearest else (self.enemy_base - unit.x if unit.team == "player" else unit.x - self.player_base)

            if dist > unit.data["range"]:
                unit.move(dt)
            else:
                unit.attack_timer -= dt
                if unit.attack_timer <= 0:
                    unit.attack_timer = unit.data["cooldown"]
                    if nearest:
                        self.projectiles.append(Projectile(
                            unit.x, unit.y - 23, nearest,
                            unit.data["damage"], unit.projectile_color
                        ))
                    else:
                        if unit.team == "player":
                            self.enemy_hp -= unit.data["damage"]
                        else:
                            self.player_hp -= unit.data["damage"]

        # อัปเดตตำแหน่งกระสุนและกรองเอากระสุนที่ใช้งานอยู่ออก
        for proj in self.projectiles:
            proj.update(dt)
        self.projectiles = [p for p in self.projectiles if p.alive]
        self.units = [u for u in self.units if u.alive]

        # ตรวจสอบเงื่อนไขแพ้-ชนะ
        if self.enemy_hp <= 0:
            self.game_over = "WIN"
            if not self.reward_given:
                PLAYER_DATA["coins"] += self.stage_data["gold_reward"]
                PLAYER_DATA["rubies"] += self.stage_data["ruby_reward"]
                self.reward_given = True
        elif self.player_hp <= 0:
            self.game_over = "LOSE"

    def draw(self):
        """วาดองค์ประกอบทั้งหมดบนหน้าจอ"""
        # พื้นหลังฉากเกม
        bg_img = ASSETS.get(self.stage_data["bg_key"])
        if bg_img:
            screen.blit(bg_img, (0, 0))
        else:
            screen.fill(SKY)
            pygame.draw.rect(screen, GRASS, (0, 420, WIDTH, 100))
        
        # วาดฐานทัพและหลอดเลือดป้อม
        screen.blit(ASSETS["player_base"], (self.player_base - 60, 300))
        screen.blit(ASSETS["enemy_base"], (self.enemy_base - 60, 300))
        
        pygame.draw.rect(screen, (65, 65, 65), (int(self.player_base - 21), int(275), 40, 5), border_radius=2)
        hpp = max(0, int(38 * self.player_hp / self.player_max_hp))
        pygame.draw.rect(screen, GREEN, (int(self.player_base - 20), int(276), hpp, 3), border_radius=2)
        
        pygame.draw.rect(screen, (65, 65, 65), (int(self.enemy_base - 21), int(275), 40, 5), border_radius=2)
        hpe = max(0, int(38 * self.enemy_hp / self.enemy_max_hp))
        pygame.draw.rect(screen, RED, (int(self.enemy_base - 20), int(276), hpe, 3), border_radius=2)

        # วาด UI แผงควบคุมด้านล่าง
        pygame.draw.rect(screen, DARK_PANEL, (0, 490, WIDTH, 130))
                
        for unit in self.units:
            unit.draw()
        for proj in self.projectiles:
            proj.draw()
                
        # แสดงผลแร่ปัจจุบัน
        draw_text(f"แร่: {int(self.minerals)} / {self.max_minerals}", 450, 20, BIG, YELLOW_GOLD)

        # วาดปุ่มตัวละคร
        for i, rect in enumerate(self.unit_buttons):
            u_id = self.team_units[i]
            if u_id is not None:
                data = ALL_UNITS_DATABASE[u_id]
                pygame.draw.rect(screen, data["color"], rect, border_radius=9)
                pygame.draw.rect(screen, (255, 255, 255) if ALL_UNITS_DATABASE[u_id]["stars"] == 1 else YELLOW_GOLD, rect, width=2, border_radius=9)
        
                on_cooldown = self.cooldown_timers[i] > 0
                not_enough_minerals = self.minerals < data["cost"]
        
                if on_cooldown or not_enough_minerals:
                    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 150))
                    screen.blit(overlay, rect.topleft)
        
                if on_cooldown:
                    draw_text(f"{self.cooldown_timers[i]:.1f}s", rect.centerx, rect.centery, FONT, WHITE, center=True)
        
                draw_text(f"{data['name']}", rect.centerx, rect.centery - 10, FONT, WHITE, center=True)
                draw_text(f"ใช้ {data['cost']} แร่", rect.centerx, rect.centery + 12, SMALL, YELLOW_GOLD, center=True)
        
        # วาดปุ่มอัปเกรดแร่
        upgrade_cost = 75 * self.production_level
        pygame.draw.rect(screen, YELLOW_GOLD, self.upgrade_rect, border_radius=9)
        draw_text(f"อัปเกรดแร่ (Lv.{self.production_level})", self.upgrade_rect.centerx, self.upgrade_rect.centery - 10, FONT, BLACK, center=True)
        draw_text(f"(ใช้ {upgrade_cost} แร่)", self.upgrade_rect.centerx, self.upgrade_rect.centery + 12, SMALL, DARK_PANEL, center=True)

        # วาดปุ่ม Pause
        if not self.game_over:
            pygame.draw.rect(screen, ORANGE_BORDER if self.paused else BLUE, self.pause_rect, border_radius=8)
            draw_text("PAUSED" if self.paused else "|| Pause", self.pause_rect.centerx, self.pause_rect.centery, FONT, WHITE, center=True)

        # หน้าต่าง Pause
        if self.paused and not self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 185))
            screen.blit(overlay, (0, 0))

            draw_text("PAUSE", WIDTH // 2, 205, BIG, YELLOW_GOLD, center=True)

            pygame.draw.rect(screen, GREEN, self.resume_rect, border_radius=10)
            draw_text("เล่นต่อ", self.resume_rect.centerx, self.resume_rect.centery, FONT, WHITE, center=True)

            pygame.draw.rect(screen, ORANGE_BORDER, self.restart_rect, border_radius=10)
            draw_text("เริ่มเกมใหม่", self.restart_rect.centerx, self.restart_rect.centery, FONT, WHITE, center=True)

            pygame.draw.rect(screen, RED_TAG, self.pause_home_rect, border_radius=10)
            draw_text("กลับหน้าหลัก", self.pause_home_rect.centerx, self.pause_home_rect.centery, FONT, WHITE, center=True)

        # หน้าต่างแสดงผลเมื่อจบเกม (ชนะ / แพ้)
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            if self.game_over == "WIN":
                draw_text("ชนะ!", WIDTH // 2, 220, BIG, YELLOW_GOLD, center=True)
                draw_text(f"ได้รับ: Coin +{self.stage_data['gold_reward']} | ruby +{self.stage_data['ruby_reward']}", WIDTH // 2, 280, FONT, WHITE, center=True)
            else:
                draw_text("แพ้!", WIDTH // 2, 230, BIG, RED, center=True)

            pygame.draw.rect(screen, BLUE, self.menu_rect, border_radius=10)
            draw_text("กลับหน้าหลัก", self.menu_rect.centerx, self.menu_rect.centery, FONT, WHITE, center=True)

        pygame.display.flip()

    def run(self):
        """ลูปหลักของการรันเกมต่อสู้ (Main Loop)"""
        while True:
            dt = min(clock.tick(60) / 1000.0, 0.05)

            action = self.handle_events()
            if action == "EXIT":
                return
            elif action == "RESTART":
                return "RESTART"

            self.update(dt)
            self.draw()


