"""
skill_tree.py  –  Deep branching ship upgrade tree.
Col/row positions define layout. Three branches, 9 tiers, many cross-connects.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class Skill:
    id: str
    name: str
    description: str
    branch: str
    col: int
    row: int
    cost: int
    requires: List[str]
    unlocked: bool = False

    fire_rate_bonus:     float = 0.0
    damage_bonus:        float = 0.0
    max_hp_bonus:        int   = 0
    regen_bonus:         float = 0.0
    shield_bonus:        int   = 0
    speed_bonus:         float = 0.0
    boost_cd_bonus:      float = 0.0
    reflects_bullets:    float = 0.0
    enables_missile:     bool  = False
    enables_laser:       bool  = False
    enables_double_shot: bool  = False
    enables_triple_shot: bool  = False
    enables_warp:        bool  = False
    enables_stealth:     bool  = False
    spread_shot:         bool  = False
    ricochet:            bool  = False


# ─── WEAPONS  cols 0-8 ────────────────────────────────────────────────────────
_W = [
    # Root
    Skill("w_root",       "Weapons Core",    "Foundation of weapons",
          "weapons", 4, 0, 0, []),

    # Tier 1 – two starting paths
    Skill("rapid1",       "Rapid Fire",      "Fire 20% faster",
          "weapons", 2, 1, 250, ["w_root"], fire_rate_bonus=0.20),
    Skill("power1",       "Power Cell",      "+6 damage",
          "weapons", 6, 1, 250, ["w_root"], damage_bonus=6.0),

    # Tier 2 – each splits into two
    Skill("rapid2",       "Overclocked",     "Fire 25% faster",
          "weapons", 1, 2, 450, ["rapid1"], fire_rate_bonus=0.25),
    Skill("double",       "Double Shot",     "Two parallel bullets",
          "weapons", 3, 2, 450, ["rapid1"], enables_double_shot=True),
    Skill("power2",       "Heavy Round",     "+10 damage",
          "weapons", 5, 2, 450, ["power1"], damage_bonus=10.0),
    Skill("spread",       "Spread Shot",     "3-way spread fire",
          "weapons", 7, 2, 450, ["power1"], spread_shot=True),

    # Tier 3
    Skill("gatling",      "Gatling",         "Fire 30% faster",
          "weapons", 0, 3, 750, ["rapid2"], fire_rate_bonus=0.30),
    Skill("triple",       "Triple Shot",     "Three bullets at once",
          "weapons", 2, 3, 750, ["double"], enables_triple_shot=True),
    Skill("ricochet",     "Ricochet",        "Bullets bounce once",
          "weapons", 4, 3, 750, ["double", "power2"], ricochet=True),
    Skill("armor_pierce", "Armor Pierce",    "+14 damage",
          "weapons", 6, 3, 750, ["power2"], damage_bonus=14.0),
    Skill("missile",      "Missile Rack",    "Homing missiles (E)",
          "weapons", 8, 3, 750, ["spread"], enables_missile=True),

    # Tier 4 – cross-unlocks start appearing
    Skill("hyperburst",   "Hyperburst",      "Fire 20% faster + +8 dmg",
          "weapons", 1, 4, 1100, ["gatling"], fire_rate_bonus=0.20, damage_bonus=8.0),
    Skill("laser",        "Laser Cannon",    "Piercing laser beam (Q)",
          "weapons", 3, 4, 1100, ["triple", "armor_pierce"], enables_laser=True),
    Skill("explosive",    "Explosive Round", "Shots deal +10 dmg in 2px radius",
          "weapons", 5, 4, 1100, ["ricochet"], damage_bonus=10.0),
    Skill("missile2",     "Missile Bay",     "Missile damage x1.5",
          "weapons", 8, 4, 1100, ["missile"], damage_bonus=8.0),

    # Tier 5
    Skill("death_star",   "Death Blossom",   "Triple + spread combined",
          "weapons", 2, 5, 1600, ["hyperburst", "triple"],
          enables_triple_shot=True, spread_shot=True),
    Skill("overcharge",   "Overcharge",      "+20% fire rate & +10 dmg",
          "weapons", 4, 5, 1600, ["laser"],
          fire_rate_bonus=0.20, damage_bonus=10.0),
    Skill("seeking",      "Seeker Swarm",    "Missiles auto-lock +10 dmg",
          "weapons", 7, 5, 1600, ["missile2"],
          enables_missile=True, damage_bonus=10.0),

    # Tier 6
    Skill("unstoppable",  "Unstoppable",     "+15% fire rate, +15 dmg",
          "weapons", 3, 6, 2300, ["death_star", "overcharge"],
          fire_rate_bonus=0.15, damage_bonus=15.0),
    Skill("nova",         "Nova Strike",     "Missiles explode in AoE +20 dmg",
          "weapons", 7, 6, 2300, ["seeking"], damage_bonus=20.0),

    # Tier 7
    Skill("omnifire",     "Omni-Fire",       "All shot bonuses amplified",
          "weapons", 3, 7, 3200, ["unstoppable"],
          fire_rate_bonus=0.15, damage_bonus=12.0,
          enables_triple_shot=True),
    Skill("apocalypse",   "Apocalypse",      "Nova + laser + missile combo",
          "weapons", 6, 7, 3200, ["nova", "unstoppable"],
          enables_missile=True, enables_laser=True, damage_bonus=15.0),

    # Tier 8 – capstones
    Skill("godgun",       "God's Wrath",     "Maximum firepower — all bonuses",
          "weapons", 4, 8, 5000, ["omnifire", "apocalypse"],
          fire_rate_bonus=0.20, damage_bonus=20.0,
          enables_triple_shot=True, spread_shot=True,
          enables_missile=True, enables_laser=True),
]

# ─── DEFENSE  cols 9-17 ───────────────────────────────────────────────────────
_D = [
    Skill("d_root",       "Defense Core",    "Foundation of defense",
          "defense", 13, 0, 0, []),

    # Tier 1
    Skill("hull1",        "Hull Plating",    "+35 max HP",
          "defense", 11, 1, 250, ["d_root"], max_hp_bonus=35),
    Skill("shield1",      "Shield Cell",     "+25 shield",
          "defense", 15, 1, 250, ["d_root"], shield_bonus=25),

    # Tier 2
    Skill("hull2",        "Thick Hull",      "+55 max HP",
          "defense", 10, 2, 450, ["hull1"], max_hp_bonus=55),
    Skill("regen1",       "Nano-Repair",     "Regen 2 HP/sec",
          "defense", 12, 2, 450, ["hull1"], regen_bonus=2.0),
    Skill("shield2",      "Shield Boost",    "+45 shield",
          "defense", 14, 2, 450, ["shield1"], shield_bonus=45),
    Skill("fast_rech",    "Fast Recharge",   "Shield recharges faster",
          "defense", 16, 2, 450, ["shield1"], shield_bonus=15),

    # Tier 3
    Skill("hull3",        "Bulkhead",        "+75 max HP",
          "defense", 9, 3, 750, ["hull2"], max_hp_bonus=75),
    Skill("regen2",       "Repair Drone",    "Regen 3 HP/sec more",
          "defense", 11, 3, 750, ["regen1"], regen_bonus=3.0),
    Skill("shield3",      "Heavy Shield",    "+70 shield",
          "defense", 13, 3, 750, ["shield2"], shield_bonus=70),
    Skill("reflect1",     "Deflector Mesh",  "10% bullet reflect",
          "defense", 15, 3, 750, ["fast_rech"], reflects_bullets=0.10),
    Skill("emerg_regen",  "Emergency Regen", "Regen 4 HP/sec below 25% HP",
          "defense", 17, 3, 750, ["fast_rech"], regen_bonus=2.0),

    # Tier 4
    Skill("titan_hull",   "Titan Hull",      "+100 max HP",
          "defense", 9, 4, 1100, ["hull3"], max_hp_bonus=100),
    Skill("regen3",       "Swarm Repair",    "Regen 5 HP/sec more",
          "defense", 11, 4, 1100, ["regen2"], regen_bonus=5.0),
    Skill("reflect2",     "Mirror Plating",  "Reflect +18%",
          "defense", 14, 4, 1100, ["shield3", "reflect1"], reflects_bullets=0.18),
    Skill("oversh",       "Overshield",      "+60 shield + 20 HP",
          "defense", 16, 4, 1100, ["shield3"], shield_bonus=60, max_hp_bonus=20),

    # Tier 5
    Skill("fortress",     "Fortress Mode",   "+120 HP + regen 4/sec",
          "defense", 10, 5, 1600, ["titan_hull", "regen3"],
          max_hp_bonus=120, regen_bonus=4.0),
    Skill("reflect3",     "Mirror Wall",     "Reflect +20% more",
          "defense", 15, 5, 1600, ["reflect2"], reflects_bullets=0.20),
    Skill("revival",      "Revival Cell",    "+80 HP + 3 HP/sec",
          "defense", 17, 5, 1600, ["oversh"], max_hp_bonus=80, regen_bonus=3.0),

    # Tier 6
    Skill("juggernaut",   "Juggernaut",      "+150 HP, 5 HP/sec",
          "defense", 11, 6, 2300, ["fortress"],
          max_hp_bonus=150, regen_bonus=5.0),
    Skill("full_mirror",  "Full Mirror",     "Reflect +25%",
          "defense", 15, 6, 2300, ["reflect3"], reflects_bullets=0.25),

    # Tier 7
    Skill("god_shield",   "Divine Shield",   "+200 HP, 6/sec, +100 shield",
          "defense", 12, 7, 3200, ["juggernaut", "full_mirror"],
          max_hp_bonus=200, regen_bonus=6.0, shield_bonus=100),
    Skill("perfect_ref",  "Perfect Mirror",  "Reflect any bullet with +10% dmg",
          "defense", 16, 7, 3200, ["full_mirror", "revival"],
          reflects_bullets=0.15),

    # Tier 8
    Skill("immortal",     "Immortal Core",   "Near-invincible: all defense maxed",
          "defense", 13, 8, 5000, ["god_shield", "perfect_ref"],
          max_hp_bonus=250, regen_bonus=8.0, shield_bonus=150,
          reflects_bullets=0.20),
]

# ─── ENGINE  cols 18-26 ───────────────────────────────────────────────────────
_E = [
    Skill("e_root",       "Engine Core",     "Foundation of propulsion",
          "engine", 22, 0, 0, []),

    # Tier 1
    Skill("afterburn",    "Afterburner",     "+70 max speed",
          "engine", 20, 1, 250, ["e_root"], speed_bonus=70.0),
    Skill("boost_tk",     "Boost Tank",      "Boost CD -0.5s",
          "engine", 24, 1, 250, ["e_root"], boost_cd_bonus=0.5),

    # Tier 2
    Skill("engine1",      "Engine Tune",     "+55 max speed",
          "engine", 19, 2, 450, ["afterburn"], speed_bonus=55.0),
    Skill("drift",        "Drift Control",   "+40 speed, smoother handling",
          "engine", 21, 2, 450, ["afterburn"], speed_bonus=40.0),
    Skill("boost2",       "Nitro",           "Boost CD -0.7s",
          "engine", 23, 2, 450, ["boost_tk"], boost_cd_bonus=0.7),
    Skill("boost_pow",    "Boost Power",     "Boost impulse stronger",
          "engine", 25, 2, 450, ["boost_tk"], speed_bonus=25.0),

    # Tier 3
    Skill("engine2",      "Hyperdrive",      "+90 max speed",
          "engine", 18, 3, 750, ["engine1"], speed_bonus=90.0),
    Skill("warp",         "Warp Drive",      "Short warp dash (F)",
          "engine", 20, 3, 750, ["drift"], enables_warp=True),
    Skill("boost3",       "Overclock",       "Boost CD -1.0s",
          "engine", 22, 3, 750, ["boost2"], boost_cd_bonus=1.0),
    Skill("phase",        "Phase Drive",     "+70 speed & +35 shield",
          "engine", 24, 3, 750, ["boost_pow"], speed_bonus=70.0, shield_bonus=35),
    Skill("slipstream",   "Slipstream",      "+50 speed after boost",
          "engine", 26, 3, 750, ["boost_pow"], speed_bonus=50.0),

    # Tier 4
    Skill("engine3",      "Quantum Drive",   "+110 max speed",
          "engine", 18, 4, 1100, ["engine2"], speed_bonus=110.0),
    Skill("stealth",      "Stealth Cloak",   "Invisibility (C)",
          "engine", 20, 4, 1100, ["warp"], enables_stealth=True),
    Skill("boost4",       "Flash Boost",     "Boost CD -1.0s",
          "engine", 22, 4, 1100, ["boost3"], boost_cd_bonus=1.0),
    Skill("evasion",      "Evasion Protocol","+60 speed, boost gives brief invuln",
          "engine", 25, 4, 1100, ["phase", "slipstream"], speed_bonus=60.0),

    # Tier 5
    Skill("no_limit",     "Limiter Off",     "+180 speed cap",
          "engine", 19, 5, 1600, ["engine3"], speed_bonus=180.0),
    Skill("ghost",        "Ghost Protocol",  "Stealth lasts longer",
          "engine", 21, 5, 1600, ["stealth"], enables_stealth=True),
    Skill("boost5",       "Perma-Boost",     "Boost CD -1.0s",
          "engine", 22, 5, 1600, ["boost4"], boost_cd_bonus=1.0),
    Skill("blink",        "Blink Drive",     "Boost CD -1.0s + +50 speed",
          "engine", 25, 5, 1600, ["evasion"], boost_cd_bonus=1.0, speed_bonus=50.0),

    # Tier 6
    Skill("lightspeed",   "Light Speed",     "+220 speed, boost near-instant",
          "engine", 19, 6, 2300, ["no_limit"],
          speed_bonus=220.0, boost_cd_bonus=1.0),
    Skill("phantom",      "Phantom Ship",    "Stealth + speed + shield",
          "engine", 21, 6, 2300, ["ghost", "boost5"],
          enables_stealth=True, speed_bonus=80.0, shield_bonus=30),

    # Tier 7
    Skill("transcend",    "Transcendence",   "Max speed + stealth + warp",
          "engine", 20, 7, 3200, ["lightspeed", "phantom"],
          speed_bonus=150.0, enables_stealth=True, enables_warp=True,
          boost_cd_bonus=1.0),
    Skill("blink2",       "Quantum Blink",   "Boost instant + +100 speed",
          "engine", 24, 7, 3200, ["blink"],
          boost_cd_bonus=1.5, speed_bonus=100.0),

    # Tier 8
    Skill("ascension",    "Ascension Drive", "All engine perks maximized",
          "engine", 22, 8, 5000, ["transcend", "blink2"],
          speed_bonus=200.0, boost_cd_bonus=2.0,
          enables_stealth=True, enables_warp=True, shield_bonus=60),
]

SKILL_TREE: List[Skill] = _W + _D + _E


class SkillTreeManager:
    def __init__(self):
        # Auto-unlock cost-0 roots
        self.skills = {s.id: s for s in SKILL_TREE}
        for sk in self.skills.values():
            if sk.cost == 0:
                sk.unlocked = True

    def can_unlock(self, skill_id: str, current_xp: int) -> tuple[bool, str]:
        sk = self.skills[skill_id]
        if sk.unlocked:
            return False, "Already unlocked"
        if current_xp < sk.cost:
            return False, f"Need {sk.cost} XP (have {current_xp})"
        for req in sk.requires:
            if not self.skills[req].unlocked:
                return False, f"Requires: {self.skills[req].name}"
        return True, "OK"

    def unlock(self, skill_id: str, current_xp: int) -> tuple[bool, int]:
        ok, _ = self.can_unlock(skill_id, current_xp)
        if not ok:
            return False, current_xp
        self.skills[skill_id].unlocked = True
        return True, current_xp - self.skills[skill_id].cost

    def compute_stats(self) -> dict:
        stats = {
            "fire_rate_reduction": 0.0, "damage_bonus": 0.0,
            "max_hp_bonus": 0,          "regen": 0.0,
            "shield": 0,                "speed_bonus": 0.0,
            "boost_cd_reduction": 0.0,  "missile": False,
            "laser": False,             "double_shot": False,
            "triple_shot": False,       "spread_shot": False,
            "ricochet": False,          "warp": False,
            "stealth": False,           "reflect_chance": 0.0,
        }
        for sk in self.skills.values():
            if not sk.unlocked:
                continue
            stats["fire_rate_reduction"] += sk.fire_rate_bonus
            stats["damage_bonus"]        += sk.damage_bonus
            stats["max_hp_bonus"]        += sk.max_hp_bonus
            stats["regen"]               += sk.regen_bonus
            stats["shield"]              += sk.shield_bonus
            stats["speed_bonus"]         += sk.speed_bonus
            stats["boost_cd_reduction"]  += sk.boost_cd_bonus
            stats["reflect_chance"]       = min(0.85, stats["reflect_chance"] + sk.reflects_bullets)
            if sk.enables_missile:       stats["missile"]      = True
            if sk.enables_laser:         stats["laser"]        = True
            if sk.enables_double_shot:   stats["double_shot"]  = True
            if sk.enables_triple_shot:   stats["triple_shot"]  = True
            if sk.spread_shot:           stats["spread_shot"]  = True
            if sk.ricochet:              stats["ricochet"]     = True
            if sk.enables_warp:          stats["warp"]         = True
            if sk.enables_stealth:       stats["stealth"]      = True
        return stats

    def get_branch(self, branch: str) -> List[Skill]:
        return [s for s in SKILL_TREE if s.branch == branch]
