# Catch a Titan: Research Pack (Index)

Prepared 2026-10-09 as a companion to `Room_for_Improvement.md`. Eight reports, one simulator.

## Read This First: Four Things That Matter Before Anything Else

1. **Check your content rating status today.** Reports say Roblox disabled experiences on Oct. 2 that had not completed mandatory content ratings (deadline Sept. 30), and that unrated or low-engagement games can default to 16+. If your game is affected, nothing else in this pack matters until it is fixed. (Report 02, A1. I could not read Roblox's pages directly, so confirm on Creator Hub.)
2. **Do not use the "14.3M CCU" figure for Steal An Egg.** It is in your one-shot prompt. The sources I found say a peak above 500K, and one reports the game was removed by Roblox. I found no source for 14.3M. (Report 01 s3.)
3. **Your Luck Booster, as specified, is a problem twice.** It makes every catch at least 67% likely (Report 03 s4.3), and it is a paid probability modifier that Roblox's policy summary says needs a disclosed odds table (Report 02 A3). Report 04 replaces it.
4. **The economy, as specified, is finished in days.** A casual player unlocks every biome by about day 3.5 and meets a Mythic by about day 9. Raising prices alone does not fix it. (Report 03.)

## The Reports

| # | Report | What you get |
|---|---|---|
| 01 | [Competitor teardown](01_competitor_teardown.md) | Steal a Brainrot, Steal An Egg, Grow a Garden, Catch a Brainrot, Pet Simulator 99, Fisch: mechanics, what to copy and avoid, evidence-graded |
| 02 | [Platform policy and compliance](02_platform_policy_and_compliance.md) | Content ratings, the "continuous feed" rule, paid-random-item odds disclosure, rewarded ads, payouts, checklist |
| 03 | [Economy, balance and AFK](03_economy_and_progression.md) | Simulator results, why the spec breaks, a recommended re-balance, AFK design, 10 inconsistencies in the source docs |
| 04 | [Rarity odds and monetization](04_rarity_odds_and_monetization.md) | Exact spawn tables, a replacement odds model, Luck Booster redesign, odds-disclosure design, price ladder |
| 05 | [Physical stealing spec](05_physical_stealing_spec.md) | State machine, numbers, fairness rules, edge cases, atomic ownership ledger, tests |
| 06 | [Leash-home and Titan growth specs](06_leash_home_and_titan_growth_spec.md) | Two implementation specs, protections against churn, growth timeline maths |
| 07 | [Creature style guide](07_creature_style_guide.md) | Shape language, rarity escalation budgets, silhouette test, animation and technical standards |
| 08 | [UI performance and polish playbook](08_ui_performance_and_polish_playbook.md) | Profiling protocol, lag hypotheses, HUD layout, "next purchase" chip, icon standards |

Code: `sim/economy_sim.py`, `sim/proposals.py`, `sim/run_one.py`, `sim/growth_sim.py` (see `sim/README.md`).

## Suggested Reading Order

Report 02 (risks), Report 03 (the economy), Report 04 (odds and money), then 05 and 06 (the viral loop), then 07 and 08 (presentation). Report 01 is the evidence behind the design choices.

## How Much to Trust Each Part

| Kind of claim | Reliability |
|---|---|
| Simulator outputs | Reproducible, but they model the **spec**, not your live game. Rerun with real `Config` values. Directional, not predictions |
| Calculations (spawn shares, catch chances, growth timelines) | Exact for the stated inputs. Net bonuses beyond Crystal (+0.16) are my **assumed** values |
| Competitor mechanics | From guides and news, often conflicting and months old. Tagged REPORTED or CONFLICT |
| Roblox policy | From search-result summaries of the official pages. Roblox's own pages were blocked from direct reading. **Verify before shipping** |
| All **[DESIGN]** numbers | Starting values to tune from your own data |

## What I Did Not Do

- I did not see your live game, code, art or analytics. Everything is built from your documents.
- I did not verify Roblox policy on the primary pages.
- I did not find official numeric retention targets for simulators; use your Analytics benchmark scorecards (100+ DAU needed).
- I did not build game code; these are specs and a model.

## Decisions Only You Can Make

Collected from the reports:
1. Target time to finish for a casual player (drives all pacing).
2. Replace the 2-hour raid cooldown with short cooldowns plus protections? (Report 05)
3. Mythics stealable on a leash, or protected? (Report 06)
4. Are Titans stealable at launch? How many Titan models? (Report 06)
5. Leash risk setting (Off/Normal): what should Off cost? (Report 06)
6. Is the event creature's species predictable by UTC mark (good for trackers, good for bots)? (Report 04)
7. Which of the six Luck Booster values to ship, and do boosters stack? (Report 04)
8. Art pipeline and budget for Legendary/Mythic redesigns. (Report 07)
