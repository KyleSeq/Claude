# Report 02: Roblox Platform Policy and Compliance

**Read this first.** Several findings here are time-sensitive and some could stop the game from being playable.

**Evidence limits.** I could not open Roblox's Creator Hub pages directly (network block), so everything below comes from search-result summaries of those pages and from news and forum reports. Each item says where to confirm it. This is research, not legal advice. Confirm with the official page (and your own legal counsel for monetization) before shipping.

Severity: **A** = could block the game or revenue, **B** = must design around, **C** = good practice.

---

## 1. Findings That Need Action This Week

### A1. Mandatory content ratings (age ratings) [REPORTED, time-sensitive]
- Reports describe a new rating system (Minimal, Mild, Moderate, up to Restricted for 18+) applied to experiences ([EFTM](https://eftm.com/2026/04/roblox-adding-game-and-content-ratings-to-ensure-age-appropriate-gaming-274290)).
- A search summary states that **Roblox disabled experiences on Oct. 2 after creators missed a Sept. 30 deadline to complete mandatory content ratings**, and that developers said this disrupted monetization. Today is Oct. 9.
- Developer forum posts describe games stuck at 16+ by default until they have enough engaged players ([DevForum thread](https://devforum.roblox.com/t/robloxs-new-age-restriction-update-is-killing-games-before-they-even-launch/4661801)). The thresholds quoted are second-hand and conflict (500 engaged users vs 100 highly engaged players within 60 days).
- **Action:** open the game in Creator Hub today and confirm the content-rating questionnaire is complete and the experience is not disabled. If it is disabled or defaulted to 16+, that is the top priority, above every roadmap item. Verify the exact deadlines and thresholds on the official page.
- **Design impact:** a 16+ default would cut the audience that most of this genre plays. Plan the rating answers deliberately: PvP stealing, simulated gambling-like odds and trading all affect the rating.

### A2. "Continuous feed" rule [REPORTED]
- Reports say games that reward "a continuous feed of content without natural stopping points" will not be allowed for younger accounts unless changed or removed ([Ground News summary](https://ground.news/article/roblox-ban-on-games-that-enforce-doomscrolling), [Massively OP](https://massivelyop.com/2026/08/29/roblox-clamps-down-on-gen-ai-brainrot-scrolling-games-after-steal-an-egg-goes-viral/)).
- The reported trigger was a game that let players boost run speed by watching gen-AI videos.
- **Design impact for us:**
  - Rewarded video must be a single, bounded, clearly disclosed opt-in (for example one optional ad per claim), never a loop that keeps paying out.
  - The AFK economy needs natural stopping points: capped offline accrual, an explicit claim step, daily caps. This is good design anyway (Report 03).
  - Do not build any "watch more to progress faster" chain.

### A3. Paid random items must show odds [REPORTED, from the policy page summary]
Source: [Paid random items](https://create.roblox.com/docs/en-us/production/monetization/paid-random-items). As summarised:
- Applies to random items bought **directly or indirectly** with Robux, including items bought with in-game currency. The examples include paying Robux for gems or spin tickets that are then spent on a prize wheel.
- Covered types include capsules, enhancements, combination items, and **probability modifiers such as luck boosts and pity systems**.
- Must show **every possible outcome and its numeric odds**, as **percentages that total exactly 100%**, **before purchase**. A large list may sit in a pop-up opened from a button with a **descriptive word** ("Odds", "Details"); a bare (i) icon is not enough.
- Odds for enhanced items must **update dynamically** when the enhancement changes.
- Separate guidance covers users the API marks ineligible: do not let them trade results of paid random items. The `IsPaidItemTradingAllowed` setting governs trading of items bought with Robux or in-game currency.

**What that means for each feature in our roadmap.**

| Feature | Covered? | Required |
|---|---|---|
| **Luck Booster** (paid, multiplies catch odds) | **Yes**: it is a probability modifier | Odds table, updated while active, shown before purchase |
| **Lure packs** (planned) | Yes if they change spawn odds | Same |
| **Fuse machine** | Yes if any input is Robux-purchasable (directly or via coins) | Full outcome table with percentages |
| **Mutation rolls on catch** | Arguably yes when a paid booster is active; ask Roblox or counsel | Show the mutation table in the catch/shop UI |
| **Coins purchasable with Robux** | Makes anything bought with coins "indirect" | Treat coin-priced random features as covered |
| **Rarity spawn weights** | Not paid on their own, but they become covered when a paid booster modifies them | Publish both base and boosted tables |

**Rule of thumb for design:** assume *any random outcome that a paid item can influence is covered*. Build one odds-data source that both the server roll and the UI read (Report 04, section 6) so the displayed and real odds can never diverge.

### A4. Payout model changed [REPORTED]
- Roblox's engagement-based payouts program was deprecated effective **2025-07-24** and replaced by **Creator Rewards** ([docs](https://create.roblox.com/docs/en-us/production/monetization/engagement-based-payouts)), with a reported emphasis on acquisition and reactivation, and a payout hold period reported by developers.
- **Impact:** your notes treat "playtime credit, capped at 60 minutes a day" as a rule that favours short repeatable sessions. That description may be out of date. **Verify the current Creator Rewards rules before building session design around it.** The short-session design still stands on its own merits (retention, the continuous-feed rule).

---

## 2. Rewarded Video Ads [REPORTED]

Sources: [Rewarded video ads](https://create.roblox.com/docs/en-us/production/promotion/rewarded-video-ads), [More creators can use rewarded video](https://devforum.roblox.com/t/more-creators-can-now-use-rewarded-video-ads/3838678).

| Requirement | Detail |
|---|---|
| Eligibility | Public experience; creator 13+; ID-verified with 2FA; completed maturity questionnaire |
| Traffic | **[CONFLICT]** one source says 2,000 monthly unique visitors, a DevForum post describes self-serve access for 100K+ average DAU. Check the Creator Hub page |
| Audience | Shown only to users 13+. Under-13 players never see ads, so do not make progression depend on them |
| Rewards | **Cannot be randomized items.** Ad must be clearly disclosed (what the player does, what they get) |
| Implementation | Choose a reward (existing developer product or new), client script checks availability, server script shows the ad and grants the reward |

**Design rules for us.**
- Reward = a deterministic item (for example "double this offline claim once", "10 minutes of a fixed income bonus"). Never "free random lure".
- At most one ad offer per claim or per fixed interval, with a visible cooldown (satisfies the stopping-point concern in A2).
- Never gate core progression on ads.

---

## 3. Gifting and Trading

- I found **no official source** for a developer gift API; the results were low-quality. Roblox does not let users send Robux directly to each other. **Verify** what gifting mechanisms exist for developer products and passes before committing to the "gift versions" in your catalogue.
- Trading: respect `IsPaidItemTradingAllowed` and the guidance on ineligible users (A3). If creatures can be obtained through paid random items, **trading them has compliance consequences**. Decide this before building the Trade Hub rules.
- The Grow a Garden case shows a real-money grey market forms around rare tradable items ([Wikipedia](https://en.wikipedia.org/wiki/Grow_a_Garden) and critique pieces). Real-money trading violates Roblox rules. If creatures are tradable and valuable, plan monitoring and terms for it.

---

## 4. Child Safety and Reputation [REPORTED]

- Roblox has been tightening child-safety measures (chat age checks, ratings, large-scale removal reports). The direction of travel is *more* restriction, not less.
- Games in the genre are criticised for pressuring young players to spend ([critique](https://medium.com/@alvarlaigna/robloxs-grow-a-garden-a-predatory-scam-targeting-kids-2b05e34e4d43), **[OPINION]**).
- **Design rules for us:**
  - No fake countdowns or "limited time" labels that reset.
  - Every random purchase has odds visible *before* the button.
  - Show the Robux price in the same place as the item's effect, not behind an extra tap.
  - No Robux requirement for any creature or core progression.
  - Consider a spending-confirmation step for the top-priced products.

---

## 5. Performance and Quality Guidance [REPORTED]

- Roblox's [MicroProfiler](https://create.roblox.com/docs/en-us/performance-optimization/microprofiler) docs give 16.67 ms as the 60 FPS frame budget. On a phone, you enable it in Settings and open the shown address from a computer on the same network.
- I found **no official GuiObject-count threshold**. UI advice that circulates is from forum posts (see Report 08), so measure before trusting any rule of thumb.

---

## 6. Compliance Checklist (use before every release)

- [ ] Content rating questionnaire complete and answers reviewed (A1)
- [ ] Experience not disabled or defaulted to 16+ (A1)
- [ ] Every paid probability modifier has a pre-purchase odds table (A3)
- [ ] Odds shown are generated from the same data as the server roll (Report 04 section 6)
- [ ] Odds percentages total exactly 100% (automated test)
- [ ] Odds tables update when a booster is active (A3)
- [ ] Rewarded ads: deterministic rewards only, disclosed, bounded (section 2, A2)
- [ ] No "continuous feed" loop (A2)
- [ ] Trading restrictions applied for paid random items and ineligible users (section 3)
- [ ] No creature is Robux-only
- [ ] Creator Rewards assumptions checked (A4)

## 7. Open Items to Verify (primary sources needed)

1. Current content-rating deadlines, thresholds and what blocks distribution (A1).
2. Exact current wording of the paid-random-items policy, especially pity systems and dynamic odds (A3).
3. Whether rewarded-video access applies to your game size (section 2).
4. Creator Rewards mechanics and payout timing (A4).
5. Gifting options for developer products (section 3).
6. Whether an in-game idle timeout applies to long AFK sessions (Roblox has historically disconnected idle players after about 20 minutes; **I did not verify the current behaviour**, and your AFK design depends on it).
