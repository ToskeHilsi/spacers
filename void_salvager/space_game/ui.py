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

        # ── Boss HP bar (top-center) ──────────────────────────────────────
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

        # ── Zone indicator ────────────────────────────────────────────────
        zone_col = getattr(world.border, "color", (200,200,200))
        z_lbl = self._f_tiny.render(
            f"ZONE {world.current_zone}  |  Boss: {'ALIVE' if (boss and boss.alive) else 'DEFEATED'}",
            True, zone_col)
        surf.blit(z_lbl, (sw//2 - z_lbl.get_width()//2, 38))

        # ── Coordinates ───────────────────────────────────────────────────
        coord = self._f_tiny.render(
            f"X:{int(player.x)}  Y:{int(player.y)}", True, (80, 80, 120))
        surf.blit(coord, (mm_x, mm_y - 16))

        # ── Stealth / nebula indicator ────────────────────────────────────
        if player.is_stealthed:
            has_stealth_skill = stats.get("stealth", False)
            label = "[ STEALTH ACTIVE ]" if has_stealth_skill else "[ NEBULA COVER ]"
            color = (150, 255, 150) if has_stealth_skill else (100, 180, 255)
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

BRANCH_COLORS = {
    "weapons": (255, 120, 50),
    "defense": (80, 200, 255),
    "engine":  (100, 255, 130),
}

NODE_R      = 26    # node circle radius
COL_W       = 90    # pixels per column
ROW_H       = 110   # pixels per row
TOP_MARGIN  = 100   # space for header
LEFT_MARGIN = 30


class SkillTreeUI:
    def __init__(self):
        self._f      = _font(15, bold=True)
        self._f_sm   = _font(12)
        self._f_tiny = _font(11)
        self._f_head = _font(22, bold=True)
        self.selected_id = None
        self._scroll_x   = 0   # camera offset in canvas pixels
        self._drag_start = None
        self._drag_origin = None

    def _node_canvas_pos(self, skill):
        """Return (x, y) in canvas space."""
        x = LEFT_MARGIN + skill.col * COL_W + COL_W // 2
        y = TOP_MARGIN  + skill.row * ROW_H + ROW_H // 2
        return x, y

    def _canvas_to_screen(self, cx, cy, sw, sh):
        return cx - self._scroll_x, cy

    def _screen_to_canvas(self, sx, sy, sw, sh):
        return sx + self._scroll_x, sy

    def _clamp_scroll(self, sw):
        max_col = max(s.col for s in SKILL_TREE) + 1
        canvas_w = LEFT_MARGIN + max_col * COL_W + 60
        self._scroll_x = max(0, min(self._scroll_x, canvas_w - sw))

    def handle_mousedown(self, mx, my, sw, sh):
        self._drag_start  = (mx, my)
        self._drag_origin = self._scroll_x

    def handle_mousemove(self, mx, my, sw, sh):
        if self._drag_start:
            dx = mx - self._drag_start[0]
            self._scroll_x = self._drag_origin - dx
            self._clamp_scroll(sw)

    def handle_mouseup(self, mx, my, sw, sh, skill_tree, player_xp):
        """Select node on click (not drag)."""
        if self._drag_start:
            drag_dist = math.sqrt((mx - self._drag_start[0])**2 +
                                  (my - self._drag_start[1])**2)
            self._drag_start  = None
            self._drag_origin = None
            if drag_dist < 6:
                # It's a click — find nearest node
                cx, cy = self._screen_to_canvas(mx, my, sw, sh)
                for skill in skill_tree.skills.values():
                    nx, ny = self._node_canvas_pos(skill)
                    if math.sqrt((cx - nx)**2 + (cy - ny)**2) < NODE_R + 8:
                        self.selected_id = skill.id
                        return

    def scroll(self, dx):
        self._scroll_x += dx

    def draw(self, surf, skill_tree, player_xp):
        sw, sh = surf.get_size()
        self._clamp_scroll(sw)

        # ── Dim background ────────────────────────────────────────────────
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 215))
        surf.blit(overlay, (0, 0))

        # ── Header ────────────────────────────────────────────────────────
        title = self._f_head.render("SHIP SKILL TREE", True, (200, 220, 255))
        surf.blit(title, (sw // 2 - title.get_width() // 2, 12))

        xp_lbl = self._f.render(f"Available XP: {player_xp}", True, (0, 220, 255))
        surf.blit(xp_lbl, (sw // 2 - xp_lbl.get_width() // 2, 44))

        # Branch column headers
        branch_cols = {}
        for sk in skill_tree.skills.values():
            branch_cols.setdefault(sk.branch, []).append(sk.col)
        for branch, cols in branch_cols.items():
            mid_col = (min(cols) + max(cols)) / 2
            bx = LEFT_MARGIN + mid_col * COL_W + COL_W // 2 - self._scroll_x
            if -60 < bx < sw + 60:
                color = BRANCH_COLORS[branch]
                lbl = self._f.render(branch.upper(), True, color)
                surf.blit(lbl, (bx - lbl.get_width() // 2, 72))

        # ── Clipping region for tree (below header) ───────────────────────
        clip_top = 95
        surf.set_clip(pygame.Rect(0, clip_top, sw, sh - clip_top - 130))

        # ── Connection lines ──────────────────────────────────────────────
        for skill in skill_tree.skills.values():
            x2, y2 = self._node_canvas_pos(skill)
            sx2, sy2 = self._canvas_to_screen(x2, y2, sw, sh)
            for req_id in skill.requires:
                req = skill_tree.skills[req_id]
                x1, y1 = self._node_canvas_pos(req)
                sx1, sy1 = self._canvas_to_screen(x1, y1, sw, sh)
                # Skip if completely offscreen
                if max(sx1, sx2) < -10 or min(sx1, sx2) > sw + 10:
                    continue
                color = BRANCH_COLORS.get(skill.branch, (150,150,150)) if req.unlocked \
                        else (50, 50, 70)
                pygame.draw.line(surf, color, (sx1, sy1), (sx2, sy2), 2)

        # ── Skill nodes ───────────────────────────────────────────────────
        for skill in skill_tree.skills.values():
            cx, cy = self._node_canvas_pos(skill)
            sx, sy = self._canvas_to_screen(cx, cy, sw, sh)
            if sx < -NODE_R - 40 or sx > sw + NODE_R + 40:
                continue

            color  = BRANCH_COLORS.get(skill.branch, (200, 200, 200))
            is_sel = (skill.id == self.selected_id)
            can, _ = skill_tree.can_unlock(skill.id, player_xp)

            r = NODE_R
            if skill.unlocked:
                pygame.draw.circle(surf, color, (sx, sy), r)
                pygame.draw.circle(surf, (255, 255, 255), (sx, sy), r, 2)
            elif can:
                pygame.draw.circle(surf, (25, 25, 45), (sx, sy), r)
                pygame.draw.circle(surf, color, (sx, sy), r, 2)
            else:
                pygame.draw.circle(surf, (15, 15, 25), (sx, sy), r)
                pygame.draw.circle(surf, (50, 50, 65), (sx, sy), r, 1)

            if is_sel:
                pygame.draw.circle(surf, (255, 255, 100), (sx, sy), r + 5, 2)

            # Name (split to 2 short lines if needed)
            name_c = (255,255,255) if skill.unlocked else (color if can else (70,70,85))
            words  = skill.name.split()
            # Fit into ~2 lines of max ~10 chars each
            lines  = []
            cur    = ""
            for w in words:
                if len(cur) + len(w) + 1 > 10 and cur:
                    lines.append(cur.strip())
                    cur = w
                else:
                    cur += " " + w
            if cur.strip():
                lines.append(cur.strip())

            for i, line in enumerate(lines[:2]):
                lsurf = self._f_tiny.render(line, True, name_c)
                surf.blit(lsurf, (sx - lsurf.get_width() // 2,
                                  sy + r + 2 + i * 13))

            if not skill.unlocked:
                cost_c = (0, 200, 255) if can else (70, 70, 85)
                ct = self._f_tiny.render(f"{skill.cost}xp", True, cost_c)
                surf.blit(ct, (sx - ct.get_width() // 2, sy + r + 30))

        surf.set_clip(None)

        # ── Scroll arrows ─────────────────────────────────────────────────
        arrow_col = (120, 120, 160)
        # Left
        pygame.draw.polygon(surf, arrow_col, [(18,sh//2-20),(18,sh//2+20),(4,sh//2)])
        # Right
        pygame.draw.polygon(surf, arrow_col, [(sw-18,sh//2-20),(sw-18,sh//2+20),(sw-4,sh//2)])

        # ── Detail panel ──────────────────────────────────────────────────
        if self.selected_id and self.selected_id in skill_tree.skills:
            sk = skill_tree.skills[self.selected_id]
            panel_w, panel_h = min(420, sw - 40), 130
            px = sw // 2 - panel_w // 2
            py = sh - panel_h - 10
            pygame.draw.rect(surf, (8, 8, 26), (px, py, panel_w, panel_h), border_radius=8)
            pygame.draw.rect(surf, BRANCH_COLORS[sk.branch], (px, py, panel_w, panel_h), 2, border_radius=8)

            nm  = self._f.render(sk.name, True, BRANCH_COLORS[sk.branch])
            ds  = self._f_sm.render(sk.description, True, (210, 210, 210))
            ct  = self._f_sm.render(f"Cost: {sk.cost} XP  (TAB opens/closes)", True, (0, 200, 255))

            can, reason = skill_tree.can_unlock(sk.id, player_xp)
            if sk.unlocked:
                act = self._f_sm.render("✓ UNLOCKED", True, (100, 255, 100))
            elif can:
                act = self._f_sm.render("ENTER to unlock", True, (255, 220, 50))
            else:
                act = self._f_sm.render(reason, True, (200, 80, 80))

            surf.blit(nm,  (px + 10, py + 8))
            surf.blit(ds,  (px + 10, py + 34))
            surf.blit(ct,  (px + 10, py + 58))
            surf.blit(act, (px + 10, py + 84))
        else:
            hint = self._f_sm.render("Click a node to inspect  ·  drag or arrow keys to scroll",
                                     True, (70, 70, 100))
            surf.blit(hint, (sw // 2 - hint.get_width() // 2, sh - 28))

    def try_unlock_selected(self, skill_tree, player_xp):
        if not self.selected_id:
            return player_xp, False
        ok, new_xp = skill_tree.unlock(self.selected_id, player_xp)
        return new_xp, ok
