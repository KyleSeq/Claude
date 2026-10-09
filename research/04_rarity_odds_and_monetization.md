# Report 04: Rarity Odds, Catch Odds and Monetization

**Scope.** The exact rarity numbers in your spec, why they do not deliver "rarity should mean something", a replacement odds model, a compliance-ready odds-disclosure design, and a price-ladder plan for the expanded Robux catalogue.

All numbers marked **[DESIGN]** are proposals. Compliance claims come from search summaries of Roblox's policy pages (see Report 02); verify before shipping.

---

## 1. The Problem in One Paragraph

Your spec gives each creature a spawn weight and a catch difficulty, then lets a net **subtract** from difficulty and a Luck Booster **divide** it. The result is that rarity is cheap to see (Legendary appears in about one in 18 spawns in three biomes) and cheap to catch (Mythic 47% with a top net, 82% with a booster). Rarity should be the scarcest thing in the game, because every other system (announcements, trading, fusing, Titans, clips) depends on it.

---

## 2. Exact Spawn Odds From the Spec

Share of spawns by rarity, computed from Appendix A weights (relative weights normalised per biome):

| Biome | Common | Uncommon | Rare | Epic | Legendary | Mythic |
|---|---|---|---|---|---|---|
| Meadow | 74.0% | 22.0% | 3.0% | n/a | 0.90% (1 in 111) | 0.10% (1 in 1,000) |
| Crystal Cave | 50.5% | 32.3% | 10.1% | 5.1% | 2.0% (1 in 50) | 0.10% |
| Deep Ocean | 50.5% | 18.9% | 14.7% | 14.7% | 1.05% (1 in 95) | 0.11% |
| Volcano | 54.7% | n/a | 21.4% | 21.4% | 2.4% (1 in 42) | 0.12% |
| Sky Islands | 62.3% | n/a | 20.8% | 11.7% | **5.2% (1 in 19)** | 0.13% |
| Arctic Tundra | 29.7% | 32.4% | n/a | 32.4% | **5.4% (1 in 19)** | 0.13% |
| Ancient Ruins | 30.5% | n/a | 47.2% | 16.6% | **5.6% (1 in 18)** | 0.14% |
| Shadow Realm | n/a | 38.5% | n/a | n/a | **31.5%** | **30.0%** |

**Observations.**
- The global `RarityData.weight` column (60 / 25 / 10 / 4 / 0.9 / 0.1) is **not** what the per-creature weights produce. Late biomes violate it badly.
- With 12 players per server and announcements on every Legendary and Mythic, Sky/Arctic/Ruins would produce a Legendary banner every few minutes, and the Shadow Realm would produce them continuously.
- Epic is absent from Meadow and common in Volcano/Arctic (21-32%), so "Epic" feels routine by mid-game.

---

## 3. Catch Odds From the Spec

See the table in Report 03 section 4.3. Summary: with the assumed net ladder, a Mythic is 2% with no net, 15% with Crystal, 47% with the top net, and **at least 67% with a Luck Booster regardless of net**.

---

## 4. Replacement Model

### 4.1 Principles

1. **Rarity is carried by spawn scarcity and event timing, not by making catches near-impossible.** A catch that fails 98% of the time just feels broken; a *spawn* that appears rarely feels special.
2. **Catch odds stay meaningful but skill-driven.** The minigame (Throw, Struggle, Seal) provides the skill layer. The base odds set the floor; skill moves the result; nets and boosters nudge, not decide.
3. **Everything random that a paid item touches is one disclosed table** (Report 02 A3).
4. **Announcements are earned.** Few enough Legendary/Mythic events that each one matters.

### 4.2 Two spawn channels

**Channel A: ambient spawns** (what exists now). Reduce Epic, Legendary and Mythic weights as in Report 03 (Epic x0.7, Legendary and Mythic x0.35), and rebuild Shadow Realm so Mythic is not a third of spawns.

**Channel B: scheduled rare events** on exact UTC marks (every 5 minutes, per Room for Improvement 2.10). Each mark, every server spawns **one** event creature in a random unlocked biome, with the rarity drawn from this table **[DESIGN]**:

| Event rarity | Chance per mark | Expected per server per hour (12 marks) |
|---|---|---|
| Rare | 55.0% | 6.6 |
| Epic | 35.0% | 4.2 |
| Legendary | 9.5% | 1.14 |
| Mythic | 0.5% | 0.06 (about one per 17 server-hours) |

- **Legendary** roughly once an hour in each server: frequent enough for a session to include one, rare enough that the banner means something.
- **Mythic** once per ~17 server-hours: an event players talk about. With many servers online, the platform as a whole sees them constantly, which feeds clips.
- Make the species deterministic from the UTC mark and a server-independent seed if you want trackers and Discord groups to be able to predict *what* spawns (a major community driver). Decide this with the team: it helps the community but also helps bots.
- Server-wide announcements fire only for Channel B Legendary/Mythic and for catches (not for ambient spawns).

### 4.3 Catch probability

Replace the subtractive net bonus with a **multiplier on a rarity-based base**:

```
pBase(rarity) = { Common .85, Uncommon .70, Rare .50, Epic .35, Legendary .22, Mythic .12 }   [DESIGN]
pNet          = pBase * (1 + 0.06 * (netTier - 1))     -- tier 7 = +36%
pSkill        = 1 - (1 - pNet)^E                       -- E from the minigame (throw x struggle x sneak), capped 2.5-4.0
```

- Mythic at the top net with a perfect run: `pNet = 0.12 * 1.36 = 0.163`, `E = 4` gives `1 - 0.837^4 = 0.51`. Strong players see ~50%; a casual player (E about 1.9) sees `1 - 0.837^1.9 = 29%`; a no-skill, no-net attempt sees 12%.
- Nets remain worth buying (up to +36% before skill) but cannot erase the gap between rarities.
- Tune `pBase` after playtests; keep the 1.9-4.0 skill exponent range from the minigame spec so skill roughly doubles a casual player's odds.

### 4.4 Luck Booster redesign

Do **not** divide the threshold. Instead:

| Rarity | Spawn weight multiplier while active | Duration |
|---|---|---|
| Rare, Epic | x1.5 | 60 min |
| Legendary | x1.25 | 60 min |
| Mythic | x1.1 | 60 min |

**[DESIGN]** values. Properties:
- Catch odds are not touched, so the minigame stays honest and the "guaranteed catch" pitfall disappears.
- The effect is a spawn table change, so it is exactly the kind of thing the odds table can show (section 6).
- It cannot make Mythic common (x1.1), but it measurably helps lower tiers, which is where most spending conversions happen.
- Stacking: boosters **do not stack with each other**; the largest applies, or stack multiplicatively under a hard cap (x2). Decide and disclose.

### 4.5 Pity (optional)

A soft pity counter can protect against long droughts: after N failed Legendary-eligible catches, raise pBase by a small step until one succeeds. **Pity systems are explicitly named in the policy summary as covered probability modifiers**, so if you add one, display it and keep it free (not tied to purchases). Keep it off at launch unless data shows drought churn.

---

## 5. Monetization Plan (Catalogue Expansion)

### 5.1 Principles

1. **Nothing essential behind Robux.** Every creature is obtainable free.
2. **Deterministic items are simplest to ship.** Prefer them; they avoid disclosure work and complaints.
3. **Random items get a visible odds table, always** (section 6).
4. **Cheap floor, a few anchors.** A low-priced ladder converts the impulse buyers; a couple of high-priced items serve committed players.
5. **No decay tricks.** No fake timers, no unexplained currencies, no hiding the price.

### 5.2 Ladder (all prices [DESIGN]; test and adjust)

Your notes cite a floor of 19-49 R$ impulse buys. One verified analogue is the Catch a Brainrot capture-box ladder of 15 / 45 / 90 / 110 / 140 R$ with a 380 R$ anchor ([Beebom](https://beebom.com/catch-a-brainrot-rotboxes/)), which supports the floor-plus-anchor shape.

| Tier | Price band | Item types | Random? |
|---|---|---|---|
| Floor | 19-49 R$ | Lure x1 (15 min), Growth Boost x1, Extra Fuse attempt, cosmetic net trail | Lure and fuse: yes. Growth Boost, cosmetic: no |
| Core | 79-199 R$ | Lure x3 pack, Growth Boost x3, Raid Shield 24 h, Slot +2 | Lure: yes |
| Plus | 249-499 R$ | Lure x10 pack, Growth Boost x10, extra offline stash hours (cap +2 h permanent) | Lure: yes |
| Anchor | 599-1,999 R$ | VIP, Sanctuary Expander, Pro Net Bundle, Season Pass | No |
| Whale | 2,000+ R$ | x50 Lure bundle (heavily discounted per unit), cosmetic aura set | Lure: yes |

- "Lure" here means a timed spawn-weight modifier (section 4.4) that you can gift. Gifting should be **checked against current platform options** (Report 02 section 3) before you promise it.
- Offer a **starter pack** once, at a fixed price, on first-session success (after the first catch), clearly showing contents.
- Add **rewarded video** as a free alternative for deterministic rewards only.
- Do not sell coins directly at first. Direct coin sales make every coin-priced random feature "indirect" under the policy summary (Report 02 A3), expanding what you must disclose.

### 5.3 Items to avoid

- A "100% catch" item (the Catch a Brainrot anchor). It deletes the skill moment.
- Robux-only creatures.
- Random items priced above the floor with no disclosed odds.
- Timers that reset to show urgency.

---

## 6. Odds Disclosure Design (Compliance-Ready)

### 6.1 One source of truth

Create `OddsTables.luau` in `ReplicatedStorage/Shared`. **Both** the server roll and the shop UI read from it. Example shape:

```lua
--!strict
export type Outcome = { id: string, label: string, weight: number }
export type Table = { id: string, title: string, outcomes: { Outcome } }

local Odds = {}

-- Pure function: normalise a table, optionally with active modifiers.
function Odds.percentages(t: Table, mods: { [string]: number }?): { { label: string, pct: number } }
	local total = 0
	local ws = {}
	for i, o in t.outcomes do
		local w = o.weight * ((mods and mods[o.id]) or 1)
		ws[i] = w
		total += w
	end
	local out = {}
	for i, o in t.outcomes do
		out[i] = { label = o.label, pct = 100 * ws[i] / total }
	end
	return out
end

return Odds
```

- The **server roll** calls the same normalisation with the same modifiers (booster active or not) and rolls a `Random` against it.
- The **UI** calls `Odds.percentages` to render. It cannot diverge because it is the same function and the same data.
- **Rounding.** Policy summary says percentages must total exactly 100%. Round to 2 decimals using the largest-remainder method so the displayed numbers always sum to exactly 100.00.

### 6.2 Automated tests

1. Every table's displayed percentages sum to exactly 100.00.
2. Monte Carlo: 1,000,000 rolls per table; observed frequencies within tolerance of displayed values (chi-square).
3. With each booster active, the displayed table equals the rolled table.
4. A build fails if a purchasable random product has no odds entry.

### 6.3 UI requirements

- A **text button** labelled "Odds" (not just an (i) icon) on every random product, opening a panel before purchase ([policy summary](https://create.roblox.com/docs/en-us/production/monetization/paid-random-items)).
- List **every** outcome with a percentage. For long lists, a scrollable panel is fine.
- When a booster is active, the panel shows both "base" and "with boost" columns and updates live.
- The Robux price and the effect sit in the same view as the Odds button.

### 6.4 Example copy (no emoji)

**Lure (15 min)** - 49 R$
> Raises the spawn chance of Rare, Epic, Legendary and Mythic creatures in your server for 15 minutes. It does not change your catch chance. Tap **Odds** to see the full spawn table before you buy.

**Odds panel title:** "Spawn odds with Lure active"

| Rarity | Base | With Lure |
|---|---|---|
| (filled from `Odds.percentages`) | | |

**Fuse Machine confirmation**
> Fuse 3 Rare creatures. Possible results are listed below with their exact chances. Fusing uses up the three creatures you selected.

---

## 7. Fuse Machine Odds (Room for Improvement 2.11)

If any input can be obtained by spending Robux (directly or via coins), the fuse outcome table is covered. Proposed design **[DESIGN]**:

| Inputs | Result table |
|---|---|
| 3 of the same species | 70% same rarity re-roll (new weight and mutation roll), 28% next rarity, 2% guaranteed mutation |
| 5 of the same species | 55% same rarity, 40% next rarity, 5% guaranteed mutation |

- Prevent the fuse, release, rebuy loop by pricing release value below fuse input cost.
- Show the table (section 6) before each fuse.
- No Mythic output from fuse until you have measured the economy impact (Mythics should come from events).

---

## 8. Recommended Sequence

1. Fix the document inconsistencies (Report 03 section 7).
2. Build `OddsTables.luau` and the tests first. Every other random feature plugs into it.
3. Re-weight ambient spawns; add the UTC-synchronized event channel.
4. Replace the Luck Booster with the spawn-weight version and update the shop copy.
5. Switch catch odds to the multiplicative model together with the minigame.
6. Expand the catalogue once the above is live and disclosed.

## 9. Metrics

- Observed rarity rates versus design (daily).
- Legendary/Mythic announcements per server-hour (target near the section 4.2 numbers).
- Booster conversion and refund/complaint rate.
- Share of players who open the Odds panel before buying (a trust indicator).
- Spend distribution by price band; first-purchase timing.
