# Report 05: Physical Stealing, Defence and Base Lock (Implementation Spec)

**Status.** Design spec for Room for Improvement item 2.6. Written to the same standard as the catch-minigame prompt: server-authoritative, testable, with explicit numbers. Numbers marked **[DESIGN]** are starting tunings; keep them in `Config.STEAL`.

**What I could not see.** The existing `RaidService`, plot layout and `State` code are not in this session, so file names below are proposals that follow the conventions in your minigame spec (Rojo layout, `Env`/`State`, `UIKit`/`Theme`). Reconcile them with the real code before building.

**Evidence base.** Competitor behaviour is summarised in Report 01 (Steal a Brainrot: carry slows you, items are disabled, owner is notified, hitting the thief returns the item, base lock with timer; Jan 2026 fix that stops stolen items being destroyed by griefing). Platform constraints are in Report 02.

---

## 0. Goal and Non-Goals

**Goal.** Replace the menu raid (pick target, pick card, roll dice) with a short physical chase: enter a plot, grab a creature, carry it home while the owner chases, and either escape or get netted. It must produce clips, stay fair, and never lose or duplicate a creature.

**Non-goals.**
- No free-for-all combat. The only interaction between players is: grab, carry, net, lock.
- No raids on offline players. No raids across more than one rebirth tier.
- No permanent destruction of a creature as a side effect of any edge case.
- No new currency or Robux-only creatures.

---

## 1. Non-Negotiable Rules

1. **The server owns every state transition.** Clients send intent (`RequestGrab`, `RequestNetThief`, `RequestLock`). They never report positions, hits or outcomes.
2. **A creature is in exactly one place at all times**: owner's plot slot, a carrier, a recovery drop, or banked in the thief's inventory. One authoritative record, atomic transitions, no duplicate on retry (Section 8).
3. **No unrecoverable loss.** Every failure path returns the creature to its owner (Section 7). This is the lesson from Steal a Brainrot's Jan 2026 fix.
4. **Fairness gates are server-side:** online-only, rebirth window, cooldowns, protection windows, newbie protection (Section 5).
5. **Heavier creatures are slower to carry** (kg system), with a clamped floor so the heaviest creature is a risk, not a dead stop.
6. **Mobile-first.** One-thumb actions. No precise aiming. No emoji in UI.
7. **Determinism where it matters.** Speed and cooldown values come from one function in `Formulas.luau` that both the server and the HUD use.

---

## 2. Player Experience

### 2.1 Thief

1. Walk to a plot's gate. If the plot is **locked**, a laser-gate effect blocks entry and the prompt reads "Locked (0:42)".
2. Enter. Creatures in pens show a `Take` prompt. Hold the prompt for **0.6 s** to grab.
3. The creature jumps onto your head (visual). Your speed drops. A HUD chip shows `Carrying: Cave Phoenix 47 kg - speed 74%` and an arrow points to your safe zone.
4. Run home. The owner is alerted and may chase you.
5. Reach your plot's safe zone (the **banking radius**) and the creature moves to your inventory with a short reveal.

### 2.2 Owner

1. A screen-edge alert: "A creature is being taken from your plot" with a compass arrow to the thief.
2. Chase and use the **Net** action (one button, short range, cooldown) to hit the thief.
3. A successful net hit **recovers** the creature: it returns to its original slot and the thief is **stunned** briefly.
4. Alternatively press **Lock** before an attempt starts to seal the plot for a duration.

### 2.3 Moments to make clippable

- The grab (camera pulse, alarm sting, creature squeal).
- A heavy Mythic wobbling on the thief's head as speed drops.
- The net hit: hit-stop 70 ms (same as the catch minigame), the creature flying back.
- The banking moment: confetti burst in the thief's colour.

---

## 3. State Machine (server)

Per creature record `c.state` and a `c.carry` table:

```
InSlot ──Grab(valid)──▶ Carried ──Bank(valid)──▶ Banked (thief inventory)
   ▲                       │
   │                       ├─NetHit(valid)──▶ Recovered ──(auto)──▶ InSlot   [thief stunned]
   │                       ├─Disconnect(thief)──▶ Returned ──▶ InSlot
   │                       ├─Disconnect(owner)──▶ ReturnedAfterGrace ──▶ InSlot  (see 7.2)
   │                       ├─Timeout(carry max)──▶ Returned ──▶ InSlot
   │                       └─ThiefDeath/Reset──▶ DroppedPickup ──(owner or thief re-grab) / Timeout ──▶ InSlot
   └────────────────────────────────────────────────────────────────────────────┘
```

**Carry record** `c.carry = { thief: Player, ownerId: number, t0: number, kg: number, sid: string }`.

| Transition | Preconditions (all checked on the server) |
|---|---|
| Grab | Thief and owner both online; thief within `GRAB_RANGE` (6 studs) of the creature; plot not locked; rebirth window; cooldowns clear; thief not already carrying; creature `InSlot` and not Vaulted; thief not in newbie protection; owner not under post-raid protection |
| NetHit | Net action off cooldown; target is the carrier; within `NET_RANGE` (10 studs) and a server line-of-sight check; net caller is the owner, a plot co-defender, or (for leashed creatures, Report 06) any player |
| Bank | Carrier inside own `SAFE_ZONE` radius; carry not expired; creature still `Carried` by the same `sid` |
| Timeout | `os.clock() - t0 > CARRY_MAX_SECONDS` |

---

## 4. Numbers (`Config.STEAL`) **[DESIGN]**

```lua
STEAL = {
	-- grab
	GRAB_RANGE = 6, GRAB_HOLD_SECONDS = 0.6,
	-- carry
	CARRY_MAX_SECONDS = 90,
	SPEED_K = 0.12, SPEED_MIN = 0.40, SPEED_MAX = 0.95,      -- see formula in 4.1
	-- net-back
	NET_RANGE = 10, NET_COOLDOWN = 4.0, THIEF_STUN_SECONDS = 1.2,
	-- lock
	LOCK_SECONDS = 45, LOCK_COOLDOWN = 120, LOCK_LOCKS_OWNER_IN = false,
	LOCK_SECONDS_PER_REBIRTH = 5,
	-- fairness
	REBIRTH_WINDOW = 1, RAID_COOLDOWN_SECONDS = 60,          -- per thief; see 5.1
	POST_RAID_PROTECTION_SECONDS = 600,                      -- per owner after a loss
	NEWBIE_PROTECTION_MINUTES = 30,
	MAX_STEALS_PER_VICTIM_PER_HOUR = 3,
	-- safe zone
	SAFE_ZONE_RADIUS = 18,
	-- recovery
	DROP_PICKUP_SECONDS = 20,
	OWNER_DISCONNECT_GRACE = 8,
}
```

### 4.1 Carry speed from weight

Speed multiplier from the creature's weight in kg, on a log scale so a 1000 kg Mythic is slow but a 2 kg Common is almost free:

```
speedMult = clamp(1 - SPEED_K * log10(1 + kg), SPEED_MIN, SPEED_MAX)
```

| kg | Example | speedMult | WalkSpeed if base is 16 |
|---|---|---|---|
| 0.5 | small Common | 0.95 | 15.2 |
| 2 | Common max | 0.94 | 15.0 |
| 15 | Rare max | 0.86 | 13.7 |
| 50 | Epic max | 0.80 | 12.7 |
| 200 | Legendary max | 0.72 | 11.5 |
| 1000 | Mythic max | 0.64 | 10.2 |

(`log10` is fine here: this runs on the server only and is not part of any deterministic client/server simulation.)

- Compute with the **server's** weight value; send only the resulting multiplier to the HUD.
- Apply by setting `Humanoid.WalkSpeed` on the server and remove it on every exit path (use a single `releaseCarry()` function that all transitions call).
- If you later add Titans (Report 06), kg can exceed 1000. The clamp keeps carry speed at 0.40.

---

## 5. Fairness and Anti-Grief Rules

| Rule | Value | Notes |
|---|---|---|
| Online-only | owner must be in-server | If the owner leaves mid-carry, see 7.2 |
| Rebirth window | thief within +/-1 rebirth of owner | Already in your rules |
| Newbie protection | first 30 minutes of playtime cannot be stolen from | Counted server-side, persisted |
| Post-raid protection | 10 minutes after losing a creature | Prevents farming one victim |
| Per-victim cap | 3 successful steals per hour | Soft anti-grief |
| Thief cooldown | 60 s after a grab ends | Replaces your 2-hour raid cooldown |
| Vault | top 3 creatures cannot be grabbed | Your existing upgrade |
| Lock | owner-activated, timed, cooldown | See section 6 |
| One carry at a time | a thief carries at most one creature | Simplifies state |

**Cooldown change to flag.** Your one-shot spec has a 2-hour raid cooldown per raider. That is incompatible with a physical loop, where the fun is repeatable attempts. The table above replaces it with a short cooldown plus per-victim caps and protection windows. This is a major design decision: confirm it.

**Visibility.** Always tell a player *before* they are exposed (tutorial text, shop copy, settings). Offer a clearly worded **opt-out/low-risk mode** only if playtests show churn from losses; if you add one, decide what it costs (for example, protected plots earn less).

---

## 6. Defence

### 6.1 Base lock

- Button on the HUD and at the plot gate. Owner presses it; the plot's gates seal for `LOCK_SECONDS + rebirths * LOCK_SECONDS_PER_REBIRTH` with a visible countdown dome/laser effect.
- Cooldown `LOCK_COOLDOWN` begins when the lock *ends*, so locks cannot chain.
- `LOCK_LOCKS_OWNER_IN = false`: unlike the competitor's lock that traps its owner (Report 01), do not trap the owner in; defence should not be a penalty on the defender's own movement. If you want the trade-off, make it economic: a locked plot earns income at 80% while sealed **[DESIGN]**.
- **A lock cannot save a creature already being carried**; it only prevents new grabs. Entering is blocked by server-side checks (not only by collision), because physical walls can be exploited.
- Competitor note: guides describe owners forgetting to re-arm the lock as a key exploit window. Add an optional **auto-lock** setting with a visible cost (shorter duration) so careful players are not punished by attention.

### 6.2 Net-back

- Owner or co-defenders only (Report 06 extends it to leashed creatures).
- On a valid hit: creature returns to its slot, thief stunned `THIEF_STUN_SECONDS`, `RAID_COOLDOWN_SECONDS` still applies to the thief, thief and owner both get a short toast.
- Net visual reuses the catch-minigame net (section 7 of the catch minigame prompt).

### 6.3 Existing upgrades mapped

| Existing | Becomes |
|---|---|
| Alarm Trap | Louder alert, longer owner notification radius, reveals thief on the map for 5 s per trap (max 3) |
| Vault | Unchanged (cannot be grabbed) |
| Shield Dome (R$29) | Plot invulnerable for 24 h; visible dome. It is a deterministic product, not random |
| Guard Creature | A placed creature that slows grabbers within 10 studs by 20% (visible defender) |

The old `defenceScore` roll disappears; defence is now spatial and skill-based. Remove or repurpose `raid_skill` / `defence_level` rather than leaving dead stats.

---

## 7. Edge Cases (each needs a test)

### 7.1 Thief disconnects mid-carry
`releaseCarry()` returns the creature to `InSlot` immediately. Persist the transition before the player data is released (ProfileStore/DataStore save ordering).

### 7.2 Owner disconnects mid-carry
Grant the thief a grace window of `OWNER_DISCONNECT_GRACE` seconds to bank (so the owner cannot save a creature just by leaving to cancel, and the thief is not punished for the owner's lag). If the thief banks within the window the steal stands; otherwise the creature returns. Log these cases for review. This follows the competitor lesson (Report 01): do not destroy an item when one party leaves.

### 7.3 Thief dies, resets or is teleported
Drop the creature at the position as a `DroppedPickup` for `DROP_PICKUP_SECONDS`. The owner or the thief may re-grab it (owner re-grab returns it to the slot). After the timer it returns to `InSlot`.

### 7.4 Teleport and speed exploits
- Sample the carrier's position every 0.25 s on the server. If it moves farther than `maxSpeed * dt * 1.5`, void the carry and return the creature.
- Clamp `Humanoid.WalkSpeed` server-side every tick while carrying; do not trust client-reported values.
- Ignore `Humanoid.Jump` boosts above a threshold or disable jump while carrying **[DESIGN]**.

### 7.5 Two players grab at once
A single `grabLock` per creature id and per plot slot, acquired before any check. Second request fails with a toast.

### 7.6 Retried or duplicated remotes
Every transition carries `sid`. A transition with a stale `sid` is ignored. Rate-limit remotes (`REMOTE_LIMITS`).

### 7.7 Server shutdown / BindToClose
On close, any `Carried` creature returns to `InSlot` before saves flush.

### 7.8 Owner in the pen when a grab starts
Allowed; the owner can net the thief immediately (they are already nearby).

### 7.9 Group plays / co-defenders
Only allow named co-defenders (friends or party) to net a thief if they are in the owner's party. Never allow arbitrary players to net on someone else's plot, to prevent three-way griefing (the leashed-creature rules in Report 06 are different on purpose).

---

## 8. Atomic Ownership Transfer

The commonest source of duplicate/loss bugs. Use a single function:

```lua
-- ServerScriptService/Services/CreatureLedger.luau  (new)
-- Moves a creature id between exactly one source and one destination, in memory, then marks both
-- profiles dirty. Returns false (no change) if the creature is not where the caller thinks.
function Ledger.transfer(id: string, from: Location, to: Location, sid: string): boolean
```

- `Location` is `{ kind: "Slot"|"Carry"|"Inventory"|"Drop", ownerId: number, ref: any }`.
- The function verifies `from` equals the creature's current location, mutates, and returns true; otherwise it changes nothing.
- Persist after the transition. A crash between memory and save must never produce a state where both profiles contain the creature; save the *destination* first, then the source removal, and on load reconcile any creature id found in two profiles by keeping the one with the later `sid`.
- Add a periodic server audit (every 5 minutes) that asserts every creature id appears in exactly one location.

---

## 9. Remotes (add to `Remotes.luau` and `REMOTE_LIMITS`)

| Remote | Direction | Args | Limit |
|---|---|---|---|
| `RequestGrab` | C->S | `creatureId` | 2/s, burst 4 |
| `RequestNetThief` | C->S | `thiefUserId` | 4/s, burst 6 |
| `RequestLock` | C->S | none | 1/s |
| `StealState` | S->C | `{ phase, creatureId, kg, speedMult, safeZone, expiresAt, carrierId }` | none |
| `StealAlert` | S->C | `{ plotOwnerId, creatureId, thiefId, position }` | none |

The server pushes `StealState` on every transition. The HUD renders from it; it never infers state locally.

---

## 10. Client

- **Carry visual.** Weld the creature model to the thief's head/upper torso on the **server** (so every client sees the same thing), scale it down for large creatures so the camera is not blocked, and add a sway animation proportional to speed loss.
- **HUD.** A carry chip (name, kg, speed percent), a banking arrow, a countdown for `CARRY_MAX_SECONDS`. For the owner: an alert banner, a compass arrow, a Net button (one thumb), a Lock button with cooldown ring.
- **Audio.** Alarm sting on grab, whoosh on net, ka-ching on bank. All through the existing `Sound.play` keys.
- **Accessibility.** Shape and text cues in addition to colour; assist setting extends `NET_RANGE` and `GRAB_HOLD_SECONDS` tolerance.
- **Performance.** Cap simultaneous carry-HUD updates to 10 Hz; do not tween per frame.

---

## 11. Build Order

1. `Config.STEAL`, `Formulas.carrySpeed`, unit checks.
2. `CreatureLedger` with transfer, audit and tests (the riskiest part first).
3. `StealService` state machine (Grab, Carry, Bank, Timeout, Disconnect) without net-back or lock.
4. Net-back and thief stun.
5. Base lock and defence mapping.
6. Client carry visuals, HUD, alerts.
7. Fairness gates (newbie, post-raid, per-victim, rebirth window).
8. Edge-case hardening (Section 7) and telemetry.
9. Closed playtest with real players before release.

---

## 12. Acceptance Tests

1. **Conservation.** In 1,000 scripted steal attempts (random outcomes, forced disconnects of either party, forced resets), every creature id exists in exactly one location afterwards.
2. **No loss on any disconnect.** Parameterised test for each state in Section 3.
3. **Speed.** A carrier's server-side WalkSpeed equals `16 * speedMult(kg)` and returns to normal on every exit path.
4. **Fairness gates.** Raid attempts against offline players, out-of-window rebirths, protected plots, vaulted creatures and plots at the per-victim cap are rejected with the correct message.
5. **Lock.** A locked plot rejects `RequestGrab`; lock duration and cooldown match config; the cooldown starts when the lock ends.
6. **Net-back.** A valid hit returns the creature and stuns the thief; an out-of-range or out-of-line-of-sight attempt is rejected; hit cooldown enforced.
7. **Exploit resistance.** Teleporting the carrier more than the allowed distance voids the carry and returns the creature.
8. **Persistence.** Kill the server mid-carry; on rejoin the creature is in the owner's slot.
9. **Mobile.** At 812x375 touch-only: grab, net and lock are reachable with one thumb.
10. **No regressions.** Existing smoke tests pass.

---

## 13. Telemetry and Tuning

Log per steal: thief/owner rebirth tier, creature rarity and kg, route length, duration, outcome (banked / netted / timed out / disconnect), whether the plot was locked, owner reaction time to alert.

Watch these health signals after launch:

| Signal | Concern if |
|---|---|
| Steal success rate | Above ~70% (defence feels pointless) or below ~20% (offence feels pointless) **[DESIGN]** |
| Churn within 10 minutes after losing a creature | Noticeably higher than baseline |
| Share of steals targeting recently raided players | High: the protections are not working |
| Lock usage | Near 100% (the lock is mandatory) or near 0% (nobody understands it) |

---

## 14. Open Decisions for the Owner

1. Replace the 2-hour raid cooldown with the short-cooldown-plus-caps model? (Recommended.)
2. Allow co-defenders, or owner only?
3. Do you want an opt-out low-risk mode, and what should it cost?
4. Should creature theft be possible during the first hour of a player's life at all? (Recommended: no.)
5. How do rebirth tiers interact with plot proximity so that cross-tier players are never neighbours?
