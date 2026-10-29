import pygame
import math
from game_data import *

# ==========================================
# Team Screen (หน้าจัดทีมแบบเต็มจอ ลากการ์ดไปวางบนแท่น)
# ==========================================
_FIG_CACHE = {}

def _fig_image(unit_id, height):
    """รูป unit_X.png ย่อให้สูง height (ไม่มีไฟล์ -> None)"""
    key = (unit_id, height)
    if key not in _FIG_CACHE:
        img = load_image(f"unit_{unit_id}.png")
        if img:
            w = max(1, int(img.get_width() * height / img.get_height()))
            img = pygame.transform.smoothscale(img, (w, height))
        _FIG_CACHE[key] = img
    return _FIG_CACHE[key]

def draw_unit_figure(surf, unit_id, cx, cy, scale=1.0, alpha=255):
    """วาดตัวละคร (รูปถ้ามี ไม่มีก็วาดตัวกลมจากสีใน database) เท้าอยู่ที่ประมาณ cy+28*scale"""
    layer = pygame.Surface((240, 240), pygame.SRCALPHA)
    ox, oy = 120, 120
    img = _fig_image(unit_id, int(100 * scale))
    if img:
        layer.blit(img, (ox - img.get_width() // 2, oy + int(28 * scale) - img.get_height()))
    else:
        c = ALL_UNITS_DATABASE[unit_id]["color"]
        dark = tuple(max(0, v - 60) for v in c)
        r = int(34 * scale)
        body = (ox - r, oy - int(r * 1.3), r * 2, int(r * 2.1))
        pygame.draw.ellipse(layer, c, body)
        pygame.draw.ellipse(layer, dark, body, 3)
        for sx in (-1, 1):
            pygame.draw.circle(layer, WHITE, (int(ox + sx * r * 0.38), int(oy - r * 0.25)), max(2, int(7 * scale)))
            pygame.draw.circle(layer, (30, 30, 40), (int(ox + sx * r * 0.38), int(oy - r * 0.22)), max(1, int(3.5 * scale)))
        pygame.draw.arc(layer, dark, (ox - 8, oy - 2, 16, 12), 3.4, 6.0, 2)
    if alpha < 255:
        layer.set_alpha(alpha)
    surf.blit(layer, (cx - ox, cy - oy))

def draw_star_shape(cx, cy, r, color):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    pygame.draw.polygon(screen, color, pts)

def draw_star_row(cx, cy, n, size=7):
    start = cx - (n - 1) * (size + 2)
    for i in range(n):
        draw_star_shape(start + i * (size * 2 + 4), cy, size, YELLOW_GOLD)

def assign_to_loadout(src, target):
    """src = ("slot", ช่องเดิม) หรือ ("card", id ตัวละคร); วางลงช่อง target
    - ลากจากช่อง / ตัวที่อยู่ในทีมแล้ว -> สลับตำแหน่งกัน
    - ตัวใหม่จากคลัง -> แทนที่ช่องนั้น"""
    load = PLAYER_DATA["loadout"]
    kind, ref = src
    if kind == "slot":
        load[ref], load[target] = load[target], load[ref]
    elif ref in load:
        old = load.index(ref)
        load[old], load[target] = load[target], load[old]
    else:
        load[target] = ref

def run_team_screen():
    drag = None          # dict(src=("card", id)|("slot", i), unit=id, pos=(x,y))
    scroll = 0
    slot_pos = [(WIDTH // 2 + (i - 1) * 240, 225) for i in range(3)]
    CARD_W, CARD_H, GAP, CARD_Y = 180, 150, 14, 385
    back_rect = pygame.Rect(20, 8, 120, 36)

    def slot_rect(i):
        cx, cy = slot_pos[i]
        return pygame.Rect(cx - 80, cy - 95, 160, 190)

    def card_rect(idx):
        return pygame.Rect(24 + idx * (CARD_W + GAP) - scroll, CARD_Y, CARD_W, CARD_H)

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            elif event.type == pygame.MOUSEWHEEL:
                scroll -= event.y * 40
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(event.pos):
                    return
                for i in range(3):
                    u = PLAYER_DATA["loadout"][i]
                    if u is not None and slot_rect(i).collidepoint(event.pos):
                        drag = dict(src=("slot", i), unit=u, pos=event.pos)
                if drag is None:
                    for idx, u_id in enumerate(PLAYER_DATA["inventory"]):
                        if card_rect(idx).collidepoint(event.pos):
                            drag = dict(src=("card", u_id), unit=u_id, pos=event.pos)
                            break
            elif event.type == pygame.MOUSEMOTION and drag:
                drag["pos"] = event.pos
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and drag:
                for i in range(3):
                    if slot_rect(i).collidepoint(event.pos):
                        assign_to_loadout(drag["src"], i)
                        break
                drag = None                 # ปล่อยนอกแท่น = ยกเลิก

        max_scroll = max(0, 24 + len(PLAYER_DATA["inventory"]) * (CARD_W + GAP) - WIDTH)
        scroll = max(0, min(scroll, max_scroll))

        # ----- พื้นหลังอิฐ -----
        screen.fill((222, 196, 150))
        for y in range(0, 365, 40):
            for x in range(0, WIDTH + 80, 80):
                off = 40 if (y // 40) % 2 else 0
                pygame.draw.rect(screen, (210, 184, 138), (x - off, y, 80, 40), 1)

        # ----- แท่นวาง 3 ช่อง -----
        for i, (cx, cy) in enumerate(slot_pos):
            hover = drag is not None and slot_rect(i).collidepoint(drag["pos"])
            pygame.draw.ellipse(screen, (70, 60, 90), (cx - 68, cy + 28, 136, 40))
            pygame.draw.ellipse(screen, (150, 110, 190) if hover else (110, 130, 170), (cx - 68, cy + 18, 136, 40))
            if hover:
                pygame.draw.ellipse(screen, WHITE, (cx - 68, cy + 18, 136, 40), 4)
            u_id = PLAYER_DATA["loadout"][i]
            if u_id is None:
                draw_text("ว่าง", cx, cy + 38, FONT, (120, 110, 100), center=True)
                continue
            u = ALL_UNITS_DATABASE[u_id]
            if not (drag and drag["src"] == ("slot", i)):
                draw_unit_figure(screen, u_id, cx, cy + 10)
            draw_star_row(cx, cy + 38, u["stars"], 6)
            draw_text(u["name"], cx, cy + 82, FONT, BLACK, center=True)
            draw_text(f"ATK {u['damage']}  ระยะ {u['range']}", cx, cy + 104, SMALL, (70, 50, 40), center=True)

        # ----- แถบด้านบน -----
        pygame.draw.rect(screen, (60, 50, 80), (0, 0, WIDTH, 52))
        pygame.draw.rect(screen, RED_TAG, back_rect, border_radius=10)
        draw_text("‹ กลับ", back_rect.centerx, back_rect.centery, FONT, WHITE, center=True)
        draw_text("จัดทีมเรนเจอร์", WIDTH // 2, 26, BIG, WHITE, center=True)
        total = sum(ALL_UNITS_DATABASE[u]["damage"] for u in PLAYER_DATA["loadout"] if u is not None)
        draw_text(f"พลังโจมตีรวม: {total}", WIDTH - 20 - 200, 14, FONT, YELLOW_GOLD)

        # ----- แถบการ์ดตัวละครในคลัง -----
        pygame.draw.rect(screen, (95, 65, 45), (0, CARD_Y - 20, WIDTH, HEIGHT - CARD_Y + 20))
        pygame.draw.line(screen, ORANGE_BORDER, (0, CARD_Y - 20), (WIDTH, CARD_Y - 20), 3)
        for idx, u_id in enumerate(PLAYER_DATA["inventory"]):
            u = ALL_UNITS_DATABASE[u_id]
            rect = card_rect(idx)
            if rect.right < 0 or rect.left > WIDTH:
                continue
            gold = u["stars"] >= 2
            fg = (70, 40, 10) if gold else WHITE
            pygame.draw.rect(screen, (240, 200, 60) if gold else (150, 105, 70), rect, border_radius=10)
            pygame.draw.rect(screen, (90, 60, 40), rect, 3, border_radius=10)
            draw_star_row(rect.centerx, rect.y + 16, u["stars"], 6)
            draw_unit_figure(screen, u_id, rect.x + 45, rect.y + 82, 0.65)
            draw_text(u["name"], rect.x + 88, rect.y + 32, FONT, fg)
            draw_text(f"ATK {u['damage']}", rect.x + 88, rect.y + 60, SMALL, fg)
            draw_text(f"ระยะ {u['range']}", rect.x + 88, rect.y + 80, SMALL, fg)
            draw_text(f"ใช้ {u['cost']} แร่", rect.x + 88, rect.y + 100, SMALL, fg)
            if drag and drag["src"] == ("card", u_id):
                dim = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(dim, (0, 0, 0, 110), dim.get_rect(), border_radius=10)
                screen.blit(dim, rect.topleft)
            if u_id in PLAYER_DATA["loadout"]:
                tag = SMALL.render("IN TEAM", True, WHITE)
                pygame.draw.rect(screen, (60, 140, 90), (rect.x + 6, rect.bottom - 26, tag.get_width() + 12, 20), border_radius=6)
                screen.blit(tag, (rect.x + 12, rect.bottom - 25))

        draw_text("กดค้างที่การ์ดแล้วลากไปวางบนแท่น  |  ลากระหว่างแท่นเพื่อสลับ  |  ESC หรือ ‹ กลับ เพื่อออก",
                  20, HEIGHT - 30, SMALL, (255, 235, 200))

        # ----- ตัวละครที่ติดเมาส์ (วาดบนสุด) -----
        if drag:
            draw_unit_figure(screen, drag["unit"], drag["pos"][0], drag["pos"][1], 1.1, alpha=215)

        pygame.display.flip()
