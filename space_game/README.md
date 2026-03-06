# VOID SALVAGER 🚀
An open-world space exploration game. Salvage wrecks, collect data, upgrade your ship, survive enemy fleets.

---

## Setup & Run

```bash
pip install pygame
python main.py
```

---

## Controls

| Key | Action |
|-----|--------|
| WASD / Arrow Keys | Rotate & Thrust |
| SPACE | Fire primary weapon |
| **SHIFT** | **Boost dash** (3s cooldown, ice-physics slide after) |
| E | Launch homing missile *(unlock required)* |
| Q | Fire laser beam *(unlock required)* |
| F | Warp dash *(unlock required)* |
| C | Stealth cloak *(unlock required)* |
| TAB | Open / close Skill Tree |
| R | Hot-reload custom sprites from disk |

---

## Gameplay Loop

1. **Explore** the open world — chunks generate as you fly
2. **Fight** enemy patrols (Scouts → Cruisers → Dreadnoughts get harder as you go further from origin)
3. **Collect** glowing orbs dropped by destroyed enemies:
   - 🔵 **Data orbs** = XP (used to unlock skills)
   - 🟡 **Scrap orbs** = Heals your ship
4. **Salvage** wrecks by flying close and holding position — watch the green arc fill up
5. **Spend XP** in the Skill Tree (TAB) to unlock new weapons and upgrades

---

## Skill Tree

Three branches — each 4 tiers deep:

```
WEAPONS               DEFENSE               ENGINE
────────              ────────              ──────
Rapid Fire ────┐      Hull Armor ──┐        Afterburner ──┐
               │                   │                       │
Double Shot    │      Reinforced    │        Drift Control  │
Power Shot ────┘      Hull         │        Engine Boost ──┘
                                   │
Missile Rack          Shield Gen ──┤        Warp Drive
Laser Cannon          Nano-Repair ─┘                │
                                                Stealth
Overcharge            Deflector Field         Overdrive
```

Open TAB, click a node to select it, press ENTER to purchase.

---

## Custom Sprites

Drop `.png` files into the `sprites/` folder. Press **R** in-game to hot-reload without restarting.

All sprites should face **upward** (top of the image = front of the ship/object). Use transparent PNGs (RGBA).

| Filename | Recommended size | Description |
|---|---|---|
| `player_ship.png` | **48 × 48** | Your ship — nose pointing UP |
| `enemy_scout.png` | **40 × 40** | Small fast enemy — nose pointing UP |
| `enemy_cruiser.png` | **64 × 48** | Medium enemy — nose pointing UP |
| `enemy_dreadnought.png` | **80 × 64** | Heavy enemy — nose pointing UP |
| `wreck.png` | **52 × 52** | Salvageable debris — any orientation, it spins |
| `bullet_player.png` | **8 × 16** | Your bullet — tip pointing UP |
| `bullet_enemy.png` | **8 × 16** | Enemy bullet — tip pointing UP |
| `missile.png` | **10 × 20** | Homing missile — tip pointing UP |
| `laser_beam.png` | **6 × 32** | Laser segment — drawn pointing UP |
| `xp_orb.png` | **16 × 16** | Data / XP pickup orb |
| `scrap_orb.png` | **16 × 16** | Scrap / heal pickup orb |
| `explosion_0.png` | **48 × 48** | Explosion frame 0 (brightest) |
| `explosion_1.png` | **48 × 48** | Explosion frame 1 |
| `explosion_2.png` | **48 × 48** | Explosion frame 2 |
| `explosion_3.png` | **48 × 48** | Explosion frame 3 (fading) |

**Tips:**
- The game scales your image to the recommended size, so exact pixels don't matter — but the aspect ratio should match
- Any file that is missing or can't load falls back to the built-in colored placeholder automatically
- After dropping new PNGs in, press **R** in-game and changes appear immediately — no restart needed

---

## File Structure

```
space_game/
├── main.py           ← entry point
├── game.py           ← game loop, collisions, state machine
├── entities.py       ← Player, Enemy types, Bullet, Missile, Wreck, Pickup
├── world.py          ← procedural chunk generation, star field
├── skill_tree.py     ← all 18 upgrades, stat computation
├── ui.py             ← HUD, minimap, skill tree UI
├── sprites_manager.py← sprite loader + placeholder generator
├── sprites/          ← drop your custom PNGs here
└── README.md
```
