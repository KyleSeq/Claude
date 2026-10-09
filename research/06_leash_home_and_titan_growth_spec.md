# Report 06: Leash-Home and Titan Growth (Implementation Specs)

Two systems in one report because they share machinery and one risk: **loss and growth both attach emotional value to individual creatures**, so correctness of ownership matters more than polish.

Numbers marked **[DESIGN]** are starting tunings for `Config`. This builds on Report 05 (the ledger, carry rules, net action). Do not start either system before the `CreatureLedger` from Report 05 exists.

---

# Part A: Leash-Home ("a catch is not safe until it is home")

## A0. Why, and the honest risk

Evidence: the closest comparable loop is "earn it in a dangerous place, carry it home, then it pays" (Steal An Egg, Report 01). The risk is that losing a creature you just earned feels worse than losing one you owned. This is the single most churn-sensitive feature in the roadmap, so every rule below is biased toward **recoverability and fairness**.

## A1. Goal and Non-Goals

**Goal.** After a successful catch (Seal passed), the creature is **leashed** and follows the catcher. It is not in the inventory until it reaches the catcher's Sanctuary safe zone. Other players can net it off the leash.

**Non-goals.** No loss without a chance to react; no loss from lag; no theft inside safe zones; no leash for tutorial catches; no leash longer than a few minutes.

## A2. State Machine

```
Wild ──Seal success──▶ Leashed(catcher) ──Bank(safe zone)──▶ Banked (inventory)
                           │
                           ├─NetOff(valid, by other player)──▶ Leashed(thief)   [the creature now follows the netter]
                           ├─NetBack(valid, by original catcher)──▶ Leashed(catcher)
                           ├─Timeout(LEASH_MAX_SECONDS)──▶ Banked(catcher)   [auto-bank, see A5]
                           ├─Disconnect(leash holder)──▶ Banked(original catcher)
                           ├─Death/Reset(holder)──▶ Dropped ──▶ pickup window ──▶ Banked(original catcher)
                           └─Server close──▶ Banked(original catcher)
```

Key difference from Report 05: **a timeout or any failure banks the creature to the original catcher, not back into the wild.** The leash is a window of risk, never a way to destroy a catch.

## A3. Numbers (`Config.LEASH`) **[DESIGN]**

```lua
LEASH = {
	ENABLED_FROM_REBIRTH = 0,
	LEASH_MAX_SECONDS = 180,          -- then auto-bank to original catcher
	NET_OFF_RANGE = 10, NET_OFF_COOLDOWN = 5.0,
	GRACE_SECONDS = 6,                -- nobody can net it for 6 s after the catch (reaction time)
	SAFE_RADIUS_FROM_SPAWN = 0,       -- 0 = off; set > 0 to make spawn areas safe
	MAX_NETOFFS_PER_CREATURE = 2,     -- after 2 steals it banks to its current holder
	RARITY_PROTECTED = { Mythic = true },   -- see A4
	PROTECT_MIN_MINUTES = 30,         -- newbies cannot be netted off
	FOLLOW_SPEED_MULT = { Common=1.0, Uncommon=0.98, Rare=0.95, Epic=0.9, Legendary=0.85, Mythic=0.8 },
}
```

## A4. Protection Rules (the part a strict reviewer will check hardest)

1. **Grace period.** For `GRACE_SECONDS` after the catch, only the catcher can interact. This prevents a camper from stealing the instant a net lands.
2. **Cap on chain steals.** After `MAX_NETOFFS_PER_CREATURE` steals, the creature auto-banks to its current holder. This stops endless ping-pong and tilts toward closure.
3. **Newbie protection.** A player in their first `PROTECT_MIN_MINUTES` cannot have leashed creatures netted off.
4. **Same-tier rule.** Only players within one rebirth tier may net a leashed creature (consistent with Report 05).
5. **Mythic decision (open).** Two options; pick one with playtest data:
   - *A:* Mythics are **not leashable-stealable** (they auto-bank to the catcher; the thrill is the catch itself and the announcement).
   - *B:* Mythics are fully stealable but follow slowly (0.8x), making the scramble the clip.
   I recommend **A at launch** and testing **B** later, because losing a once-per-17-server-hours Mythic to a stranger is the worst possible churn event.
6. **Visibility.** The leashed creature has a visible leash, a name tag showing the holder, and a HUD chip for the holder (`Leashed: Cave Phoenix - bank in 0:52`). Everyone should always know what is happening.
7. **Opt-in intensity.** Add a server option or a setting: "Leash risk: Off / Normal". Off means the catch banks immediately and the player earns a lower reward bonus **[DESIGN]**. Decide this with the owner.

## A5. Mechanics Details

- **Following.** The creature's logical position is server-authoritative but updated at 5 Hz as `holderPos + offset`, clamped to a max trailing distance of 6 studs. Clients interpolate visually. No physics ownership transfer for the creature (avoid network-ownership exploits).
- **Teleport/speed exploits.** If the holder moves beyond `maxSpeed * dt * 1.5`, the leash snaps and the creature banks to the original catcher.
- **Net-off.** `RequestNetOff(creatureId)` validated for range, line of sight, cooldown, tier rule, grace expiry, protection flags, and `netoffCount < MAX_NETOFFS_PER_CREATURE`. Success transfers the *leash* (not ownership) to the netter via `Ledger.transfer`.
- **Banking.** Entering the holder's own `SAFE_ZONE` banks the creature to **that holder**. If the holder is a thief who netted it off, they keep it. This is the stakes.
- **Ownership history.** Store `originalCatcher` and `holder` on the leash record; log both for support and analytics.
- **Interaction with the catch minigame.** Leash starts after the Seal succeeds, so the reveal still plays; the creature then follows. For fast players, show the reveal on the HUD while walking (do not freeze the world).
- **Tutorial catch.** Never leashed.

## A6. Remotes

| Remote | Direction | Args | Limit |
|---|---|---|---|
| `RequestNetOff` | C->S | `creatureId` | 4/s |
| `LeashState` | S->C | `{ creatureId, holderId, originalCatcherId, expiresAt, protectedUntil, netoffsLeft }` | none |
| `LeashAlert` | S->C | to the holder and original catcher on any change | none |

## A7. Acceptance Tests

1. **Conservation.** 1,000 scripted leash scenarios (net-off, net-back, timeouts, disconnects of either player, resets). The creature always ends in exactly one inventory.
2. **No destruction path.** No transition leaves a creature in the wild or deleted.
3. **Grace and caps.** Net-off during grace fails; the third net-off is rejected and the creature banks to the current holder.
4. **Protection.** Newbie holders and protected rarities cannot be netted off.
5. **Exploit resistance.** A teleporting holder snaps the leash and banks to the original catcher.
6. **Telemetry gate before wide release.** Collect leash loss rate and next-day return for players who lost a creature; if it exceeds a threshold agreed with the owner, tighten protections (shorter leash, more grace, safe radius around spawns) before expanding.

## A8. Telemetry

Per leash: rarity, kg, duration, outcome (banked by original / banked by thief / timeout / disconnect), number of net-offs, distance to safe zone, holder's rebirth tier. Primary guardrail: **D1 return rate of players who lost a leashed creature** versus those who did not.

---

# Part B: Titan Growth

## B0. Why

The title is *Catch a Titan* and there is currently no Titan mechanic. Growth gives players a reason to check back (timers), builds on the existing kg system, creates a prestige goal (heaviest creature leaderboards), and is the natural home for deterministic Robux accelerators that do not need odds tables.

## B1. Goal and Non-Goals

**Goal.** Players feed placed creatures to gain kg over time. Models visibly scale with weight. A creature that reaches the top of its rarity's weight range can ascend into a **Titan form** with a unique model, announcement and income bonus.

**Non-goals.** No random growth outcomes at launch (keeps it out of the paid-random-items policy); no Robux-only Titans; no unlimited growth.

## B2. Using the Existing Weight System

From the advanced research doc:

| Rarity | Min kg | Max kg |
|---|---|---|
| Common | 0.1 | 2.0 |
| Uncommon | 0.5 | 5.0 |
| Rare | 1.0 | 15.0 |
| Epic | 5.0 | 50.0 |
| Legendary | 20.0 | 200.0 |
| Mythic | 100.0 | 1000.0 |

Existing formulas (keep): coin multiplier `1 + norm * 0.5`, model scale `1.0 + norm * 0.8` (max 1.8x), `norm = (kg - min) / (max - min)`.

Growth moves a creature's `norm` upward. Because weight is rolled at catch (skewed low with power 2.5), most creatures start with a small `norm`, leaving room to grow.

## B3. Feeding and Growth Jobs

- **Feed.** From the Sanctuary detail panel: `Feed` consumes `foodCost` coins and starts a **growth job** that completes after `growthMinutes`, adding `gain = GROWTH_STEP * (max - min)` kg.
- **Concurrency.** Up to `MAX_ACTIVE_JOBS` (start 3) jobs run in parallel across all creatures; jobs on the same creature never overlap (they chain through the queue below). More slots are a gamepass/upgrade candidate (deterministic, no odds disclosure needed).
- **Queue.** Up to `MAX_QUEUE` (start 4) feeds can be queued per creature, with food paid up front. See the timeline note in B3.1 for why this is required.
- **Claim.** Jobs finish into a "Ready" state; the player taps `Collect` (a natural stopping point, as in Report 02 A2). Uncollected jobs wait up to 24 h and then complete automatically.
- **Diminishing returns.** `gain` shrinks as `norm` rises so the last stretch to Titan takes longer than the first.

### B3.1 Formulas **[DESIGN]**

```
gainFraction(norm) = GROWTH_STEP * (1 - 0.6 * norm)       -- GROWTH_STEP = 0.06
gainKg             = gainFraction(norm) * (maxKg - minKg)
growthMinutes      = 20 * rarityRank * (1 + norm)          -- rank 1..6
foodCost           = BASE_FOOD[rarity] * (1 + 2 * norm)
```

| Rarity | Rank | Minutes to first feed (norm 0) | Minutes at norm 0.8 |
|---|---|---|---|
| Common | 1 | 20 | 36 |
| Rare | 3 | 60 | 108 |
| Epic | 4 | 80 | 144 |
| Legendary | 5 | 100 | 180 |
| Mythic | 6 | 120 | 216 |

Approximate feeds to reach `norm = 1` from 0: about 25 with these constants (computed with `research/sim/growth_sim.py`). Serial job time from norm 0 to Titan:

| Rarity | Feeds | Job-hours |
|---|---|---|
| Common | 25 | 13.0 |
| Uncommon | 25 | 25.9 |
| Rare | 25 | 38.9 |
| Epic | 25 | 51.8 |
| Legendary | 25 | 64.8 |
| Mythic | 25 | 77.8 |

**Design flaw this exposes, and the fix.** If each feed must be manually collected and re-fed, a player who checks in twice a day can complete at most about two feeds a day per creature, so even a Common would take about 12 days regardless of the timers above. Timers would not be the limit; check-ins would, which punishes casual players and wastes the short timers.

**Fix: a feed queue.** Let a player queue up to `MAX_QUEUE` (start 4) sequential feeds on one creature, paying the food cost up front. The chain runs while they are away, so elapsed time approaches the job-hours in the table. Keep one "Collect" moment per check-in (a natural stopping point) that banks all finished growth and offers to refill the queue.

**Tune so a regular player reaches a first Titan in roughly 1 to 2 weeks** and a casual player in 3 to 4 **[DESIGN]**. With the queue, a Rare (39 job-hours) finishes in about 2 days of elapsed time for a player who refills it daily, which is too fast for a launch Titan: raise `growthMinutes` (for example x4) or `MIN_FEEDS` until the target is met, then re-simulate.

### B3.2 Food cost

Set `BASE_FOOD` so the total feeding cost to Titan is a meaningful but not dominant fraction of the creature's lifetime income, for example **about 1-3 days of that creature's own income** at its base rate **[DESIGN]**, so growth is a good investment but not free money.

## B4. Titan Form

- **Threshold.** `norm >= 1.0` and the creature has completed at least `MIN_FEEDS` (start 15) jobs.
- **Ascension.** A short cutscene (rarity-scaled), a new model variant (larger, redesigned silhouette per Report 07), a server announcement for Legendary and Mythic Titans, and a permanent flag `isTitan = true`.
- **Bonus.** Coin multiplier `x3` on top of the weight multiplier **[DESIGN]**, and eligibility for the "Heaviest Catch" leaderboard category "Titans".
- **Visual size.** Titans scale to `2.5x` the species base model, capped so pens and carry visuals still work.
- **Art scope.** One Titan model per species is a large art cost. Launch with Titans for **a defined subset** (for example one per biome, Rare and above) and add over time. Others can show an enlarged tinted model in the interim, clearly labelled "Giant".

## B5. Interactions With Other Systems (the places this breaks)

| System | Interaction | Rule |
|---|---|---|
| Stealing (Report 05) | A heavy Titan is slow to carry and valuable | Carry speed floor 0.40; consider making Titans non-grabbable in the first release. Open decision |
| Leash (Part A) | Titans should not be leash-stealable | A Titan is a banked asset |
| Economy (Report 03) | Growth multiplies income | Cap total multiplier per creature; run the simulator with growth before shipping |
| Fusing | Fuse inputs could be Titans | Titans cannot be fused or released |
| Trading | Titans are high value | Allow only after trade-eligibility rules are settled (Report 02 section 3) |
| Mutations | Giant mutation scale 3.0x | Resolve the 3.0x vs 1.8x vs 2.5x scale conflict (Report 03 s7 #6) |

## B6. Robux Accelerators (deterministic, no odds)

| Item | Effect | Notes |
|---|---|---|
| Growth Boost | Completes one active job immediately | Floor price band |
| Extra Job Slot | +1 concurrent job, permanent | Pass or product |
| Auto-collect | Jobs collect themselves when done | Convenience pass |
| Feed Bundle | Fixed amount of food | Deterministic |

Keep everything fixed-outcome so the policy's odds-table requirement does not apply (Report 02 A3). If you later add a random "growth surge", it becomes covered and needs a disclosed table.

## B7. Data Model Additions

```lua
creature = {
  ...,
  weightKg = 4.7,
  isTitan = false,
  feeds = 0,
  growth = { startedAt = 0, completesAt = 0, gainKg = 0 } or nil,
}
-- Player: growthJobs = { [creatureId] = { ... } }, maxJobs = 3
```

- Store absolute timestamps (`os.time()` based, server clock) so jobs complete correctly offline.
- On join, reconcile: complete or advance jobs whose `completesAt` has passed.
- Cap `weightKg` at the rarity max on the server.

## B8. Remotes

| Remote | Direction | Args | Limit |
|---|---|---|---|
| `RequestFeed` | C->S | `creatureId` | 4/s |
| `RequestCollectGrowth` | C->S | `creatureId` | 4/s |
| `RequestAscend` | C->S | `creatureId` | 1/s |
| `GrowthState` | S->C | job list and creature updates | none |

All validated on the server (ownership, funds, concurrency, thresholds). Never accept a weight value from the client.

## B9. Quick Simulation (run it before tuning)

Run `python3 research/sim/growth_sim.py` (included). Calibrate `GROWTH_STEP`, `k` and the minutes constant so the target timelines in B3.1 hold, then extend the economy simulator (Report 03 s8) with growth bonuses before shipping.

## B10. Acceptance Tests

1. **Server authority.** Weight only changes via completed jobs; the client cannot set or read-modify weight.
2. **Offline correctness.** Start a job, kill the server, rejoin after the completion time; the job is complete and collectable exactly once.
3. **Cap.** No creature exceeds its rarity max weight; no Titan flag without the threshold and minimum feeds.
4. **Economy bound.** Simulated income with maximum growth stays within the target pacing bands.
5. **Visuals.** Model scale matches `norm`; Titan model loads; performance budget holds with 10 Titans visible.
6. **Conservation.** Feed/collect/ascend never duplicate or lose a creature; interact correctly with the ledger.
7. **No regressions.**

## B11. Telemetry

Feeds per player per day, job collection latency (a direct measure of "reason to return"), time to first Titan, Titan count by rarity, income share from growth, Robux accelerator uptake.

---

## Build Order (both parts)

1. Report 05 steps 1-2 (ledger).
2. Leash state machine without net-off (just the follow-and-bank), then net-off with protections.
3. Titan growth jobs and collect UI (no Titans yet).
4. Ascension and Titan models for the launch subset.
5. Interactions (stealing/leash exclusions for Titans) and telemetry.
6. Playtest both with real players; gate wide release on churn and loss metrics.

## Open Decisions for the Owner

1. Mythic leash rule A (protected) or B (stealable)?
2. Offer a leash risk setting (Off/Normal)? What does Off cost?
3. Are Titans stealable at all in the first release?
4. How many Titan models at launch?
5. Target time to first Titan for a casual player?
