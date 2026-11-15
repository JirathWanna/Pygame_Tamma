import pygame
import math
import sys
from game_data import *

# ==========================================
# CONSTANTS & CACHE FOR TEAM SCREEN
# ==========================================
_FIG_CACHE = {}

# ขนาดและระยะห่างของการ์ดตัวละครในคลัง
CARD_WIDTH = 180
CARD_HEIGHT = 150
CARD_GAP = 14
CARD_START_Y = 385

# ตำแหน่งของแท่นวางตัวละคร 3 ช่องในทีม
SLOT_POSITIONS = [(WIDTH // 2 + (i - 1) * 240, 225) for i in range(3)]


# ==========================================
# HELPER FUNCTIONS: GRAPHICS & RENDERING
# ==========================================

def _get_cached_unit_image(unit_id, height):
    """โหลดและแคชรูปภาพตัวละคร (unit_X.png) พร้อมปรับขนาดตามความสูงที่กำหนด"""
    key = (unit_id, height)
    if key not in _FIG_CACHE:
        img = load_image(f"unit_{unit_id}.png")
        if img:
            w = max(1, int(img.get_width() * height / img.get_height()))
            img = pygame.transform.smoothscale(img, (w, height))
        _FIG_CACHE[key] = img
    return _FIG_CACHE[key]


def draw_unit_figure(surf, unit_id, cx, cy, scale=1.0, alpha=255):
    """วาดตัวละคร (แสดงรูปภาพถ้ามี หรือวาดวงรีจำลองจากสีใน Database หากไม่มีรูป)"""
    layer = pygame.Surface((240, 240), pygame.SRCALPHA)
    ox, oy = 120, 120
    
    img = _get_cached_unit_image(unit_id, int(100 * scale))
    if img:
        layer.blit(img, (ox - img.get_width() // 2, oy + int(28 * scale) - img.get_height()))
    else:
        # กรณีไม่มีรูปภาพ ใช้การวาดรูปทรงเรขาคณิตแทน
        unit_data = ALL_UNITS_DATABASE[unit_id]
        c = unit_data["color"]
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
    """วาดรูปดาวสำหรับแสดงระดับดาวของตัวละคร"""
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    pygame.draw.polygon(screen, color, pts)


def draw_star_row(cx, cy, n, size=7):
    """วาดแถวดาวเรียงกันตามจำนวนดาว (n)"""
    start = cx - (n - 1) * (size + 2)
    for i in range(n):
        draw_star_shape(start + i * (size * 2 + 4), cy, size, YELLOW_GOLD)


# ==========================================
# HELPER FUNCTIONS: TEAM LOGIC
# ==========================================

def assign_to_loadout(src, target_slot):
    """
    จัดการการย้าย/สลับตัวละครเข้าสู่ช่องจัดทีม (Loadout)
    - src: tuple เช่น ('slot', index) หรือ ('card', unit_id)
    - target_slot: ช่องเป้าหมายที่จะวาง (0, 1, 2)
    """
    loadout = PLAYER_DATA["loadout"]
    kind, ref = src
    
    if kind == "slot":
        # สลับตำแหน่งระหว่างช่องในทีมด้วยกันเอง
        loadout[ref], loadout[target_slot] = loadout[target_slot], loadout[ref]
    elif ref in loadout:
        # ถ้าตัวละครนี้อยู่ในทีมอยู่แล้ว ให้สลับตำแหน่งกับช่องเป้าหมาย
        old_slot = loadout.index(ref)
        loadout[old_slot], loadout[target_slot] = loadout[target_slot], loadout[old_slot]
    else:
        # นำตัวละครใหม่จากคลังมาใส่แทนที่ในช่องเป้าหมาย
        loadout[target_slot] = ref


def get_slot_rect(i):
    """คืนค่าพื้นที่ Rect ของแท่นวางตัวละครช่องที่ i"""
    cx, cy = SLOT_POSITIONS[i]
    return pygame.Rect(cx - 80, cy - 95, 160, 190)


def get_card_rect(idx, scroll_offset):
    """คืนค่าพื้นที่ Rect ของการ์ดตัวละครในคลังใบที่ idx ตามระยะเลื่อน scroll"""
    return pygame.Rect(24 + idx * (CARD_WIDTH + CARD_GAP) - scroll_offset, CARD_START_Y, CARD_WIDTH, CARD_HEIGHT)


# ==========================================
# MAIN TEAM SCREEN RUNNER
# ==========================================

def run_team_screen():
    drag_data = None      # เก็บข้อมูลตัวละครที่กำลังถูกลาก (src, unit_id, pos)
    scroll_offset = 0     # ระยะการเลื่อนแถบการ์ดแนวนอน
    back_button_rect = pygame.Rect(20, 8, 120, 36)

    while True:
        clock.tick(60)
        
        # 1. EVENT HANDLING (จัดการการกดปุ่มและเมาส์)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
                
            elif event.type == pygame.MOUSEWHEEL:
                # เลื่อน Wheel เพื่อ Scroll แถบการ์ดซ้าย-ขวา
                scroll_offset -= event.y * 40
                
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # ตรวจสอบการกดปุ่มกลับ
                if back_button_rect.collidepoint(event.pos):
                    return
                
                # ตรวจสอบการคลิกลากจากแท่นวางในทีม (Slots)
                for i in range(3):
                    u_id = PLAYER_DATA["loadout"][i]
                    if u_id is not None and get_slot_rect(i).collidepoint(event.pos):
                        drag_data = {"src": ("slot", i), "unit": u_id, "pos": event.pos}
                
                # ถ้ายังไม่ได้ลากจากช่องทีม ให้ตรวจสอบการคลิกลากจากการ์ดในคลัง (Inventory Cards)
                if drag_data is None:
                    for idx, u_id in enumerate(PLAYER_DATA["inventory"]):
                        if get_card_rect(idx, scroll_offset).collidepoint(event.pos):
                            drag_data = {"src": ("card", u_id), "unit": u_id, "pos": event.pos}
                            break
                            
            elif event.type == pygame.MOUSEMOTION and drag_data:
                # อัปเดตตำแหน่งเมาส์ขณะลากตัวละคร
                drag_data["pos"] = event.pos
                
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and drag_data:
                # ปล่อยเมาส์: ตรวจสอบว่าวางลงบนช่องในทีมหรือไม่
                for i in range(3):
                    if get_slot_rect(i).collidepoint(event.pos):
                        assign_to_loadout(drag_data["src"], i)
                        break
                drag_data = None  # ยกเลิกสถานะการลาก

        # 2. UPDATE LOGIC (คำนวณขอบเขตการ Scroll ไม่ให้ล้นเกินไป)
        total_content_width = 24 + len(PLAYER_DATA["inventory"]) * (CARD_WIDTH + CARD_GAP)
        max_scroll = max(0, total_content_width - WIDTH + 24)
        scroll_offset = max(0, min(scroll_offset, max_scroll))

        # 3. RENDERING (วาดองค์ประกอบทั้งหมดบนหน้าจอ)
        
        # 3.1 วาดพื้นหลังลายอิฐ
        screen.fill((222, 196, 150))
        for y in range(0, 365, 40):
            for x in range(0, WIDTH + 80, 80):
                off = 40 if (y // 40) % 2 else 0
                pygame.draw.rect(screen, (210, 184, 138), (x - off, y, 80, 40), 1)

        # 3.2 วาดแท่นวางตัวละคร 3 ช่อง (Slots)
        for i, (cx, cy) in enumerate(SLOT_POSITIONS):
            hovered = drag_data is not None and get_slot_rect(i).collidepoint(drag_data["pos"])
            
            # ฐานรองแท่น
            pygame.draw.ellipse(screen, (70, 60, 90), (cx - 68, cy + 28, 136, 40))
            pygame.draw.ellipse(screen, (150, 110, 190) if hovered else (110, 130, 170), (cx - 68, cy + 18, 136, 40))
            if hovered:
                pygame.draw.ellipse(screen, WHITE, (cx - 68, cy + 18, 136, 40), 4)
                
            u_id = PLAYER_DATA["loadout"][i]
            if u_id is None:
                draw_text("ว่าง", cx, cy + 38, FONT, (120, 110, 100), center=True)
                continue
                
            unit = ALL_UNITS_DATABASE[u_id]
            # วาดตัวละครบนแท่น (ถ้าไม่ได้กำลังลากตัวนี้อยู่)
            if not (drag_data and drag_data["src"] == ("slot", i)):
                draw_unit_figure(screen, u_id, cx, cy + 10)
                
            draw_star_row(cx, cy + 38, unit["stars"], 6)
            draw_text(unit["name"], cx, cy + 82, FONT, BLACK, center=True)
            draw_text(f"ดาเมจ {unit['damage']} เลือด {unit['hp']}", cx, cy + 104, SMALL, (70, 50, 40), center=True)

        # 3.3 วาดแถบหัวข้อด้านบน (Top Bar)
        pygame.draw.rect(screen, (60, 50, 80), (0, 0, WIDTH, 52))
        pygame.draw.rect(screen, RED_TAG, back_button_rect, border_radius=10)
        draw_text("‹ กลับ", back_button_rect.centerx, back_button_rect.centery, FONT, WHITE, center=True)
        draw_text("จัดทีมเรนเจอร์", WIDTH // 2, 26, BIG, WHITE, center=True)
        
        # คำนวณและแสดงพลังโจมตีรวมของทีม
        total_damage = sum(ALL_UNITS_DATABASE[u]["damage"] for u in PLAYER_DATA["loadout"] if u is not None)
        draw_text(f"พลังโจมตีรวม: {total_damage}", WIDTH - 220, 14, FONT, YELLOW_GOLD)

        # 3.4 วาดแถบการ์ดตัวละครในคลังด้านล่าง (Inventory Panel)
        panel_y = CARD_START_Y - 20
        pygame.draw.rect(screen, (95, 65, 45), (0, panel_y, WIDTH, HEIGHT - panel_y))
        pygame.draw.line(screen, ORANGE_BORDER, (0, panel_y), (WIDTH, panel_y), 3)

        # กำหนด Clipping Area ไม่ให้การ์ดล้นออกนอกขอบจอซ้าย-ขวาเวลากดเลื่อน
        clip_area = pygame.Rect(0, panel_y, WIDTH, HEIGHT - panel_y)
        screen.set_clip(clip_area)

        for idx, u_id in enumerate(PLAYER_DATA["inventory"]):
            unit = ALL_UNITS_DATABASE[u_id]
            rect = get_card_rect(idx, scroll_offset)
            
            # ข้ามการวาดการ์ดที่อยู่นอกจอเพื่อประหยัดการประมวลผล
            if rect.right < 0 or rect.left > WIDTH:
                continue
                
            is_rare = unit["stars"] >= 2
            text_color = (70, 40, 10) if is_rare else WHITE
            
            # วาดพื้นหลังการ์ด
            pygame.draw.rect(screen, (240, 200, 60) if is_rare else (150, 105, 70), rect, border_radius=10)
            pygame.draw.rect(screen, (90, 60, 40), rect, 3, border_radius=10)
            
            # ข้อมูลในการ์ด
            draw_star_row(rect.centerx, rect.y + 16, unit["stars"], 6)
            draw_unit_figure(screen, u_id, rect.x + 45, rect.y + 82, 0.65)
            draw_text(unit["name"], rect.x + 88, rect.y + 32, FONT, text_color)
            draw_text(f"ดาเมจ {unit['damage']}", rect.x + 88, rect.y + 60, SMALL, text_color)
            draw_text(f"เลือด {unit['hp']}", rect.x + 88, rect.y + 80, SMALL, text_color)
            draw_text(f"ใช้ {unit['cost']} แร่", rect.x + 88, rect.y + 100, SMALL, text_color)
            
            # หากการ์ดนี้กำลังถูกลาก ให้แสดงเงาดำทับ
            if drag_data and drag_data["src"] == ("card", u_id):
                dim_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(dim_surface, (0, 0, 0, 110), dim_surface.get_rect(), border_radius=10)
                screen.blit(dim_surface, rect.topleft)
                
            # หากตัวละครนี้อยู่ในทีมแล้ว ให้แสดงป้าย "IN TEAM" กำกับ
            if u_id in PLAYER_DATA["loadout"]:
                tag_surf = SMALL.render("IN TEAM", True, WHITE)
                tag_rect = pygame.Rect(rect.x + 6, rect.bottom - 26, tag_surf.get_width() + 12, 20)
                pygame.draw.rect(screen, (60, 140, 90), tag_rect, border_radius=6)
                screen.blit(tag_surf, (rect.x + 12, rect.bottom - 25))

        screen.set_clip(None)  # ยกเลิก Clipping Area

        # 3.5 แสดงคำแนะนำการใช้งานด้านล่างสุด
        draw_text("กดค้างที่การ์ดแล้วลากไปวางบนแท่น  |  ลากระหว่างแท่นเพื่อสลับ  |  Scroll เมาส์เลื่อนซ้าย-ขวา  |  ESC หรือ ‹ กลับ เพื่อออก",
                  20, HEIGHT - 30, SMALL, (255, 235, 200))

        # 3.6 วาดตัวละครที่กำลังติดเมาส์อยู่บนสุด (Drag Overlay)
        if drag_data:
            draw_unit_figure(screen, drag_data["unit"], drag_data["pos"][0], drag_data["pos"][1], 1.1, alpha=215)

        pygame.display.flip()