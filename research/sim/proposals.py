from economy_sim import BASE
import copy
def variant(name, **kw):
    c=copy.deepcopy(BASE); c["name"]=name
    for k,v in kw.items(): c[k]=v
    return c

COSTS_MID=[0,8000,60000,400000,3000000,25000000,200000000]
PROPOSED=[
  # A: only reshape the cost curve (slots + biome unlock costs)
  variant("A-cost-curve-only", slot_growth=2.0, biome_cost=COSTS_MID),
  # B: A + make Epic/Legendary/Mythic spawn less and Legendary a bit harder
  variant("B-cost+rarity", slot_growth=2.0, biome_cost=COSTS_MID, rare_mult=0.35, epic_mult=0.7,
          diff_add={"Legendary":.03,"Mythic":0}),
  # C: B + weaker net ladder (net bonus x0.6) -- nets were trivialising top-end catch odds
  variant("C-cost+rarity+weaker-nets", slot_growth=2.0, biome_cost=COSTS_MID, rare_mult=0.35, epic_mult=0.7,
          diff_add={"Legendary":.03,"Mythic":0}, net_bonus_scale=0.6),
  # D: C + 8h offline cap and 3x welcome boost for first 10 minutes
  variant("D-full-proposal", slot_growth=2.0, biome_cost=COSTS_MID, rare_mult=0.35, epic_mult=0.7,
          diff_add={"Legendary":.03,"Mythic":0}, net_bonus_scale=0.6, offline_cap_h=8,
          welcome_boost=3.0, welcome_minutes=10),
]

COSTS_HI=[0,25000,400000,6000000,60000000,600000000,6000000000]
PROPOSED += [
  variant("E-D+compressed-mutations", slot_growth=2.0, biome_cost=COSTS_HI, rare_mult=0.35, epic_mult=0.7,
          diff_add={"Legendary":.03,"Mythic":0}, net_bonus_scale=0.6, offline_cap_h=8,
          welcome_boost=3.0, welcome_minutes=10, mut_scale=0.7),
  variant("F-E+index-gate-60pct", slot_growth=2.0, biome_cost=COSTS_HI, rare_mult=0.35, epic_mult=0.7,
          diff_add={"Legendary":.03,"Mythic":0}, net_bonus_scale=0.6, offline_cap_h=8,
          welcome_boost=3.0, welcome_minutes=10, mut_scale=0.7, index_gate=0.6),
]
# keep only the variants worth reporting beyond baseline: A (cost only), D (rarity+nets+AFK), E, F
PROPOSED=[c for c in PROPOSED if c["name"][0] in "ADEF"]

COSTS_G=[0,20000,250000,2500000,15000000,90000000,500000000]
RECOMMENDED=variant("G-recommended-starting-point", slot_growth=2.0, biome_cost=COSTS_G, rare_mult=0.35, epic_mult=0.7,
          diff_add={"Legendary":.03,"Mythic":0}, net_bonus_scale=0.6, offline_cap_h=8,
          welcome_boost=3.0, welcome_minutes=10, mut_scale=0.7, index_gate=0.6)

D_MUT=variant("D-plus-mutation-compression-only", slot_growth=2.0, biome_cost=COSTS_MID, rare_mult=0.35, epic_mult=0.7,
          diff_add={"Legendary":.03,"Mythic":0}, net_bonus_scale=0.6, offline_cap_h=8,
          welcome_boost=3.0, welcome_minutes=10, mut_scale=0.7)
