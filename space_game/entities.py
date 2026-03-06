"""
entities.py - All game object classes.
"""

import pygame
import math
import random


def angle_to_vec(angle_deg):
    r = math.radians(angle_deg)
    return math.cos(r), math.sin(r)

def vec_length(vx, vy):
    return math.sqrt(vx * vx + vy * vy)

def normalize(vx, vy):
    l = vec_length(vx, vy)
    if l == 0:
        return 0.0, 0.0
    return vx / l, vy / l

def angle_diff(a, b):
    return (a - b + 540) % 360 - 180


# ── Player ────────────────────────────────────────────────────────────────────

class Player:
    BASE_SPEED      = 300.0
    BASE_MAX_HP     = 100
    BASE_FIRE_CD    = 0.18
    BASE_DAMAGE     = 15
    INVINCIBLE_TIME = 0.8
    WARP_DIST       = 600
    WARP_CD         = 3.5
    STEALTH_DUR     = 4.0
    STEALTH_CD      = 8.0
    MISSILE_CD      = 1.5
    LASER_CD        = 3.0
    LASER_DUR       = 0.6
    SHIELD_REGEN_CD = 4.0
    BOOST_SPEED     = 450.0
    BOOST_CD        = 3.0
    BOOST_ICE_TIME  = 1.4
    BOOST_FRICTION  = 0.995

    LEVEL_HP_BONUS     = 8
    LEVEL_DAMAGE_BONUS = 1.5
    LEVEL_SPEED_BONUS  = 6.0

    def __init__(self, x, y, sprite_mgr, skill_stats):
        self.x, self.y   = float(x), float(y)
        self.vx, self.vy = 0.0, 0.0
        self.angle       = -90.0
        self.sprite_mgr  = sprite_mgr
        self.skill_stats = skill_stats
        self._apply_skills()
        self.hp             = self.max_hp
        self.shield         = self.max_shield
        self._shield_dmg_cd = 0.0
        self._fire_cd     = 0.0
        self._inv_timer   = 0.0
        self._warp_cd     = 0.0
        self._stealth_cd  = 0.0
        self._stealth_t   = 0.0
        self._missile_cd  = 0.0
        self._laser_cd    = 0.0
        self._laser_t     = 0.0
        self._boost_cd    = 0.0
        self._ice_t       = 0.0
        self.is_stealthed = False
        self.firing_laser = False
        self.is_boosting  = False
        self.xp                = 0
        self.level             = 1
        self.xp_to_next        = 500
        self._level_up_pending = False

    def _apply_skills(self):
        s = self.skill_stats
        self.max_hp       = self.BASE_MAX_HP + s["max_hp_bonus"]
        self.max_shield   = s["shield"]
        self.max_speed    = self.BASE_SPEED + s["speed_bonus"]
        self.damage       = self.BASE_DAMAGE + s["damage_bonus"]
        self.fire_cd      = self.BASE_FIRE_CD * max(0.2, 1.0 - s["fire_rate_reduction"])
        self.regen        = s["regen"]
        self.reflect_chance = s["reflect_chance"]
        self.has_missile  = s["missile"]
        self.has_laser    = s["laser"]
        self.has_double   = s["double_shot"]
        self.has_triple   = s["triple_shot"]
        self.has_spread   = s["spread_shot"]
        self.has_ricochet = s["ricochet"]
        self.has_warp     = s["warp"]
        self.has_stealth  = s["stealth"]
        self.has_dual_missile = s["dual_missile"]
        self.boost_cd_base = max(0.4, self.BOOST_CD - s["boost_cd_reduction"])

    def refresh_skills(self, skill_stats):
        self.skill_stats = skill_stats
        level_hp  = (self.level - 1) * self.LEVEL_HP_BONUS
        level_dmg = (self.level - 1) * self.LEVEL_DAMAGE_BONUS
        level_spd = (self.level - 1) * self.LEVEL_SPEED_BONUS
        prev_max_hp     = self.max_hp
        prev_max_shield = self.max_shield
        self._apply_skills()
        self.max_hp    += level_hp
        self.damage    += level_dmg
        self.max_speed += level_spd
        self.hp     = min(self.max_hp,     self.hp    + max(0, self.max_hp    - prev_max_hp))
        self.shield = min(self.max_shield, self.shield + max(0, self.max_shield - prev_max_shield))

    @property
    def rect(self):
        img = self.sprite_mgr.get("player_ship")
        w, h = img.get_size()
        return pygame.Rect(self.x - w//2, self.y - h//2, w, h)

    @property
    def alive(self):
        return self.hp > 0

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def take_damage(self, amount):
        if self._inv_timer > 0:
            return
        if self.shield > 0:
            absorbed = min(self.shield, amount)
            self.shield -= absorbed
            amount -= absorbed
            self._shield_dmg_cd = self.SHIELD_REGEN_CD
        if amount > 0:
            self.hp -= amount
            self._inv_timer = self.INVINCIBLE_TIME

    def gain_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.35)
            self.max_hp    += self.LEVEL_HP_BONUS
            self.hp         = min(self.max_hp, self.hp + self.LEVEL_HP_BONUS)
            self.damage    += self.LEVEL_DAMAGE_BONUS
            self.max_speed += self.LEVEL_SPEED_BONUS
            self._level_up_pending = True

    def try_warp(self):
        if self.has_warp and self._warp_cd <= 0:
            dx, dy = angle_to_vec(self.angle)
            self.x += dx * self.WARP_DIST
            self.y += dy * self.WARP_DIST
            self._warp_cd = self.WARP_CD
            return True
        return False

    def try_stealth(self):
        if self.has_stealth and self._stealth_cd <= 0 and not self.is_stealthed:
            self.is_stealthed = True
            self._stealth_t   = self.STEALTH_DUR
            self._stealth_cd  = self.STEALTH_CD
            return True
        return False

    def try_boost(self):
        if self._boost_cd > 0:
            return False
        dx, dy = angle_to_vec(self.angle)
        self.vx = dx * self.BOOST_SPEED
        self.vy = dy * self.BOOST_SPEED
        self._boost_cd   = self.boost_cd_base
        self._ice_t      = self.BOOST_ICE_TIME
        self.is_boosting = True
        return True

    def update(self, dt, keys):
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            self.angle -= 180 * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle += 180 * dt
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dx, dy = angle_to_vec(self.angle)
            accel = (self.max_speed * 3.5) * (0.25 if self._ice_t > 0 else 1.0)
            self.vx += dx * accel * dt
            self.vy += dy * accel * dt

        spd = vec_length(self.vx, self.vy)
        top = max(self.max_speed, spd if self._ice_t > 0 else 0)
        if spd > top:
            self.vx = self.vx / spd * top
            self.vy = self.vy / spd * top

        friction = self.BOOST_FRICTION if self._ice_t > 0 else 0.985
        self.vx *= (friction ** (dt * 60))
        self.vy *= (friction ** (dt * 60))

        self.x += self.vx * dt
        self.y += self.vy * dt

        self._fire_cd    = max(0, self._fire_cd    - dt)
        self._inv_timer  = max(0, self._inv_timer  - dt)
        self._warp_cd    = max(0, self._warp_cd    - dt)
        self._stealth_cd = max(0, self._stealth_cd - dt)
        self._missile_cd = max(0, self._missile_cd - dt)
        self._laser_cd   = max(0, self._laser_cd   - dt)
        self._boost_cd   = max(0, self._boost_cd   - dt)

        if self._ice_t > 0:
            self._ice_t -= dt
            if self._ice_t <= 0:
                self.is_boosting = False
        if self.is_stealthed:
            self._stealth_t -= dt
            if self._stealth_t <= 0:
                self.is_stealthed = False
        if self.firing_laser:
            self._laser_t -= dt
            if self._laser_t <= 0:
                self.firing_laser = False
        if self.regen > 0:
            self.hp = min(self.max_hp, self.hp + self.regen * dt)
        if self.max_shield > 0 and self.shield < self.max_shield:
            self._shield_dmg_cd -= dt
            if self._shield_dmg_cd <= 0:
                self.shield = min(self.max_shield, self.shield + 10 * dt)

    def try_fire(self):
        if self._fire_cd > 0:
            return []
        self._fire_cd = self.fire_cd
        dx, dy = angle_to_vec(self.angle)
        bullets = []
        if self.has_triple:
            for sa in (-18, 0, 18):
                a2 = self.angle + sa
                bx, by = math.cos(math.radians(a2)), math.sin(math.radians(a2))
                bullets.append(Bullet(self.x, self.y, bx, by, self.damage,
                                      self.sprite_mgr, owner="player",
                                      ricochet=self.has_ricochet))
        elif self.has_double:
            perp = (-dy, dx)
            for sign in (-1, 1):
                ox, oy = perp[0]*sign*10, perp[1]*sign*10
                bullets.append(Bullet(self.x+ox, self.y+oy, dx, dy, self.damage,
                                      self.sprite_mgr, owner="player",
                                      ricochet=self.has_ricochet))
        else:
            bullets.append(Bullet(self.x, self.y, dx, dy, self.damage,
                                  self.sprite_mgr, owner="player",
                                  ricochet=self.has_ricochet))
        if self.has_spread:
            for sa in (-28, 28):
                a2 = self.angle + sa
                bx, by = math.cos(math.radians(a2)), math.sin(math.radians(a2))
                bullets.append(Bullet(self.x, self.y, bx, by, self.damage * 0.8,
                                      self.sprite_mgr, owner="player",
                                      ricochet=self.has_ricochet))
        return bullets

    def try_missile(self):
        if not self.has_missile or self._missile_cd > 0:
            return []
        self._missile_cd = self.MISSILE_CD
        dx, dy = math.cos(math.radians(self.angle)), math.sin(math.radians(self.angle))
        missiles = [Missile(self.x, self.y, dx, dy, self.damage * 2.5, self.sprite_mgr)]
        if self.has_dual_missile:
            # Second missile offset 20px to the side
            perp_x, perp_y = -dy, dx
            m2 = Missile(self.x + perp_x * 20, self.y + perp_y * 20,
                         dx, dy, self.damage * 2.5, self.sprite_mgr)
            missiles.append(m2)
        return missiles

    def try_laser(self):
        if not self.has_laser or self._laser_cd > 0 or self.firing_laser:
            return False
        self._laser_cd    = self.LASER_CD
        self._laser_t     = self.LASER_DUR
        self.firing_laser = True
        return True

    def draw(self, surf, cam_x, cam_y):
        img = self.sprite_mgr.get("player_ship")
        rotated = pygame.transform.rotate(img, -self.angle - 90)
        alpha = 80 if self.is_stealthed else 255
        if self._inv_timer > 0:
            alpha = int(128 + 127 * math.sin(self._inv_timer * 30))
        rotated.set_alpha(alpha)
        sx = self.x - cam_x - rotated.get_width()  // 2
        sy = self.y - cam_y - rotated.get_height() // 2
        surf.blit(rotated, (sx, sy))
        if not self.is_stealthed:
            fx = self.x - cam_x - math.cos(math.radians(self.angle)) * 22
            fy = self.y - cam_y - math.sin(math.radians(self.angle)) * 22
            fs = pygame.Surface((10, 14), pygame.SRCALPHA)
            pygame.draw.ellipse(fs, (255, 140, 0, 180), (0, 0, 10, 14))
            surf.blit(fs, (fx - 5, fy - 7))
            if self._ice_t > 0:
                intensity = int(255 * (self._ice_t / self.BOOST_ICE_TIME))
                trail_len = int(60 * (self._ice_t / self.BOOST_ICE_TIME))
                spd = vec_length(self.vx, self.vy)
                if spd > 10:
                    bdx, bdy = -self.vx / spd, -self.vy / spd
                    for i in range(3):
                        tx = self.x - cam_x + bdx * (i * trail_len // 3)
                        ty = self.y - cam_y + bdy * (i * trail_len // 3)
                        r  = max(1, 5 - i)
                        a  = max(0, intensity - i * 60)
                        ts = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
                        pygame.draw.circle(ts, (100, 220, 255, a), (r+1, r+1), r)
                        surf.blit(ts, (tx-r-1, ty-r-1))

    def draw_laser_beam(self, surf, cam_x, cam_y):
        if not self.firing_laser:
            return
        dx, dy = angle_to_vec(self.angle)
        ex = self.x + dx * 900 - cam_x
        ey = self.y + dy * 900 - cam_y
        sx, sy = self.x - cam_x, self.y - cam_y
        pygame.draw.line(surf, (255, 60, 60), (sx, sy), (ex, ey), 4)
        pygame.draw.line(surf, (255, 200, 200), (sx, sy), (ex, ey), 2)


# ── Bullet ────────────────────────────────────────────────────────────────────

class Bullet:
    SPEED    = 620.0
    LIFETIME = 1.8

    def __init__(self, x, y, dx, dy, damage, sprite_mgr, owner="player", ricochet=False):
        self.x, self.y   = float(x), float(y)
        ndx, ndy = normalize(dx, dy)
        self.dx, self.dy = ndx, ndy
        self.damage      = damage
        self.owner       = owner
        self.sprite_mgr  = sprite_mgr
        self._life       = self.LIFETIME
        self.alive       = True
        self.ricochet    = ricochet
        self._bounced    = False
        self._speed_mult = 1.0   # prestige bullet speed multiplier

    @property
    def rect(self):
        return pygame.Rect(self.x - 4, self.y - 8, 8, 16)

    def bounce(self, nx, ny):
        if self._bounced or not self.ricochet:
            self.alive = False
            return
        dot = self.dx * nx + self.dy * ny
        self.dx -= 2 * dot * nx
        self.dy -= 2 * dot * ny
        self._bounced = True

    def update(self, dt):
        self.x += self.dx * self.SPEED * self._speed_mult * dt
        self.y += self.dy * self.SPEED * self._speed_mult * dt
        self._life -= dt
        if self._life <= 0:
            self.alive = False

    def draw(self, surf, cam_x, cam_y):
        key = "bullet_player" if self.owner == "player" else "bullet_enemy"
        img = self.sprite_mgr.get(key)
        angle = math.degrees(math.atan2(self.dy, self.dx)) + 90
        rotated = pygame.transform.rotate(img, -angle)
        sx = self.x - cam_x - rotated.get_width()  // 2
        sy = self.y - cam_y - rotated.get_height() // 2
        surf.blit(rotated, (sx, sy))


# ── Missile ───────────────────────────────────────────────────────────────────

class Missile:
    SPEED    = 380.0
    TURN     = 120.0
    LIFETIME = 4.0

    def __init__(self, x, y, dx, dy, damage, sprite_mgr):
        self.x, self.y = float(x), float(y)
        self.angle     = math.degrees(math.atan2(dy, dx))
        self.damage    = damage
        self.sprite_mgr = sprite_mgr
        self._life     = self.LIFETIME
        self.alive     = True
        self.target    = None

    @property
    def rect(self):
        return pygame.Rect(self.x - 5, self.y - 10, 10, 20)

    def update(self, dt):
        if self.target and getattr(self.target, "alive", False):
            tx, ty = self.target.x, self.target.y
            desired = math.degrees(math.atan2(ty - self.y, tx - self.x))
            diff = angle_diff(desired, self.angle)
            turn = self.TURN * dt
            self.angle += max(-turn, min(turn, diff))
        dx, dy = angle_to_vec(self.angle)
        self.x += dx * self.SPEED * dt
        self.y += dy * self.SPEED * dt
        self._life -= dt
        if self._life <= 0:
            self.alive = False

    def draw(self, surf, cam_x, cam_y):
        img = self.sprite_mgr.get("missile")
        rotated = pygame.transform.rotate(img, -self.angle - 90)
        sx = self.x - cam_x - rotated.get_width()  // 2
        sy = self.y - cam_y - rotated.get_height() // 2
        surf.blit(rotated, (sx, sy))


# ── Asteroid (solid cover, blocks bullets) ────────────────────────────────────

class Asteroid:
    def __init__(self, x, y, radius):
        self.x, self.y = float(x), float(y)
        self.radius    = radius
        self._angle    = random.uniform(0, 360)
        self._spin     = random.uniform(-8, 8)
        # Pre-bake per-vertex radius offsets so shape is stable each frame
        sides = 10
        rng = random.Random(int(x * 1000 + y))
        self._jags = [rng.uniform(0.65, 1.0) for _ in range(sides)]
        self._sides = sides

    def update(self, dt):
        self._angle += self._spin * dt

    def blocks_bullet(self, bullet):
        dx = bullet.x - self.x
        dy = bullet.y - self.y
        return (dx*dx + dy*dy) < self.radius * self.radius

    def draw(self, surf, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r  = self.radius
        sw, sh = surf.get_size()
        if sx < -r or sx > sw+r or sy < -r or sy > sh+r:
            return
        pts = []
        for i in range(self._sides):
            a   = math.radians(self._angle + 360 * i / self._sides)
            jag = r * self._jags[i]
            pts.append((sx + math.cos(a) * jag, sy + math.sin(a) * jag))
        pygame.draw.polygon(surf, (90, 85, 80), pts)
        pygame.draw.polygon(surf, (130, 120, 110), pts, 2)

    def draw_minimap(self, mm_surf, px, py, mm_size, mm_scale):
        ex = mm_size // 2 + int((self.x - px) * mm_scale)
        ey = mm_size // 2 + int((self.y - py) * mm_scale)
        if 0 <= ex < mm_size and 0 <= ey < mm_size:
            pygame.draw.circle(mm_surf, (100, 95, 90), (ex, ey), max(1, int(self.radius * mm_scale)))


# ── Dense Nebula (stealth cloud — hides anyone inside) ────────────────────────

class DenseNebula:
    def __init__(self, x, y, radius, color):
        self.x, self.y = float(x), float(y)
        self.radius    = radius
        self.color     = color
        self._pulse    = random.uniform(0, math.tau)

    def contains(self, ex, ey):
        dx, dy = ex - self.x, ey - self.y
        return dx*dx + dy*dy < self.radius * self.radius

    def update(self, dt):
        self._pulse += dt * 0.8

    def draw(self, surf, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r  = self.radius
        sw, sh = surf.get_size()
        if sx < -r or sx > sw+r or sy < -r or sy > sh+r:
            return
        pulse_alpha = int(55 + 20 * math.sin(self._pulse))
        neb = pygame.Surface((int(r*2), int(r*2)), pygame.SRCALPHA)
        pygame.draw.circle(neb, self.color + (pulse_alpha,),    (int(r), int(r)), int(r))
        pygame.draw.circle(neb, self.color + (pulse_alpha//2,), (int(r), int(r)), int(r * 0.6))
        surf.blit(neb, (sx - r, sy - r))

    def draw_minimap(self, mm_surf, px, py, mm_size, mm_scale):
        ex = mm_size // 2 + int((self.x - px) * mm_scale)
        ey = mm_size // 2 + int((self.y - py) * mm_scale)
        r_mm = max(2, int(self.radius * mm_scale))
        tmp = pygame.Surface((mm_size, mm_size), pygame.SRCALPHA)
        pygame.draw.circle(tmp, self.color + (60,), (ex, ey), r_mm)
        mm_surf.blit(tmp, (0, 0))


# ── Enemy base ────────────────────────────────────────────────────────────────

class Enemy:
    FIRE_CD        = 2.0
    DAMAGE         = 10
    SPEED          = 120.0
    DETECT_R       = 500.0
    PATROL_R       = 300.0
    XP_DROP        = 80
    SCRAP_CHANCE   = 0.4
    PREFERRED_DIST = 280.0
    STRAFE_SPEED   = 0.8
    VOLLEY_SHOTS   = 1

    def __init__(self, x, y, sprite_key, hp, sprite_mgr):
        self.x, self.y      = float(x), float(y)
        self.vx, self.vy    = 0.0, 0.0
        self.angle          = random.uniform(0, 360)
        self.sprite_key     = sprite_key
        self.max_hp         = hp
        self.hp             = hp
        self.sprite_mgr     = sprite_mgr
        self._fire_cd       = random.uniform(0.5, self.FIRE_CD)
        self.alive          = True
        self.patrol_origin  = (x, y)
        self._patrol_target = self._rand_patrol()
        self._state         = "patrol"
        self._strafe_dir    = random.choice([-1, 1])
        self._strafe_timer  = random.uniform(1.5, 3.5)
        self._aim_error     = random.uniform(-0.06, 0.06)
        self.is_hidden      = False
        self.zone_tint      = None   # set by world on spawn

    def _rand_patrol(self):
        ox, oy = self.patrol_origin
        return (ox + random.uniform(-self.PATROL_R, self.PATROL_R),
                oy + random.uniform(-self.PATROL_R, self.PATROL_R))

    @property
    def rect(self):
        img = self.sprite_mgr.get(self.sprite_key)
        w, h = img.get_size()
        return pygame.Rect(self.x - w//2, self.y - h//2, w, h)

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def _set_velocity(self, vx, vy):
        self.vx, self.vy = vx, vy
        if vec_length(vx, vy) > 1:
            self.angle = math.degrees(math.atan2(vy, vx)) - 90

    def _lead_shot(self, px, py, pvx, pvy):
        dx, dy = px - self.x, py - self.y
        dist   = max(1, vec_length(dx, dy))
        t      = dist / Bullet.SPEED
        ldx    = (px + pvx * t) - self.x
        ldy    = (py + pvy * t) - self.y
        nx, ny = normalize(ldx + self._aim_error, ldy + self._aim_error)
        return nx, ny

    def update(self, dt, player):
        if not self.alive:
            return []

        pdx = player.x - self.x
        pdy = player.y - self.y
        dist = vec_length(pdx, pdy)

        # Hidden enemies don't detect player either
        if player.is_stealthed or self.is_hidden:
            self._state = "patrol"
        elif dist < self.DETECT_R:
            self._state = "combat"
        else:
            self._state = "patrol"

        self._strafe_timer -= dt
        if self._strafe_timer <= 0:
            self._strafe_dir   = -self._strafe_dir
            self._strafe_timer = random.uniform(1.5, 3.5)
            self._aim_error    = random.uniform(-0.06, 0.06)

        bullets = []
        if self._state == "combat":
            self._update_combat(dt, player, dist, pdx, pdy, bullets)
        else:
            self._update_patrol(dt)

        self.x += self.vx * dt
        self.y += self.vy * dt
        return bullets

    def _update_combat(self, dt, player, dist, pdx, pdy, bullets):
        nx, ny = normalize(pdx, pdy)
        sx, sy = -ny * self._strafe_dir, nx * self._strafe_dir
        gap    = dist - self.PREFERRED_DIST
        approach = max(-1.0, min(1.0, gap / 200.0))
        move_x, move_y = normalize(nx * approach + sx * self.STRAFE_SPEED,
                                   ny * approach + sy * self.STRAFE_SPEED)
        self._set_velocity(move_x * self.SPEED, move_y * self.SPEED)

        self._fire_cd -= dt
        if self._fire_cd <= 0 and dist < self.DETECT_R * 0.9:
            self._fire_cd = self.FIRE_CD + random.uniform(-0.2, 0.4)
            bx, by = self._lead_shot(player.x, player.y,
                                     getattr(player, "vx", 0), getattr(player, "vy", 0))
            for _ in range(self.VOLLEY_SHOTS):
                sp = random.uniform(-0.05, 0.05)
                bullets.append(Bullet(self.x, self.y, bx+sp, by+sp,
                                      self.DAMAGE, self.sprite_mgr, owner="enemy"))

    def _update_patrol(self, dt):
        tx, ty = self._patrol_target
        dx, dy = tx - self.x, ty - self.y
        if vec_length(dx, dy) < 20:
            self._patrol_target = self._rand_patrol()
        nx, ny = normalize(dx, dy)
        self._set_velocity(nx * self.SPEED * 0.5, ny * self.SPEED * 0.5)

    def draw(self, surf, cam_x, cam_y):
        img = self.sprite_mgr.get(self.sprite_key)
        alpha = 60 if self.is_hidden else 255
        rotated = pygame.transform.rotate(img, -self.angle - 90)
        # Apply zone color tint
        if self.zone_tint and not self.is_hidden:
            tinted = rotated.copy()
            tint_surf = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
            tint_surf.fill(self.zone_tint + (0,))  # RGB only, no alpha change
            tinted.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            rotated = tinted
        rotated.set_alpha(alpha)
        sx = self.x - cam_x - rotated.get_width()  // 2
        sy = self.y - cam_y - rotated.get_height() // 2
        surf.blit(rotated, (sx, sy))
        if not self.is_hidden:
            bar_w = img.get_width()
            ratio = self.hp / self.max_hp
            bar_x = self.x - cam_x - bar_w // 2
            bar_y = self.y - cam_y - img.get_height() // 2 - 8
            pygame.draw.rect(surf, (80, 0, 0),    (bar_x, bar_y, bar_w, 4))
            pygame.draw.rect(surf, (220, 40, 40), (bar_x, bar_y, int(bar_w * ratio), 4))


class Scout(Enemy):
    FIRE_CD = 1.2; DAMAGE = 7;  SPEED = 200.0; DETECT_R = 500.0
    XP_DROP = 60;  SCRAP_CHANCE = 0.3
    PREFERRED_DIST = 200.0; STRAFE_SPEED = 1.4; VOLLEY_SHOTS = 1
    def __init__(self, x, y, sprite_mgr):
        super().__init__(x, y, "enemy_scout", 40, sprite_mgr)

class Cruiser(Enemy):
    FIRE_CD = 1.6; DAMAGE = 13; SPEED = 110.0; DETECT_R = 560.0
    XP_DROP = 150; SCRAP_CHANCE = 0.5
    PREFERRED_DIST = 320.0; STRAFE_SPEED = 0.7; VOLLEY_SHOTS = 2
    def __init__(self, x, y, sprite_mgr):
        super().__init__(x, y, "enemy_cruiser", 100, sprite_mgr)

class Dreadnought(Enemy):
    FIRE_CD = 2.0; DAMAGE = 20; SPEED = 65.0; DETECT_R = 640.0
    XP_DROP = 300; SCRAP_CHANCE = 0.7
    PREFERRED_DIST = 400.0; STRAFE_SPEED = 0.4; VOLLEY_SHOTS = 3
    def __init__(self, x, y, sprite_mgr):
        super().__init__(x, y, "enemy_dreadnought", 220, sprite_mgr)


# ── Boss ──────────────────────────────────────────────────────────────────────
# Each zone boss behaves like a stronger normal enemy but with ONE unique gimmick.
# Gimmicks cycle by zone index mod 4.

class Boss(Enemy):
    FIRE_CD        = 1.8
    DAMAGE         = 20
    SPEED          = 95.0
    DETECT_R       = 9999.0
    XP_DROP        = 1200
    SCRAP_CHANCE   = 1.0
    PREFERRED_DIST = 320.0
    STRAFE_SPEED   = 0.85
    VOLLEY_SHOTS   = 2

    # Gimmick names shown in HUD
    GIMMICK_NAMES = [
        "TWIN GUNS",      # zone 0: fires two parallel shots
        "CHARGE",         # zone 1: occasionally charges
        "RING BURST",     # zone 2: ring shot on cooldown
        "MIRROR",         # zone 3: reflects bullets back
    ]

    def __init__(self, x, y, sprite_mgr, zone, hp_scale=1.0):
        hp = int(500 * (1 + zone * 0.55) * hp_scale)
        super().__init__(x, y, "enemy_dreadnought", hp, sprite_mgr)
        self.zone         = zone
        self.DAMAGE       = int(18 * (1 + zone * 0.25))
        self.SPEED        = 95 + zone * 8
        self.is_boss      = True
        self._gimmick     = zone % 4
        # Gimmick-specific timers
        self._gimmick_cd  = 0.0
        self._charge_t    = 0.0
        self._charge_vx   = 0.0
        self._charge_vy   = 0.0
        self.reflect_chance = 0.0  # set per gimmick

    @property
    def phase_name(self):
        return self.GIMMICK_NAMES[self._gimmick]

    def _update_combat(self, dt, player, dist, pdx, pdy, bullets):
        # Normal strafing AI
        nx, ny = normalize(pdx, pdy)
        sx, sy = -ny * self._strafe_dir, nx * self._strafe_dir
        gap    = dist - self.PREFERRED_DIST
        approach = max(-1.0, min(1.0, gap / 200.0))
        move_x, move_y = normalize(nx * approach + sx * self.STRAFE_SPEED,
                                   ny * approach + sy * self.STRAFE_SPEED)

        # Charge gimmick overrides movement when active
        if self._gimmick == 1 and self._charge_t > 0:
            self._charge_t -= dt
            self.vx, self.vy = self._charge_vx, self._charge_vy
            if vec_length(self._charge_vx, self._charge_vy) > 1:
                self.angle = math.degrees(math.atan2(self._charge_vy, self._charge_vx)) - 90
        else:
            self._set_velocity(move_x * self.SPEED, move_y * self.SPEED)

        # Normal firing
        self._fire_cd -= dt
        if self._fire_cd <= 0 and dist < self.DETECT_R:
            self._fire_cd = self.FIRE_CD + random.uniform(-0.3, 0.5)
            bx, by = self._lead_shot(player.x, player.y,
                                     getattr(player, "vx", 0), getattr(player, "vy", 0))

            if self._gimmick == 0:
                # Twin guns: two parallel shots
                perp = (-by, bx)
                for sign in (-1, 1):
                    ox, oy = perp[0]*sign*14, perp[1]*sign*14
                    bullets.append(Bullet(self.x+ox, self.y+oy, bx, by,
                                          self.DAMAGE, self.sprite_mgr, owner="enemy"))
            else:
                # Standard shots (2 volley)
                for _ in range(2):
                    sp = random.uniform(-0.05, 0.05)
                    bullets.append(Bullet(self.x, self.y, bx+sp, by+sp,
                                          self.DAMAGE, self.sprite_mgr, owner="enemy"))

        # Gimmick cooldown abilities
        self._gimmick_cd -= dt
        if self._gimmick_cd <= 0:
            if self._gimmick == 1:
                # Charge: wind up a dash toward player
                if dist < 500:
                    nx2, ny2 = normalize(pdx, pdy)
                    self._charge_vx = nx2 * self.SPEED * 2.4
                    self._charge_vy = ny2 * self.SPEED * 2.4
                    self._charge_t  = 0.5
                self._gimmick_cd = random.uniform(3.5, 5.5)

            elif self._gimmick == 2:
                # Ring burst: fire outward ring
                count = 12 + self.zone
                for i in range(count):
                    a = math.radians(360 / count * i)
                    bullets.append(Bullet(self.x, self.y, math.cos(a), math.sin(a),
                                          self.DAMAGE * 0.7, self.sprite_mgr, owner="enemy"))
                self._gimmick_cd = random.uniform(4.0, 6.0)

            elif self._gimmick == 3:
                # Mirror: temporarily reflect bullets
                self.reflect_chance = 0.6
                self._gimmick_cd = random.uniform(5.0, 8.0)
            else:
                self._gimmick_cd = random.uniform(3.0, 5.0)

        # Decay mirror reflect over time
        if self._gimmick == 3 and self.reflect_chance > 0:
            self.reflect_chance = max(0.0, self.reflect_chance - dt * 0.15)

    def draw(self, surf, cam_x, cam_y):
        super().draw(surf, cam_x, cam_y)
        img = self.sprite_mgr.get(self.sprite_key)
        bar_w = img.get_width() * 2 + 20
        ratio = max(0, self.hp / self.max_hp)
        bx = self.x - cam_x - bar_w // 2
        by = self.y - cam_y - img.get_height() // 2 - 20
        gimmick_col = [(255,180,40),(255,80,80),(120,80,255),(80,200,255)][self._gimmick]
        pygame.draw.rect(surf, (40,0,0),     (bx, by, bar_w, 8))
        pygame.draw.rect(surf, gimmick_col, (bx, by, int(bar_w * ratio), 8))
        pygame.draw.rect(surf, (200,200,200),(bx, by, bar_w, 8), 1)


# ── Wreck ─────────────────────────────────────────────────────────────────────

class Wreck:
    SALVAGE_RANGE = 80.0
    SALVAGE_TIME  = 2.0

    def __init__(self, x, y, xp_value, sprite_mgr):
        self.x, self.y   = float(x), float(y)
        self.xp_value    = xp_value
        self.sprite_mgr  = sprite_mgr
        self.alive       = True
        self._progress   = 0.0
        self.angle       = random.uniform(0, 360)

    @property
    def rect(self):
        return pygame.Rect(self.x - 26, self.y - 26, 52, 52)

    def update(self, dt, player_x, player_y):
        dist = math.sqrt((player_x - self.x)**2 + (player_y - self.y)**2)
        if dist < self.SALVAGE_RANGE:
            self._progress += dt / self.SALVAGE_TIME
            if self._progress >= 1.0:
                self.alive = False
                return True
        else:
            self._progress = max(0, self._progress - dt * 0.5)
        return False

    def draw(self, surf, cam_x, cam_y):
        img = self.sprite_mgr.get("wreck")
        rotated = pygame.transform.rotate(img, self.angle)
        sx = self.x - cam_x - rotated.get_width()  // 2
        sy = self.y - cam_y - rotated.get_height() // 2
        surf.blit(rotated, (sx, sy))
        if self._progress > 0:
            scx, scy = self.x - cam_x, self.y - cam_y
            r = 32
            pygame.draw.arc(surf, (0, 255, 180),
                            (scx-r, scy-r, r*2, r*2),
                            0, self._progress * math.tau, 3)


# ── Pickup ────────────────────────────────────────────────────────────────────

class Pickup:
    MAGNET_R = 160.0; SPEED = 200.0; LIFETIME = 12.0

    def __init__(self, x, y, kind, value, sprite_mgr):
        self.x, self.y  = float(x), float(y)
        self.kind       = kind
        self.value      = value
        self.sprite_mgr = sprite_mgr
        self.alive      = True
        self._life      = self.LIFETIME
        self._bob       = random.uniform(0, math.tau)

    @property
    def rect(self):
        return pygame.Rect(self.x - 8, self.y - 8, 16, 16)

    def update(self, dt, px, py):
        self._life -= dt
        self._bob  += dt * 3
        if self._life <= 0:
            self.alive = False
            return
        dist = math.sqrt((px - self.x)**2 + (py - self.y)**2)
        if dist < self.MAGNET_R:
            nx, ny = normalize(px - self.x, py - self.y)
            speed  = self.SPEED * (1.0 + (1.0 - dist / self.MAGNET_R) * 2)
            self.x += nx * speed * dt
            self.y += ny * speed * dt

    def draw(self, surf, cam_x, cam_y):
        key = "xp_orb" if self.kind == "xp" else "scrap_orb"
        img = self.sprite_mgr.get(key)
        bob = math.sin(self._bob) * 3
        surf.blit(img, (self.x - cam_x - img.get_width()//2,
                        self.y - cam_y - img.get_height()//2 + bob))
        color = (0, 200, 255) if self.kind == "xp" else (200, 160, 50)
        glow = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(glow, color + (int(80 + 40*math.sin(self._bob*2)),), (16,16), 12)
        surf.blit(glow, (self.x - cam_x - 16, self.y - cam_y - 16))


# ── Explosion ─────────────────────────────────────────────────────────────────

class Explosion:
    FRAME_DUR = 0.08

    def __init__(self, x, y, sprite_mgr):
        self.x, self.y  = x, y
        self.sprite_mgr = sprite_mgr
        self._frame     = 0
        self._timer     = self.FRAME_DUR
        self.alive      = True

    def update(self, dt):
        self._timer -= dt
        if self._timer <= 0:
            self._timer = self.FRAME_DUR
            self._frame += 1
            if self._frame >= 4:
                self.alive = False

    def draw(self, surf, cam_x, cam_y):
        key = f"explosion_{min(self._frame, 3)}"
        img = self.sprite_mgr.get(key)
        surf.blit(img, (self.x - cam_x - img.get_width()//2,
                        self.y - cam_y - img.get_height()//2))
