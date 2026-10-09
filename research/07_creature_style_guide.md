# Report 07: Creature Art Direction and Style Guide

**Why this matters.** In a collection game the creatures are the product. Rarity only reads if you can see it, trading only works if creatures are recognisable, and clips only travel if the star of the clip is appealing. Room for Improvement item 2.3 calls the current creatures under-designed; this guide turns that into rules a team can review work against.

**Honest scope note.** I have not seen your current models or any art, so this is a *standard to build to*, not a critique of existing assets. Where I give numbers (part counts, texture sizes) they are **[DESIGN]** starting budgets; verify them on a mid-range phone with the MicroProfiler (Report 08).

Existing constraints I have taken from your documents: bright cartoon style, rounded chunky shapes, saturated palettes, thick-outline UI, eight biome palettes, rarity colours, a weight system that scales models up to 1.8x, mutations with defined visuals, a Giant mutation at 3.0x, and a plan to fill `modelId` with uploaded models.

---

## 1. Principles

1. **Silhouette first.** A creature must be identifiable as a solid black shape at icon size.
2. **Rarity is visible without the label.** Rarer creatures are more complex, more luminous and move more distinctively.
3. **One style, many species.** Shared proportions, outline treatment and shading rules make 50+ species feel like one world.
4. **Cheap to render.** Dozens of creatures on screen on a phone. Detail comes from shape and colour discipline, not texture weight.
5. **Readable at distance, charming up close.** Primary read at 40 studs; secondary details reward the viewport.
6. **Animation is half the design.** A well-moving simple creature beats a static complex one.

---

## 2. Shape Language and Proportion

| Rule | Spec |
|---|---|
| Overall feel | Rounded, chunky, toy-like. No sharp thin protrusions (they read as noise and break silhouettes) |
| Head to body | Head is 35-55% of body height for Common/Uncommon (cute); 25-40% for Epic and above (imposing) |
| Eyes | Large, simple, high contrast. A highlight dot adds life at almost no cost |
| Limbs | Short and thick; minimum visible thickness at 40 studs is 0.5 studs |
| Tail/crest/horns | One signature feature per species that survives the silhouette test |
| Symmetry | Bilateral by default; asymmetry only as a rarity marker (one oversized claw, a single crown) |

**Family archetypes** (reuse across species, matching the animation families in your minigame spec: quad, bird, fish, lizard, turtle, golem, penguin, insect, bat, spider, crab, kraken, blob, jelly, serpent, dragon, deity). Each species is a variant of one archetype with its own head, tail and markings. This keeps rigs and animations reusable.

---

## 3. Colour and Palette

- **Base palette per biome** (from your one-shot): Meadow warm green, Cave cool grey-blue, Ocean deep cyan, Volcano red-orange, Sky pastel purple-white, Arctic pale ice-blue, Ruins dusty gold, Shadow Realm purple-black.
- **Species palette: 3 + 1.** Three main colours (body, secondary, accent) plus one "pop" colour used for eyes/markings. Keep to 4 colours for Common/Uncommon; allow 5-6 for Epic and up.
- **Contrast rule.** Body colour must differ from the biome floor colour by a clear value difference (check in greyscale). A fox on a green meadow needs warm or dark values, not mid-green.
- **Saturation.** High but not neon. Reserve neon materials for rarity effects (Section 4).
- **Rarity colours (UI).** Your two documents disagree on Rare/Epic colours (Report 03 s7 #4). Pick one set and use it for creature auras, UI borders and announcements. Suggested single set: Common grey, Uncommon green, Rare blue, Epic purple, Legendary gold, Mythic animated gradient.

---

## 4. Rarity Escalation (the key table)

Each tier adds visible complexity. Use the *complexity budget* so artists have a target.

| Rarity | Silhouette | Parts (MeshParts) | Materials / effects | Idle animation | Aura / particles |
|---|---|---|---|---|---|
| Common | Simple, one signature feature | up to 12 | Plastic/SmoothPlastic only | Basic idle + walk | None |
| Uncommon | Common + 1 extra feature | up to 16 | + subtle two-tone markings | Idle with a secondary motion (tail swish) | None |
| Rare | Distinct extra shape (wings, shell, crest) | up to 22 | + one emissive detail (eyes/markings) | Idle with personality, a "look around" | Faint rim glow |
| Epic | Large, layered silhouette | up to 30 | + two emissive details, gradient shading | Signature idle + a reaction animation | Small ambient emitter (1) |
| Legendary | Unique silhouette; unmistakable from far | up to 40 | + emissive crest/wings, ForceField or Neon accents (sparingly) | Cinematic idle, 3 animation variants | Aura emitter + light (1 PointLight, low range) |
| Mythic | Bespoke, species-defining | up to 50 | + animated material/shader-like effect (UIGradient/texture scroll on a part, beams) | Bespoke set including a "roar"/reveal | Aura + trail + light, within the particle budget |

Budgets are per creature and **[DESIGN]**; measure total cost with 10 creatures visible. Do not add particles beyond the emitter caps without profiling.

**Why complexity is a good rarity signal.** It works even for colour-blind players, in screenshots with no UI, and survives small icons.

---

## 5. The Silhouette and Thumbnail Test (gate every species)

1. Render the model as a solid black shape on white at 128 px. Can five testers name the species family?
2. Render all species of one biome in one row at 64 px. Are any two confusable?
3. Render at 64 px in greyscale. Is the rarity tier guessable?
4. Place on its biome floor at 40 studs. Is it visible against the background?

A species fails if any test fails. Fix the design, not the test.

---

## 6. Animation Standards

Families share rigs. Minimum set per species:

| Animation | Notes |
|---|---|
| Idle (2 variants) | Looped; weighted random so the common one dominates |
| Walk | Matches speed ranges (6-10 studs/s wandering) |
| Flee | Distinct, faster, visible panic |
| Struggle | For the catch minigame; `CreatureAnimator.setStruggle(model, amount)` drives intensity |
| Caught / reveal | Played once at reveal; rarity-scaled flourish |
| Carry sway | For the steal/leash systems (Reports 05-06) |

- Load tracks at spawn, not per state change (your animation research doc is right about this).
- Use a single Heartbeat loop for all creature state machines.
- Epic and above get one signature animation that appears in announcements and trade previews.

---

## 7. Mutation Visual Treatments

Your mutation table defines effects; these rules make them readable.

| Mutation | Treatment | Readability rule |
|---|---|---|
| Shiny | Gold sparkle emitter + gold PointLight (range ~10) | Sparkle count capped; must not hide silhouette |
| Giant | Model scale increase | Resolve scale conflict; cap final scale so pens/carry still work |
| Shadow | Dark aura emitter + dark light | Add a bright eye so the creature stays readable |
| Corrupted | Hue-shift glitch | Rate-limit updates (10 Hz) to save CPU |
| Rainbow | Full colour cycle | Cycle at the part colour level once per second, not per-frame per-part |

Mutations stack. Define the maximum simultaneous effects (suggest two visible effect layers) so a double mutation never becomes a particle storm.

---

## 8. Technical Standards

| Item | Spec **[DESIGN]** |
|---|---|
| Mesh triangles | Common up to ~2,000; Mythic up to ~8,000 per creature |
| Textures | One 512x512 atlas per species max; prefer vertex colour / material colour for Common-Rare |
| Collision | Collision off (`CanCollide = false`, `CanQuery` as needed); a simple invisible hitbox |
| LOD | Use Roblox's level-of-detail where available; swap to a simple impostor beyond ~80 studs |
| Pivot | Pivot at the feet centre so `PivotTo` and `ScaleTo` behave (your weight research notes the pivot caveat) |
| Naming | `Species_Part` consistent; rig bones named per family |
| Icons | Render once from the model, 256x256 source for 64-128 px display; store as images or use ViewportFrames only where needed (cost) |
| Scale | Author at base scale 1.0; `ScaleTo` for weight/Giant; test hitboxes at 1.8x and 3.0x |

---

## 9. Review Process

Every new species passes four gates before it ships:

1. **Concept** (sketch + palette): fits the family and biome, silhouette test on the sketch.
2. **Model** (untextured): proportion and part budget check.
3. **Animated build**: all animations present, transitions clean.
4. **In-game test**: on a mid-range phone with 10 creatures in view; frame time and readability checked.

Keep a species sheet (image + stats + palette + animation list) in the repo so reviewers compare against the guide instead of memory.

---

## 10. Priorities and Sequencing

1. **Starter biome (Meadow):** all 8 species. It is the first-impression biome; its Legendary and Mythic are your marketing images.
2. **Top rarities everywhere** (the clips): Legendary and Mythic first, in every biome.
3. **Epic**, then fill Uncommon/Common.
4. **Titan variants** (Report 06) once base models are stable.

Aim for a small number of excellent creatures before a large number of adequate ones.

---

## 11. Sourcing and Pipeline Notes

- Your one-shot mentions filling `modelId` after uploading AI-generated models. If you use AI-assisted 3D tools, treat output as a *starting mesh*: retopologise to the triangle budget, fix the pivot, bake to the 4-colour palette, and apply the style guide. Raw generated meshes usually fail the silhouette and budget tests.
- **Verify Roblox's current rules on AI-generated assets and any disclosure requirements** before upload; I did not confirm them.
- Keep source files and an export checklist so every model arrives in the same state (pivot, naming, scale, collision).

## 12. Acceptance Criteria

- Style guide adopted and linked from the repo.
- Every species has a species sheet and has passed the four gates.
- Silhouette tests passed for all species; no two species confusable in a biome row.
- Rarity readable in greyscale at 64 px.
- With 10 creatures visible on the reference phone, frame time remains within budget.
- Mutation visuals pass the "silhouette still readable" check.
- All animations in Section 6 present for every species.
