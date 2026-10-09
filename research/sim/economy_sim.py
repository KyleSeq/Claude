#!/usr/bin/env python3
"""Catch a Titan economy simulator.

Models the economy exactly as written in the one-shot spec (CatchATitan one-shot
prompt: Appendix A creature table, slot cost 100*1.8^(slots-5), biome unlock costs,
catch roll p = 1 - threshold/luck). It is a MODEL, not the live game. Replace the
CONFIG blocks with real values from Config.luau / CreatureData.luau to audit the
shipped build. Anything marked ASSUMED is not in the spec.

Usage: python3 economy_sim.py [--seeds N] [--days D]
"""
import argparse, random, statistics, json, copy

# name, rarity, spawnWeight, coinRate, difficulty
BIOMES = {
 "Meadow": [("EmberFox","Common",28,1,.40),("MeadowBunny","Common",26,2,.35),("GoldenDeer","Common",20,3,.48),
   ("CrystalWing","Uncommon",14,8,.60),("MossyTurtle","Uncommon",8,12,.58),("PrismDragonfly","Rare",3,30,.74),
   ("ShimmerFox","Legendary",.9,600,.92),("AncestralSpirit","Mythic",.1,3000,.97)],
 "CrystalCave": [("CaveCrawler","Common",27,3,.42),("StoneMole","Common",23,4,.38),("Glowbat","Uncommon",18,10,.62),
   ("CrystalSpider","Uncommon",14,15,.65),("GeodeGolem","Rare",10,40,.75),("CrystalGolem","Epic",5,180,.85),
   ("CavePhoenix","Legendary",2,750,.92),("VoidCrawler","Mythic",.1,4000,.97)],
 "DeepOcean": [("CoralFish","Common",26,4,.44),("SandDolphin","Common",22,5,.50),("Luminjelly","Uncommon",18,12,.60),
   ("Deepfin","Rare",14,35,.76),("TitanCrab","Epic",8,200,.86),("SeaDragon","Epic",6,250,.88),
   ("AbyssalKraken","Legendary",1,800,.93),("OceanGod","Mythic",.1,5000,.97)],
 "Volcano": [("LavaLizard","Common",25,6,.46),("CinderBat","Common",21,7,.50),("EmberSalamander","Rare",18,45,.78),
   ("MoltenGolem","Epic",10,220,.84),("Magmawing","Epic",8,280,.88),("InfernoDrake","Legendary",2,900,.93),
   ("PhoenixGod","Mythic",.1,6000,.98)],
 "SkyIslands": [("CloudPuff","Common",26,8,.48),("WindSparrow","Common",22,10,.52),("Stormbird","Rare",16,50,.79),
   ("ZephyrSerpent","Epic",9,240,.85),("Cloudwhale","Legendary",3,1100,.92),("StormGod","Legendary",1,1400,.94),
   ("CosmicWyrmling","Mythic",.1,7500,.98)],
 "ArcticTundra": [("Frostfang","Uncommon",24,18,.62),("IcePenguin","Common",22,9,.47),("GlacialBear","Epic",14,260,.84),
   ("SnowDrake","Epic",10,320,.87),("IcePhoenix","Legendary",3,1300,.93),("FrostTitan","Legendary",1,1600,.94),
   ("AbsoluteZero","Mythic",.1,9000,.98)],
 "AncientRuins": [("FossilCrawler","Common",22,12,.46),("RuneGolem","Rare",18,60,.76),("GoldenHawk","Rare",16,70,.78),
   ("SunGolem","Epic",12,350,.85),("Starwarden","Legendary",3,1800,.93),("AncientDragon","Legendary",1,2200,.95),
   ("CosmicWarden","Mythic",.1,11000,.99)],
}
ORDER = list(BIOMES)
RANK = {"Common":1,"Uncommon":2,"Rare":3,"Epic":4,"Legendary":5,"Mythic":6}
MUT = [("None",85,1),("Shiny",8,5),("Giant",4,8),("Shadow",1.5,12),("Corrupted",.4,20),("Rainbow",.1,30)]

BASE = dict(
  name="spec-baseline",
  biome_cost=[0,5000,25000,100000,500000,2000000,10000000],   # spec
  slot_base=100, slot_growth=1.8, slots_start=5, slots_cap=50,  # spec
  # ASSUMED net ladder (spec only gives Crystal = tier3 = +0.16 for 5,000)
  net_cost=[0,1000,5000,20000,100000,500000,2500000], net_bonus=[0,.05,.16,.24,.32,.40,.48],
  offline_cap_h=24, claim_required=False,                      # spec: 24h cap, silent deposit
  online_mult=1.0,                                             # spec: none
  welcome_boost=1.0, welcome_minutes=0,
  rare_mult=1.0, epic_mult=1.0,                                # spawn-weight multipliers
  diff_add={"Legendary":0,"Mythic":0},                         # catch difficulty additions
  attempts_per_min=3.0, weight_diff=.04,
)

def mut_roll(r, scale=1.0):
    t=sum(w for _,w,_ in MUT); x=r.random()*t
    for n,w,m in MUT:
        x-=w
        if x<=0: return m**scale
    return 1

def pick(r, biome, cfg):
    cs=BIOMES[biome]; ws=[]
    for c in cs:
        w=c[2]
        if c[1]=="Epic": w*=cfg["epic_mult"]
        if c[1] in("Legendary","Mythic"): w*=cfg["rare_mult"]
        ws.append(w)
    x=r.random()*sum(ws)
    for c,w in zip(cs,ws):
        x-=w
        if x<=0: return c
    return cs[-1]

def run(cfg, arche, days, seed):
    r=random.Random(seed)
    coins=0.0; slots=cfg["slots_start"]; net=0; biome_i=0
    placed=[]            # list of per-minute incomes (best N)
    ms={}                # milestones: name -> day
    stash=0.0; last_active_min=0; caught=set()
    def income(): return sum(sorted(placed,reverse=True)[:slots])
    for minute in range(days*1440):
        day=minute/1440
        tod=minute%1440
        active=any(s<=tod<s+arche["sess_len"] for s in arche["starts"])
        inc=income()
        if active:
            coins+=inc*cfg["online_mult"]
            if minute<cfg["welcome_minutes"]: coins+=inc*(cfg["welcome_boost"]-1)
            # active catching
            for _ in range(int(cfg["attempts_per_min"]+ (1 if r.random()<cfg["attempts_per_min"]%1 else 0))):
                bi=biome_i if (biome_i==0 or r.random()<.8) else r.randrange(biome_i+1)
                c=pick(r,ORDER[bi],cfg)
                diff=c[4]+cfg["diff_add"].get(c[1],0)+cfg["weight_diff"]
                thr=min(.98,max(.05,diff-cfg["net_bonus"][net]*cfg.get("net_bonus_scale",1.0)))
                if r.random()>thr:   # catch succeeds (luck=1)
                    v=c[3]*mut_roll(r,cfg.get("mut_scale",1.0))
                    placed.append(v); caught.add(c[0])
                    if len(placed)>200: placed=sorted(placed,reverse=True)[:100]
                    ms.setdefault("catch_"+c[1],day)
        else:
            # offline accrual with cap
            cap=cfg["offline_cap_h"]*60
            off_min=(minute-last_active_min)
            if off_min<=cap: coins+=inc
        if active: last_active_min=minute
        # spending: cheapest affordable of {slot, net, biome}
        for _ in range(6):
            opts=[]
            if slots<cfg["slots_cap"]: opts.append((cfg["slot_base"]*cfg["slot_growth"]**(slots-cfg["slots_start"]),"slot"))
            if net<6: opts.append((cfg["net_cost"][net+1],"net"))
            if biome_i<6:
                gate=cfg.get("index_gate",0.0)
                cur=[x for x in BIOMES[ORDER[biome_i]] if x[1]!="Mythic"]
                ok=(sum(1 for x in cur if x[0] in caught)/len(cur))>=gate
                if ok: opts.append((cfg["biome_cost"][biome_i+1],"biome"))
            if not opts: break
            cost,kind=min(opts)
            if coins<cost: break
            coins-=cost
            if kind=="slot": slots+=1; ms.setdefault(f"slots_{slots}",day)
            elif kind=="net": net+=1; ms.setdefault(f"net_{net+1}",day)
            else: biome_i+=1; ms.setdefault(f"biome_{ORDER[biome_i]}",day)
    return ms

ARCH = {
 "casual (2x15min/day)": dict(starts=[600,1200], sess_len=15),
 "regular (3x30min/day)": dict(starts=[480,780,1200], sess_len=30),
 "dedicated (3h/day)":   dict(starts=[420,780,1140], sess_len=60),
}
KEYS=["slots_10","slots_20","biome_CrystalCave","biome_DeepOcean","biome_Volcano","biome_SkyIslands",
      "biome_ArcticTundra","biome_AncientRuins","catch_Epic","catch_Legendary","catch_Mythic"]

def study(cfg, seeds, days):
    out={}
    for an,a in ARCH.items():
        runs=[run(cfg,a,days,s) for s in range(seeds)]
        row={}
        for k in KEYS:
            vals=[m[k] for m in runs if k in m]
            row[k]=(round(statistics.median(vals),1) if len(vals)>=seeds/2 else None, f"{len(vals)}/{seeds}")
        out[an]=row
    return out

def show(cfg, res):
    print(f"\n=== {cfg['name']} === (median DAY reached; n/N = runs that reached it within horizon)")
    for an,row in res.items():
        print(f"\n  {an}")
        for k,(v,n) in row.items():
            print(f"    {k:22s} {('day '+str(v)) if v is not None else '> horizon':>12s}  ({n})")

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--seeds",type=int,default=24); ap.add_argument("--days",type=int,default=60)
    ap.add_argument("--json",action="store_true"); a=ap.parse_args()
    from proposals import PROPOSED
    allres={}
    for cfg in [BASE]+PROPOSED:
        res=study(cfg,a.seeds,a.days); allres[cfg["name"]]=res
        if not a.json: show(cfg,res)
    if a.json: print(json.dumps(allres,indent=1))
