import pygame
import random
import math
import sys
import os

# --- Pygame Setup ---
pygame.init()
WIDTH, HEIGHT = 1000, 620
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LINE Rangers - Full Feature Edition")
clock = pygame.time.Clock()

# --- Fonts & Colors ---
FONT = pygame.font.SysFont("Tahoma", 18, bold=True)
SMALL = pygame.font.SysFont("Tahoma", 13, bold=True)
BIG = pygame.font.SysFont("Tahoma", 28, bold=True)

WHITE        = (255, 255, 255)
BLACK        = (20, 20, 20)
DARK_PANEL   = (35, 30, 25)
YELLOW_GOLD  = (255, 210, 40)
ORANGE_BORDER= (230, 110, 30)
WOOD_BROWN   = (120, 65, 30)
RED_TAG      = (235, 60, 50)
BLUE         = (70, 145, 235)
GREEN        = (63, 190, 105)
RED          = (224, 78, 82)
SKY          = (194, 226, 245)
GRASS        = (105, 183, 100)
PURPLE       = (150, 80, 220)

# --- Global Player Economy Data ---
PLAYER_DATA = {
    "coins": 500,
    "rubies": 100,
    "inventory": [0, 1, 2],       # ID ตัวละครที่มีในคลัง
    "loadout": [0, 1, 2]          # ID ตัวละครที่จัดลงทีม (3 ช่อง)
}

# --- Database ตัวละคร ( Template รองรับการเพิ่มตัวละครภายหลัง ) ---
ALL_UNITS_DATABASE = [
    {"id": 0, "name": "หมัดหมี", "stars": 1, "range": 58, "damage": 18, "cooldown": 2.0, "cost": 35, "color": (230, 130, 80)},
    {"id": 1, "name": "นักธนู", "stars": 1, "range": 190, "damage": 11, "cooldown": 3.0, "cost": 55, "color": (65, 170, 105)},
    {"id": 2, "name": "จอมเวท", "stars": 2, "range": 310, "damage": 24, "cooldown": 4.5, "cost": 85, "color": (145, 100, 220)},
    {"id": 3, "name": "ตัวแถม", "stars": 2, "range": 310, "damage": 24, "cooldown": 4.5, "cost": 85, "color": (145, 100, 220)},
    {"id": 4, "name": "ck", "stars": 2, "range": 310, "damage": 24, "cooldown": 4.5, "cost": 85, "color": (145, 100, 220)}
]

STAGES = [
    {"id": 1, "name": "ด่าน 1: ทุ่งหญ้าสงบสุข", "enemy_hp": 400, "spawn_timer": 4.5, "enemy_weights": [60, 30, 10], "bg_key": "bg_grass", "gold_reward": 150, "ruby_reward": 5},
    {"id": 2, "name": "ด่าน 2: ทะเลทรายเดือด", "enemy_hp": 650, "spawn_timer": 3.5, "enemy_weights": [30, 50, 20], "bg_key": "bg_desert", "gold_reward": 250, "ruby_reward": 8},
    {"id": 3, "name": "ด่าน 3: ภูเขาไฟมรณะ", "enemy_hp": 1000, "spawn_timer": 2.5, "enemy_weights": [20, 40, 40], "bg_key": "bg_volcano", "gold_reward": 400, "ruby_reward": 12}
]

BOTTOM_NAV_ITEMS = [
    {"id": "TEAM",    "label": "🛡️ ทีม",    "color": WOOD_BROWN},
    {"id": "GACHA",   "label": "🎰 กาชา",   "color": WOOD_BROWN},
    {"id": "UPGRADE", "label": "⚡ อัพเกรด", "color": WOOD_BROWN},
]

# --- Asset Loader Manager ---
ASSETS = {}

def load_image(filename, size=None):
    path = os.path.join("assets", filename)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                img = pygame.transform.smoothscale(img, size)
            return img
        except Exception as e:
            print(f"Failed to load image {filename}: {e}")
    return None

def init_assets():
    ASSETS["bg_lobby"] = load_image("bg_lobby.png", (WIDTH, HEIGHT))
    ASSETS["bg_grass"] = load_image("bg_grass.png", (WIDTH, HEIGHT))
    ASSETS["bg_desert"] = load_image("bg_desert.png", (WIDTH, HEIGHT))
    ASSETS["bg_volcano"] = load_image("bg_volcano.png", (WIDTH, HEIGHT))
    ASSETS["btn_stage"] = load_image("btn_stage.png", (240, 130))
    for i in range(len(ALL_UNITS_DATABASE)):
        ASSETS[f"unit_{i}"] = load_image(f"unit_{i}.png", (50, 50))

init_assets()

# --- Helper Functions ---
def draw_text(text, x, y, font=FONT, color=WHITE, center=False):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)

def draw_top_bar():
    items = [
        (f"💎 {PLAYER_DATA['rubies']}", (680, 25), (130, 36)),
        (f"🪙 {PLAYER_DATA['coins']:,}", (830, 25), (150, 36))
    ]
    for text, pos, size in items:
        rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
        pygame.draw.rect(screen, BLACK, rect, border_radius=15)
        pygame.draw.rect(screen, YELLOW_GOLD, rect, 2, border_radius=15)
        draw_text(text, rect.centerx, rect.centery, FONT, WHITE, center=True)

def draw_bottom_navigation(active_tab):
    nav_height = 80
    panel_rect = pygame.Rect(0, HEIGHT - nav_height, WIDTH, nav_height)
    pygame.draw.rect(screen, DARK_PANEL, panel_rect)
    pygame.draw.line(screen, ORANGE_BORDER, (0, HEIGHT - nav_height), (WIDTH, HEIGHT - nav_height), 3)

    btn_count = len(BOTTOM_NAV_ITEMS)
    btn_w, btn_h = 200, 60
    gap = (WIDTH - (btn_count * btn_w)) // (btn_count + 1)
    clickable_buttons = []

    for i, item in enumerate(BOTTOM_NAV_ITEMS):
        x = gap + i * (btn_w + gap)
        y = HEIGHT - nav_height + 10
        rect = pygame.Rect(x, y, btn_w, btn_h)

        is_active = (active_tab == item["id"])
        fill_color = ORANGE_BORDER if is_active else WOOD_BROWN
        pygame.draw.rect(screen, fill_color, rect, border_radius=12)
        pygame.draw.rect(screen, YELLOW_GOLD if is_active else WHITE, rect, 3, border_radius=12)

        draw_text(item["label"], rect.centerx, rect.centery, BIG, WHITE, center=True)
        clickable_buttons.append((rect, item["id"]))

    return clickable_buttons
