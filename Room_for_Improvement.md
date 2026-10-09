# Catch a Titan: Room for Improvement (Professional Review)

> **Reviewer stance.** This is written the way a senior Roblox developer or live-ops lead would assess a game before it goes in front of a large audience: strict, specific and measurable. Each item states what is wrong, why it costs us players or revenue, what the best games in the genre do, what we must change, and how we will know it worked.
>
> **Conventions.**
> - **Severity:** P0 = blocks launch or growth, P1 = major gap against genre standard, P2 = polish that compounds.
> - **Effort:** S (days), M (1–2 weeks), L (3+ weeks or cross-system).
> - Numbers tagged **[DESIGN]** are starting values to tune from analytics, not facts. Keep them in `Config`, never inline.
> - **UI rule:** no emoji anywhere in shipped UI strings. Use drawn icons and outlined FredokaOne text.

---

## 0. Executive Summary

The game has a working core: catch, place in Sanctuary, earn, raid, trade. It reads as a **prototype with a loop**, not yet a **product with a hook**. The strict assessment, in order of importance:

1. **The viral moment does not exist yet.** Games in this genre grew on clips: sprinting home with a stolen creature on your head, a Mythic breaking out on the last shake. Our stealing and catching are menu interactions. Nothing here makes a 15-second clip.
2. **The economy is too generous and too passive in the wrong places.** It is easy to complete, yet it does not reward staying logged in. Both are retention failures. Easy completion means players run out of goals. Weak AFK rewards mean concurrent users (CCU) fall off when players leave the tab.
3. **The presentation undersells the product.** The UI is laggy, oversized and cluttered. The catch has no cutscene. The creatures are not well designed. The Legendary and Mythic notices are flat. A new player forms a quality judgement in the first 30–60 seconds, and today that judgement will be "unfinished".
4. **Monetization is thin and under-instrumented.** Seven products against a genre norm in the dozens leaves a large impulse-purchase gap, but any expansion must be legally compliant (odds disclosure) and must not feel predatory.
5. **Several requests conflict** (slower progress vs. no slow start; harder rare odds vs. the minigame's skill bonuses; "cash-grab" feel vs. honest odds). Section 3 resolves these explicitly, because unresolved they will cause rework.

**Recommended sequencing:** fix first-impression and balance (Phase 1), then ship the catch minigame and animation (Phase 2), then the structural change that creates the viral loop: physical stealing and leash-home (Phase 3), then long-tail systems and monetization (Phase 4). Details in section 4.

---

## 1. Priority Matrix

| # | Item | Severity | Effort | Phase |
|---|------|----------|--------|-------|
| 1 | UI performance, scale, icon quality, layout | P0 | M | 1 |
| 5 | Balance, pacing and AFK economy | P0 | M | 1 |
| 13 | Rarity odds (spawn and catch) | P0 | S | 1 |
| 3 | Creature design quality | P0 | L | 1–2 |
| 2 | Catch animation and capture cutscene | P1 | M | 2 |
| 8 | Catch minigame (Throw, Struggle, Seal) | P1 | M | 2 |
| 4 | Legendary and Mythic notifiers | P1 | S | 2 |
| 10 | UTC-synced rare spawns | P1 | S | 2 |
| 6 | Physical stealing, defence and base lock | P0 | L | 3 |
| 7 | Leash-home (a catch is not safe until it is home) | P1 | M | 3 |
| 9 | Titan growth system | P1 | M | 4 |
| 11 | Fuse machine | P2 | S | 4 |
| 12 | Robux catalogue expansion | P1 | S–M | 4 |

---

## 2. Detailed Findings

### 2.1 UI: performance, scale, resolution and positioning (P0, M)

**Original note.** The UI looks a bit laggy. Icons should be smoother and higher resolution. It is too big for the screen. Icons may be excessive. Fix positioning and give it a more "cash-grab hungry" game feel.

**Verdict.** Fails the first-impression test. Laggy UI is the first thing a player feels, before any gameplay, and on mobile (the majority of the Roblox audience) it is disqualifying.

**Problems, stated precisely.**
- **Lag.** Likely causes to confirm with the MicroProfiler and the Developer Console before changing anything: too many `GuiObject`s alive at once, per-frame tweens or loops on many elements, `UIGradient` or `UIStroke` on large numbers of instances, `ImageLabel`s with oversized source textures, and layouts (`UIListLayout`, `UIGridLayout`) recalculating every frame because of text or size changes. Measure first. Do not guess.
- **Scale.** The UI overflows or crowds the screen. The reference test device is a landscape phone at roughly 812 x 375 with safe-area insets. If a button is unreachable by a thumb or overlaps the top-right system menu area, that is a bug, not a style choice.
- **Icon quality.** Blurry icons come from low-resolution sources scaled up, or from non-power-of-two and badly packed assets. Icons must be authored at the display size times 2 to 3 for high-DPI screens, with consistent stroke weight and corner style across the whole set.
- **Icon excess.** Too many icons dilute hierarchy. If everything has an icon, nothing is prioritised. Each screen should have one primary action that is visually dominant.
- **Positioning.** Currency, the primary action, and navigation should sit in conventional, learnable positions. The top-right is reserved by the Roblox system menu.

**What the best games do.** A minimal always-on HUD (currency and one progress element), a bottom or side nav with 4–6 clearly labelled entries, large thumb-reachable primary actions, and everything else behind a panel that opens and closes with a short, springy animation. Hot-path numbers (coins ticking up) animate cheaply and never trigger a re-layout.

**Required changes.**
1. Profile on a real mid-range phone and on a throttled Studio device emulator. Record frame time and instance count before and after. Set a budget (for example, a stable 60 fps on the reference device with the HUD and one panel open) **[DESIGN]**.
2. Collapse the HUD to the minimum: coins and coin rate, the active net, and a rare-spawn timer. Move the rest into panels.
3. Rebuild icons as a single consistent set at 2–3x resolution. Replace decorative icons with text where the text is clearer. Remove any icon that does not change a decision.
4. Lay out for safe-area insets and the landscape-phone viewport. Keep touch targets at 44 px minimum and 64 px or more for primary actions. Nothing interactive in the top-right.
5. Make hot-path updates cheap: set a label's `Text` only when the displayed value changes, avoid per-frame tweens on lists, and pool or reuse card instances in scrolling lists instead of destroying and recreating them.
6. **"Cash-grab hungry" feel, done tastefully.** This means the player should always see the next purchase and be one tap from it: a persistent "next upgrade" chip showing cost and progress, coin counters that pop on income, shop entries that glow when affordable, and limited-time offer badges. It does **not** mean fake urgency, hidden odds or misleading countdowns (see 2.12).

**Acceptance criteria.**
- Stable target frame rate on the reference phone with HUD and one panel open.
- No overlap with the system menu; all primary actions reachable by one thumb on the reference viewport.
- Icon audit: every icon is crisp at 2x, belongs to one visual family, and has a reason to exist.
- A "next purchase" chip is visible within the first minute of play.

**Risks.** Over-trimming the HUD can hide information that power users want. Mitigate with a settings option or a collapsible detail row.

---

### 2.2 Catch animation and capture cutscene (P1, M)

**Original note.** There needs to be a catch animation or cutscene. Research a catching net animation and a capture effect like a Poké Ball capturing a Pokémon. Do in-depth research.

**Verdict.** The catch is the core dopamine moment and currently has no staging. A result toast with no animation reads as a receipt, not a reward.

**What the best capture sequences share (the staging beats).**
1. **Anticipation.** A short wind-up before the throw (net pulled back, camera eases in slightly).
2. **Throw and arc.** A readable flight with a floaty, cartoon arc, not a straight line.
3. **Impact and hit stop.** A brief freeze (about 50–100 ms) on the actors involved, plus a squash on the net. Freeze the net and creature, not the whole world.
4. **Containment.** The creature is wrapped or drawn into the net with a clear transformation, usually shrinking or compressing.
5. **Suspense.** The net settles and wobbles. Each wobble should be a real check (see 2.8), so the suspense is honest.
6. **Resolution.** Success: flash, chime, reveal. Failure: the net bursts and the creature escapes, clearly distinct from success.
7. **Reveal.** Show name, rarity, weight and mutation with rarity-scaled drama (see 2.4).

**Required changes.**
1. Build the net as a model that grows from a small ball to wrap the creature's bounding box by impact.
2. Add hit stop, net squash, a small camera kick, and a particle burst keyed to rarity colour.
3. Add the wobble sequence with a rising-pitch click per passed check. Keep the total time short: roughly 4 seconds for a Common and under 10 for a Mythic. Players have limited credit-earning time per day, and long unskippable animations punish the most engaged players.
4. Provide a **skip or fast-forward** for repeat catches and for Commons. Veterans will catch thousands of creatures.
5. Respect a low-effects setting (no camera shake, fewer particles) for performance and accessibility.
6. All sound goes through the existing sound groups. Spatial sounds on the net and creature, non-spatial for UI and result stingers.

**Acceptance criteria.**
- Every catch plays the same staged sequence, scaled by rarity.
- Total time targets met; Commons skippable.
- Success and failure are distinguishable with sound off (visual only) and with visuals ignored (audio only).
- No frame-time spike when the burst fires on a mid-range phone.

**Risks.** Animation length versus grinding fatigue. Handle with skip and rarity-scaled duration.

---

### 2.3 Creature design quality (P0, L)

**Original note.** The creatures need to be well designed.

**Verdict.** In a collection game, the creatures **are** the product. Weak models cap everything else: screenshots, clips, trading appeal, and the emotional value of a rare find.

**Problems, stated precisely.**
- A rare creature must look rarer than a common one at a glance. If silhouettes and palettes are interchangeable, rarity is only a label.
- Models built from primitives or low-detail assets look unfinished next to competitors.
- No consistent art direction across biomes undermines the sense of a world.

**What the best games do.** A defined style guide (shape language, proportion rules, outline weight, saturation range), a silhouette test (each species readable as a solid black shape), rarity expressed through form and effects (more complex silhouette, glow, particle aura, animation flourishes), and a consistent rig and animation set per body family.

**Required changes.**
1. Write a one-page **creature style guide**: proportions, outline and shading rules, palette per biome, and how rarity escalates (silhouette complexity, emissive details, aura, idle flourishes).
2. Run a **silhouette and thumbnail test** on every species: it must be identifiable at icon size and as a black silhouette.
3. Redesign in rarity order of impact: Legendary and Mythic first (they are the clips), then Epic, then fill in the lower tiers. Never ship a Mythic that looks like a recoloured Common.
4. Give each body family a consistent animation set (idle, walk, flee, struggle, caught) so motion quality is uniform.
5. Mutations (Shiny, Giant, Shadow, Corrupted, Rainbow) need distinct, readable visual treatments, not just tints.
6. Verify the mesh and part budget per creature so many creatures on screen do not hurt performance.

**Acceptance criteria.**
- Style guide exists and every new model is reviewed against it.
- Silhouette test passed by every species; rarity readable without the label.
- Side-by-side comparison against two comparable games' creatures shows no obvious quality deficit at typical viewing distance.

**Risks.** Large effort and an art bottleneck. Mitigate by prioritising the top rarities and the starter biome, where first impressions form.

---

### 2.4 Legendary and Mythic notifiers (P1, S)

**Original note.** The Legendary and Mythic notifiers need to be more dramatic and sleek.

**Verdict.** These are the game's marketing moments. They should make every other player in the server look up. Today they do not.

**Principles.** Drama and sleekness pull in opposite directions. The way to get both is **restraint plus precision**: fewer elements, better timing, strong contrast, and one memorable flourish per tier, rather than more particles.

**Required changes.**
1. **Tier the drama.**
   - Legendary: a clean banner with a gold gradient, a short stinger, a brief edge glow.
   - Mythic: a full-width banner with an animated gradient border, a distinct sound, a brief screen-edge pulse, and an optional short camera settle for the catcher only.
2. **Typography and layout.** Large outlined FredokaOne, strong hierarchy (player, creature, rarity), generous spacing, and no emoji. Show the creature's icon or a viewport render.
3. **Timing.** Slide in with an overshoot, hold about 5–6 seconds, slide out. Stack and queue multiple banners without overlapping.
4. **Audience-aware.** The catcher gets the full reveal. Other players get a lighter banner so a busy server does not become unusable. Provide a setting to reduce effects.
5. **Shareability.** Include the server and the biome so players can chase it. Pair with synchronized spawns (2.10) so the notification is actionable.
6. **Do not block gameplay.** Banners must never cover the catch bar or the primary action.

**Acceptance criteria.**
- A clear visual and audio step between Epic, Legendary and Mythic.
- A busy server cannot stack banners into an unreadable wall.
- Low-effects mode supported.

---

### 2.5 Balance, pacing and the AFK economy (P0, M)

**Original note.** Make sure the game is more balanced. It is too easy to complete, but do not give it a slow start. Add more of an AFK grinding aspect to encourage CCU playtime. Make progress slower.

**Verdict.** Currently the game is front-loaded and completable. That is the worst combination: the player burns through content, then has nothing to do, and nothing that rewards staying.

**The tension to resolve (and how).** "Slower progress", "no slow start" and "more AFK" look contradictory. They are not, if progress is shaped as a curve:
- **Minutes 0–10: fast.** Generous early rewards, guaranteed first catch, visible first upgrade within about 60 seconds. This protects retention in the first session, where early bounce is the biggest loss.
- **Hour 1 onward: steeper.** Costs scale faster than income, so each new tier takes meaningfully longer.
- **AFK as the engine for the slow part.** Waiting is acceptable when something is accruing and the player has a reason to return.

**Required changes.**
1. **Reshape the cost curve.** Keep early costs low, then make unlock and upgrade costs grow geometrically. Specify target time-to-milestone for each biome unlock and each net tier, then tune income and costs to hit those times. **[DESIGN]** Build a spreadsheet model first, simulate a casual and an active player, and only then change `Config`.
2. **AFK income with a reason to be present.**
   - Keep offline accrual but **cap it** (the cap is the lever that makes returning valuable).
   - Add a **claim** step for the offline stash (a satisfying "welcome back" moment) rather than silent deposits.
   - Add active-session multipliers (for example, a bonus that builds while online and engaged), so being present beats being absent without making absence worthless.
   - Add periodic timed rewards and online-time gifts that give a reason to stay in the server.
3. **Session design.** Short loops that fit a 10–20 minute session. Daily goals and streaks. Remember that credit for playtime is limited per day, so reward consistent returning more than single marathon sessions.
4. **Anti-trivialisation.** Late-game rebirth should reset enough to matter but keep a visible permanent bonus, so the second playthrough is faster but not instantly complete.
5. **Instrument everything.** Log time-to-first-catch, time-to-first-upgrade, session length, D1 and D7 retention, and funnel drop-off per biome. Balance from data, not intuition.

**Acceptance criteria.**
- First catch under 15 seconds. First upgrade purchase inside the first minute.
- A target full-completion time defined and met by simulation (for example, weeks of casual play rather than hours) **[DESIGN]**.
- Offline stash is capped, claimable and communicated clearly.
- Dashboards exist for the retention and progression metrics above.

**Risks.** Slowing progress can feel punishing if not paired with clear short-term goals. Always show the next goal and its ETA.

---

### 2.6 Physical stealing (P0, L), the biggest gap

**Original note.** Make stealing physical. A raid is currently a menu: pick a target, pick a card, roll the dice. In comparable games you run into someone's base, grab the creature, carry it on your head, and sprint home while they chase you. That is the clip their growth came from. Do the same, and make heavier creatures slow you down (the kg system already exists). The owner can net a creature back off a thief, and a base-lock button with a timer adds defence. Keep fairness rules: no raids on offline players, only within one rebirth of you. Effort: large.

**Verdict.** This is the single largest gap between our game and the genre's breakout titles. A menu raid is a probability roll with no story. A physical raid is a short, tense, shareable game with a protagonist, an antagonist, risk, and a payoff. It is also the strongest organic marketing engine we can build.

**Why it matters.** It creates three things that menus cannot: **skill expression** (route, timing, evasion), **emotional stakes** (both sides care), and **clips** (the core growth mechanism).

**Design (the loop).**
1. **Approach.** The raider enters a target's Sanctuary area. The owner is notified.
2. **Grab.** The raider interacts with a creature (a short hold, interruptible) and picks it up.
3. **Carry.** The creature is carried visibly (on the head or in the arms). Movement speed is reduced by a function of the creature's weight in kg. **[DESIGN]** Start with a modest penalty that scales with weight relative to the raider's tier, and clamp it so the heaviest creature is slow but never immobile.
4. **Chase.** The owner can pursue and net the thief. A successful net hit recovers the creature (returns it to its slot) and briefly stuns the thief.
5. **Escape.** Reaching the raider's own Sanctuary (or a safe zone) completes the theft and transfers ownership server-side.
6. **Defence.** A base-lock button with a duration and a cooldown. A locked base cannot be entered or grabbed from. Cooldown prevents permanent lock.

**Fairness rules (non-negotiable).**
- No raids on offline players.
- Only within one rebirth tier of the raider.
- Cooldowns on both raiding and locking.
- A recently raided player gets a short protection window so they cannot be farmed.
- Newbie protection before a minimum progression.

**Server authority and anti-exploit.**
- The server owns carry state, ownership transfer, speed modification and lock state. Clients only send intent.
- Validate range and line of access for the grab, and validate that the carry is still active at the safe zone.
- Handle edge cases explicitly: thief disconnects mid-carry (creature returns to owner), owner disconnects mid-chase (raid ends, creature returns), thief dies or resets, teleport and speed exploits (clamp and verify server-side), and duplicate transfer on lag.
- Make the data transfer atomic so a creature can never be duplicated or lost.

**Required deliverables.**
1. Grab and carry state machine with weight-based speed.
2. Owner net-back mechanic and a thief stun.
3. Base lock with timer, cooldown and visible feedback (a dome or gate effect).
4. Clear UI: a raid alert for the owner, a carry indicator for the thief, a distance-to-safe-zone cue.
5. Clip-friendly polish: a distinct alarm sound, a camera pulse on grab, and a visible carried creature that wobbles with movement.
6. Tuning table for speed penalty, grab time, lock duration and cooldowns.

**Acceptance criteria.**
- A full raid can be completed or defeated by two players without any menu step after the initial approach.
- Heavier creatures measurably slow the thief; the penalty is displayed.
- Zero duplication or loss across 1,000 scripted raid trials, including forced disconnects.
- Fairness rules enforced server-side and covered by tests.

**Risks.** Griefing and quitting. If raids feel unfair, players leave. Mitigate with protection windows, lock, matching limits, and a clear explanation before a player is exposed. Test with real players early and tune from their feedback.

---

### 2.7 Leash-home: "a catch is not safe until it is home" (P1, M)

**Original note.** A catch is not safe until it is home. Caught creatures follow you on a leash back to your Sanctuary, and other players can net them off you on the way. This is the "one structural change" recommended in the earlier notes. A comparable game did exactly this with eggs and it made the game. Effort: medium, once item 6 exists.

**Verdict.** This turns every catch into a short risk-reward story and gives the open world a PvP undertone. It reuses the machinery from item 6 (carry, net-back, ownership transfer), which is why it follows it.

**Design.**
- After a successful catch, the creature is **leashed** and follows the player. It is not yet in the inventory.
- Other players can net the leashed creature to take it. The catcher can net back.
- Reaching the Sanctuary (or a safe zone) **banks** the catch.
- Heavier or rarer creatures could follow slower or be more visible, raising the stakes proportionally.

**Critical caveats (a strict reviewer would flag these).**
- **Frustration risk is high.** Losing a Mythic you just earned, to a stranger, can feel terrible. The fairness rules from item 6 must apply here as well, and rarity tiers may need a protective rule (for example, a short ownership grace period or a safe-zone radius near spawns) **[DESIGN]**.
- **Opt-in intensity.** Consider a PvP toggle or separate server types so players who dislike PvP are not driven away.
- **Interaction with the catch minigame.** A skill catch followed by a chance of immediate loss compounds frustration. Playtest this pairing specifically.
- **Bank-on-disconnect rule.** Define exactly what happens if either player leaves mid-leash.

**Acceptance criteria.**
- A leashed creature can be stolen, recovered or banked, with no duplication or loss in any disconnect case.
- Telemetry shows leash-loss rate and its effect on session length and next-day return. If losses correlate with churn, adjust protection rules before shipping broadly.

---

### 2.8 Catch minigame (P1, M)

**Original note.** A real catch minigame instead of holding E. Weaken creatures, then throw. A timing throw (a shrinking ring) plus a short struggle where rarer creatures fight harder would make catches feel earned and create "missed the Mythic by a hair" moments. Effort: medium.

**Verdict.** Holding a key is not gameplay. A skill layer is what makes catching feel earned, and it creates the near-miss moments that people clip and retell.

**Status.** A detailed implementation spec already exists (`catch-minigame-prompt`). This section records the review-level requirements it must satisfy, so the two documents stay consistent.

**Requirements.**
- **Three beats:** Throw (a timing ring), Struggle (a one-button bar with a creature that fights harder at higher rarity), Seal (honest shake checks).
- **One-button input** that works with one thumb on mobile.
- **Server-authoritative.** The client sends intent and timestamps; the server decides. The server re-simulates the struggle from the input log using a seed only it chose.
- **Economy preserved.** Skill multiplies the base catch chance through an exponent and never replaces it. Net tier, Luck Booster, weight and rarity keep their effect.
- **Honest odds.** The displayed percentage and every shake reflect the real roll. No fake near-misses. A paid Luck Booster makes this a compliance requirement, not just good practice.
- **The first catch cannot fail** and teaches the controls in under 15 seconds.
- **Short.** About 4 seconds for a Common and about 9 for a Mythic.
- **Easy catches skip the struggle** so late-game players are not forced to play a minigame on trivial targets.
- **Accessibility.** An assist mode (slower ring, wider zone, lower skill ceiling) and non-colour cues for the zone.

**Strict reviewer notes.**
- **Conflict with item 13.** The minigame spec forbids changing spawn rates and rarity weights, but item 13 asks for harder rare odds. Resolve by changing **spawn weights** and **base catch difficulty** in a separate balance pass (section 3), not inside the minigame work.
- **Bot risk.** A script that computes perfect inputs from the shared simulation is always possible in timing games. This is acceptable as long as the base odds, rarity and cooldowns cap the benefit.
- **Determinism.** The simulation must give identical results on client and server (fixed timestep, no transcendental functions inside the sim). Test with printed hashes across many seeds.

**Acceptance criteria.** As listed in the spec: determinism test, formula tests, bot-catch smoke test, anti-cheat rejection tests, tutorial test, mobile viewport test, economy-intact test, timing test and no regressions in the existing smoke tests.

---

### 2.9 Creatures that grow into Titans (P1, M)

**Original note.** This is the "Eat a" / "Grow a" lesson, and it is in the title. Feed creatures in your Sanctuary so they gain kg and visibly get bigger, with the biggest becoming a Titan form. Growth timers give players a reason to check back, and it builds on the weight system. Effort: medium.

**Verdict.** The game is called **Catch a Titan** and currently has no Titans as a mechanic. This is a brand-promise gap. It is also the best answer to retention, because it creates ongoing investment in creatures the player already owns.

**Design.**
- **Feeding.** Spend coins or a consumable to add kg to a placed creature. Growth is visible: the model scales with weight.
- **Growth timers.** Feeding starts a timer. Returning to collect the growth creates a recurring reason to log in. Timers can be sped up with Robux consumables (see 2.12), which must be optional and never required to progress.
- **Titan form.** Past a weight threshold, a creature transforms into its Titan form: a distinct, larger, more impressive model with a bonus to income. This is the hero moment and needs its own cutscene and announcement.
- **Weight ceiling per rarity** so growth is bounded and balanced. Revisit the coin-per-weight multiplier so a Titan is valuable but cannot break the economy.
- **Leaderboards.** A heaviest-creature board turns growth into competition.

**Strict reviewer notes.**
- Define the diminishing-returns curve up front. Unbounded growth breaks the economy.
- Titan models are an art cost on top of item 3. Scope this to a defined subset of species at launch.
- Growth interacts with raiding and the leash (heavier means slower and a more attractive target). Playtest those interactions.

**Acceptance criteria.** A creature can be fed, visibly grows, reaches a Titan threshold, transforms, and the economy stays within the target progression curve in simulation.

---

### 2.10 Synchronized rare spawns (P1, S)

**Original note.** Each server picks its own random 5-minute timer. Spawning on exact UTC marks (:00, :05 and so on) in every server is what made fans build trackers and Discord ping groups. Effort: small.

**Verdict.** Cheap and high-leverage. Predictable, shared events create community behaviour (trackers, alert groups, content), which is free marketing and a retention hook.

**Required changes.**
1. Derive spawn slots from UTC (for example, every 5 minutes on the mark), identical across all servers.
2. Make **what** spawns deterministic or at least shared in structure. Decide whether the species is also synchronized or only the timing.
3. Keep fairness: servers have different populations, so the spawn is "available everywhere", not "one per global". Consider a per-server instance with a visible countdown.
4. Show a countdown in the HUD and announce on spawn (ties into 2.4).
5. Handle server start mid-window (spawn on the next mark, do not backfill), and clock skew (use a trusted server time source).

**Strict reviewer notes.** Synchronization concentrates load at the marks. Check for spawn-time hitches, and stagger heavy work. If rare spawns become *too* predictable, a bot or a tracker can farm them, so keep the catch itself skill-gated (2.8).

**Acceptance criteria.** Two servers started at different times spawn at the same UTC marks. A late-starting server does not spawn out of window.

---

### 2.11 Fuse machine (P2, S)

**Original note.** Combine duplicates into a higher rarity or a guaranteed mutation. A comparable game keeps bringing its fuse and craft machine back. Right now duplicates can only be released for coins. Effort: small.

**Verdict.** Duplicates are currently dead weight. A fuse sink turns surplus into progress, gives the economy a healthy item sink, and gives players a goal.

**Design.**
- Input: N duplicates (the same species or the same rarity) **[DESIGN]**.
- Output: a chance at the next rarity, or a guaranteed mutation roll. Display the exact odds before confirming.
- A short fuse animation with a reveal.
- Inputs are consumed server-side atomically.

**Strict reviewer notes.**
- **If outcomes are random and paid inputs can be used, odds disclosure is mandatory** (see 2.12).
- Avoid a deterministic path that trivialises rarity. Tune the input count so fusing is a real cost.
- Prevent exploit loops (fuse, release, rebuy). Check the entire coin and item flow.

**Acceptance criteria.** Fuse consumes inputs and grants outputs atomically, shows odds, and the rarity distribution after fusing in simulation matches the disclosed odds.

---

### 2.12 Robux catalogue expansion (P1, S–M)

**Original note.** There are 7 products. A comparable game runs about 104 cheap consumables: a floor of 19–49 R$ impulse buys, "lure" packs at x1/x3/x10/x50, gift versions, rewarded video ads. Randomised items legally need a shown odds table. Effort: small to medium.

**Verdict.** The catalogue is too thin to capture impulse spending. A wide, low-priced ladder converts far more players than a few expensive passes. But this is also where the largest compliance and trust risk sits, so it must be built carefully.

**Required changes.**
1. **Price ladder.** Add a floor of low-priced consumables **[DESIGN]**, a mid tier, and a few anchors at the top. The ladder should let a player spend at any budget.
2. **Consumables.** Luck and lure packs at tiered multipliers and durations, growth speed-ups (2.9), and extra fuse attempts (2.11).
3. **Gifting.** Gift versions of popular items, which also drive social growth.
4. **Rewarded video** where the platform allows it, as an optional alternative to spending.
5. **Odds disclosure.** Every item with randomised outcomes must show a clear odds table **before** purchase, in the shop UI, matching the real server-side roll exactly. Build one shared odds-data source that both the roll and the display read from, so they can never diverge.
6. **Fairness.** Nothing essential is paywalled. Paying makes progress faster or more cosmetic, not possible. Avoid dark patterns (fake timers, misleading "limited" labels, confusing currencies).
7. **Receipt handling.** Idempotent `ProcessReceipt`, grant-before-confirm ordering, and a purchase history so support issues can be resolved.

**Strict reviewer notes.**
- Check current platform policy on paid random items, ads and gifting before shipping each, since rules change.
- Instrument conversion by price point and by first-purchase timing. Tune the ladder from data.
- Do not let monetization rewrite core balance. Keep the economy design (2.5) and the monetization design (2.12) coupled but reviewed separately.

**Acceptance criteria.** A purchase is granted exactly once even across lag, retries and disconnects. Every random product displays odds that match the server roll. Conversion analytics are in place.

---

### 2.13 Rarity odds: harder to spawn, harder to catch (P0, S)

**Original note.** Make the odds of a higher rarity spawning more difficult, let alone catching them.

**Verdict.** Currently the top rarities are too attainable, which devalues them and shortens the game. Rarity only has meaning if it is rare.

**Required changes.**
1. **Re-weight spawn tables** so Legendary and Mythic are meaningfully rarer. Set explicit targets in "expected time to see one" terms, not just percentages (for example, an average player should see a Legendary every X hours of play and a Mythic every Y) **[DESIGN]**.
2. **Raise base catch difficulty** at the top end, while keeping the skill layer (2.8) able to meaningfully improve the odds, so a good player has a real edge on a hard target.
3. **Keep the first hour generous** (see 2.5). Tighten rare odds only after the early game so new players still get early wins.
4. **Pity or bad-luck protection.** Consider a soft pity counter so a long drought never feels hopeless. It must be disclosed if it affects odds.
5. **Luck Booster interaction.** Paid luck must remain honest and the displayed odds must reflect it. Re-balance so it helps without trivialising rarity.
6. **Server-wide supply.** With synchronized spawns (2.10) and announcements (2.4), the global feel of rarity matters. Verify that a busy server does not flood Legendaries.

**Strict reviewer notes.**
- This directly conflicts with the minigame spec's non-goal of leaving spawn rates untouched. Resolve by doing the rarity re-balance as its own change, then re-tune the minigame's skill multipliers against the new base odds.
- Rarer top tiers raise the value of leash-home (2.7) and raiding (2.6) targets, so stakes rise. Re-check fairness rules.

**Acceptance criteria.** A simulation shows target time-to-first-Legendary and time-to-first-Mythic for casual and active players. Live telemetry confirms real rates are within tolerance of design.

---

## 3. Cross-Cutting Conflicts and How to Resolve Them

| Conflict | Resolution |
|---|---|
| **Slower progress vs. no slow start** (2.5) | Fast first 10 minutes, then a steeper curve. Pace is a curve, not a constant. |
| **Harder rare odds (2.13) vs. minigame "do not change spawn rates" (2.8)** | Separate the changes. Re-balance base odds first, then tune the skill exponent on top. Never tune both at once. |
| **"Cash-grab hungry" feel (2.1) vs. honest odds and no dark patterns (2.12)** | Persistent next-purchase prompts and affordable glow are fine. Fake urgency and hidden odds are not. |
| **Leash-home loss (2.7) vs. earned-catch satisfaction (2.8)** | Add protection rules (grace period, safe zones, PvP opt-in) and measure loss-driven churn before wide rollout. |
| **Rich animation (2.2, 2.4) vs. fast sessions and performance (2.1, 2.5)** | Rarity-scaled duration, skip for repeats, and a low-effects setting. |
| **Titan growth (2.9) vs. economy stability (2.5)** | Bounded weight ceilings and diminishing returns, validated by simulation. |
| **Physical raiding (2.6) vs. new-player experience** | Newbie protection, post-raid protection windows, and base lock. |

---

## 4. Suggested Roadmap

**Phase 1: Fix first impressions and the economy (weeks 1–3).**
UI performance and layout (2.1), balance and AFK model (2.5), rarity odds (2.13), and the start of creature redesign for the top rarities and starter biome (2.3). Add analytics before changing numbers.

**Phase 2: The catch feels great (weeks 3–6).**
Catch animation (2.2), minigame (2.8), notifier overhaul (2.4), and UTC-synced spawns (2.10). By the end of this phase, a single catch should be a clippable moment.

**Phase 3: The viral loop (weeks 6–10).**
Physical stealing, defence and base lock (2.6), then leash-home (2.7). Closed playtest with real players before release, because these systems are the most likely to produce frustration.

**Phase 4: Depth and revenue (weeks 10+).**
Titan growth (2.9), fuse machine (2.11) and the expanded catalogue with odds tables (2.12).

---

## 5. Success Metrics (What "Better" Means)

| Area | Metric | Direction |
|---|---|---|
| First impression | Time to first catch; session-1 bounce rate | Down |
| Retention | D1, D7, D30 | Up |
| Engagement | Median session length; sessions per day | Up |
| AFK | Share of players returning to claim offline stash | Up |
| Economy | Time to each milestone vs. target | Within tolerance |
| Rarity | Observed Legendary/Mythic rate vs. design | Within tolerance |
| Virality | Raids per session; clips shared | Up |
| Monetization | Conversion rate; ARPPU; spend by price point | Up, without a rise in refunds or complaints |
| Quality | Frame-time on reference phone; crash and error rate | Stable or better |

---

## 6. Open Questions for the Owner

1. What is the **target full-completion time** for a casual player? The whole balance model depends on it.
2. Should PvP stealing and leash-home be **opt-in** or universal? This changes protection design significantly.
3. How many **Titan forms** at launch, given the art cost?
4. What is the **budget and pipeline** for creature art (in-house, commissioned, or generated and cleaned up)?
5. Which **analytics tooling** is in place today? Without it, Phase 1 balance work is guesswork.
6. Is there a **mobile-first** device target list for performance testing?
