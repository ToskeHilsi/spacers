"""
skill_tree.py — Regular skill trees (3 branches) + Prestige trees (3 branches).

Costs scale faster per tier:  tier_cost = base * 1.55^tier  (was 1.4^tier-ish)
Prestige trees cost prestige points (earned by maxing + resetting a regular tree).
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Skill:
    id: str
    name: str
    description: str
    branch: str        # "weapons"|"defense"|"engine"|"p_weapons"|"p_defense"|"p_engine"
    col: int
    row: int
    cost: int          # XP cost for regular; prestige pts cost for prestige
    requires: List[str]
    unlocked: bool = False
    is_prestige: bool = False  # prestige-tree skill

    # Stats
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
    dual_missile:        bool  = False
    # Prestige-only stats
    bullet_speed_mult:   float = 1.0   # multiply bullet speed
    damage_mult:         float = 1.0   # multiply all damage
    xp_mult:             float = 1.0   # multiply XP gain
    invuln_on_boost:     bool  = False  # brief invincibility on boost
    auto_missile:        bool  = False  # missiles fire automatically
    chain_lightning:     bool  = False  # bullets chain to nearby enemies
    time_slow:           bool  = False  # slows nearby enemies
    shield_spike:        bool  = False  # shield deals damage on hit


# ─── Cost helper ──────────────────────────────────────────────────────────────
def _c(tier):
    """Regular tree cost. Scales faster: ~1.55x per tier."""
    bases = [0, 300, 600, 1000, 1600, 2500, 3800, 5500, 8000]
    return bases[min(tier, len(bases)-1)]

def _pc(tier):
    """Prestige tree cost in prestige points."""
    bases = [1, 1, 2, 2, 3, 4, 5, 7, 10]
    return bases[min(tier, len(bases)-1)]


# ─── WEAPONS  cols 0-8 ────────────────────────────────────────────────────────
_W = [
    Skill("w_root",      "Weapons Core",    "Foundation of weapons",            "weapons",4,0,0,[]),
    Skill("rapid1",      "Rapid Fire",      "+22% fire rate",                   "weapons",2,1,_c(1),["w_root"],fire_rate_bonus=0.22),
    Skill("power1",      "Power Cell",      "+7 damage",                        "weapons",6,1,_c(1),["w_root"],damage_bonus=7),
    Skill("rapid2",      "Overclocked",     "+26% fire rate",                   "weapons",1,2,_c(2),["rapid1"],fire_rate_bonus=0.26),
    Skill("double",      "Double Shot",     "Two parallel bullets",             "weapons",3,2,_c(2),["rapid1"],enables_double_shot=True),
    Skill("power2",      "Heavy Round",     "+12 damage",                       "weapons",5,2,_c(2),["power1"],damage_bonus=12),
    Skill("spread",      "Spread Shot",     "3-way spread fire",                "weapons",7,2,_c(2),["power1"],spread_shot=True),
    Skill("gatling",     "Gatling",         "+30% fire rate",                   "weapons",0,3,_c(3),["rapid2"],fire_rate_bonus=0.30),
    Skill("triple",      "Triple Shot",     "Three bullets at once",            "weapons",2,3,_c(3),["double"],enables_triple_shot=True),
    Skill("ricochet",    "Ricochet",        "Bullets bounce once",              "weapons",4,3,_c(3),["double","power2"],ricochet=True),
    Skill("armor_pierce","Armor Pierce",    "+16 damage",                       "weapons",6,3,_c(3),["power2"],damage_bonus=16),
    Skill("missile",     "Missile Rack",    "Homing missiles (E)",              "weapons",8,3,_c(3),["spread"],enables_missile=True),
    Skill("hyperburst",  "Hyperburst",      "+20% fire rate & +9 dmg",          "weapons",1,4,_c(4),["gatling"],fire_rate_bonus=0.20,damage_bonus=9),
    Skill("laser",       "Laser Cannon",    "Piercing laser (Q)",               "weapons",3,4,_c(4),["triple","armor_pierce"],enables_laser=True),
    Skill("explosive",   "Explosive Round", "+12 dmg",                          "weapons",5,4,_c(4),["ricochet"],damage_bonus=12),
    Skill("missile2",    "Missile Bay",     "Missile damage +8",                "weapons",8,4,_c(4),["missile"],damage_bonus=8),
    Skill("death_star",  "Death Blossom",   "Triple + spread combined",         "weapons",2,5,_c(5),["hyperburst","triple"],enables_triple_shot=True,spread_shot=True),
    Skill("overcharge",  "Overcharge",      "+20% fire rate & +12 dmg",         "weapons",4,5,_c(5),["laser"],fire_rate_bonus=0.20,damage_bonus=12),
    Skill("seeking",     "Seeker Swarm",    "Dual homing missiles +12 dmg",     "weapons",7,5,_c(5),["missile2"],enables_missile=True,damage_bonus=12,dual_missile=True),
    Skill("unstoppable", "Unstoppable",     "+15% fire rate, +18 dmg",          "weapons",3,6,_c(6),["death_star","overcharge"],fire_rate_bonus=0.15,damage_bonus=18),
    Skill("nova",        "Nova Strike",     "Missiles explode +22 dmg",         "weapons",7,6,_c(6),["seeking"],damage_bonus=22),
    Skill("omnifire",    "Omni-Fire",       "All shot bonuses amplified",       "weapons",3,7,_c(7),["unstoppable"],fire_rate_bonus=0.15,damage_bonus=14,enables_triple_shot=True),
    Skill("apocalypse",  "Apocalypse",      "Nova+laser+missile combo",         "weapons",6,7,_c(7),["nova","unstoppable"],enables_missile=True,enables_laser=True,damage_bonus=16),
    Skill("godgun",      "God's Wrath",     "Maximum firepower",                "weapons",4,8,_c(8),["omnifire","apocalypse"],fire_rate_bonus=0.22,damage_bonus=22,enables_triple_shot=True,spread_shot=True,enables_missile=True,enables_laser=True),
]

# ─── DEFENSE  cols 9-17 ──────────────────────────────────────────────────────
_D = [
    Skill("d_root",      "Defense Core",    "Foundation of defense",            "defense",13,0,0,[]),
    Skill("hull1",       "Hull Plating",    "+40 max HP",                       "defense",11,1,_c(1),["d_root"],max_hp_bonus=40),
    Skill("shield1",     "Shield Cell",     "+30 shield",                       "defense",15,1,_c(1),["d_root"],shield_bonus=30),
    Skill("hull2",       "Thick Hull",      "+60 max HP",                       "defense",10,2,_c(2),["hull1"],max_hp_bonus=60),
    Skill("regen1",      "Nano-Repair",     "Regen 2 HP/sec",                   "defense",12,2,_c(2),["hull1"],regen_bonus=2.0),
    Skill("shield2",     "Shield Boost",    "+50 shield",                       "defense",14,2,_c(2),["shield1"],shield_bonus=50),
    Skill("fast_rech",   "Fast Recharge",   "Shield regen faster +15",          "defense",16,2,_c(2),["shield1"],shield_bonus=15),
    Skill("hull3",       "Bulkhead",        "+80 max HP",                       "defense",9,3,_c(3),["hull2"],max_hp_bonus=80),
    Skill("regen2",      "Repair Drone",    "Regen +3 HP/sec",                  "defense",11,3,_c(3),["regen1"],regen_bonus=3.0),
    Skill("shield3",     "Heavy Shield",    "+80 shield",                       "defense",13,3,_c(3),["shield2"],shield_bonus=80),
    Skill("reflect1",    "Deflector Mesh",  "10% bullet reflect",               "defense",15,3,_c(3),["fast_rech"],reflects_bullets=0.10),
    Skill("emerg_regen", "Emerg. Regen",    "Regen +2 HP/sec",                  "defense",17,3,_c(3),["fast_rech"],regen_bonus=2.0),
    Skill("titan_hull",  "Titan Hull",      "+110 max HP",                      "defense",9,4,_c(4),["hull3"],max_hp_bonus=110),
    Skill("regen3",      "Swarm Repair",    "Regen +5 HP/sec",                  "defense",11,4,_c(4),["regen2"],regen_bonus=5.0),
    Skill("reflect2",    "Mirror Plating",  "Reflect +18%",                     "defense",14,4,_c(4),["shield3","reflect1"],reflects_bullets=0.18),
    Skill("oversh",      "Overshield",      "+70 shield, +22 HP",               "defense",16,4,_c(4),["shield3"],shield_bonus=70,max_hp_bonus=22),
    Skill("fortress",    "Fortress Mode",   "+130 HP, regen +4/sec",            "defense",10,5,_c(5),["titan_hull","regen3"],max_hp_bonus=130,regen_bonus=4.0),
    Skill("reflect3",    "Mirror Wall",     "Reflect +22%",                     "defense",15,5,_c(5),["reflect2"],reflects_bullets=0.22),
    Skill("revival",     "Revival Cell",    "+90 HP, regen +3/sec",             "defense",17,5,_c(5),["oversh"],max_hp_bonus=90,regen_bonus=3.0),
    Skill("juggernaut",  "Juggernaut",      "+160 HP, regen +5/sec",            "defense",11,6,_c(6),["fortress"],max_hp_bonus=160,regen_bonus=5.0),
    Skill("full_mirror", "Full Mirror",     "Reflect +27%",                     "defense",15,6,_c(6),["reflect3"],reflects_bullets=0.27),
    Skill("god_shield",  "Divine Shield",   "+220 HP, regen +6/sec, +100 sh",   "defense",12,7,_c(7),["juggernaut","full_mirror"],max_hp_bonus=220,regen_bonus=6.0,shield_bonus=100),
    Skill("perfect_ref", "Perfect Mirror",  "Reflect +16%",                     "defense",16,7,_c(7),["full_mirror","revival"],reflects_bullets=0.16),
    Skill("immortal",    "Immortal Core",   "All defense maxed",                "defense",13,8,_c(8),["god_shield","perfect_ref"],max_hp_bonus=260,regen_bonus=8.0,shield_bonus=160,reflects_bullets=0.22),
]

# ─── ENGINE  cols 18-26 ──────────────────────────────────────────────────────
_E = [
    Skill("e_root",      "Engine Core",     "Foundation of propulsion",         "engine",22,0,0,[]),
    Skill("afterburn",   "Afterburner",     "+75 max speed",                    "engine",20,1,_c(1),["e_root"],speed_bonus=75),
    Skill("boost_tk",    "Boost Tank",      "Boost CD -0.5s",                   "engine",24,1,_c(1),["e_root"],boost_cd_bonus=0.5),
    Skill("engine1",     "Engine Tune",     "+60 max speed",                    "engine",19,2,_c(2),["afterburn"],speed_bonus=60),
    Skill("drift",       "Drift Control",   "+45 speed",                        "engine",21,2,_c(2),["afterburn"],speed_bonus=45),
    Skill("boost2",      "Nitro",           "Boost CD -0.7s",                   "engine",23,2,_c(2),["boost_tk"],boost_cd_bonus=0.7),
    Skill("boost_pow",   "Boost Power",     "+28 speed, stronger boost",        "engine",25,2,_c(2),["boost_tk"],speed_bonus=28),
    Skill("engine2",     "Hyperdrive",      "+95 max speed",                    "engine",18,3,_c(3),["engine1"],speed_bonus=95),
    Skill("warp",        "Warp Drive",      "Short warp dash (F)",              "engine",20,3,_c(3),["drift"],enables_warp=True),
    Skill("boost3",      "Overclock",       "Boost CD -1.0s",                   "engine",22,3,_c(3),["boost2"],boost_cd_bonus=1.0),
    Skill("phase",       "Phase Drive",     "+75 speed & +40 shield",           "engine",24,3,_c(3),["boost_pow"],speed_bonus=75,shield_bonus=40),
    Skill("slipstream",  "Slipstream",      "+55 speed",                        "engine",26,3,_c(3),["boost_pow"],speed_bonus=55),
    Skill("engine3",     "Quantum Drive",   "+120 max speed",                   "engine",18,4,_c(4),["engine2"],speed_bonus=120),
    Skill("stealth",     "Stealth Cloak",   "Invisibility (C)",                 "engine",20,4,_c(4),["warp"],enables_stealth=True),
    Skill("boost4",      "Flash Boost",     "Boost CD -1.0s",                   "engine",22,4,_c(4),["boost3"],boost_cd_bonus=1.0),
    Skill("evasion",     "Evasion Protocol","+65 speed",                        "engine",25,4,_c(4),["phase","slipstream"],speed_bonus=65),
    Skill("no_limit",    "Limiter Off",     "+190 speed cap",                   "engine",19,5,_c(5),["engine3"],speed_bonus=190),
    Skill("ghost",       "Ghost Protocol",  "Stealth lasts longer",             "engine",21,5,_c(5),["stealth"],enables_stealth=True),
    Skill("boost5",      "Perma-Boost",     "Boost CD -1.0s",                   "engine",22,5,_c(5),["boost4"],boost_cd_bonus=1.0),
    Skill("blink",       "Blink Drive",     "Boost CD -1.0s, +55 speed",        "engine",25,5,_c(5),["evasion"],boost_cd_bonus=1.0,speed_bonus=55),
    Skill("lightspeed",  "Light Speed",     "+230 speed, near-instant boost",   "engine",19,6,_c(6),["no_limit"],speed_bonus=230,boost_cd_bonus=1.0),
    Skill("phantom",     "Phantom Ship",    "Stealth+speed+shield",             "engine",21,6,_c(6),["ghost","boost5"],enables_stealth=True,speed_bonus=85,shield_bonus=35),
    Skill("transcend",   "Transcendence",   "Max speed+stealth+warp",           "engine",20,7,_c(7),["lightspeed","phantom"],speed_bonus=160,enables_stealth=True,enables_warp=True,boost_cd_bonus=1.0),
    Skill("blink2",      "Quantum Blink",   "Boost instant, +110 speed",        "engine",24,7,_c(7),["blink"],boost_cd_bonus=1.5,speed_bonus=110),
    Skill("ascension",   "Ascension Drive", "All engine perks maxed",           "engine",22,8,_c(8),["transcend","blink2"],speed_bonus=210,boost_cd_bonus=2.0,enables_stealth=True,enables_warp=True,shield_bonus=65),
]

# ─── PRESTIGE WEAPONS  cols 0-8 ──────────────────────────────────────────────
_PW = [
    Skill("pw_root",     "Void Arsenal",    "Prestige weapons foundation",      "p_weapons",4,0,0,[],is_prestige=True),
    Skill("pw_faster",   "Temporal Rounds", "Bullets move 35% faster",          "p_weapons",2,1,_pc(1),["pw_root"],is_prestige=True,bullet_speed_mult=1.35),
    Skill("pw_dmgmult",  "Dark Matter",     "All damage x1.25",                 "p_weapons",6,1,_pc(1),["pw_root"],is_prestige=True,damage_mult=1.25),
    Skill("pw_chain",    "Chain Lightning", "Bullets arc to nearby enemies",    "p_weapons",2,2,_pc(2),["pw_faster"],is_prestige=True,chain_lightning=True),
    Skill("pw_dmgmult2", "Singularity Core","All damage x1.35",                 "p_weapons",6,2,_pc(2),["pw_dmgmult"],is_prestige=True,damage_mult=1.35),
    Skill("pw_auto",     "Auto-Targeting",  "Missiles fire automatically",      "p_weapons",4,2,_pc(2),["pw_root"],is_prestige=True,auto_missile=True,enables_missile=True),
    Skill("pw_faster2",  "Railgun Drive",   "Bullets move 45% faster",          "p_weapons",1,3,_pc(3),["pw_chain"],is_prestige=True,bullet_speed_mult=1.45),
    Skill("pw_quad",     "Quad Shot",       "Triple + double combined",         "p_weapons",3,3,_pc(3),["pw_chain"],is_prestige=True,enables_triple_shot=True,enables_double_shot=True),
    Skill("pw_pierce",   "Void Pierce",     "+40 dmg, triple shot",             "p_weapons",5,3,_pc(3),["pw_dmgmult2"],is_prestige=True,damage_bonus=40,enables_triple_shot=True),
    Skill("pw_dmgmult3", "Reality Shatter", "All damage x1.5",                  "p_weapons",7,3,_pc(3),["pw_dmgmult2"],is_prestige=True,damage_mult=1.5),
    Skill("pw_frenzy",   "Bullet Frenzy",   "+40% fire rate, bullets x1.4 spd", "p_weapons",2,4,_pc(4),["pw_quad","pw_faster2"],is_prestige=True,fire_rate_bonus=0.40,bullet_speed_mult=1.40),
    Skill("pw_omnidmg",  "Omnistrike",      "x1.4 dmg, triple, spread, missile","p_weapons",5,4,_pc(4),["pw_pierce","pw_dmgmult3"],is_prestige=True,damage_mult=1.4,enables_triple_shot=True,spread_shot=True,enables_missile=True),
    Skill("pw_god",      "Weapons of God",  "x2 dmg, +50% rate, all shots",     "p_weapons",4,5,_pc(5),["pw_frenzy","pw_omnidmg"],is_prestige=True,damage_mult=2.0,fire_rate_bonus=0.50,enables_triple_shot=True,spread_shot=True,enables_missile=True,enables_laser=True,chain_lightning=True),
]

# ─── PRESTIGE DEFENSE  cols 9-17 ─────────────────────────────────────────────
_PD = [
    Skill("pd_root",     "Void Armor",      "Prestige defense foundation",      "p_defense",13,0,0,[],is_prestige=True),
    Skill("pd_spike",    "Shield Spike",    "Shield deals dmg on bullet hit",   "p_defense",11,1,_pc(1),["pd_root"],is_prestige=True,shield_spike=True),
    Skill("pd_xp",       "Data Absorption", "Gain 30% more XP",                 "p_defense",15,1,_pc(1),["pd_root"],is_prestige=True,xp_mult=1.30),
    Skill("pd_hp",       "Void Plating",    "+300 max HP",                      "p_defense",11,2,_pc(2),["pd_spike"],is_prestige=True,max_hp_bonus=300),
    Skill("pd_regen",    "Nano Swarm",      "Regen 12 HP/sec",                  "p_defense",13,2,_pc(2),["pd_root"],is_prestige=True,regen_bonus=12.0),
    Skill("pd_xp2",      "Memory Harvest",  "Gain 50% more XP",                 "p_defense",15,2,_pc(2),["pd_xp"],is_prestige=True,xp_mult=1.50),
    Skill("pd_mirror",   "Void Mirror",     "Reflect 40% of bullets",           "p_defense",11,3,_pc(3),["pd_hp"],is_prestige=True,reflects_bullets=0.40),
    Skill("pd_shield",   "Quantum Shield",  "+400 shield",                      "p_defense",13,3,_pc(3),["pd_regen"],is_prestige=True,shield_bonus=400),
    Skill("pd_xp3",      "Void Scholar",    "Gain 75% more XP",                 "p_defense",15,3,_pc(3),["pd_xp2"],is_prestige=True,xp_mult=1.75),
    Skill("pd_regen2",   "Phoenix Cell",    "Regen 20 HP/sec",                  "p_defense",11,4,_pc(4),["pd_mirror","pd_shield"],is_prestige=True,regen_bonus=20.0),
    Skill("pd_xp4",      "Ascendant Mind",  "Gain 2x XP",                       "p_defense",15,4,_pc(4),["pd_xp3"],is_prestige=True,xp_mult=2.0),
    Skill("pd_god",      "Void Incarnate",  "+500 HP, 25 regen, 40% reflect, 2x XP","p_defense",13,5,_pc(5),["pd_regen2","pd_xp4"],is_prestige=True,max_hp_bonus=500,regen_bonus=25.0,reflects_bullets=0.40,xp_mult=2.0,shield_bonus=300),
]

# ─── PRESTIGE ENGINE  cols 18-26 ─────────────────────────────────────────────
_PE = [
    Skill("pe_root",     "Void Thrusters",  "Prestige engine foundation",       "p_engine",22,0,0,[],is_prestige=True),
    Skill("pe_invuln",   "Phase Burst",     "Brief invincibility on boost",     "p_engine",20,1,_pc(1),["pe_root"],is_prestige=True,invuln_on_boost=True),
    Skill("pe_speed",    "Void Drive",      "+350 max speed",                   "p_engine",24,1,_pc(1),["pe_root"],is_prestige=True,speed_bonus=350),
    Skill("pe_timeslow", "Time Dilation",   "Nearby enemies move 60% slower",   "p_engine",20,2,_pc(2),["pe_invuln"],is_prestige=True,time_slow=True),
    Skill("pe_blink",    "Void Blink",      "Boost CD 0.3s (near-instant)",     "p_engine",22,2,_pc(2),["pe_root"],is_prestige=True,boost_cd_bonus=2.5),
    Skill("pe_speed2",   "Lightspeed Core", "+500 max speed",                   "p_engine",24,2,_pc(2),["pe_speed"],is_prestige=True,speed_bonus=500),
    Skill("pe_invuln2",  "Temporal Armor",  "Invuln on boost, +200 speed",      "p_engine",20,3,_pc(3),["pe_timeslow"],is_prestige=True,invuln_on_boost=True,speed_bonus=200),
    Skill("pe_warp",     "Void Warp",       "Warp + stealth + blink",           "p_engine",22,3,_pc(3),["pe_blink"],is_prestige=True,enables_warp=True,enables_stealth=True,boost_cd_bonus=1.5),
    Skill("pe_speed3",   "Tachyon Engine",  "+700 max speed",                   "p_engine",24,3,_pc(3),["pe_speed2"],is_prestige=True,speed_bonus=700),
    Skill("pe_matrix",   "Bullet Time",     "Time slow + invuln on boost",      "p_engine",21,4,_pc(4),["pe_invuln2","pe_warp"],is_prestige=True,time_slow=True,invuln_on_boost=True,boost_cd_bonus=1.0),
    Skill("pe_god",      "Singularity",     "+1000 speed, instant boost, phase","p_engine",23,4,_pc(4),["pe_speed3","pe_matrix"],is_prestige=True,speed_bonus=1000,boost_cd_bonus=3.0,invuln_on_boost=True,time_slow=True,enables_warp=True,enables_stealth=True),
]

SKILL_TREE:         List[Skill] = _W + _D + _E
PRESTIGE_TREE:      List[Skill] = _PW + _PD + _PE
ALL_SKILLS:         List[Skill] = SKILL_TREE + PRESTIGE_TREE

# Branch to capstone skill ID (the one that "maxes" the tree)
BRANCH_CAPSTONES = {
    "weapons": "godgun",
    "defense": "immortal",
    "engine":  "ascension",
}
REGULAR_BRANCHES = ["weapons", "defense", "engine"]


class SkillTreeManager:
    def __init__(self):
        self.skills = {s.id: s for s in ALL_SKILLS}
        # Auto-unlock free roots
        for sk in self.skills.values():
            if sk.cost == 0:
                sk.unlocked = True
        self.prestige_points = 0
        # Track which prestige trees are unlocked (require a prestige point spent on root)
        # Prestige roots are free to unlock once you have ≥1 prestige point

    # ── Querying ──────────────────────────────────────────────────────────────

    def branch_is_maxed(self, branch: str) -> bool:
        cap = BRANCH_CAPSTONES.get(branch)
        return cap is not None and self.skills[cap].unlocked

    def branch_can_reset(self, branch: str) -> bool:
        return self.branch_is_maxed(branch)

    def can_unlock(self, skill_id: str, current_xp: int) -> tuple:
        sk = self.skills[skill_id]
        if sk.unlocked:
            return False, "Already unlocked"
        # Check prerequisites
        for req in sk.requires:
            if not self.skills[req].unlocked:
                return False, f"Requires: {self.skills[req].name}"
        if sk.is_prestige:
            # Free roots only need ≥1 prestige point to open
            if sk.cost == 0:
                if self.prestige_points < 1:
                    return False, "Need 1 prestige point to open"
                return True, "OK"
            if self.prestige_points < sk.cost:
                return False, f"Need {sk.cost} prestige pts (have {self.prestige_points})"
            return True, "OK"
        else:
            if current_xp < sk.cost:
                return False, f"Need {sk.cost} XP (have {current_xp})"
            return True, "OK"

    def unlock(self, skill_id: str, current_xp: int) -> tuple:
        """Returns (success, new_xp). Deducts XP or prestige as appropriate."""
        ok, _ = self.can_unlock(skill_id, current_xp)
        if not ok:
            return False, current_xp
        sk = self.skills[skill_id]
        sk.unlocked = True
        if sk.is_prestige:
            if sk.cost > 0:
                self.prestige_points -= sk.cost
            return True, current_xp
        else:
            return True, current_xp - sk.cost

    def reset_branch(self, branch: str) -> bool:
        """Reset all non-root skills in branch, award 1 prestige point."""
        if not self.branch_can_reset(branch):
            return False
        for sk in self.skills.values():
            if sk.branch == branch and sk.cost > 0:
                sk.unlocked = False
        self.prestige_points += 1
        return True

    # ── Stats ─────────────────────────────────────────────────────────────────

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
            "dual_missile": False,
            # Prestige
            "bullet_speed_mult": 1.0,   "damage_mult": 1.0,
            "xp_mult": 1.0,             "invuln_on_boost": False,
            "auto_missile": False,      "chain_lightning": False,
            "time_slow": False,         "shield_spike": False,
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
            stats["reflect_chance"] = min(0.75, 1.0 - (1.0 - stats["reflect_chance"]) * (1.0 - sk.reflects_bullets))
            stats["bullet_speed_mult"]   *= sk.bullet_speed_mult
            stats["damage_mult"]         *= sk.damage_mult
            stats["xp_mult"]             *= sk.xp_mult
            if sk.enables_missile:    stats["missile"]         = True
            if sk.enables_laser:      stats["laser"]           = True
            if sk.enables_double_shot:stats["double_shot"]     = True
            if sk.enables_triple_shot:stats["triple_shot"]     = True
            if sk.spread_shot:        stats["spread_shot"]     = True
            if sk.ricochet:           stats["ricochet"]        = True
            if sk.enables_warp:       stats["warp"]            = True
            if sk.enables_stealth:    stats["stealth"]         = True
            if sk.dual_missile:       stats["dual_missile"]    = True
            if sk.invuln_on_boost:    stats["invuln_on_boost"] = True
            if sk.auto_missile:       stats["auto_missile"]    = True
            if sk.chain_lightning:    stats["chain_lightning"] = True
            if sk.time_slow:          stats["time_slow"]       = True
            if sk.shield_spike:       stats["shield_spike"]    = True
        return stats

    def get_branch(self, branch: str) -> List[Skill]:
        return [s for s in ALL_SKILLS if s.branch == branch]
