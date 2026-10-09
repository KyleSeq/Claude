# Simulators

Pure Python 3 (standard library only). They model the **spec** in the one-shot prompt, not the live game. Replace the data tables with your real `CreatureData`, `BiomeData`, `NetData` and `Config` values to audit the shipped build.

| File | Purpose |
|---|---|
| `economy_sim.py` | Minute-by-minute progression model for casual / regular / dedicated players. Reports median day per milestone |
| `proposals.py` | Configuration variants (A, D, E, F, G, and an isolated mutation test) |
| `run_one.py` | Run a single variant: `python3 run_one.py G 16 150` (variant, seeds, days) |
| `growth_sim.py` | Titan growth feeds and job-hours per rarity |
| `results*.json` | Saved outputs used in Report 03 |

## Run

```bash
python3 economy_sim.py --seeds 12 --days 120      # baseline + variants (about 2-3 minutes)
python3 run_one.py G 16 150                        # recommended starting point only
python3 growth_sim.py
```

## Known simplifications

- Greedy purchasing (cheapest affordable upgrade first); real players differ.
- Fixed 3 catch attempts per active minute.
- No rebirth, Luck Booster, raids, trading, leash or Titans in the baseline.
- Net bonuses beyond Crystal (+0.16) and all net/slot prices beyond the spec are **assumed** (marked ASSUMED in code).
- A constant 0.04 weight-difficulty bonus.
- Seeds are fixed (0..N-1), so results are reproducible. Small N means medians move a day or two between runs with different N.
