"""
sprites.py - Sprite manager with placeholder generation and custom sprite support.

CUSTOM SPRITES:
  Drop .png files into the /sprites/ folder named exactly as listed below.
  They will be auto-loaded. If a file is missing, a placeholder is drawn instead.

  sprites/player_ship.png        - 48x48  your player ship
  sprites/enemy_scout.png        - 40x40  small fast enemy
  sprites/enemy_cruiser.png      - 64x48  medium enemy
  sprites/enemy_dreadnought.png  - 80x64  large heavy enemy
  sprites/wreck.png              - 52x52  salvageable wreck
  sprites/bullet_player.png      - 8x16   player bullet
  sprites/bullet_enemy.png       - 8x16   enemy bullet
  sprites/xp_orb.png             - 16x16  data orb (XP)
  sprites/scrap_orb.png          - 16x16  scrap orb (heal)
  sprites/star_bg.png            - tiled background star (8x8)
  sprites/explosion_0.png        - 48x48  explosion frame 0
  sprites/explosion_1.png        - 48x48  explosion frame 1
  sprites/explosion_2.png        - 48x48  explosion frame 2
  sprites/explosion_3.png        - 48x48  explosion frame 3
  sprites/missile.png            - 10x20  missile projectile
  sprites/laser_beam.png         - 6x32   laser projectile
"""

import pygame
import math
import os

SPRITE_DIR = os.path.join(os.path.dirname(__file__), "sprites")


def _load_or_placeholder(filename, size, draw_fn):
    path = os.path.join(SPRITE_DIR, filename)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    draw_fn(surf, size)
    return surf


# ── Placeholder draw functions ────────────────────────────────────────────────

def _draw_player(surf, size):
    w, h = size
    cx, cy = w // 2, h // 2
    # Body
    pygame.draw.polygon(surf, (80, 200, 255), [
        (cx, 2), (cx + 16, h - 8), (cx + 6, h - 14),
        (cx - 6, h - 14), (cx - 16, h - 8)
    ])
    # Cockpit
    pygame.draw.ellipse(surf, (160, 240, 255, 200), (cx - 5, cy - 8, 10, 14))
    # Engine glow
    pygame.draw.ellipse(surf, (100, 180, 255, 180), (cx - 6, h - 14, 12, 8))
    # Wings
    pygame.draw.polygon(surf, (50, 150, 210), [
        (cx - 6, h - 14), (cx - 20, h - 4), (cx - 10, h - 10)
    ])
    pygame.draw.polygon(surf, (50, 150, 210), [
        (cx + 6, h - 14), (cx + 20, h - 4), (cx + 10, h - 10)
    ])


def _draw_enemy_scout(surf, size):
    w, h = size
    cx, cy = w // 2, h // 2
    pygame.draw.polygon(surf, (220, 60, 60), [
        (cx, h - 2), (cx - 14, 6), (cx, 12), (cx + 14, 6)
    ])
    pygame.draw.ellipse(surf, (255, 120, 120, 180), (cx - 4, cy - 4, 8, 10))


def _draw_enemy_cruiser(surf, size):
    w, h = size
    cx, cy = w // 2, h // 2
    pygame.draw.polygon(surf, (180, 40, 40), [
        (cx, h - 2), (cx - 20, 10), (cx - 8, 16), (cx + 8, 16), (cx + 20, 10)
    ])
    pygame.draw.rect(surf, (220, 80, 80), (cx - 6, cy - 10, 12, 18))
    pygame.draw.line(surf, (255, 160, 0), (cx - 18, 12), (cx - 6, 20), 2)
    pygame.draw.line(surf, (255, 160, 0), (cx + 18, 12), (cx + 6, 20), 2)


def _draw_enemy_dreadnought(surf, size):
    w, h = size
    cx, cy = w // 2, h // 2
    pygame.draw.polygon(surf, (140, 20, 20), [
        (cx, h - 2), (cx - 30, 14), (cx - 12, 20),
        (cx + 12, 20), (cx + 30, 14)
    ])
    pygame.draw.rect(surf, (180, 50, 50), (cx - 10, cy - 14, 20, 26))
    for dx in [-22, 22]:
        pygame.draw.line(surf, (255, 200, 0), (cx + dx, 16), (cx + dx // 2, 28), 3)


def _draw_wreck(surf, size):
    w, h = size
    cx, cy = w // 2, h // 2
    # Broken hull chunks
    pygame.draw.polygon(surf, (120, 120, 140), [
        (cx - 18, cy - 10), (cx - 4, cy - 20), (cx + 6, cy - 12), (cx - 8, cy)
    ])
    pygame.draw.polygon(surf, (100, 100, 120), [
        (cx + 4, cy - 8), (cx + 20, cy - 14), (cx + 22, cy + 8), (cx + 6, cy + 6)
    ])
    pygame.draw.polygon(surf, (90, 90, 110), [
        (cx - 12, cy + 2), (cx + 4, cy + 8), (cx + 2, cy + 20), (cx - 16, cy + 14)
    ])
    pygame.draw.circle(surf, (255, 120, 20, 160), (cx + 2, cy), 6)


def _draw_bullet_player(surf, size):
    w, h = size
    cx = w // 2
    pygame.draw.ellipse(surf, (0, 255, 200), (cx - 2, 0, 4, h))
    pygame.draw.ellipse(surf, (200, 255, 255), (cx - 1, 2, 2, h - 4))


def _draw_bullet_enemy(surf, size):
    w, h = size
    cx = w // 2
    pygame.draw.ellipse(surf, (255, 80, 0), (cx - 2, 0, 4, h))
    pygame.draw.ellipse(surf, (255, 200, 100), (cx - 1, 2, 2, h - 4))


def _draw_missile(surf, size):
    w, h = size
    cx = w // 2
    pygame.draw.polygon(surf, (200, 200, 50), [(cx, 0), (cx - 4, 14), (cx + 4, 14)])
    pygame.draw.rect(surf, (180, 180, 40), (cx - 4, 12, 8, 8))
    pygame.draw.polygon(surf, (255, 120, 0), [(cx - 4, 20), (cx, 16), (cx + 4, 20)])


def _draw_laser(surf, size):
    w, h = size
    cx = w // 2
    pygame.draw.rect(surf, (255, 50, 50, 200), (cx - 2, 0, 4, h))
    pygame.draw.rect(surf, (255, 180, 180), (cx - 1, 0, 2, h))


def _draw_xp_orb(surf, size):
    w, h = size
    cx, cy = w // 2, h // 2
    pygame.draw.circle(surf, (50, 200, 255), (cx, cy), 6)
    pygame.draw.circle(surf, (180, 240, 255), (cx, cy), 3)


def _draw_scrap_orb(surf, size):
    w, h = size
    cx, cy = w // 2, h // 2
    pygame.draw.circle(surf, (200, 160, 50), (cx, cy), 6)
    pygame.draw.circle(surf, (255, 220, 120), (cx, cy), 3)


def _draw_star(surf, size):
    surf.fill((0, 0, 0, 0))
    w, h = size
    pygame.draw.circle(surf, (255, 255, 255, 200), (w // 2, h // 2), 1)


def _draw_explosion(surf, size, frame):
    w, h = size
    cx, cy = w // 2, h // 2
    colors = [
        (255, 200, 50), (255, 140, 20), (200, 80, 10), (120, 40, 10)
    ]
    radii = [20, 26, 18, 10]
    alphas = [200, 160, 120, 80]
    r = radii[frame]
    color = colors[frame] + (alphas[frame],)
    pygame.draw.circle(surf, color, (cx, cy), r)
    if frame < 2:
        inner = colors[frame + 1] + (200,)
        pygame.draw.circle(surf, inner, (cx, cy), r // 2)


# ── Public loader ─────────────────────────────────────────────────────────────

class SpriteManager:
    def __init__(self):
        self._cache = {}
        self._load_all()

    def _load_all(self):
        specs = [
            ("player_ship",        (48, 48),  _draw_player),
            ("enemy_scout",        (40, 40),  _draw_enemy_scout),
            ("enemy_cruiser",      (64, 48),  _draw_enemy_cruiser),
            ("enemy_dreadnought",  (80, 64),  _draw_enemy_dreadnought),
            ("wreck",              (52, 52),  _draw_wreck),
            ("bullet_player",      (8, 16),   _draw_bullet_player),
            ("bullet_enemy",       (8, 16),   _draw_bullet_enemy),
            ("missile",            (10, 20),  _draw_missile),
            ("laser_beam",         (6, 32),   _draw_laser),
            ("xp_orb",             (16, 16),  _draw_xp_orb),
            ("scrap_orb",          (16, 16),  _draw_scrap_orb),
            ("star_bg",            (4, 4),    _draw_star),
        ]
        for name, size, fn in specs:
            self._cache[name] = _load_or_placeholder(f"{name}.png", size, fn)

        for i in range(4):
            key = f"explosion_{i}"
            self._cache[key] = _load_or_placeholder(
                f"{key}.png", (48, 48),
                lambda s, sz, frame=i: _draw_explosion(s, sz, frame)
            )

    def get(self, name):
        return self._cache.get(name)

    def reload(self):
        """Call this to hot-reload sprites from disk."""
        self._load_all()
