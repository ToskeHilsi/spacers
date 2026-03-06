"""
ui.py - HUD and Skill Tree UI.
"""

import pygame
import math
from skill_tree import SKILL_TREE


def _font(size, bold=False):
    return pygame.font.SysFont("monospace", size, bold=bold)


# ── HUD ───────────────────────────────────────────────────────────────────────

class HUD:
    def __init__(self):
        self._f_small  = _font(14)
        self._f_medium = _font(18, bold=True)
        self._f_large  = _font(24, bold=True)
        self._f_tiny   = _font(12)
        self._messages = []   # [(text, timer, color)]

    def add_message(self, text, duration=2.5, color=(255, 255, 255)):
        self._messages.append([text, duration, color])

    def update(self, dt):
        for m in self._messages:
            m[1] -= dt
        self._messages = [m for m in self._messages if m[1] > 0]

    def draw(self, surf, player, world, skill_tree):
        sw, sh = surf.get_size()
        stats = skill_tree.compute_stats()
        boss  = getattr(world, "boss", None)   # resolved once, used throughout

        # ── HP / Shield bar ───────────────────────────────────────────────
        bar_x, bar_y = 20, sh - 80
        bar_w, bar_h = 220, 16

        # Shield
        if player.max_shield > 0:
            sh_ratio = player.shield / player.max_shield
            pygame.draw.rect(surf, (0, 80, 160),   (bar_x, bar_y - 20, bar_w, 12))
            pygame.draw.rect(surf, (50, 160, 255),  (bar_x, bar_y - 20, int(bar_w * sh_ratio), 12))
            lbl = self._f_tiny.render(f"SH {int(player.shield)}/{player.max_shield}", True, (150, 200, 255))
            surf.blit(lbl, (bar_x + 4, bar_y - 20))

        # HP
        hp_ratio = max(0, player.hp / player.max_hp)
        r = int(255 * (1 - hp_ratio))
        g = int(200 * hp_ratio)
        pygame.draw.rect(surf, (60, 0, 0),    (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surf, (r, g, 30),    (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
        pygame.draw.rect(surf, (200, 200, 200), (bar_x, bar_y, bar_w, bar_h), 1)
        hp_lbl = self._f_tiny.render(f"HP {int(player.hp)}/{player.max_hp}", True, (255, 255, 255))
        surf.blit(hp_lbl, (bar_x + 4, bar_y + 1))

        # ── XP bar ────────────────────────────────────────────────────────
        # Show progress within current level bracket
        prev_thresh = player.xp_to_next // int(1.35 + 0.0001)  # rough previous threshold
        xp_ratio = min(1.0, player.xp / player.xp_to_next)
        pygame.draw.rect(surf, (0, 40, 60),   (bar_x, bar_y + 22, bar_w, 10))
        pygame.draw.rect(surf, (0, 200, 255), (bar_x, bar_y + 22, int(bar_w * xp_ratio), 10))
        xp_lbl = self._f_tiny.render(
            f"LVL {player.level}  {player.xp}/{player.xp_to_next} XP  (skill pool: {player.xp})",
            True, (0, 220, 255))
        surf.blit(xp_lbl, (bar_x, bar_y + 34))

        # ── Ability cooldowns ─────────────────────────────────────────────
        ability_x = bar_x
        ability_y = bar_y - 54
        abilities = []
        # Boost is always available (no unlock required)
        boost_cd = player._boost_cd
        boost_active = player.is_boosting
        abilities.append(("SH:Boost", boost_cd, player.BOOST_CD, (100, 220, 255), boost_active))
        if stats["warp"]:
            cd = player._warp_cd
            abilities.append(("F:Warp", cd, player.WARP_CD, (100, 200, 255)))
        if stats["stealth"]:
            cd = player._stealth_cd
            active = player.is_stealthed
            abilities.append(("C:Stealth", cd, player.STEALTH_CD, (150, 255, 150), active))
        if stats["missile"]:
            cd = player._missile_cd
            abilities.append(("E:Missile", cd, player.MISSILE_CD, (255, 220, 50)))
        if stats["laser"]:
            cd = player._laser_cd
            abilities.append(("Q:Laser", cd, player.LASER_CD, (255, 80, 80)))

        for i, ab in enumerate(abilities):
            name, cd, max_cd, color = ab[:4]
            active = ab[4] if len(ab) > 4 else False
            ax = ability_x + i * 80
            ay = ability_y
            # Background
            bg_color = (20, 20, 50) if cd <= 0 else (10, 10, 20)
            pygame.draw.rect(surf, bg_color, (ax, ay, 70, 34), border_radius=4)
            if active:
                pygame.draw.rect(surf, color, (ax, ay, 70, 34), 2, border_radius=4)
            ratio = 1.0 - (cd / max_cd) if max_cd > 0 else 1.0
            pygame.draw.rect(surf, color + (int(80 * ratio),),
                             (ax, ay + 26, int(70 * ratio), 6))
            nm = self._f_tiny.render(name, True, color if cd <= 0 else (100, 100, 100))
            surf.blit(nm, (ax + 2, ay + 4))
            if cd > 0:
                cd_t = self._f_tiny.render(f"{cd:.1f}s", True, (180, 180, 180))
                surf.blit(cd_t, (ax + 2, ay + 16))
            else:
                rdy = self._f_tiny.render("READY", True, color)
                surf.blit(rdy, (ax + 2, ay + 16))

        # ── Minimap ───────────────────────────────────────────────────────
        mm_size  = 140
        mm_x     = sw - mm_size - 16
        mm_y     = sh - mm_size - 16
        # Scale so the whole current zone fits in the minimap
        border_r = world.border.radius
        mm_scale = (mm_size * 0.45) / max(border_r, 1)

        mm_surf = pygame.Surface((mm_size, mm_size), pygame.SRCALPHA)
        mm_surf.fill((0, 0, 20, 170))
        pygame.draw.rect(mm_surf, (80, 80, 120), (0, 0, mm_size, mm_size), 1)

        # Minimap centre = world origin (0,0) projected through player offset
        # Player is always at mm_cx, mm_cy in minimap space
        mm_cx = mm_size // 2 + int(-player.x * mm_scale)
        mm_cy = mm_size // 2 + int(-player.y * mm_scale)

        # Border circle — centred on world origin (mm_cx+player.x*scale, etc = mm_size//2)
        border_r_mm = int(border_r * mm_scale)
        origin_x_mm = mm_size // 2 + int(-player.x * mm_scale)
        origin_y_mm = mm_size // 2 + int(-player.y * mm_scale)
        bcol = world.border.color
        pygame.draw.circle(mm_surf, bcol + (180,), (origin_x_mm, origin_y_mm), border_r_mm, 2)

        # Asteroids (grey blobs)
        for ast in world.asteroids:
            ax = mm_size // 2 + int((ast.x - player.x) * mm_scale)
            ay = mm_size // 2 + int((ast.y - player.y) * mm_scale)
            if 0 <= ax < mm_size and 0 <= ay < mm_size:
                pygame.draw.circle(mm_surf, (90, 85, 80), (ax, ay), max(1, int(ast.radius * mm_scale)))

        # Dense nebulae (tinted blobs)
        for dn in world.dense_nebulae:
            dx = mm_size // 2 + int((dn.x - player.x) * mm_scale)
            dy = mm_size // 2 + int((dn.y - player.y) * mm_scale)
            r_mm = max(2, int(dn.radius * mm_scale))
            if -r_mm < dx < mm_size+r_mm and -r_mm < dy < mm_size+r_mm:
                tmp = pygame.Surface((mm_size, mm_size), pygame.SRCALPHA)
                pygame.draw.circle(tmp, dn.color + (50,), (dx, dy), r_mm)
                mm_surf.blit(tmp, (0, 0))

        # Enemy dots
        for enemy in world.enemies:
            if getattr(enemy, "is_boss", False):
                continue
            ex = mm_size // 2 + int((enemy.x - player.x) * mm_scale)
            ey = mm_size // 2 + int((enemy.y - player.y) * mm_scale)
            if 0 <= ex < mm_size and 0 <= ey < mm_size:
                pygame.draw.circle(mm_surf, (220, 60, 60), (ex, ey), 2)

        # Wreck dots
        for wreck in world.wrecks:
            wx = mm_size // 2 + int((wreck.x - player.x) * mm_scale)
            wy = mm_size // 2 + int((wreck.y - player.y) * mm_scale)
            if 0 <= wx < mm_size and 0 <= wy < mm_size:
                pygame.draw.circle(mm_surf, (200, 160, 50), (wx, wy), 2)

        # Boss dot — always clamped to minimap edge so it stays visible
        if boss and boss.alive:
            bx_raw = mm_size // 2 + int((boss.x - player.x) * mm_scale)
            by_raw = mm_size // 2 + int((boss.y - player.y) * mm_scale)
            bx_mm  = max(4, min(mm_size-4, bx_raw))
            by_mm  = max(4, min(mm_size-4, by_raw))
            gcol   = [(255,180,40),(255,80,80),(120,80,255),(80,200,255)][boss._gimmick]
            pygame.draw.circle(mm_surf, gcol,        (bx_mm, by_mm), 5)
            pygame.draw.circle(mm_surf, (255,255,255),(bx_mm, by_mm), 5, 1)

        # Player dot (on top of everything)
        pygame.draw.circle(mm_surf, (0, 220, 255), (mm_size // 2, mm_size // 2), 3)

        surf.blit(mm_surf, (mm_x, mm_y))
        mm_lbl = self._f_tiny.render("MAP", True, (120, 120, 180))
        surf.blit(mm_lbl, (mm_x + 4, mm_y + 2))

        # ── Boss HP bar(s) (top-center) ───────────────────────────────────
        if boss and boss.alive:
            bar_w = min(500, sw - 40)
            bx = sw // 2 - bar_w // 2
            by = 14
            ratio = max(0, boss.hp / boss.max_hp)
            gcol  = [(255,180,40),(255,80,80),(120,80,255),(80,200,255)][boss._gimmick]
            pygame.draw.rect(surf, (40,0,0),      (bx, by, bar_w, 20))
            pygame.draw.rect(surf, gcol,          (bx, by, int(bar_w*ratio), 20))
            pygame.draw.rect(surf, (200,200,200), (bx, by, bar_w, 20), 1)
            lbl = self._f_tiny.render(
                f"ZONE BOSS  [{boss.phase_name}]  {int(max(0,boss.hp))}/{boss.max_hp}",
                True, (255,255,255))
            surf.blit(lbl, (sw//2 - lbl.get_width()//2, by + 3))
            # Show extra bosses still alive
            extra_alive = sum(1 for b in world.bosses
                              if b.alive and not getattr(b, "_is_required", True))
            if extra_alive:
                ex_lbl = self._f_tiny.render(
                    f"+ {extra_alive} extra boss{'es' if extra_alive>1 else ''} (optional)",
                    True, (255, 140, 60))
                surf.blit(ex_lbl, (sw//2 - ex_lbl.get_width()//2, by + 26))

        # ── Zone indicator ────────────────────────────────────────────────
        zone_col = getattr(world.border, "color", (200,200,200))
        pp = getattr(skill_tree, "prestige_points", 0) if skill_tree else 0
        pp_str = f"  |  {pp}P" if pp > 0 else ""
        z_lbl = self._f_tiny.render(
            f"ZONE {world.current_zone}  |  Boss: {'ALIVE' if (boss and boss.alive) else 'DEFEATED'}{pp_str}",
            True, zone_col)
        surf.blit(z_lbl, (sw//2 - z_lbl.get_width()//2, 38))

        # ── Coordinates ───────────────────────────────────────────────────
        coord = self._f_tiny.render(
            f"X:{int(player.x)}  Y:{int(player.y)}", True, (80, 80, 120))
        surf.blit(coord, (mm_x, mm_y - 16))

        # ── Stealth / nebula indicator ────────────────────────────────────
        skill_stealth_active = player._stealth_t > 0
        if player.is_stealthed:
            if skill_stealth_active:
                label = f"[ STEALTH  {player._stealth_t:.1f}s ]"
                color = (150, 255, 150)
            else:
                label = "[ NEBULA COVER ]"
                color = (100, 180, 255)
            lbl = self._f_medium.render(label, True, color)
            surf.blit(lbl, (sw // 2 - lbl.get_width() // 2, 60))

        # ── Floating messages ─────────────────────────────────────────────
        for i, (text, timer, color) in enumerate(self._messages[-6:]):
            alpha = min(255, int(timer * 255))
            msg = self._f_medium.render(text, True, color)
            msg.set_alpha(alpha)
            surf.blit(msg, (sw // 2 - msg.get_width() // 2, sh // 2 - 80 - i * 28))

        # ── Controls reminder (corner) ────────────────────────────────────
        hints = [
            "WASD: Move/Thrust",
            "Mouse: Aim",
            "Click/SPACE: Fire",
            "SHIFT: Boost",
            "TAB: Skill Tree",
        ]
        for i, h in enumerate(hints):
            t = self._f_tiny.render(h, True, (60, 60, 90))
            surf.blit(t, (sw - 160, 10 + i * 16))


# ── Skill Tree UI ─────────────────────────────────────────────────────────────


# ── Skill Tree UI ─────────────────────────────────────────────────────────────

BRANCH_COLORS = {
    "weapons":   (255, 120,  50),
    "defense":   ( 80, 200, 255),
    "engine":    (100, 255, 130),
    "p_weapons": (255,  60, 200),   # prestige: hot pink
    "p_defense": (255, 200,  50),   # prestige: gold
    "p_engine":  ( 60, 220, 255),   # prestige: electric blue
}

NODE_R      = 26
COL_W       = 90
ROW_H       = 110
TOP_MARGIN  = 110   # below tab bar + header
LEFT_MARGIN = 30

# Which branches belong to each tab
REGULAR_BRANCHES  = ["weapons", "defense", "engine"]
PRESTIGE_BRANCHES = ["p_weapons", "p_defense", "p_engine"]
BRANCH_DISPLAY    = {
    "weapons": "WEAPONS", "defense": "DEFENSE", "engine": "ENGINE",
    "p_weapons": "VOID ARSENAL", "p_defense": "VOID ARMOR", "p_engine": "VOID THRUSTERS",
}


class SkillTreeUI:
    def __init__(self):
        self._f       = _font(15, bold=True)
        self._f_sm    = _font(12)
        self._f_tiny  = _font(11)
        self._f_head  = _font(22, bold=True)
        self._f_tab   = _font(14, bold=True)
        self.selected_id   = None
        self._scroll_x     = 0
        self._scroll_y     = 0   # vertical scroll (only upward clamped — no scrolling DOWN past row 0)
        self._drag_start   = None
        self._drag_origin  = None
        self._active_tab   = "normal"   # "normal" | "prestige"
        # Reset confirmation state
        self._reset_branch = None   # branch pending reset confirmation

    def _active_branches(self):
        return REGULAR_BRANCHES if self._active_tab == "normal" else PRESTIGE_BRANCHES

    def _node_canvas_pos(self, skill):
        x = LEFT_MARGIN + skill.col * COL_W + COL_W // 2
        y = TOP_MARGIN  + skill.row * ROW_H + ROW_H // 2
        return x, y

    def _canvas_to_screen(self, cx, cy):
        return cx - self._scroll_x, cy - self._scroll_y

    def _screen_to_canvas(self, sx, sy):
        return sx + self._scroll_x, sy + self._scroll_y

    def _visible_skills(self, skill_tree):
        branches = self._active_branches()
        return [s for s in skill_tree.skills.values() if s.branch in branches]

    def _clamp_scroll(self, sw, sh, skill_tree):
        vis = self._visible_skills(skill_tree)
        if not vis:
            return
        # X clamp
        max_col   = max(s.col for s in vis) + 1
        canvas_w  = LEFT_MARGIN + max_col * COL_W + 60
        self._scroll_x = max(0, min(self._scroll_x, canvas_w - sw))
        # Y clamp: can only scroll UP (negative scroll would show blank above row 0 — disallow)
        # Max Y scroll = bottom of deepest row - viewport height
        max_row   = max(s.row for s in vis)
        canvas_h  = TOP_MARGIN + (max_row + 1) * ROW_H + 60
        clip_h    = sh - TOP_MARGIN - 140   # available tree viewport height
        self._scroll_y = max(0, min(self._scroll_y, max(0, canvas_h - TOP_MARGIN - clip_h)))

    def handle_mousedown(self, mx, my, sw, sh):
        # Check tab clicks (tab bar is at y=54..84)
        if 54 < my < 88:
            mid = sw // 2
            if mx < mid:
                self._active_tab = "normal"
                self._scroll_x = self._scroll_y = 0
                self.selected_id = None
            else:
                self._active_tab = "prestige"
                self._scroll_x = self._scroll_y = 0
                self.selected_id = None
            return
        self._drag_start  = (mx, my)
        self._drag_origin = (self._scroll_x, self._scroll_y)

    def handle_mousemove(self, mx, my, sw, sh):
        if self._drag_start:
            dx = mx - self._drag_start[0]
            dy = my - self._drag_start[1]
            self._scroll_x = self._drag_origin[0] - dx
            self._scroll_y = self._drag_origin[1] - dy

    def handle_mouseup(self, mx, my, sw, sh, skill_tree, player_xp):
        if self._drag_start:
            drag_dist = math.sqrt((mx - self._drag_start[0])**2 +
                                  (my - self._drag_start[1])**2)
            self._drag_start  = None
            self._drag_origin = None
            if drag_dist < 6:
                # Click — check reset buttons first
                if self._active_tab == "normal":
                    for branch, bx, by in self._reset_button_positions:
                        if abs(mx - bx) < 45 and abs(my - by) < 13:
                            if self._reset_branch == branch:
                                # Confirmed — do reset
                                skill_tree.reset_branch(branch)
                                self._reset_branch = None
                            elif skill_tree.branch_can_reset(branch):
                                self._reset_branch = branch
                            return
                # Click on a node
                cx, cy = self._screen_to_canvas(mx, my)
                for skill in self._visible_skills(skill_tree):
                    nx, ny = self._node_canvas_pos(skill)
                    if math.sqrt((cx - nx)**2 + (cy - ny)**2) < NODE_R + 8:
                        self.selected_id = skill.id
                        self._reset_branch = None
                        return
                self._reset_branch = None

    def scroll(self, dx, dy=0):
        self._scroll_x += dx
        self._scroll_y += dy

    def draw(self, surf, skill_tree, player_xp):
        sw, sh = surf.get_size()
        self._clamp_scroll(sw, sh, skill_tree)
        self._reset_button_positions = []

        # ── Dim background ────────────────────────────────────────────────
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 215))
        surf.blit(overlay, (0, 0))

        # ── Title row ─────────────────────────────────────────────────────
        title = self._f_head.render("SKILL TREE", True, (200, 220, 255))
        surf.blit(title, (sw // 2 - title.get_width() // 2, 10))

        # ── Tab bar ───────────────────────────────────────────────────────
        tab_y = 52
        tab_h = 30
        for i, (tab_id, label, tab_color) in enumerate([
            ("normal",   ">> SHIP UPGRADES",     (100, 180, 255)),
            ("prestige", "** PRESTIGE POWERS",   (255, 160, 50)),
        ]):
            tx = sw // 4 if i == 0 else 3 * sw // 4
            active = (tab_id == self._active_tab)
            bg = (20, 25, 50) if active else (8, 8, 20)
            border = tab_color if active else (40, 40, 60)
            pygame.draw.rect(surf, bg,     (tx - sw//4, tab_y, sw//2, tab_h))
            pygame.draw.rect(surf, border, (tx - sw//4, tab_y, sw//2, tab_h), 2)
            lbl = self._f_tab.render(label, True, tab_color if active else (60, 60, 80))
            surf.blit(lbl, (tx - lbl.get_width()//2, tab_y + 7))

        # ── XP / prestige points ──────────────────────────────────────────
        if self._active_tab == "normal":
            xp_lbl = self._f.render(f"Available XP: {player_xp}", True, (0, 220, 255))
            surf.blit(xp_lbl, (sw // 2 - xp_lbl.get_width() // 2, 88))
        else:
            pp = skill_tree.prestige_points
            pp_lbl = self._f.render(
                f"[P] Prestige Points: {pp}  (reset a maxed tree to earn more)",
                True, (255, 180, 50))
            surf.blit(pp_lbl, (sw // 2 - pp_lbl.get_width() // 2, 88))

        vis = self._visible_skills(skill_tree)
        if not vis:
            msg = self._f.render("Max out a regular tree branch and reset it to unlock prestige!", True, (200, 150, 50))
            surf.blit(msg, (sw//2 - msg.get_width()//2, sh//2))
            self._draw_detail(surf, skill_tree, player_xp, sw, sh)
            return

        # ── Branch headers + reset buttons ───────────────────────────────
        branch_cols = {}
        for sk in vis:
            branch_cols.setdefault(sk.branch, []).append(sk.col)

        for branch, cols in branch_cols.items():
            mid_col = (min(cols) + max(cols)) / 2
            bx_canvas = LEFT_MARGIN + mid_col * COL_W + COL_W // 2
            bx_screen, _ = self._canvas_to_screen(bx_canvas, 0)
            label_y = TOP_MARGIN - 14 - self._scroll_y
            if -80 < bx_screen < sw + 80 and label_y > 88:
                color = BRANCH_COLORS.get(branch, (200, 200, 200))
                lbl = self._f.render(BRANCH_DISPLAY.get(branch, branch.upper()), True, color)
                surf.blit(lbl, (bx_screen - lbl.get_width() // 2, label_y))

                # Reset button (normal tab only)
                if self._active_tab == "normal":
                    can_r = skill_tree.branch_can_reset(branch)
                    btn_y = label_y + 18
                    btn_col = (200, 80, 50) if can_r else (50, 50, 70)
                    pending = (self._reset_branch == branch)
                    btn_txt = "CONFIRM RESET?" if pending else ("RESET (+1 P)" if can_r else "needs capstone")
                    btn_surf = self._f_tiny.render(btn_txt, True, (255, 200, 80) if pending else btn_col)
                    bx_btn = bx_screen - btn_surf.get_width() // 2
                    if can_r or pending:
                        bg_r = pygame.Rect(bx_btn - 4, btn_y - 2, btn_surf.get_width() + 8, 16)
                        pygame.draw.rect(surf, (30, 10, 10), bg_r, border_radius=3)
                        pygame.draw.rect(surf, (200, 80, 50) if pending else (80, 30, 20), bg_r, 1, border_radius=3)
                    surf.blit(btn_surf, (bx_btn, btn_y))
                    self._reset_button_positions.append((branch, bx_screen, btn_y + 7))

        # ── Clipping region ───────────────────────────────────────────────
        clip_y  = TOP_MARGIN - 10
        clip_h  = sh - clip_y - 140
        surf.set_clip(pygame.Rect(0, clip_y, sw, clip_h))

        # ── Connection lines ──────────────────────────────────────────────
        for skill in vis:
            x2, y2   = self._node_canvas_pos(skill)
            sx2, sy2 = self._canvas_to_screen(x2, y2)
            for req_id in skill.requires:
                req = skill_tree.skills.get(req_id)
                if not req:
                    continue
                x1, y1   = self._node_canvas_pos(req)
                sx1, sy1 = self._canvas_to_screen(x1, y1)
                if max(sx1, sx2) < -10 or min(sx1, sx2) > sw + 10:
                    continue
                col = BRANCH_COLORS.get(skill.branch, (150,150,150)) if req.unlocked else (50,50,70)
                pygame.draw.line(surf, col, (int(sx1), int(sy1)), (int(sx2), int(sy2)), 2)

        # ── Nodes ─────────────────────────────────────────────────────────
        for skill in vis:
            cx, cy   = self._node_canvas_pos(skill)
            sx, sy   = self._canvas_to_screen(cx, cy)
            if sx < -NODE_R - 40 or sx > sw + NODE_R + 40:
                continue
            if sy < clip_y - NODE_R or sy > clip_y + clip_h + NODE_R:
                continue

            color  = BRANCH_COLORS.get(skill.branch, (200, 200, 200))
            is_sel = (skill.id == self.selected_id)
            can, _ = skill_tree.can_unlock(skill.id, player_xp)
            r = NODE_R

            if skill.unlocked:
                pygame.draw.circle(surf, color, (int(sx), int(sy)), r)
                pygame.draw.circle(surf, (255, 255, 255), (int(sx), int(sy)), r, 2)
            elif can:
                pygame.draw.circle(surf, (25, 25, 45), (int(sx), int(sy)), r)
                pygame.draw.circle(surf, color, (int(sx), int(sy)), r, 2)
            else:
                pygame.draw.circle(surf, (15, 15, 25), (int(sx), int(sy)), r)
                pygame.draw.circle(surf, (50, 50, 65), (int(sx), int(sy)), r, 1)

            if is_sel:
                pygame.draw.circle(surf, (255, 255, 100), (int(sx), int(sy)), r + 5, 2)

            # Prestige glow
            if skill.is_prestige and skill.unlocked:
                gs = pygame.Surface((r*3, r*3), pygame.SRCALPHA)
                pygame.draw.circle(gs, color + (35,), (r*3//2, r*3//2), r + 10)
                surf.blit(gs, (int(sx) - r*3//2, int(sy) - r*3//2))

            name_c = (255,255,255) if skill.unlocked else (color if can else (70,70,85))
            words  = skill.name.split()
            lines, cur = [], ""
            for w in words:
                if len(cur) + len(w) + 1 > 10 and cur:
                    lines.append(cur.strip()); cur = w
                else:
                    cur += " " + w
            if cur.strip():
                lines.append(cur.strip())
            for i, line in enumerate(lines[:2]):
                ls = self._f_tiny.render(line, True, name_c)
                surf.blit(ls, (int(sx) - ls.get_width()//2, int(sy) + r + 2 + i*13))

            if not skill.unlocked:
                cost_unit = "P" if skill.is_prestige else "xp"
                cost_c = (255, 180, 50) if skill.is_prestige else ((0, 200, 255) if can else (70,70,85))
                ct = self._f_tiny.render(f"{skill.cost}{cost_unit}", True, cost_c)
                surf.blit(ct, (int(sx) - ct.get_width()//2, int(sy) + r + 30))

        surf.set_clip(None)

        # ── Scroll arrows ─────────────────────────────────────────────────
        arrow_col = (120, 120, 160)
        pygame.draw.polygon(surf, arrow_col, [(18,sh//2-20),(18,sh//2+20),(4,sh//2)])
        pygame.draw.polygon(surf, arrow_col, [(sw-18,sh//2-20),(sw-18,sh//2+20),(sw-4,sh//2)])

        self._draw_detail(surf, skill_tree, player_xp, sw, sh)

    def _draw_detail(self, surf, skill_tree, player_xp, sw, sh):
        if self.selected_id and self.selected_id in skill_tree.skills:
            sk = skill_tree.skills[self.selected_id]
            panel_w = min(500, sw - 40)
            panel_h = 140
            px = sw // 2 - panel_w // 2
            py = sh - panel_h - 10
            pygame.draw.rect(surf, (8, 8, 26), (px, py, panel_w, panel_h), border_radius=8)
            color = BRANCH_COLORS.get(sk.branch, (200,200,200))
            pygame.draw.rect(surf, color, (px, py, panel_w, panel_h), 2, border_radius=8)

            # Prestige badge
            prefix = "[PRESTIGE] " if sk.is_prestige else ""
            nm  = self._f.render(prefix + sk.name, True, color)
            ds  = self._f_sm.render(sk.description, True, (210, 210, 210))
            cost_unit = "P prestige pts" if sk.is_prestige else "XP"
            ct  = self._f_sm.render(f"Cost: {sk.cost} {cost_unit}", True, (0, 200, 255) if not sk.is_prestige else (255,180,50))

            can, reason = skill_tree.can_unlock(sk.id, player_xp)
            if sk.unlocked:
                act = self._f_sm.render("✓ UNLOCKED", True, (100, 255, 100))
            elif can:
                act = self._f_sm.render("ENTER to unlock", True, (255, 220, 50))
            else:
                act = self._f_sm.render(reason, True, (200, 80, 80))

            surf.blit(nm,  (px + 10, py + 8))
            surf.blit(ds,  (px + 10, py + 34))
            surf.blit(ct,  (px + 10, py + 60))
            surf.blit(act, (px + 10, py + 86))
        else:
            hint = self._f_sm.render(
                "Click a node · drag/arrow-keys to scroll · TAB to close",
                True, (70, 70, 100))
            surf.blit(hint, (sw // 2 - hint.get_width() // 2, sh - 28))

    def try_unlock_selected(self, skill_tree, player_xp):
        if not self.selected_id:
            return player_xp, False
        ok, new_xp = skill_tree.unlock(self.selected_id, player_xp)
        return new_xp, ok
