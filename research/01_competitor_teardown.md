# Report 01: Competitor Teardown

**Purpose.** What the closest competing Roblox games actually do, what is verified versus rumour, and what each finding means for Catch a Titan.

**How to read the evidence tags.**
- **[REPORTED]** appears in one or more third-party sources (guides, news, wikis). Not independently confirmed.
- **[CONFLICT]** sources disagree. Do not rely on the number.
- **[OPINION]** an author's argument, not data.
- **[INFERENCE]** my reasoning from the facts above it. Challenge it.

**Method and limits.** This is desk research from web searches run on 2026-10-09. I could not open Roblox's own documentation pages or some news sites directly (the network blocked them), so Roblox policy statements come from search-result summaries of those pages. Treat every price, CCU and revenue number below as indicative until checked in-game or on the developer's own channels. Many guide sites are low-quality SEO content, and I dropped results that looked machine-generated or that contradicted better sources.

---

## 1. Summary Table

| Game | Core hook | What we should take | What we should not copy |
|---|---|---|---|
| **Steal a Brainrot** | Physical stealing: grab, carry, flee; base lock; rebirth | The grab-carry-flee loop, base lock with timer, the *unrecoverable-loss fix* (Jan 2026) | Over-reliance on Robux shortcuts around the lock |
| **Steal An Egg** | Raid guarded biomes for eggs, carry home, hatch pets, run-speed gates biomes | Carry-home-under-threat structure; speed as a progression gate | Rewarding gen-AI video watching (reportedly cost it its place on the platform) |
| **Grow a Garden** | Idle plant/harvest, mutations, weather events | Mutation-as-multiplier spectacle; event-driven spikes | Pressure-selling to young players (see criticism) |
| **Catch a Brainrot** | Open-world catch with consumable capture tools | A consumable capture-tool price ladder | Its hard 100%-catch Robux item as a model for our odds |
| **Pet Simulator 99** | Hatching, extreme rarity, enchants, trading | Multiplicative stacking with diminishing returns; slot tiers | Unpublished odds (conflicts with Roblox's disclosure rule) |
| **Fisch** | Equipment-driven reel minigame, luck stacking | Rod stat model (Control/Resilience/Luck) mapped to nets | Skill that is mostly gear-solved |

---

## 2. Steal a Brainrot

**Mechanic loop [REPORTED].** Enter an unlocked enemy base, pick up a creature, carry it to your own base. Sources: [Methods of Stealing](https://stealabrainrot.fandom.com/wiki/Methods_Of_Stealing), [ProGameGuides: steal and defend](https://progameguides.com/roblox/how-to-steal-and-defend-in-steal-a-brainrot-pvp-base-protection-tips/), [Wikipedia](https://en.wikipedia.org/wiki/Steal_a_Brainrot).

**What the carry state does [REPORTED].**
- Movement speed "drops dramatically", items are disabled while carrying, the owner is notified immediately, and any player who hits the thief returns the creature to the original base.
- Farther targets are riskier, so route choice matters.

**Base lock [CONFLICT].** One source gives a 30-second spawn lock and a 60-second button lock that grows by 10 seconds per rebirth; another gives different per-rebirth examples; a third says VIP adds 10 seconds. Use these as *ballparks* only. The structure is what matters: a lock with a timer, a trade-off (it traps the owner inside too), and owners who forget to re-arm it.

**The anti-griefing fix [REPORTED, strong lesson].** Per [Nerdschalk](https://nerdschalk.com/anti-griefing-system-in-steal-a-brainrot-stealing/), an update on 2026-01-31 changed it so a stolen creature is never destroyed purely because of griefing; it stays in the world. The previous rule destroyed an item if the owner had left and another player hit the thief. The tradeoff the article names: stealing becomes fairer but more dangerous, with more PvP fights.
- **[INFERENCE]** *Unrecoverable loss is what makes PvP feel unfair.* Our design should never delete or duplicate a creature as a side effect of disconnects or edge cases. See the stealing spec (Report 05).

**Economy hooks [REPORTED / CONFLICT].**
- Rebirth resets the base for a permanent multiplier and unlocks ([PlayNews](https://www.playnews.gg/en/guides/steal-a-brainrot-roblox-the-complete-strategy-rebirth-and-tier-list-guide-for-july-2026)).
- Mutation multipliers are reported (for example Rainbow 10x, Cursed 9x, Diamond 1.5x, Gold 1.25x), but other sources give different values.
- Pass prices **[CONFLICT]**: 2x Money is reported at 139, 299 and 800 Robux depending on the source. Do not use any of them. See [Deltias pass list](https://deltiasgaming.com/roblox-steal-a-brainrot-all-gear-and-game-passes).
- Selling returns 50% of the purchase price, which makes stealing more profitable than buying and reselling.
- Seasonal events with mini-bosses pull "half the server" to one place. **[INFERENCE]** Shared, visible, time-boxed events create density, and density creates PvP stories.

**Takeaways for us.**
1. Make carry, chase and base lock the raid. Keep weight-based slowdown (our kg system is a genuine edge).
2. Adopt the "never destroy" rule as an invariant, with a test.
3. A lock that traps its owner is a good trade-off; copy the idea that defence has a cost.

---

## 3. Steal An Egg

**Loop [REPORTED].** Raid guarded biomes for eggs, carry them to your base, hatch rare pets that earn coins, spend coins on treadmills that raise run speed, and use speed to reach the next biome. Other players can raid your base. Passes include 2x Money and 2x Growth Speed. Sources: [AllThings.how](https://allthings.how/steal-an-egg-how-to-get-gamepasses-in-roblox/), [Player.One](https://www.player.one/robloxs-steal-egg-beating-some-platforms-biggest-games-164086).

**Platform action [REPORTED, important].** [Massively OP](https://massivelyop.com/2026/08/29/roblox-clamps-down-on-gen-ai-brainrot-scrolling-games-after-steal-an-egg-goes-viral/) and [Ground News](https://ground.news/article/roblox-ban-on-games-that-enforce-doomscrolling) report that the game let players boost run speed by paying or by **watching gen-AI videos in the game**, that it peaked above 500K concurrent players, and that Roblox removed it and announced restrictions on games that reward consuming "a continuous feed of content without natural stopping points" for younger accounts. A later article reports a third-party tracker listing it at roughly 1.3M concurrent players, so the reports are **[CONFLICT]** on its current status.

**A number in your own notes does not match.** Your one-shot prompt says the game peaked at **14.3M CCU in July 2026**. The sources I found say **500K+ at peak**, and a later tracker figure of ~1.3M. I could not find a source for 14.3M. **Do not repeat that figure in any pitch, store text or investor material until you have a primary source.**

**Takeaways for us.**
1. Structure beats novelty: the transferable idea is "earn it in a dangerous place, carry it home, then it pays". That is our leash-home (Report 06).
2. **Avoid rewarded features that look like a feed.** Our AFK loop is safe if it has natural stopping points (claims, caps). A rewarded-video boost is only safe as a single, bounded, clearly disclosed opt-in (see Report 02).

---

## 4. Grow a Garden

**Scale [REPORTED].** [Game Developer](https://www.gamedeveloper.com/business/roblox-s-grow-a-garden-had-nearly-22-million-concurrent-users-in-july) reports nearly 22 million concurrent users in July (2025). [Wikipedia](https://en.wikipedia.org/wiki/Grow_a_Garden) covers the game generally. One tech report claims ~$12M from virtual items in May 2025; treat as unverified.

**Mechanics that matter [REPORTED].**
- Mutations multiply value (Gold 20x and Shocked 50x are cited), and **weather events change mutation odds**, with gear that raises them.
- Dual currency: in-game Sheckles plus Robux.
- Shops restock on short timers (5 minutes is cited), creating a reason to be present.
- A grey market trades rare pets for real money outside the platform, which is against Roblox's rules.

**Monetization framing [OPINION, split].** [MaxPower Gaming](https://www.maxpowergaming.co/post/inside-the-monetization-playbook-of-roblox-s-biggest-hit) frames Robux as logical shortcuts rather than pop-up pressure. A [Medium critique](https://medium.com/@alvarlaigna/robloxs-grow-a-garden-a-predatory-scam-targeting-kids-2b05e34e4d43) argues the opposite and cites specific prices (for example 779 Robux for a rare seed). The critique is advocacy, so I would not quote its prices.

**Takeaways for us.**
1. **Event + mutation odds** (weather in their case) is a mechanism we can adapt: biome "conditions" that change mutation or rare-spawn odds, announced on the clock. It pairs with UTC-synced spawns.
2. **Restock timers drive return visits.** Our equivalent is the claim timer for AFK income and growth jobs.
3. The reputational risk is real. Design the shop so a parent reading it would not feel tricked (Report 04).

---

## 5. Catch a Brainrot

**Loop [REPORTED].** Open-world creature RPG (launched May 2026): fight wild creatures, then throw a capture box. Rarity runs Common to Epic (one source says "Insane"; the guides are more recent). Every catch rolls a random, unswappable ability set. See [Beebom: Rotboxes](https://beebom.com/catch-a-brainrot-rotboxes/) and [Games.gg](https://games.gg/roblox/guides/catch-a-brainrot-all-rotbox-explained/).

**Capture-tool price ladder [REPORTED].** Rot Box 15 R$, Silver Box 45, Gold Box 90, Snowman Box 70, Miner Box 110, Frozen Box 140, **Exclusive Infinity Box 380 R$ with a 100% catch rate**. Boxes are sold in-zone for coins, Robux or both, and gated by player level. Prices may have changed.

**Takeaways for us.**
1. A **ladder of consumable capture tools** (cheap floor, mid tiers, one premium anchor) is the closest verified analogue to your "lure pack" idea. The 15 R$ floor supports your 19-49 R$ impulse-buy idea.
2. A "guaranteed catch" item removes the randomness it replaces. That is simpler for compliance but it also removes the clip moment. For us, prefer *odds boosters* that stay inside a disclosed table (Report 04).
3. Level-gating consumables (so a beginner cannot waste an expensive item) is a good protection pattern.

---

## 6. Pet Simulator 99

**Odds and stacking [REPORTED / CONFLICT].** Huge-pet odds are community estimates from large-sample tracking, quoted around 1 in 1,000,000 up to ~1 in 2,000,000 for standard eggs, and the developer does not publish official rates ([Marix](https://marix.app/library/games/pet-simulator-99-huge-pet-chances)). Same-type enchants stack **multiplicatively** with diminishing returns, and loadout slots are tiered between free and premium ([Ginx](https://www.ginx.tv/en/pet-sim-99-enchant-builds)).

**Takeaways for us.**
1. **Multiplicative stacking with a cap** is a clean way to let many boosters coexist without breaking the economy (our mutations already stack multiplicatively; see the economy findings in Report 03 for why that is dangerous without compression).
2. **Do not copy the unpublished-odds approach.** Roblox's paid-random-item policy requires disclosure, so our tables must be published in-game (Reports 02 and 04). I make no claim about whether that game is compliant; I could not verify it.
3. Extreme rarity works commercially, but our session design (10-20 minutes) cannot rely on 1-in-a-million events as the hook. Our rarity needs a *visible* ladder of near-term goals.

---

## 7. Fisch

**Model [REPORTED].** Rods carry stats: Lure Speed, Luck, **Control** (bar size in the reel minigame), **Resilience** (less fish movement). "Preferred Luck" from bait applies to specific species. Enchants can add curses (for example a 10% luck penalty), and a Random Rod re-rolls its stats. Sources: [Deltias: rod progression](https://deltiasgaming.com/roblox-fisch-rod-progression-guide), [Deltias: preferred luck](https://deltiasgaming.com/?p=192886).

**Takeaways for us.**
1. **Map net tiers to Control/Resilience-style stats.** That is already in the minigame spec (`zoneBonus`, `fillMult`). Good.
2. **Gear-solved skill is a design choice with a cost.** If the best net trivialises the struggle, skill stops mattering. Keep a floor of skill relevance (Report 03 recommends capping what nets can do).
3. A **Random Rod** style item is a paid/earned random item and falls under the odds-disclosure rule.

The retention and revenue figures that surfaced for Fisch came from modelled third-party estimates and I did not use them.

---

## 8. Benchmarks and Retention Reality Check

Roblox says to prioritise D1 retention and session time before scaling acquisition, and offers benchmark scorecards inside Analytics for games with 100+ DAU ([Analytics docs](https://create.roblox.com/docs/en-us/production/analytics)). Third-party tier lists exist, such as D1 below 20% being weak, but they are unverified aggregates, and one source explicitly warns against a single genre-agnostic target ([RoWatcher](https://rowatcher.com/news/retention-benchmarks-by-roblox-genre-what-good-actually-looks-like)). Another claim, that an idle simulator without events loses about 60% of peak CCU in 30 days, is unverified.

**Recommendation.** Do not adopt a numeric D1/D7 target from the internet. Use your own Analytics benchmark scorecard once you have 100+ DAU, segment by acquisition source, and track the *first-session funnel* (Roblox's "new user first session retention" chart) starting now.

---

## 9. What This Means for Your Roadmap

| Roadmap item | Evidence from competitors | Confidence |
|---|---|---|
| Physical stealing (2.6) | Core growth loop of the closest comparable; carry, lock, hit-to-return | High that it is the right bet; medium on exact numbers |
| Leash-home (2.7) | The structure of Steal An Egg's loop; risk is unrecoverable loss | Medium; protection rules are essential |
| Mutation spectacle | Grow a Garden (weather-driven odds) | Medium |
| Consumable ladder (2.12) | Catch a Brainrot's 15-380 R$ ladder | Medium |
| Odds disclosure | Platform policy plus PS99 contrast | High (policy) |
| Rewarded-video design | Steal An Egg platform action | Medium; verify current rules |

## 10. Open Research Gaps

- Primary sources for CCU and revenue figures (use Roblox's own analytics for your game; use trackers only as a rough guide).
- The current exact text of Roblox's paid-random-item, rewarded-video and content-rating rules (see Report 02 for what to verify).
- Measured retention for games in this specific genre (needs your own data).
