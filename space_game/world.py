"""
world.py - Procedural world with zone border, asteroids, and dense nebulae.
"""

import random, math, pygame
from entities import Scout, Cruiser, Dreadnought, Boss, Wreck, Pickup, Explosion, Asteroid, DenseNebula

CHUNK_SIZE = 1200

# Color tints per zone (applied to enemy sprites via draw alpha modulation)
ZONE_ENEMY_TINTS = [
    None,            # zone 0 — default
    (255, 200, 100), # zone 1 — gold
    (180, 100, 255), # zone 2 — purple
    (100, 220, 255), # zone 3 — cyan
    (255, 100, 100), # zone 4 — crimson
    (100, 255, 160), # zone 5 — emerald
    (255, 140, 200), # zone 6 — pink
]

def _make_enemy(kind, ex, ey, sprite_mgr, zone):
    """Create an enemy scaled to the current zone."""
    if kind == "scout":
        e = Scout(ex, ey, sprite_mgr)
    elif kind == "cruiser":
        e = Cruiser(ex, ey, sprite_mgr)
    else:
        e = Dreadnought(ex, ey, sprite_mgr)
    # Scale HP and damage with zone
    scale = 1 + zone * 0.35
    e.hp = e.max_hp = int(e.max_hp * scale)
    e.DAMAGE = int(e.DAMAGE * (1 + zone * 0.25))
    e.zone_tint = ZONE_ENEMY_TINTS[zone % len(ZONE_ENEMY_TINTS)]
    return e


class ZoneBorder:
    ZONE_RADII  = [2400, 4800, 8000, 12000, 17000, 24000]
    ZONE_COLORS = [(255,80,80),(255,160,40),(200,80,255),(40,200,255),(80,255,120),(255,220,50)]
    WALL_THICKNESS = 40

    def __init__(self, zone_index):
        self.zone   = zone_index
        self.radius = self._radius_for(zone_index)
        self.color  = self.ZONE_COLORS[zone_index % len(self.ZONE_COLORS)]
        self._pulse = 0.0

    def _radius_for(self, z):
        if z < len(self.ZONE_RADII):
            return self.ZONE_RADII[z]
        base = self.ZONE_RADII[-1]
        for _ in range(z - len(self.ZONE_RADII) + 1):
            base = int(base * 1.5)
        return base

    def confine(self, player):
        dist  = math.sqrt(player.x**2 + player.y**2)
        limit = self.radius - self.WALL_THICKNESS // 2
        if dist > limit:
            if dist > 0:
                nx, ny = player.x / dist, player.y / dist
            else:
                nx, ny = 1.0, 0.0
            player.x = nx * limit
            player.y = ny * limit
            dot = player.vx * nx + player.vy * ny
            if dot > 0:
                player.vx -= dot * nx * 1.4
                player.vy -= dot * ny * 1.4
            player.take_damage(2)
            return True
        return False

    def update(self, dt):
        self._pulse = (self._pulse + dt * 2) % math.tau

    def draw(self, surf, cam_x, cam_y):
        sw, sh = surf.get_size()
        # World origin (0,0) in screen space
        ox = -cam_x
        oy = -cam_y
        r  = self.radius

        # Skip if circle is entirely off-screen
        if math.sqrt((ox - sw//2)**2 + (oy - sh//2)**2) > r + max(sw, sh):
            return

        alpha = int(160 + 60 * math.sin(self._pulse))
        col   = self.color + (alpha,)
        bs    = pygame.Surface((sw, sh), pygame.SRCALPHA)
        segs  = 200
        prev  = None
        for i in range(segs + 1):
            a  = math.tau * i / segs
            px = int(ox + math.cos(a) * r)
            py = int(oy + math.sin(a) * r)
            pt = (px, py)
            if prev and -60 < px < sw+60 and -60 < py < sh+60:
                pygame.draw.line(bs, col, prev, pt, self.WALL_THICKNESS)
            prev = pt
        surf.blit(bs, (0, 0))


class StarField:
    def __init__(self, seed=42):
        rng = random.Random(seed)
        self.layers = []
        for count in [300, 150, 60]:
            stars = [(rng.uniform(0,4000), rng.uniform(0,4000),
                      rng.choice([1,1,1,2]), rng.randint(140,255))
                     for _ in range(count)]
            self.layers.append(stars)
        self.parallax = [0.05, 0.15, 0.35]

    def draw(self, surf, cam_x, cam_y):
        sw, sh = surf.get_size()
        for layer, speed in zip(self.layers, self.parallax):
            ox = (cam_x * speed) % 4000
            oy = (cam_y * speed) % 4000
            for (sx, sy, r, b) in layer:
                px = (sx - ox) % 4000
                py = (sy - oy) % 4000
                if px < sw and py < sh:
                    pygame.draw.circle(surf, (b,b,b), (int(px), int(py)), r)


class Chunk:
    def __init__(self, cx, cy, sprite_mgr, difficulty, zone=0):
        self.cx, self.cy   = cx, cy
        self.enemies       = []
        self.wrecks        = []
        self.nebula        = []
        self.asteroids     = []
        self.dense_nebulae = []
        self._generate(sprite_mgr, difficulty, zone)

    def _generate(self, sprite_mgr, difficulty, zone):
        rng = random.Random((self.cx * 73856093) ^ (self.cy * 19349663))
        ox, oy = self.cx * CHUNK_SIZE, self.cy * CHUNK_SIZE

        for _ in range(rng.randint(2, 5)):
            self.nebula.append((
                ox + rng.uniform(100, CHUNK_SIZE-100),
                oy + rng.uniform(100, CHUNK_SIZE-100),
                rng.uniform(80, 250),
                rng.choice([(60,20,120),(20,60,140),(140,30,20),(20,120,80)])
            ))

        if not (self.cx == 0 and self.cy == 0):
            for _ in range(rng.randint(1, 4)):
                ax = ox + rng.uniform(120, CHUNK_SIZE-120)
                ay = oy + rng.uniform(120, CHUNK_SIZE-120)
                self.asteroids.append(Asteroid(ax, ay, rng.uniform(45, 120)))

        if rng.random() < 0.35 and not (self.cx == 0 and self.cy == 0):
            nx = ox + rng.uniform(150, CHUNK_SIZE-150)
            ny = oy + rng.uniform(150, CHUNK_SIZE-150)
            hue = rng.choice([(40,80,160),(100,40,160),(40,140,80),(160,60,40)])
            self.dense_nebulae.append(DenseNebula(nx, ny, rng.uniform(100, 200), hue))

        if self.cx == 0 and self.cy == 0:
            return

        num = int(rng.uniform(1, 3) * (1 + difficulty * 0.4))
        for _ in range(num):
            ex = ox + rng.uniform(80, CHUNK_SIZE-80)
            ey = oy + rng.uniform(80, CHUNK_SIZE-80)
            roll = rng.random()
            if difficulty < 1:   kind = "scout"
            elif difficulty < 2: kind = "scout" if roll<0.6 else "cruiser"
            elif difficulty < 3: kind = "scout" if roll<0.3 else "cruiser" if roll<0.7 else "dread"
            else:                kind = "scout" if roll<0.2 else "cruiser" if roll<0.5 else "dread"
            self.enemies.append(_make_enemy(kind, ex, ey, sprite_mgr, zone))

        for _ in range(rng.randint(0, 3)):
            wx = ox + rng.uniform(80, CHUNK_SIZE-80)
            wy = oy + rng.uniform(80, CHUNK_SIZE-80)
            self.wrecks.append(Wreck(wx, wy, int(rng.uniform(50, 180)), sprite_mgr))


class World:
    LOAD_RADIUS = 2

    def __init__(self, sprite_mgr):
        self.sprite_mgr   = sprite_mgr
        self.chunks:      dict = {}
        self.bullets:     list = []
        self.missiles:    list = []
        self.pickups:     list = []
        self.explosions:  list = []
        self.bosses:      list = []
        self._loaded_chunks: set = set()
        self.current_zone    = 0
        self.bosses_defeated = 0   # total bosses killed across all zones
        self.border          = ZoneBorder(0)
        self._spawn_zone_bosses()

    def _extra_boss_count(self):
        """Extra (optional) bosses in zone: zone 3→1, zone 4→2, etc."""
        return max(0, self.current_zone - 2)

    def _spawn_zone_bosses(self):
        """Spawn the required boss + any extra decorative bosses."""
        r   = self.border.radius * 0.75
        # Required boss
        ang = random.uniform(0, math.tau)
        self.bosses.append(Boss(math.cos(ang)*r, math.sin(ang)*r,
                                self.sprite_mgr, self.current_zone))
        # Extra bosses (zone ≥3) — different angles, slightly weaker
        for i in range(self._extra_boss_count()):
            ang2 = random.uniform(0, math.tau)
            b = Boss(math.cos(ang2)*r*0.6, math.sin(ang2)*r*0.6,
                     self.sprite_mgr, self.current_zone, hp_scale=0.7)
            b._is_required = False   # killing extras is optional
            self.bosses.append(b)

    def on_boss_killed(self, boss):
        """Call when the REQUIRED boss dies. Returns new zone number."""
        self.bosses_defeated += 1
        self.current_zone += 1
        self.border = ZoneBorder(self.current_zone)
        # Clear leftover bosses from old zone
        self.bosses = []
        self._spawn_zone_bosses()
        return self.current_zone

    @property
    def required_boss(self):
        """The boss that must be defeated to advance."""
        for b in self.bosses:
            if getattr(b, "_is_required", True) and b.alive:
                return b
        return None

    @property
    def boss(self):
        return self.required_boss

    def _chunk_at(self, wx, wy):
        return int(math.floor(wx / CHUNK_SIZE)), int(math.floor(wy / CHUNK_SIZE))

    def _difficulty(self, cx, cy):
        return math.sqrt(cx*cx + cy*cy)

    def update_chunks(self, px, py):
        pcx, pcy = self._chunk_at(px, py)
        needed = {(pcx+dx, pcy+dy)
                  for dx in range(-self.LOAD_RADIUS, self.LOAD_RADIUS+1)
                  for dy in range(-self.LOAD_RADIUS, self.LOAD_RADIUS+1)}
        for key in needed:
            if key not in self.chunks:
                self.chunks[key] = Chunk(key[0], key[1], self.sprite_mgr,
                                         self._difficulty(*key),
                                         zone=self.current_zone)
        self._loaded_chunks = needed

    def _active_chunks(self):
        return [self.chunks[k] for k in self._loaded_chunks if k in self.chunks]

    @property
    def enemies(self):
        for chunk in self._active_chunks():
            yield from chunk.enemies
        yield from self.bosses

    @property
    def wrecks(self):
        for chunk in self._active_chunks():
            yield from chunk.wrecks

    @property
    def asteroids(self):
        for chunk in self._active_chunks():
            yield from chunk.asteroids

    @property
    def dense_nebulae(self):
        for chunk in self._active_chunks():
            yield from chunk.dense_nebulae

    def spawn_pickup(self, x, y, kind, value):
        self.pickups.append(Pickup(x, y, kind, value, self.sprite_mgr))

    def spawn_explosion(self, x, y):
        self.explosions.append(Explosion(x, y, self.sprite_mgr))

    def remove_dead(self):
        self.bullets    = [b for b in self.bullets    if b.alive]
        self.missiles   = [m for m in self.missiles   if m.alive]
        self.pickups    = [p for p in self.pickups    if p.alive]
        self.explosions = [e for e in self.explosions if e.alive]
        self.bosses     = [b for b in self.bosses     if b.alive]
        for chunk in self._active_chunks():
            chunk.enemies = [e for e in chunk.enemies if e.alive]
            chunk.wrecks  = [w for w in chunk.wrecks  if w.alive]

    def draw_nebulae(self, surf, cam_x, cam_y):
        sw, sh = surf.get_size()
        for chunk in self._active_chunks():
            for (nx, ny, nr, color) in chunk.nebula:
                sx, sy = nx - cam_x, ny - cam_y
                if -nr < sx < sw+nr and -nr < sy < sh+nr:
                    neb = pygame.Surface((int(nr*2), int(nr*2)), pygame.SRCALPHA)
                    pygame.draw.circle(neb, color+(18,), (int(nr), int(nr)), int(nr))
                    surf.blit(neb, (sx-nr, sy-nr))
