"""
game.py - Main game controller.
"""

import pygame
import math
import random

from sprites_manager import SpriteManager
from skill_tree import SkillTreeManager
from entities import Player, Bullet, Missile, Explosion, Boss
from world import World, StarField
from ui import HUD, SkillTreeUI


class GameState:
    PLAYING    = "playing"
    SKILL_TREE = "skill_tree"
    GAME_OVER  = "game_over"


class Game:
    CAMERA_SMOOTH = 6.0

    def __init__(self, screen):
        self.screen     = screen
        self.sprites    = SpriteManager()
        self.skill_tree = SkillTreeManager()
        self.hud        = HUD()
        self.skill_ui   = SkillTreeUI()
        self.state      = GameState.PLAYING
        self.starfield  = StarField()

        stats = self.skill_tree.compute_stats()
        self.player = Player(0, 0, self.sprites, stats)
        self.world  = World(self.sprites)

        sw, sh = screen.get_size()
        self._cam_x = float(-sw // 2)
        self._cam_y = float(-sh // 2)
        self._reveal_timer = 0.0
        self._go_font    = pygame.font.SysFont("monospace", 48, bold=True)
        self._go_sm_font = pygame.font.SysFont("monospace", 20)

        self.world.update_chunks(self.player.x, self.player.y)
        self.hud.add_message("VOID SALVAGER", 3.0, (0, 220, 255))
        self.hud.add_message("WASD: Move  SPACE: Fire  SHIFT: Boost  TAB: Skills", 4.0, (180, 180, 180))
        self.hud.add_message("Defeat the ZONE BOSS to expand your territory!", 5.0, (255, 160, 60))

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        if self.state == GameState.PLAYING:
            self._handle_playing(event)
        elif self.state == GameState.SKILL_TREE:
            self._handle_skill_tree(event)
        elif self.state == GameState.GAME_OVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self._restart()

    def _handle_playing(self, event):
        # Left-click: aim and fire toward cursor
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._aim_and_shoot(event.pos)
            return

        if event.type != pygame.KEYDOWN:
            return
        k = event.key
        if k == pygame.K_TAB:
            self.state = GameState.SKILL_TREE
        elif k in (pygame.K_LSHIFT, pygame.K_RSHIFT):
            if self.player.try_boost():
                self.hud.add_message("BOOST!", 0.5, (100, 220, 255))
        elif k == pygame.K_f:
            if self.player.try_warp():
                self.hud.add_message("WARP!", 0.6, (100, 200, 255))
        elif k == pygame.K_c:
            if self.player.try_stealth():
                self.hud.add_message("STEALTH ENGAGED", 1.0, (150, 255, 150))
        elif k == pygame.K_e:
            missiles = self.player.try_missile()
            if missiles:
                nearest, nd = None, float("inf")
                for enemy in self.world.enemies:
                    d = math.hypot(enemy.x - self.player.x, enemy.y - self.player.y)
                    if d < nd:
                        nd, nearest = d, enemy
                for missile in missiles:
                    missile.target = nearest
                    self.world.missiles.append(missile)
        elif k == pygame.K_q:
            if self.player.try_laser():
                self.hud.add_message("LASER!", 0.5, (255, 80, 80))
        elif k == pygame.K_r:
            self.sprites.reload()
            self.hud.add_message("Sprites reloaded!", 1.5, (255, 220, 50))

    def _handle_skill_tree(self, event):
        sw, sh = self.screen.get_size()
        if event.type == pygame.KEYDOWN:
            k = event.key
            if k in (pygame.K_TAB, pygame.K_ESCAPE):
                self.state = GameState.PLAYING
            elif k == pygame.K_RETURN:
                new_xp, ok = self.skill_ui.try_unlock_selected(self.skill_tree, self.player.xp)
                if ok:
                    self.player.xp = new_xp
                    self.player.refresh_skills(self.skill_tree.compute_stats())
                    sk = self.skill_tree.skills[self.skill_ui.selected_id]
                    self.hud.add_message(f"Unlocked: {sk.name}!", 2.5, (100, 255, 100))
                    # Check if branch just got maxed
                    for branch in ["weapons", "defense", "engine"]:
                        if self.skill_tree.branch_is_maxed(branch):
                            self.hud.add_message(
                                f"{branch.upper()} tree maxed! Reset it for a Prestige Point ★", 5.0, (255, 200, 50))
                            break
            elif k == pygame.K_LEFT:
                self.skill_ui.scroll(-60)
            elif k == pygame.K_RIGHT:
                self.skill_ui.scroll(60)
            elif k == pygame.K_DOWN:
                self.skill_ui.scroll(0, 60)
            elif k == pygame.K_UP:
                self.skill_ui.scroll(0, -60)
        elif event.type == pygame.MOUSEWHEEL:
            if self.state == GameState.SKILL_TREE:
                self.skill_ui.scroll(0, -event.y * 50)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.skill_ui.handle_mousedown(*event.pos, sw, sh)
        elif event.type == pygame.MOUSEMOTION:
            self.skill_ui.handle_mousemove(*event.pos, sw, sh)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.skill_ui.handle_mouseup(*event.pos, sw, sh, self.skill_tree, self.player.xp)

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        if self.state == GameState.GAME_OVER:
            return
        if self.state == GameState.SKILL_TREE:
            self.hud.update(dt)
            return

        keys = pygame.key.get_pressed()

        # Aim toward mouse cursor always; fire on SPACE or held left-click
        mx, my = pygame.mouse.get_pos()
        self._aim_at_screen(mx, my)

        p_stats = self.skill_tree.compute_stats()
        bspd_mult  = p_stats.get("bullet_speed_mult", 1.0)
        time_slow  = p_stats.get("time_slow", False)

        if keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0]:
            new_b = self.player.try_fire()
            if new_b:
                # Firing reveals position: break stealth skill and flag nebula reveal
                if self.player._stealth_t > 0:
                    self.player._stealth_t = 0.0
                    self.player.is_stealthed = False
                if any(dn.contains(self.player.x, self.player.y)
                       for dn in self.world.dense_nebulae):
                    self._reveal_timer = 3.0
            for b in new_b:
                b._speed_mult = bspd_mult
            self.world.bullets.extend(new_b)

        self.player.update(dt, keys)
        self.hud.update(dt)

        # Border update + player confinement
        self.world.border.update(dt)
        if self.world.border.confine(self.player):
            self.hud.add_message("BORDER — defeat the BOSS to escape!", 1.5, (255, 80, 80))

        self.world.update_chunks(self.player.x, self.player.y)

        for b in self.world.bullets:
            b.update(dt)
        for m in self.world.missiles:
            m.update(dt)

        # Update environment
        for asteroid in self.world.asteroids:
            asteroid.update(dt)
        for dn in self.world.dense_nebulae:
            dn.update(dt)

        # Nebula stealth — player is hidden if inside a nebula OR using stealth skill
        # Track a "revealed" timer: firing cancels nebula cover and breaks stealth skill
        in_nebula = any(dn.contains(self.player.x, self.player.y)
                        for dn in self.world.dense_nebulae)

        # Decrement reveal timer
        self._reveal_timer = max(0.0, self._reveal_timer - dt)

        # Player is stealthed if: (nebula AND not revealed) OR (skill stealth active)
        skill_stealth = self.player._stealth_t > 0   # skill-based stealth still ticking
        self.player.is_stealthed = (skill_stealth or (in_nebula and self._reveal_timer <= 0))

        for enemy in self.world.enemies:
            enemy.is_hidden = any(dn.contains(enemy.x, enemy.y)
                                  for dn in self.world.dense_nebulae)

        # Bullets blocked by asteroids
        asteroids = list(self.world.asteroids)
        for b in self.world.bullets:
            if not b.alive:
                continue
            for ast in asteroids:
                if ast.blocks_bullet(b):
                    # Ricochet bullets bounce, others die
                    if b.ricochet and not b._bounced:
                        nx = (b.x - ast.x) / max(1, ast.radius)
                        ny = (b.y - ast.y) / max(1, ast.radius)
                        b.bounce(nx, ny)
                    else:
                        b.alive = False
                    break

        # Enemy updates (includes boss in world.enemies)
        prev_bosses = set(id(b) for b in self.world.bosses)
        enemy_dt = dt * (0.45 if time_slow else 1.0)
        for enemy in list(self.world.enemies):
            new_b = enemy.update(enemy_dt, self.player)
            self.world.bullets.extend(new_b)

        # Wrecks
        for wreck in list(self.world.wrecks):
            if wreck.update(dt, self.player.x, self.player.y):
                self._give_xp(wreck.xp_value, wreck.x, wreck.y)

        # Pickups
        for p in self.world.pickups:
            p.update(dt, self.player.x, self.player.y)
        for e in self.world.explosions:
            e.update(dt)

        # Collect pickups
        pr = self.player.rect
        for pickup in self.world.pickups:
            if pickup.alive and pr.colliderect(pickup.rect):
                if pickup.kind == "xp":
                    self._give_xp(pickup.value, pickup.x, pickup.y)
                else:
                    heal = min(pickup.value, self.player.max_hp - int(self.player.hp))
                    self.player.heal(pickup.value)
                    if heal > 0:
                        self.hud.add_message(f"+{heal} HP", 0.8, (80, 255, 80))
                pickup.alive = False

        # Level up flash
        if self.player._level_up_pending:
            self.player._level_up_pending = False
            self.hud.add_message(
                f"LEVEL {self.player.level}!  +{self.player.LEVEL_HP_BONUS} HP  "
                f"+{self.player.LEVEL_DAMAGE_BONUS:.0f} DMG  "
                f"+{self.player.LEVEL_SPEED_BONUS:.0f} SPD",
                3.0, (255, 230, 80))

        # Player bullets → enemies
        for b in self.world.bullets:
            if not b.alive or b.owner != "player":
                continue
            for enemy in list(self.world.enemies):
                if not enemy.alive:
                    continue
                if b.rect.colliderect(enemy.rect):
                    b.alive = False
                    enemy.take_damage(b.damage)
                    if not enemy.alive:
                        self._on_enemy_killed(enemy)
                    break

        # Missiles → enemies
        for m in self.world.missiles:
            if not m.alive:
                continue
            for enemy in list(self.world.enemies):
                if not enemy.alive:
                    continue
                if m.rect.colliderect(enemy.rect):
                    m.alive = False
                    enemy.take_damage(m.damage)
                    self.world.spawn_explosion(m.x, m.y)
                    if not enemy.alive:
                        self._on_enemy_killed(enemy)
                    break

        # Laser
        if self.player.firing_laser:
            self._process_laser()

        # Enemy bullets → player
        pr = self.player.rect
        for b in self.world.bullets:
            if not b.alive or b.owner != "enemy":
                continue
            if b.rect.colliderect(pr):
                if random.random() < self.player.reflect_chance:
                    b.owner = "player"
                    b.dx, b.dy = -b.dx, -b.dy
                    self.hud.add_message("REFLECTED!", 0.6, (200, 255, 200))
                else:
                    b.alive = False
                    self.player.take_damage(b.damage)

        # Check if REQUIRED boss was just killed — expand zone
        for boss in list(self.world.bosses):
            if not boss.alive and getattr(boss, "_is_required", True):
                if id(boss) in prev_bosses:
                    new_zone = self.world.on_boss_killed(boss)
                    self.hud.add_message("ZONE BOSS DEFEATED!", 4.0, (255, 230, 50))
                    self.hud.add_message(f"ZONE {new_zone} UNLOCKED — border expanded!", 5.0, (100, 255, 100))
                    extra = self.world._extra_boss_count()
                    if extra > 0:
                        self.hud.add_message(f"WARNING: {extra} extra boss{'es' if extra>1 else ''} in this zone!", 4.0, (255, 100, 60))
                    break

        # Camera
        target_cx = self.player.x - self.screen.get_width()  // 2
        target_cy = self.player.y - self.screen.get_height() // 2
        a = min(1.0, self.CAMERA_SMOOTH * dt)
        self._cam_x += (target_cx - self._cam_x) * a
        self._cam_y += (target_cy - self._cam_y) * a

        self.world.remove_dead()

        if not self.player.alive:
            self.state = GameState.GAME_OVER

    def _aim_at_screen(self, mx, my):
        """Rotate player to face screen position (mx, my)."""
        wx = mx + self._cam_x
        wy = my + self._cam_y
        dx, dy = wx - self.player.x, wy - self.player.y
        if abs(dx) > 1 or abs(dy) > 1:
            self.player.angle = math.degrees(math.atan2(dy, dx))

    def _aim_and_shoot(self, screen_pos):
        """Instantly aim at screen_pos and fire."""
        self._aim_at_screen(*screen_pos)
        self.world.bullets.extend(self.player.try_fire())

    def _give_xp(self, amount, x, y):
        mult = self.skill_tree.compute_stats().get("xp_mult", 1.0)
        actual = int(amount * mult)
        self.player.gain_xp(actual)
        self.hud.add_message(f"+{actual} DATA", 1.0, (0, 200, 255))

    def _process_laser(self):
        dx = math.cos(math.radians(self.player.angle))
        dy = math.sin(math.radians(self.player.angle))
        dmg = self.player.damage * 3 / 60.0
        hit = set()
        for i in range(45):
            px = self.player.x + dx * i * 20
            py = self.player.y + dy * i * 20
            test = pygame.Rect(px-6, py-6, 12, 12)
            for enemy in self.world.enemies:
                if id(enemy) in hit or not enemy.alive:
                    continue
                if test.colliderect(enemy.rect):
                    enemy.take_damage(dmg)
                    hit.add(id(enemy))
                    if not enemy.alive:
                        self._on_enemy_killed(enemy)

    def _on_enemy_killed(self, enemy):
        self.world.spawn_explosion(enemy.x, enemy.y)
        self.world.spawn_pickup(enemy.x, enemy.y, "xp", enemy.XP_DROP)
        if random.random() < enemy.SCRAP_CHANCE:
            self.world.spawn_pickup(
                enemy.x + random.uniform(-20, 20),
                enemy.y + random.uniform(-20, 20),
                "scrap", random.randint(15, 40))
        is_boss = getattr(enemy, "is_boss", False)
        if is_boss:
            self.hud.add_message(f"BOSS DOWN! +{enemy.XP_DROP} XP", 3.0, (255, 230, 50))
        else:
            self.hud.add_message(f"DESTROYED! +{enemy.XP_DROP} XP", 1.5, (255, 180, 50))

    def _restart(self):
        old_tree = self.skill_tree
        old_ui   = self.skill_ui
        screen   = self.screen
        self.hud        = HUD()
        self.state      = GameState.PLAYING
        self.starfield  = StarField()
        self.skill_tree = old_tree
        self.skill_ui   = old_ui
        self.player = Player(0, 0, self.sprites, self.skill_tree.compute_stats())
        self.world  = World(self.sprites)
        sw, sh = screen.get_size()
        self._cam_x = float(-sw // 2)
        self._cam_y = float(-sh // 2)
        self._reveal_timer = 0.0
        self.world.update_chunks(self.player.x, self.player.y)
        self.hud.add_message("RESPAWNED — skills preserved", 3.0, (100, 255, 100))

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self):
        surf = self.screen
        sw, sh = surf.get_size()
        cx, cy = int(self._cam_x), int(self._cam_y)

        # Show/hide system cursor: visible in skill tree, hidden in play (crosshair replaces it)
        pygame.mouse.set_visible(self.state == GameState.SKILL_TREE)

        surf.fill((2, 4, 14))
        self.starfield.draw(surf, cx, cy)
        self.world.draw_nebulae(surf, cx, cy)

        # Dense nebulae (stealth clouds) — drawn early so entities appear on top
        for dn in self.world.dense_nebulae:
            dn.draw(surf, cx, cy)

        # Zone border
        self.world.border.draw(surf, cx, cy)

        # Asteroids (solid cover)
        for asteroid in self.world.asteroids:
            asteroid.draw(surf, cx, cy)

        for wreck in self.world.wrecks:
            wreck.draw(surf, cx, cy)
        for p in self.world.pickups:
            p.draw(surf, cx, cy)
        for e in self.world.explosions:
            e.draw(surf, cx, cy)

        # Regular enemies
        for enemy in self.world.enemies:
            if not getattr(enemy, "is_boss", False):
                enemy.draw(surf, cx, cy)

        # Boss on top (with glow)
        for boss in self.world.bosses:
            if boss.alive:
                self._draw_boss_glow(surf, cx, cy, boss)
                boss.draw(surf, cx, cy)

        self.player.draw(surf, cx, cy)
        self.player.draw_laser_beam(surf, cx, cy)

        for b in self.world.bullets:
            b.draw(surf, cx, cy)
        for m in self.world.missiles:
            m.draw(surf, cx, cy)

        if self.state != GameState.GAME_OVER:
            self.hud.draw(surf, self.player, self.world, self.skill_tree)

        if self.state == GameState.SKILL_TREE:
            self.skill_ui.draw(surf, self.skill_tree, self.player.xp)
        else:
            # Crosshair only when playing
            mx, my = pygame.mouse.get_pos()
            r = 10
            col = (200, 80, 80)
            pygame.draw.line(surf, col, (mx - r, my), (mx + r, my), 1)
            pygame.draw.line(surf, col, (mx, my - r), (mx, my + r), 1)
            pygame.draw.circle(surf, col, (mx, my), r, 1)

        if self.state == GameState.GAME_OVER:
            self._draw_game_over(surf, sw, sh)

    def _draw_boss_glow(self, surf, cx, cy, boss):
        bsx = boss.x - cx
        bsy = boss.y - cy
        gimmick_col = [(255,180,40),(255,80,80),(120,80,255),(80,200,255)][boss._gimmick]
        glow = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(glow, gimmick_col + (40,), (60, 60), 55)
        pygame.draw.circle(glow, gimmick_col + (20,), (60, 60), 50)
        surf.blit(glow, (bsx - 60, bsy - 60))

    def _draw_boss_hud(self, surf, sw, sh):
        boss = self.world.boss
        if not boss or not boss.alive:
            return
        f  = pygame.font.SysFont("monospace", 18, bold=True)
        ft = pygame.font.SysFont("monospace", 14)
        bar_w = 400
        bx = sw // 2 - bar_w // 2
        by = 20
        ratio = boss.hp / boss.max_hp
        phase_color = [(255, 160, 40), (80, 180, 255), (220, 50, 50)][boss._phase]
        pygame.draw.rect(surf, (40, 0, 0),   (bx, by, bar_w, 22))
        pygame.draw.rect(surf, phase_color,  (bx, by, int(bar_w * ratio), 22))
        pygame.draw.rect(surf, (200,200,200),(bx, by, bar_w, 22), 1)
        lbl = f.render(f"ZONE BOSS  [{boss.phase_name}]  {int(boss.hp)}/{boss.max_hp}", True, (255,255,255))
        surf.blit(lbl, (sw//2 - lbl.get_width()//2, by + 2))

        # Arrow pointing to boss if off-screen
        bdx = boss.x - self.player.x
        bdy = boss.y - self.player.y
        dist = math.hypot(bdx, bdy)
        if dist > 600:
            ang = math.atan2(bdy, bdx)
            ax = sw//2 + math.cos(ang) * min(sw//2 - 40, dist * 0.5 * sw / max(sw,sh))
            ay = sh//2 + math.sin(ang) * min(sh//2 - 40, dist * 0.5 * sh / max(sw,sh))
            # Clamp to screen edge
            margin = 30
            ax = max(margin, min(sw - margin, ax))
            ay = max(margin, min(sh - margin, ay))
            pygame.draw.circle(surf, phase_color, (int(ax), int(ay)), 8)
            pygame.draw.circle(surf, (255,255,255), (int(ax), int(ay)), 8, 2)
            dist_lbl = ft.render(f"{int(dist)}m", True, phase_color)
            surf.blit(dist_lbl, (int(ax) - dist_lbl.get_width()//2, int(ay) + 10))

    def _draw_game_over(self, surf, sw, sh):
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surf.blit(overlay, (0, 0))
        go  = self._go_font.render("YOU WERE DESTROYED", True, (220, 50, 50))
        lvl = self._go_sm_font.render(f"Reached Level {self.player.level}  —  Zone {self.world.current_zone}", True, (200, 180, 100))
        sk  = self._go_sm_font.render("Your skills are preserved — press R to respawn", True, (100, 255, 100))
        surf.blit(go,  (sw//2 - go.get_width()//2,  sh//2 - 70))
        surf.blit(lvl, (sw//2 - lvl.get_width()//2, sh//2 - 20))
        surf.blit(sk,  (sw//2 - sk.get_width()//2,  sh//2 + 20))
