# Report 08: UI Performance and Polish Playbook

**Covers** Room for Improvement item 2.1 (laggy, oversized, excessive icons, positioning, "cash-grab" feel) and the UI side of items 2.2 and 2.4.

**Honest scope.** I have not seen your UI or your frame-time data. Treat the causes below as a **checklist of hypotheses to test with the profiler**, not diagnoses. The first step is always to measure.

**Sources.** [MicroProfiler docs](https://create.roblox.com/docs/en-us/performance-optimization/microprofiler) (official, via search summary), and [DevForum: GUI optimization tips](https://devforum.roblox.com/t/gui-optimization-tips/3986563) (community advice, not official). I found no official GuiObject-count limit. Treat community claims as hypotheses to confirm on your game.

---

## 1. Measure Before You Change Anything

**Reference devices.** Pick two and keep them fixed: a mid-range Android phone and an older iPhone. Plus Studio's device emulator for quick layout checks (emulator does not give real performance).

**Protocol.**

1. Enable the MicroProfiler on the phone (Settings), open the shown address from a computer on the same network.
2. Record 30 seconds in each of: idle HUD only; HUD plus Sanctuary panel open; catch sequence; a busy server with 10+ creatures visible.
3. Note the frame time (16.67 ms budget for 60 FPS), the heaviest tasks, and the GUI-related entries.
4. Record `#descendants` of each `ScreenGui` and total GUI instance count.
5. Save screenshots. This is your baseline for before/after.

**Budgets [DESIGN]** (adjust after baseline):

| Metric | Target |
|---|---|
| Frame time, HUD only | Under 12 ms on reference phone |
| Frame time, HUD + one panel | Under 16.67 ms |
| Time to open a panel | Under 150 ms, no visible hitch |
| GUI instances, HUD only | Keep as low as practical; record baseline and reduce |

---

## 2. Likely Causes of UI Lag (hypotheses to test)

| # | Hypothesis | How to test | Fix |
|---|---|---|---|
| 1 | One big ScreenGui re-renders on any change | Compare frame cost when updating one label | Split into logical ScreenGuis (HUD, panels, toasts, modal, tutorial) with their own `DisplayOrder` |
| 2 | Too many instances alive | Count descendants; hide-only panels still cost | Destroy or pool panels you rarely open; create lists on open |
| 3 | Per-frame loops or tweens on many elements | Search for `RenderStepped`/`Heartbeat` in UI code | Event-driven updates; tween only visible elements; one shared loop |
| 4 | Text/labels updated every frame | Log how often `.Text` is assigned | Assign only when the value changes; throttle counters to a few Hz |
| 5 | Layout objects recalculating constantly | Profile layout cost; watch `UIListLayout`/`UIGridLayout` inside frequently resized parents | Fixed cell sizes; avoid `AutomaticSize` on large dynamic lists |
| 6 | Heavy images (large source textures, many ImageLabels) | Check texture sizes and counts | Downscale to display size x2-3; reuse atlases; use Frames + `UICorner` + `UIStroke` where an image is not needed |
| 7 | `UIGradient`/`UIStroke`/`CanvasGroup` overused | Toggle them in a test build | Use sparingly; reserve gradients for high-value elements (rarity, Mythic) |
| 8 | ViewportFrames left running | Count active viewports | Create on open, destroy on close; pause rotation when offscreen |
| 9 | Inventory grids built with hundreds of full cards | Time panel open with 100+ creatures | Virtualise: only build visible rows and recycle |
| 10 | Effects (shake, particles, banners) stacking | Trigger multiple at once | Cap concurrent banners; respect a low-effects setting |

Community advice on `CanvasGroup` is to use it with care, because it can look blurry on low graphics settings and may show white textures when a device runs out of memory ([DevForum](https://devforum.roblox.com/t/gui-optimization-tips/3986563)). Confirm on your target devices before deciding.

---

## 3. Sizing and Layout ("too big for the screen")

**Reference viewport.** Phone landscape around **812 x 375** with safe-area insets (the same reference used in the catch minigame spec). Everything must fit and be reachable.

**Rules.**

1. Use `ScreenInsets = DeviceSafeInsets` on every ScreenGui.
2. Use one `UIScale` per ScreenGui driven by viewport height so layouts scale consistently:

```lua
--!strict
local function updateScale(scaleObj: UIScale, viewport: Vector2)
	-- Design height 720; clamp so tiny phones and huge monitors both work. [DESIGN]
	scaleObj.Scale = math.clamp(viewport.Y / 720, 0.55, 1.4)
end
```

3. Prefer `Scale`-based sizes for panels and `Offset`-based sizes for touch targets inside them (min 44 px; primary 64+ px).
4. Test at: 812x375, 667x375, 1280x720 and one tablet size, plus a very tall narrow window.
5. Nothing interactive in the top-right (Roblox system menu area).
6. Panels never exceed ~70% of screen height on phones; the world should remain visible.

---

## 4. HUD Spec (rebuilt, minimal)

Landscape 812x375 reference. Safe-area insets applied.

```
+--------------------------------------------------------------+
| [Coins  1.4M  +3.2K/min]                       (system menu) |
| [Next: Slot 7  4.2K  ████░░ 62%]                             |
|                                                              |
|                                                              |
|                 (play area: keep clear)                      |
|                                                              |
|  [Net: Crystal +16%]       [CATCH]                           |
| [Menu] [Shop] [Trade]                          [Rare: 3:12]  |
+--------------------------------------------------------------+
```

| Element | Position | Notes |
|---|---|---|
| Currency pod | Top-left | Coins and rate. One pop animation on income ticks (throttled) |
| **Next-purchase chip** | Under currency pod | The "cash-grab hungry" element, done honestly: shows the next upgrade, its price and a progress bar; glows when affordable; one tap opens it |
| Primary action (Catch) | Bottom-centre | Largest touch target; also drives the minigame |
| Net indicator | Bottom-left of centre | Current net and bonus |
| Rare-spawn timer | Bottom-right | Counts to the next UTC mark; pulses at 30 s |
| Navigation | Bottom-left | 3 to 5 labelled buttons; icons plus text |
| Status/alerts | Top-centre | Banners (queued, never overlapping the play area centre) |

**Remove from the HUD:** anything not needed in the next 10 seconds of play. Put the rest behind panels.

### 4.1 The "next purchase" chip, specified

- Data: the cheapest meaningful upgrade (slot, net, biome) ranked by payback or by player-set pin.
- States: unaffordable (progress bar fills), affordable (glow + gentle pulse, once per minute, not constant), purchased (brief confirmation, then re-targets).
- Honesty rules: shows the real price; no fake urgency; the Robux version of an upgrade, if any, is shown separately and clearly.
- Instrument taps and conversions.

This is the legitimate version of "cash-grab hungry": reduce the number of decisions between a player and their next purchase, and make progress visible.

---

## 5. Icon Standards

Problems to fix: blur, inconsistency, excess.

| Item | Spec **[DESIGN]** |
|---|---|
| Source size | Author at 3x display size (a 32 px display icon = 96 px source), export at 256 px for large uses |
| Style | One family: same stroke weight, corner radius, perspective. Outline colour from `Theme.ink` |
| Count | Every icon must change a decision or be a navigation label. Remove decorative icons |
| Packing | Use an atlas (sprite sheet) for small icons to cut image loads; avoid non-power-of-two oddities |
| Colour | Single colour glyphs tinted via `ImageColor3` where possible, so one asset serves many states |
| Text pairing | Icon + short text label for navigation; icon-only only for universally understood symbols (close, settings) |
| No emoji | Replace every emoji in UI strings with drawn icons or text (your rule). The one-shot spec still contains emoji in templates; strip them |

---

## 6. Technique Cheatsheet (copy into your UI guidelines)

1. **Throttled counters.**
```lua
--!strict
local last = ""
local function setText(label: TextLabel, text: string)
	if text ~= last then
		last = text
		label.Text = text
	end
end
```
2. **Pooled list rows.** Keep a pool of N row frames; on scroll, rebind data instead of creating/destroying.
3. **Open/close lifecycle.** Create heavy panels on open; `Destroy()` (or hide and release references) on close; disconnect every connection you made.
4. **One UI heartbeat.** A single loop updates all periodic UI (timers, pulses) at 5-10 Hz; avoid per-element loops.
5. **Tween only what is visible.** Skip tweens for off-screen or closed panels.
6. **Springs vs tweens.** Springs (`spr`) feel better for interruptible motion; your animation research recommends them for panels and toasts. Keep to a small number of animating elements at once.
7. **Cap simultaneous banners** at 3 and queue the rest.
8. **Low-effects setting** (global): disables screen shake, reduces particles, shortens banners.

---

## 7. Polish: Banners and Reveals (UI side of items 2.2 and 2.4)

- **Legendary banner.** Gold gradient, short stinger, edge glow, 5-6 s hold. **Mythic banner.** Full-width, animated gradient border, distinct sound, brief edge pulse. Both: large outlined FredokaOne, creature icon, biome name, no emoji.
- **Reveal card.** Name, rarity, weight (kg) as a prominent pill, mutation pills, coin rate. Rarity border; Mythic uses the animated gradient.
- **Audience-aware.** Full reveal for the catcher; a lighter banner for others.
- **Never cover** the catch bar or the primary action.

---

## 8. Accessibility and Safety

- Non-colour cues (shape/pattern) for the catch zone and rarity.
- Touch targets and text size minimums; contrast checked.
- Respect system reduced-motion if exposed; otherwise provide the low-effects setting.
- Honest shop UI: price and effect together, odds button where required (Report 04 s6), no fake timers.

---

## 9. Rollout Plan

1. Baseline profiling and screenshots (Section 1).
2. Quick wins: fix text-update frequency, destroy unused panels, remove per-frame loops, cap banners.
3. Layout pass: UIScale, safe areas, HUD rebuild, remove excess icons.
4. Icon pass: new set at correct resolution.
5. Next-purchase chip and shop honesty pass.
6. Banner/reveal polish after the catch animation work.
7. Re-profile; compare to baseline; ship only when budgets are met.

## 10. Acceptance Criteria

- Baseline and after profiles recorded on both reference phones; budgets in Section 1 met.
- All primary actions reachable with one thumb at 812x375; nothing in the top-right system area.
- Icon audit passed (crisp at 2x, one family, each justified).
- HUD shows only the essentials; next-purchase chip live with tracking.
- No UI strings contain emoji.
- Low-effects setting works and is respected by banners, shake and particles.
