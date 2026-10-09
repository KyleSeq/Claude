# Report 03: Economy, Balance and AFK Progression

**What this is.** A quantitative audit of the economy as written in your one-shot prompt, a simulation of how long players take to progress under that spec, and a recommended re-balance with the reasoning.

**What this is not.** I do not have the live game's code or `Config`, so this audits the *spec*. If the shipped numbers differ, rerun the simulator with the real values (instructions in section 8). The qualitative conclusions should hold, but the day counts will move.

All simulator code is in `research/sim/`. Results below come from running it.

---

## 1. Headline Findings

1. **As specified, the game is completable in days.** A casual player (two 15-minute sessions a day) unlocks all seven non-rebirth biomes by about **day 3.5** and catches a Mythic by about **day 9**. A dedicated player (3 hours a day) is done in **under 2 days** for biomes. This matches your "too easy to complete" note.
2. **Raising prices barely helps.** Making slot and biome costs 10-20x steeper delayed full unlocks to about day 10 for a casual player, not weeks. The reason is structural (finding 3).
3. **Income grows faster than costs can follow.** Creature income spans **1 to 25,000 coins/min** (25,000x). Biome costs span **5,000 to 10,000,000** (2,000x). Mutations then multiply income again (stacking up to x600). Costs can never keep pace with income, so players leave the cost curve behind and nothing gates them.
4. **The Luck Booster removes catch difficulty.** With the spec formula, a x3 booster makes every catch **at least 67% likely**, even a Mythic with no net.
5. **Late-biome rarity is far too common.** In the spec's spawn tables, Legendary is roughly **5% of spawns** (1 in 18) in Sky Islands, Arctic and Ruins. The Shadow Realm is **~30% Mythic and ~32% Legendary**.
6. **Offline income has no hook.** A silent 24-hour accrual gives players no reason to come back sooner than daily, and nothing visible to claim.

---

## 2. Method

A Python model (`research/sim/economy_sim.py`) simulates one minute at a time. It uses the exact creature table (Appendix A), slot-cost formula `100 * 1.8^(slots-5)`, biome costs, mutation table and catch formula from your one-shot spec.

**Player archetypes.**

| Archetype | Pattern | Total active |
|---|---|---|
| Casual | 2 sessions of 15 min | 30 min/day |
| Regular | 3 sessions of 30 min | 90 min/day |
| Dedicated | 3 sessions of 60 min | 180 min/day |

**Behaviour.** 3 catch attempts per active minute, hunting mostly in the best unlocked biome, placing the highest-income creatures in available slots, and spending on the cheapest affordable upgrade among next slot, next net and next biome. Offline, income accrues (up to a cap) between sessions.

**Assumptions not in the spec (labelled ASSUMED in code).**
- Net ladder: bonuses `0 / 0.05 / 0.16 / 0.24 / 0.32 / 0.40 / 0.48` costing `0 / 1k / 5k / 20k / 100k / 500k / 2.5M`. (The spec gives only Crystal Net = +0.16 for 5,000.)
- A constant 0.04 weight-difficulty bonus.
- No Luck Booster, rebirth, raids or trading in the baseline run.

**Limits.** Greedy buying is simplistic; real players are less efficient early and more strategic later. Use the results to **compare configurations**, not as a prediction of exact days. Medians over 12-16 seeds; a few Mythic runs did not finish inside the horizon (shown as n/N).

---

## 3. Results: Spec Baseline vs Variants

Median **day** reached. "A" changes only costs. "D" adds rarity, net and offline changes. "E" also compresses mutations and steepens costs. "G" is the recommended starting point.

### Casual (2 x 15 min per day)

| Milestone | Spec | A: costs | D: +rarity/nets/AFK | E: +mutations | **G: recommended** |
|---|---|---|---|---|---|
| Crystal Cave | 0.5 | 0.6 | 0.5 | 0.9 | **0.8** |
| Deep Ocean | 0.9 | 1.0 | 1.0 | 2.6 | **2.5** |
| Volcano | 1.2 | 1.6 | 1.9 | 6.9 | **4.8** |
| Sky Islands | 1.7 | 2.7 | 4.2 | 19.9 | **10.0** |
| Arctic Tundra | 2.4 | 5.0 | 8.0 | 57.6 | **20.2** |
| Ancient Ruins | 3.5 | 10.0 | 19.4 | >120 | **49.7** |
| First Epic | 0.8 | 0.8 | 1.1 | 1.8 | **1.8** |
| First Legendary | 1.8 | 2.6 | 6.1 | 9.1 | **7.1** |
| First Mythic | 8.9 | 12.6 | 28.3 (8/12) | 25.9 (8/12) | **78.6 (14/16)** |

### Regular (3 x 30 min per day)

| Milestone | Spec | A | D | E | **G** |
|---|---|---|---|---|---|
| Deep Ocean | 0.5 | 0.6 | 0.6 | 1.6 | **1.5** |
| Volcano | 0.7 | 0.9 | 1.0 | 4.0 | **2.8** |
| Sky Islands | 0.9 | 1.6 | 2.1 | 11.9 | **5.9** |
| Arctic Tundra | 1.3 | 2.7 | 4.2 | 36.0 | **11.9** |
| Ancient Ruins | 2.1 | 6.4 | 10.3 | 111.8 (7/12) | **30.9** |
| First Legendary | 0.8 | 0.7 | 2.3 | 3.3 | **3.1** |
| First Mythic | 4.3 | 3.9 | 29.9 | 18.3 | **30.4** |

### Dedicated (3 h per day)

| Milestone | Spec | A | D | E | **G** |
|---|---|---|---|---|---|
| Deep Ocean | 0.4 | 0.5 | 0.6 | 1.1 | **1.0** |
| Volcano | 0.6 | 0.7 | 0.8 | 3.0 | **2.1** |
| Sky Islands | 0.7 | 1.2 | 1.7 | 8.9 | **4.6** |
| Arctic Tundra | 0.9 | 2.0 | 3.2 | 27.6 | **8.8** |
| Ancient Ruins | 1.6 | 4.8 | 8.2 | 87.6 | **23.5** |
| First Legendary | 0.7 | 0.7 | 1.3 | 2.3 | **1.6** |
| First Mythic | 3.6 | 6.6 | 13.5 | 11.8 | **14.6** |

**Reading the table.**
- A and D show that cost and rarity tweaks alone leave the whole game inside three weeks.
- E shows the opposite failure: overshooting makes the last biome take **88-120+ days**, which is a churn cliff. (An Index-gate variant "F" produced identical results to E, which tells us that costs were already the binding constraint, so Index gating adds no pacing in that setup; keep it for *content* reasons, not pacing.)
- **G** keeps the early game fast (Crystal Cave under a day, Deep Ocean in 1-2.5 days) and stretches the late game to roughly 3.5-7 weeks. The Mythic target of ~2 weeks (dedicated) to 11 weeks (casual) is deliberately long; see section 6 for how the synchronized-spawn events keep it from feeling empty.

> **These are starting targets, not facts.** Tune from live data. The right "time to finish" is a product decision (see the open questions at the end of the Room for Improvement review).

---

## 4. Why the Spec Breaks: Structural Problems

### 4.1 Income and cost scales do not match
- Creature income: 1 to 25,000 coins/min.
- Biome costs: 5,000 to 10,000,000.
- Mutation stacking: up to 30 x 20 = 600x (Rainbow + Corrupted), and Shiny + Shadow = 60x.
- Slot cost is `100 * 1.8^(n-5)`: grows steadily, but once a player holds a few Rare or Epic creatures the next slot costs only minutes of income. In the baseline run a casual player has 20 slots by day 1.6.

**Principle:** pace unlocks against *income*, not against absolute coins. A common pro technique is to price each gate as "N hours of current income at the point the player is expected to reach it", then check the result with a simulator like this one.

### 4.2 Mutations are a large hidden multiplier, but a moderate pacing lever
Mutation stacking reaches x600 in the spec, which dominates late income. I tested compressing each multiplier to the power 0.7 (Shiny 5x becomes ~3.1x, Rainbow 30x becomes ~10.9x) **in isolation**, on top of variant D (same costs, only the mutation change):

| Casual median day | D (spec mutations) | D + compression only |
|---|---|---|
| Arctic Tundra | 8.0 | 9.9 |
| Ancient Ruins | 19.4 | 24.8 |
| First Legendary | 6.1 | 5.9 |

So compression alone slows the late game by roughly 25-30%. It is worth doing for *spectacle control* (a x600 pet distorts the economy and trading values), but it is not what stretches the curve. **Correction note:** my first reading attributed variant E's large slowdown to mutation compression. E also raised costs by 3x to 30x; the isolation run shows most of E's effect came from the costs.

Recommended multiplier set after compression: Shiny x3, Giant x4, Shadow x6, Corrupted x8, Rainbow x11 (rounded from the 0.7 power). Stacking stays multiplicative but with a **cap** on total mutation multiplier (suggest x50) so two top mutations cannot erase the curve.

### 4.3 The catch formula and nets
Spec: `p = clamp(1 - threshold/luck, 0, 1)`, `threshold = clamp(difficulty + weightBonus - netBonus, 0.05, 0.98)`.

Catch chance with the assumed net ladder (weight bonus 0.04):

| Species difficulty | No net | Crystal (+.16) | Best (+.48) | Best net + Luck x3 |
|---|---|---|---|---|
| Common .40 | 56% | 72% | 95% | 98% |
| Rare .74 | 22% | 38% | 70% | 90% |
| Epic .86 | 10% | 26% | 58% | 86% |
| Legendary .92 | 4% | 20% | 52% | 84% |
| Mythic .97 | 2% | 15% | 47% | 82% |
| Mythic .995 | 2% | 12.5% | 44.5% | 81.5% |

Two problems:
1. A **subtractive** net bonus makes the best net erase most of the difficulty gap between rarities (Common 95% vs Mythic 47% at top net).
2. Luck x3 divides the threshold. With the clamp at 0.98, the **minimum** catch chance under x3 is `1 - 0.98/3 = 67%`. A paid booster therefore turns a Mythic from a rare event into a coin flip you usually win.

**Also:** the catch-minigame spec's own balance table assumes a Mythic base chance of 5%. The formula gives 2-4% with no or a basic net, and 15-47% with mid-to-top nets. The two documents describe different games; align them (recommendation below).

### 4.4 Spawn tables (details in Report 04)
Exact shares from the spec are in Report 04 section 2. The key numbers: Legendary ~5.2-5.6% of spawns in Sky/Arctic/Ruins; Shadow Realm 31.5% Legendary and 30% Mythic. Every Legendary and Mythic catch triggers a server announcement, so banners would fire constantly in late biomes.

### 4.5 Offline income
Silent 24-hour accrual: leaving for 23 hours and 59 minutes is optimal, and there is nothing to see on return. Pair a shorter cap with a visible claim moment.

---

## 5. Recommended Re-balance (Variant G)

All values are **[DESIGN]**, held in `Config`, and meant to be tuned.

| Lever | Spec | Recommended | Why |
|---|---|---|---|
| Slot cost growth | `100 * 1.8^(n-5)` | `100 * 2.0^(n-5)` | Steeper mid-game, still cheap early |
| Biome unlock costs | 5k / 25k / 100k / 500k / 2M / 10M | **20k / 250k / 2.5M / 15M / 90M / 500M** | Reaches ~day 50 casual, ~day 24 dedicated |
| Mutation multipliers | 5 / 8 / 12 / 20 / 30 | **3 / 4 / 6 / 8 / 11**, stack cap x50 | Controls spectacle and trade-value distortion; moderate pacing effect (~25%) |
| Epic spawn weight | 1.0 | x0.7 | Epic should not be routine on day 1 |
| Legendary and Mythic weights | 1.0 | x0.35 (ambient) + scheduled events (Report 04) | Rarity must mean something; events carry the spectacle |
| Legendary base difficulty | as listed | +0.03 | Small extra gate at the top |
| Net bonus | up to +0.48 | scale to ~60% (max about +0.29) *or* switch to a multiplicative model | Keep rarity difficulty gaps visible |
| Luck Booster | divides threshold by 3 | **Replace** with a spawn-weight modifier on Rare+ (Report 04) | Remove the 67% floor; make it disclosable |
| Offline accrual | 24 h, silent | **8 h cap, claim required** | Return incentive, stopping point (Report 02 A2) |
| First 10 minutes | none | **x3 income "welcome boost"** | Protects the fast start you asked for |
| Index gating | none | Unlock a biome only after catching ~60% of the previous biome's non-Mythic species (in addition to cost) | Content pacing and Index engagement |

**Early-game protection (your "no slow start" requirement).** In G, a casual player unlocks Crystal Cave in under a day and Deep Ocean in about 2.5 days, buys 10 slots in about half a day, and sees an Epic in about 2 days. Combine with the guaranteed-first-catch tutorial and the 3x welcome boost.

---

## 6. AFK Design That Encourages CCU Without Creating a Feed

You asked for an AFK grinding aspect to encourage concurrent playtime. AFK idle income and "being present" pull in different directions, so design them as two layers.

**Layer 1: Offline stash (calm, scheduled).**
- Accrues up to **8 hours**, then stops. Rate: 100% for the first 2 hours, 50% after **[DESIGN]**.
- Shows a "Welcome back" panel with an explicit claim button and what accrued while away.
- One optional rewarded-video doubling per claim (deterministic, disclosed; see Report 02). Never a chain.

**Layer 2: Presence bonus (the CCU lever).**
- While logged in, a visible meter grows `+5% income per 10 minutes` up to `+50%`, and decays slowly when idle in menus **[DESIGN]**. Leaving resets it.
- Keeps players in-server without requiring constant input.
- **Anti-exploit:** the server computes it from connected time; no client input counts.

**Layer 3: Clocked reasons to be there.**
- Synchronized rare spawns on exact UTC marks (:00, :05, ...) (Room for Improvement 2.10).
- Biome "conditions" that change spawn odds for a window, announced on a timer (adapted from Grow a Garden's weather).
- Growth jobs (Titans, Report 06) that finish on timers.

**Things to avoid.**
- Anything that pays per ad view in a loop (Report 02 A2).
- Idle income so large that active play feels pointless. Keep active catching worth roughly 40-60% of income for an engaged player **[DESIGN]**, and measure it.

> **Verify the platform idle timeout.** If Roblox disconnects idle players after a period, AFK farming needs a design that works with it (for example, small periodic movement is not a fix; the offline stash is). I did not verify the current behaviour.

---

## 7. Inconsistencies Found in the Source Documents

These are bugs in the *design docs*. Fix them before anyone builds from them.

| # | Where | Problem |
|---|---|---|
| 1 | One-shot s3.3 vs Appendix D | Giant weight is **5** in the formula text and **4** in the table; the table then sums to 99, not 100 |
| 2 | One-shot Appendix A | Text says biome weights sum to 100. Only Meadow does (Crystal Cave 99.1, Deep Ocean 95.1, Volcano 84.1, Sky 77.1, Arctic 74.1, Ruins 72.1, Shadow 57.1). Relative weights still work, but the claim is wrong |
| 3 | One-shot Appendix A, Shadow Realm | Voidspectre is a **Mythic with spawn weight 15**: Mythics are ~30% of spawns there |
| 4 | One-shot s9.0 vs Appendix C | Rarity colours differ (Rare is blue in one, purple in the other; Epic is purple vs orange) |
| 5 | One-shot Appendix C | `RarityData.coinMult` (1/5/25/100/500/2500) overlaps `creature.coinRate`; unclear which applies. Risk of double counting |
| 6 | Mutations vs weight system | Giant mutation sets model scale to **3.0x**; the weight system caps at **1.8x**. Combined 5.4x may break hitboxes and pens |
| 7 | Minigame spec s5 vs formula | The minigame table assumes Mythic base chance 5%; the live formula gives 2-47% depending on net |
| 8 | Minigame spec s11 vs Room for Improvement 13 | Minigame says do not change spawn rates; the improvement list asks for harder rare odds |
| 9 | One-shot s9.2 vs sound/UI rules | Spec uses emoji in UI strings; you ruled out emoji. Strip them in all templates |
| 10 | One-shot s3.5 vs s6.1 | Raid cooldown 7200 s (2 h) per raider is incompatible with a physical-steal loop where raids should be frequent. Revisit (Report 05) |

---

## 8. How to Rerun the Model With Real Numbers

```bash
cd research/sim
python3 economy_sim.py --seeds 12 --days 120       # baseline + proposals
python3 run_one.py G 16 150                         # the recommended variant alone
```

1. Replace the `BIOMES` table, `BASE` costs and `net_*` arrays in `economy_sim.py` with values from the live `CreatureData.luau`, `BiomeData.luau`, `NetData.luau` and `Config.luau`.
2. Add a variant in `proposals.py` and run it.
3. Compare the day tables with your target pacing.

**Next model upgrades (worth doing).** Add rebirth, Luck Booster and raid losses; model player skill via the minigame multiplier; replace the greedy buyer with a few strategy profiles; calibrate "attempts per minute" from real telemetry.

---

## 9. Telemetry Required Before and After Any Change

| Metric | Why |
|---|---|
| Time to first catch, first upgrade, first biome unlock | Validates the fast start |
| Days to each biome unlock (median, p25, p75) | Compares to the simulator |
| Rarity pull rates per biome | Confirms live odds match design |
| Income per minute distribution by day | Detects runaway growth |
| Share of income from offline vs active vs presence bonus | Tests the AFK design |
| D1 / D7 / D30 retention, session length | The outcome that matters |
| Claim rate on offline stash; ad-doubling uptake | AFK health |

Use Roblox's own [Analytics](https://create.roblox.com/docs/en-us/production/analytics) (including benchmark scorecards once you pass 100 DAU) and custom events for the rest.
