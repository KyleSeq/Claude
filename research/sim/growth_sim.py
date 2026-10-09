#!/usr/bin/env python3
"""Titan growth timeline calculator (Report 06 part B). All constants are [DESIGN]."""
RANK={"Common":1,"Uncommon":2,"Rare":3,"Epic":4,"Legendary":5,"Mythic":6}
def timeline(rarity, g=0.06, k=0.6, start_norm=0.0, min_feeds=15):
    norm=start_norm; feeds=0; minutes=0.0
    while (norm<1.0 or feeds<min_feeds) and feeds<500:
        minutes += 20*RANK[rarity]*(1+norm)     # growth job duration at current norm
        norm = min(1.0, norm + g*(1-k*norm))
        feeds += 1
    return feeds, minutes/60.0
if __name__=="__main__":
    print("rarity      start_norm  feeds  job-hours (serial, one job at a time)")
    for r in RANK:
        for s in (0.0, 0.15, 0.3):
            f,h=timeline(r,start_norm=s)
            print(f"{r:10s}  {s:9.2f}  {f:5d}  {h:8.1f}")
    print("\nParallelism: with 3 concurrent jobs across 3 creatures, each creature still needs the serial hours above;")
    print("with 1 creature and 3 slots, jobs on the SAME creature cannot overlap (design rule), so serial hours apply.")
