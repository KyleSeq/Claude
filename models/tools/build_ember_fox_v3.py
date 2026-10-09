#!/usr/bin/env python3
"""Ember Fox v3: chunky, faceted "Roblox cartoon" fox with glowing crystals (numpy + PIL only).
Style reference: faceted low-poly creature with glowing crystal spikes, striped markings, big expressive head.
Units: studs. Faces -Z (Roblox LookVector), Y up.
Usage: python3 build_ember_fox_v3.py OUT_DIR [--fast]
"""
import json, math, os, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
OUT = sys.argv[1] if len(sys.argv) > 1 else "ember_fox_v3"
FAST = "--fast" in sys.argv
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(11)

# ------------------------------------------------------------------ SDF anatomy (chunky proportions)
G = dict(body=0, neck=1, head=2, snout=3, ear=4, legF=5, legH=6, tail=7, cheek=8, ruff=9)
PRIMS = []
def P_(g, a, b, ra, rb, scale=(1, 1, 1), k=0.2): PRIMS.append((G[g], np.array(a, float), np.array(b, float), ra, rb, np.array(scale, float), k))

P_("body", (0,1.18,-0.35), (0,1.12,0.50), .68, .62, k=0.0)
P_("body", (0,1.12,0.50), (0,1.08,0.95), .62, .58, k=0.30)
P_("ruff", (0,0.98,-0.78), (0,0.88,-0.62), .40, .38, k=0.25)
P_("neck", (0,1.60,-0.78), (0,1.95,-1.10), .46, .44, k=0.30)
P_("head", (0,2.08,-1.10), (0,1.98,-1.30), .84, .76, k=0.25)
P_("snout",(0,1.86,-1.72), (0,1.74,-2.12), .36, .24, k=0.18)
for s in (-1, 1):
    P_("cheek", (s*.52,1.84,-1.28), (s*.62,1.76,-1.42), .34, .30, k=0.16)
    P_("ear",   (s*.44,2.60,-1.00), (s*.80,3.72,-.88), .36, .05, scale=(1,1,2.2), k=0.08)
    P_("legF", (s*.37,1.00,-.45), (s*.37,.42,-.50), .31, .25, k=0.18)
    P_("legF", (s*.37,.42,-.50), (s*.37,.16,-.62), .25, .27, k=0.10)
    P_("legH", (s*.42,1.02,.62), (s*.40,.46,.72), .38, .27, k=0.20)
    P_("legH", (s*.40,.46,.72), (s*.40,.16,.62), .27, .28, k=0.10)
tail_pts = [((0,1.20,.90),.24), ((0,1.26,1.55),.46), ((0,1.58,2.15),.60), ((0,2.08,2.58),.55), ((0,2.62,2.82),.40), ((0,3.05,2.88),.22)]
for i in range(len(tail_pts) - 1):
    P_("tail", tail_pts[i][0], tail_pts[i+1][0], tail_pts[i][1], tail_pts[i+1][1], k=0.28 if i == 0 else 0.18)

def prim_d(P, pr):
    g, a, b, ra, rb, sc, k = pr
    c = (a + b) / 2
    Q = (P - c) * sc + c
    pa = Q - a; ba = b - a
    h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return np.sqrt(((pa - h[..., None] * ba) ** 2).sum(-1)) - (ra + (rb - ra) * h)

def smin(a, b, k):
    if k <= 0: return np.minimum(a, b)
    h = np.maximum(k - np.abs(a - b), 0) / k
    return np.minimum(a, b) - h * h * k * 0.25

def sdf(P):
    d = None
    for pr in PRIMS:
        di = prim_d(P, pr)
        d = di if d is None else smin(d, di, pr[6])
    return d

def labels(P):
    ds = np.stack([prim_d(P, pr) for pr in PRIMS], 0)
    gid = np.array([pr[0] for pr in PRIMS])
    return gid[np.argmin(ds, 0)]

# ------------------------------------------------------------------ surface nets
def surface_nets(res, lo=(-1.15, -0.10, -2.60), hi=(1.15, 4.00, 4.10)):
    lo = np.array(lo); n = np.ceil((np.array(hi) - lo) / res).astype(int) + 1
    xs = lo[0] + np.arange(n[0]) * res; ys = lo[1] + np.arange(n[1]) * res; zs = lo[2] + np.arange(n[2]) * res
    F = np.empty(tuple(n))
    for i in range(n[0]):                       # slab-by-slab to bound memory
        Y, Z = np.meshgrid(ys, zs, indexing="ij")
        P = np.stack([np.full_like(Y, xs[i]), Y, Z], -1)
        F[i] = sdf(P)
    out = F > 0
    cs = tuple(n - 1)
    corners = [(i, j, k) for i in (0, 1) for j in (0, 1) for k in (0, 1)]
    edges = [(a, b) for a, ca in enumerate(corners) for b, cb in enumerate(corners) if b > a and sum(abs(x - y) for x, y in zip(ca, cb)) == 1]
    cv = lambda arr, o: arr[o[0]:o[0] + cs[0], o[1]:o[1] + cs[1], o[2]:o[2] + cs[2]]
    ci, cj, ck = np.meshgrid(np.arange(cs[0]), np.arange(cs[1]), np.arange(cs[2]), indexing="ij")
    base = np.stack([lo[0] + ci * res, lo[1] + cj * res, lo[2] + ck * res], -1)
    acc = np.zeros(cs + (3,)); cnt = np.zeros(cs)
    for a, b in edges:
        fa, fb = cv(F, corners[a]), cv(F, corners[b])
        m = (fa > 0) != (fb > 0)
        t = np.where(m, fa / (fa - fb + 1e-12), 0)
        pa = base + np.array(corners[a]) * res; pb = base + np.array(corners[b]) * res
        acc += np.where(m[..., None], pa + t[..., None] * (pb - pa), 0); cnt += m
    has = cnt > 0
    V = acc[has] / cnt[has][:, None]
    vid = -np.ones(cs, int); vid[has] = np.arange(has.sum())
    tris = []
    def quads(mask, cells):
        idx = np.argwhere(mask)
        if len(idx) == 0: return
        q = [vid[tuple((idx + off).T)] for off in cells]
        q = np.stack(q, 1)
        tris.append(q[:, [0, 1, 2]]); tris.append(q[:, [0, 2, 3]])
    nx, ny, nz = n
    # x-edges: nodes (i,j,k)-(i+1,j,k), valid j>=1,k>=1
    m = np.zeros((nx - 1, ny, nz), bool); m[:, 1:ny - 1, 1:nz - 1] = (out[:-1, 1:ny - 1, 1:nz - 1] != out[1:, 1:ny - 1, 1:nz - 1])
    quads(m, [(0, -1, -1), (0, 0, -1), (0, 0, 0), (0, -1, 0)])
    m = np.zeros((nx, ny - 1, nz), bool); m[1:nx - 1, :, 1:nz - 1] = (out[1:nx - 1, :-1, 1:nz - 1] != out[1:nx - 1, 1:, 1:nz - 1])
    quads(m, [(-1, 0, -1), (0, 0, -1), (0, 0, 0), (-1, 0, 0)])
    m = np.zeros((nx, ny, nz - 1), bool); m[1:nx - 1, 1:ny - 1, :] = (out[1:nx - 1, 1:ny - 1, :-1] != out[1:nx - 1, 1:ny - 1, 1:])
    quads(m, [(-1, -1, 0), (0, -1, 0), (0, 0, 0), (-1, 0, 0)])
    T = np.vstack(tris)
    return V, T

def grad(P, eps=0.01):
    e = np.eye(3) * eps
    g = np.stack([sdf(P + e[i]) - sdf(P - e[i]) for i in range(3)], -1)
    return g / np.maximum(np.linalg.norm(g, axis=-1, keepdims=True), 1e-9)

def fix_winding(V, T, N):
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    ng = np.cross(b - a, c - a)
    nv = N[T[:, 0]] + N[T[:, 1]] + N[T[:, 2]]
    flip = (ng * nv).sum(1) < 0
    T = T.copy(); T[flip] = T[flip][:, [0, 2, 1]]
    return T

def laplace(V, T, it=1, w=0.5):
    for _ in range(it):
        acc = np.zeros_like(V); cnt = np.zeros(len(V))
        for i, j in ((0, 1), (1, 2), (2, 0)):
            np.add.at(acc, T[:, i], V[T[:, j]]); np.add.at(cnt, T[:, i], 1)
            np.add.at(acc, T[:, j], V[T[:, i]]); np.add.at(cnt, T[:, j], 1)
        m = cnt > 0
        V = V.copy(); V[m] = V[m] * (1 - w) + (acc[m] / cnt[m][:, None]) * w
    return V


# ------------------------------------------------------------------ painting (cartoon markings)
C = lambda h: np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], float) / 255
ORANGE, LIGHT, DEEP, CREAM, BROWN, NOSE = C("#F28A26"), C("#FFA63E"), C("#C25312"), C("#FFF2DA"), C("#46281A"), C("#241512")
GLOW_LO, GLOW_HI = C("#FF6A14"), C("#FFD14D")
def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a * (1 - t[..., None]) + b * t[..., None]
def hashnoise(P, f):
    s = np.sin(P @ np.array([12.9898, 78.233, 37.719]) * f) * 43758.5453
    return s - np.floor(s)

EYE_POS = [np.array([s * .40, 2.12, -1.90]) for s in (-1, 1)]

def paint(P, N, g):
    n = len(P); x, y, z = P[:, 0], P[:, 1], P[:, 2]
    isg = lambda *ids: np.isin(g, [G[i] for i in ids]).astype(float)
    T = lambda c: np.tile(c, (n, 1))
    col = lerp(T(ORANGE), T(LIGHT), np.clip(N[:, 1], 0, 1) * 0.55)
    # cartoon stripes over back, flanks and tail
    f = (z * 2.1 + 0.15) % 1.0
    stripe_body = sstep(0.0, 0.05, f) * sstep(0.38, 0.33, f) * sstep(-0.15, 0.15, N[:, 1]) * isg("body", "neck", "legH")
    ft = (z * 1.6 + y * 1.5) % 1.0
    stripe_tail = sstep(0.0, 0.05, ft) * sstep(0.42, 0.37, ft) * isg("tail")
    col = lerp(col, T(DEEP), np.maximum(stripe_body, stripe_tail) * 0.95)
    cream = np.zeros(n); mx = np.maximum
    cream = mx(cream, sstep(-0.10, -0.40, N[:, 1]) * isg("body", "legF", "legH", "ruff", "neck"))
    cream = mx(cream, isg("ruff", "cheek"))
    cream = mx(cream, isg("head") * sstep(1.98, 1.78, y))
    cream = mx(cream, isg("snout") * sstep(0.45, -0.05, N[:, 1]))
    cream = mx(cream, isg("ear") * sstep(-0.05, -0.45, N[:, 2]) * sstep(2.8, 2.95, y) * sstep(3.5, 3.3, y))
    cream = mx(cream, isg("tail") * sstep(2.62, 2.9, y))          # pale tip under the crystal flame
    col = lerp(col, T(CREAM), cream)
    dark = isg("ear") * mx(sstep(0.05, 0.5, N[:, 2]) * sstep(2.75, 2.95, y), sstep(3.45, 3.62, y))
    dark = mx(dark, isg("legF", "legH") * sstep(0.46, 0.24, y))
    col = lerp(col, T(BROWN), dark)
    for e in EYE_POS:                                              # dark eye-ring so the glowing eyes pop
        d = np.linalg.norm((P - e) * np.array([1.0, 0.9, 1.4]), axis=1)
        col = lerp(col, T(BROWN), sstep(0.34, 0.27, d) * isg("head", "cheek", "snout"))
    col = lerp(col, T(NOSE), isg("snout") * sstep(-2.20, -2.30, z))
    col = np.clip(col, 0, 1)
    return col, np.zeros(n)

def ao_at(P, N, h=0.12):
    occ = 0
    for i, w in ((1, 1.0), (2, 0.5), (3, 0.25)):
        occ += w * np.maximum(i * h - sdf(P + N * i * h), 0) / (i * h)
    return np.clip(1 - 0.8 * occ / 1.75, 0.38, 1)

def project_to_surface(p, it=4):
    p = np.array(p, float)
    for _ in range(it):
        d = sdf(p[None])[0]; g = grad(p[None])[0]; p = p - g * d
    return p, grad(p[None])[0]

# ------------------------------------------------------------------ crystals, face details
def crystal(base, direction, L, r, sides=6, twist=0.5):
    d = np.array(direction, float); d /= np.linalg.norm(d)
    u = np.cross(d, [0, 1, 0]); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-3 else np.array([1, 0, 0]); w = np.cross(d, u)
    rings = [(-0.04, 0.78 * r, 0.0), (0.28, 1.0 * r, 0.0), (0.68, 0.46 * r, twist)]
    V, Cc, F = [], [], []
    for (t, rad, tw) in rings:
        for k in range(sides):
            a = 2 * math.pi * k / sides + tw
            V.append(np.array(base) + d * (L * t) + (u * math.cos(a) + w * math.sin(a)) * rad)
            Cc.append(GLOW_LO + (GLOW_HI - GLOW_LO) * max(t, 0) ** 0.8)
    V.append(np.array(base) + d * L); Cc.append(GLOW_HI)
    tip = len(V) - 1
    for ri in range(2):
        for k in range(sides):
            a, b = ri * sides + k, ri * sides + (k + 1) % sides
            c, dd = (ri + 1) * sides + k, (ri + 1) * sides + (k + 1) % sides
            F += [[a, b, dd], [a, dd, c]]
    for k in range(sides): F.append([2 * sides + k, 2 * sides + (k + 1) % sides, tip])
    return np.array(V), np.array(F), np.array(Cc)

def orient_out(V, F):
    cen = V.mean(0); A, B, Cc = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    flip = (np.cross(B - A, Cc - A) * ((A + B + Cc) / 3 - cen)).sum(1) < 0
    F = F.copy(); F[flip] = F[flip][:, [0, 2, 1]]; return F

def crystals():
    out = []
    def add(approx, dirhint, L, r, blend=0.5, sides=6, snap=True):
        p, n = project_to_surface(approx) if snap else (np.array(approx, float), np.array([0, 1, 0.0]))
        d = np.array(dirhint, float); d /= np.linalg.norm(d); d = d * (1 - blend) + n * blend; d /= np.linalg.norm(d)
        V, F, Cc = crystal(p - n * 0.05, d, L, r, sides, twist=rng.random() * 0.8)
        out.append((V, orient_out(V, F), Cc))
    for z in np.linspace(-0.55, 0.95, 8):                           # spine
        add((0, 2.0, z), (0, 0.8, 0.6), 0.55 + 0.4 * math.sin(math.pi * (z + 0.55) / 1.5), 0.14 + 0.03 * math.sin(math.pi * (z + 0.55) / 1.5), 0.45)
    for s in (-1, 1):
        add((s*.66, 1.62, -0.25), (s*0.8, 0.5, 0.4), 0.46, 0.12, 0.35)       # shoulder
        add((s*.62, 1.52, 0.55), (s*0.7, 0.55, 0.5), 0.52, 0.13, 0.35)       # hip
        add((s*.88, 1.92, -1.18), (s*0.9, 0.2, 0.7), 0.50, 0.12, 0.3)        # cheek
        add((s*.80, 1.70, -1.05), (s*0.9, -0.1, 0.8), 0.36, 0.09, 0.3)       # cheek 2
        for dx in (-0.12, 0.0, 0.12):                                         # front claws
            add((s*.37+dx, .10, -.90), (0, -0.15, -1), 0.26, 0.065, 0.1, 5)
        for dx in (-0.12, 0.0, 0.12):                                         # hind claws
            add((s*.40+dx, .10, .38), (0, -0.15, -1), 0.26, 0.065, 0.1, 5)
        add((s*.40, 2.70, -1.10), (s*0.2, 1, 0.1), 0.30, 0.08, 0.1)          # crown, beside the ears
    add((0, 2.95, -0.95), (0, 1, 0.1), 0.42, 0.10, 0.1)                       # crown centre
    add((0, 0.62, -1.18), (0, -0.3, -1), 0.38, 0.10, 0.45)                    # chest crystal
    add((0.20, 0.72, -1.08), (0.4, -0.2, -1), 0.28, 0.08, 0.4)
    tip = np.array([0, 3.05, 2.88])                                           # tail flame cluster
    for hint, L, r in (((0, 1, 0), 1.05, 0.20), ((0.5, 1, 0.1), 0.80, 0.16), ((-0.5, 1, 0.1), 0.80, 0.16), ((0, 0.6, 1), 0.60, 0.14), ((0.3, 0.2, 1), 0.46, 0.11), ((-0.3, 0.3, 1), 0.46, 0.11), ((0, 1, -0.5), 0.55, 0.12)):
        add(tip + np.array([0, -0.1, 0.0]), hint, L, r, 0.0, 6, snap=False)
    return out

def ell(center, radii, rotation=(0, 0, 0), n_lat=10, n_lon=14):
    verts = [[0, 1, 0]]
    for i in range(1, n_lat):
        v = math.pi * i / n_lat
        for j in range(n_lon):
            u = 2 * math.pi * j / n_lon
            verts.append([math.sin(v) * math.cos(u), math.cos(v), math.sin(v) * math.sin(u)])
    verts.append([0, -1, 0]); U = np.array(verts)
    a, b, c = map(math.radians, rotation)
    Rx = np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
    Rz = np.array([[math.cos(c),-math.sin(c),0],[math.sin(c),math.cos(c),0],[0,0,1]])
    R = Rz @ Rx
    V = (U * np.array(radii)) @ R.T + np.array(center)
    Nn = (U / np.array(radii)); Nn = Nn @ R.T; Nn /= np.linalg.norm(Nn, axis=1, keepdims=True)
    F = []
    for j in range(n_lon): F.append([0, 1 + j, 1 + (j + 1) % n_lon])
    for i in range(n_lat - 2):
        a0 = 1 + i * n_lon; b0 = 1 + (i + 1) * n_lon
        for j in range(n_lon):
            j2 = (j + 1) % n_lon; F.append([a0 + j, b0 + j, b0 + j2]); F.append([a0 + j, b0 + j2, a0 + j2])
    last = len(V) - 1; base = 1 + (n_lat - 2) * n_lon
    for j in range(n_lon): F.append([last, base + (j + 1) % n_lon, base + j])
    F = np.array(F); F = orient_out(V, F)
    return V, F, Nn

def cone(base, direction, L, r, sides=6):
    d = np.array(direction, float); d /= np.linalg.norm(d)
    u = np.cross(d, [0, 1, 0]); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-3 else np.array([1, 0, 0]); w = np.cross(d, u)
    V = [np.array(base) + (u * math.cos(2 * math.pi * k / sides) + w * math.sin(2 * math.pi * k / sides)) * r for k in range(sides)] + [np.array(base) + d * L]
    F = np.array([[k, (k + 1) % sides, sides] for k in range(sides)])
    return np.array(V), orient_out(np.array(V), F)

def face_parts():
    P = []
    def smooth(V, F, N, col, emit=0.0, spec=0.0): P.append(dict(V=V, T=F, C=np.tile(col, (len(V), 1)), N=N, ao=np.ones(len(V)), emit=np.full(len(V), emit), spec=np.full(len(V), spec), flat=False))
    def flat(V, F, col, emit=0.0): P.append(dict(V=V, T=F, C=np.tile(col, (len(V), 1)), N=None, ao=np.ones(len(V)), emit=np.full(len(V), emit), spec=np.zeros(len(V)), flat=True))
    for s in (-1, 1):
        ex, ey, ez = s * .40, 2.12, -1.90
        smooth(*ell((ex, ey, ez - .01), (.25, .29, .12), (0, 0, -s*14)), BROWN)                           # outline ring
        smooth(*ell((ex, ey, ez - .075), (.20, .245, .10), (0, 0, -s*14)), C("#FFB52E"), emit=0.75, spec=0.5)   # glowing iris
        smooth(*ell((ex + s*.01, ey - .01, ez - .15), (.075, .17, .05), (0, 0, -s*14)), C("#140B07"))         # pupil
        smooth(*ell((ex - s*.05, ey + .10, ez - .17), (.05, .055, .03), (0, 0, 0), 6, 8), C("#FFFFFF"), emit=1.0, spec=1.0)  # catch-light
        smooth(*ell((ex + s*.05, ey - .12, ez - .17), (.025, .028, .02), (0, 0, 0), 5, 6), C("#FFFFFF"), emit=1.0, spec=1.0)
        V, F, N = ell((ex, ey + .34, ez + .03), (.26, .065, .11), (0, 0, s*18), 7, 10); flat(V, F, BROWN)    # brow
        for dx in (.12, .26):                                                                                   # small fangs
            V, F = cone((s*dx, 1.64, -2.10), (s*0.05, -1, -0.15), .20, .055, 5); flat(V, F, CREAM)
    V, F, N = ell((0, 1.92, -2.13), (.17, .12, .13), (0, 0, 0), 7, 10); flat(V, F, NOSE)                      # nose
    return P

# ------------------------------------------------------------------ build
def fib_dirs(n):
    i = np.arange(n) + 0.5; phi = math.pi * (3 - math.sqrt(5)) * i; y = 1 - 2 * i / n; r = np.sqrt(1 - y * y)
    return np.stack([np.cos(phi) * r, y, np.sin(phi) * r], 1)
FACET_DIRS = fib_dirs(26)

def unweld(p):
    if not p.get("flat"): return p
    V, T = p["V"], p["T"]
    Vt = V[T].reshape(-1, 3); Tt = np.arange(len(Vt)).reshape(-1, 3)
    Cc = p["C"][T]
    if p.get("quant"): Cc = np.repeat(Cc.mean(1, keepdims=True), 3, axis=1)      # one flat colour per facet
    return dict(V=Vt, T=Tt, C=Cc.reshape(-1, 3), N=None, ao=np.repeat(p["ao"][T].mean(1), 3), emit=p["emit"][T].reshape(-1), spec=p["spec"][T].reshape(-1), flat=True, quant=p.get("quant", False))

def flat_normals(p):
    V, T = p["V"], p["T"]
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-9)
    if p.get("quant"): fn = FACET_DIRS[np.argmax(fn @ FACET_DIRS.T, axis=1)]          # snap to gem-cut facet directions
    N = np.zeros_like(V)
    for k in range(3): N[T[:, k]] = fn
    return N

def build(res, smooth_it, name):
    t0 = time.time()
    V, T = surface_nets(res, lo=(-1.2, -0.1, -2.7), hi=(1.2, 4.3, 4.1))
    V = laplace(V, T, smooth_it, 0.5)
    N = grad(V); T = fix_winding(V, T, N)
    g = labels(V); col, emit = paint(V, N, g); ao = ao_at(V, N)
    body = dict(V=V, T=T, C=col, N=N, ao=ao, emit=emit, spec=np.zeros(len(V)), flat=True, quant=True)
    parts = [body]
    for (cV, cF, cC) in crystals():
        emit_c = np.full(len(cV), 0.9)
        parts.append(dict(V=cV, T=cF, C=cC, N=None, ao=np.ones(len(cV)), emit=emit_c, spec=np.full(len(cV), 0.6), flat=True))
    parts += face_parts()
    parts = [unweld(p) for p in parts]
    for p in parts:
        if p.get("N") is None: p["N"] = flat_normals(p)
    print(f"[{name}] res={res} tris={sum(len(p['T']) for p in parts)} body_tris={len(T)} ({time.time()-t0:.1f}s)")
    return parts

def merge(parts):
    off, V, T, Cc, N, ao, em, sp = 0, [], [], [], [], [], [], []
    for p in parts:
        V.append(p["V"]); T.append(p["T"] + off); Cc.append(p["C"]); N.append(p["N"]); ao.append(p["ao"]); em.append(p["emit"]); sp.append(p["spec"]); off += len(p["V"])
    return [np.vstack(x) for x in (V, T, Cc, N)] + [np.concatenate(ao), np.concatenate(em), np.concatenate(sp)]

def write_ply(path, V, T, Cc):
    with open(path, "w") as f:
        f.write(f"ply\nformat ascii 1.0\nelement vertex {len(V)}\nproperty float x\nproperty float y\nproperty float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nelement face {len(T)}\nproperty list uchar int vertex_indices\nend_header\n")
        for v, c in zip(V, (Cc * 255).astype(int)): f.write("%.4f %.4f %.4f %d %d %d\n" % (*v, *c))
        for t in T: f.write("3 %d %d %d\n" % tuple(t))

def write_obj(path, V, T, Cc, N, with_vc=True):
    with open(path, "w") as f:
        for v, c in zip(V, Cc): f.write(("v %.4f %.4f %.4f %.3f %.3f %.3f\n" % (*v, *c)) if with_vc else ("v %.4f %.4f %.4f\n" % tuple(v)))
        for n in N: f.write("vn %.3f %.3f %.3f\n" % tuple(n))
        for t in T: f.write("f %d//%d %d//%d %d//%d\n" % (t[0]+1, t[0]+1, t[1]+1, t[1]+1, t[2]+1, t[2]+1))

PALETTE = {"orange": ORANGE, "light_orange": LIGHT, "deep_orange": DEEP, "cream": CREAM, "brown": BROWN, "nose": NOSE, "crystal_orange": GLOW_LO, "crystal_yellow": GLOW_HI, "eye_amber": C("#FFB52E"), "eye_pupil": C("#140B07")}
def write_color_split(dirpath, V, T, Cc, N):
    os.makedirs(dirpath, exist_ok=True)
    names = list(PALETTE); pal = np.stack([PALETTE[n] for n in names])
    tc = Cc[T].mean(1); idx = np.argmin(((tc[:, None, :] - pal[None]) ** 2).sum(-1), 1)
    info = {}
    for i, n in enumerate(names):
        sel = T[idx == i]
        if len(sel) == 0: continue
        used = np.unique(sel); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
        write_obj(f"{dirpath}/{n}.obj", V[used], remap[sel], Cc[used], N[used], with_vc=False)
        info[n] = {"color_rgb": [int(round(x * 255)) for x in PALETTE[n]], "triangles": int(len(sel))}
    json.dump({"note": "Import all .obj files with the same origin; set each MeshPart.Color3 to color_rgb. Use Neon material for crystal_* and eye_amber.", "parts": info}, open(f"{dirpath}/colors.json", "w"), indent=1)
    return info

def rot(rx=0, ry=0, rz=0):
    a, b, c = map(math.radians, (rx, ry, rz))
    Rx = np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
    Ry = np.array([[math.cos(b),0,math.sin(b)],[0,1,0],[-math.sin(b),0,math.cos(b)]])
    Rz = np.array([[math.cos(c),-math.sin(c),0],[math.sin(c),math.cos(c),0],[0,0,1]])
    return Rz @ Ry @ Rx


def render(parts, yaw, pitch=-8, size=900, ss=2):
    V, T, Cc, N, ao, em, sp = merge(parts)
    S = size * ss; R = rot(pitch, yaw, 0)
    P0 = V @ R.T; pmin, pmax = P0.min(0), P0.max(0); pc = (pmin + pmax) / 2
    scale = S * 0.86 / max(pmax[0] - pmin[0], pmax[1] - pmin[1])
    proj = lambda Q: np.stack([S / 2 + (Q[..., 0] - pc[0]) * scale, S * 0.50 - (Q[..., 1] - pc[1]) * scale], -1)
    Nv = N @ R.T; XY = proj(P0); X, Y = XY[:, 0], XY[:, 1]; Z = P0[:, 2]
    A = np.concatenate([Cc, Nv, ao[:, None], em[:, None], sp[:, None]], 1).astype(np.float32)
    zb = np.full((S, S), -1e9, np.float32); buf = np.zeros((S, S, A.shape[1]), np.float32); mk = np.zeros((S, S), bool)
    fn = np.cross(P0[T[:, 1]] - P0[T[:, 0]], P0[T[:, 2]] - P0[T[:, 0]])
    for t in np.flatnonzero(fn[:, 2] > 0):
        a, b, c = T[t]
        xs = X[[a, b, c]]; ys = Y[[a, b, c]]
        x0, x1 = int(max(0, math.floor(xs.min()))), int(min(S - 1, math.ceil(xs.max())))
        y0, y1 = int(max(0, math.floor(ys.min()))), int(min(S - 1, math.ceil(ys.max())))
        if x1 < x0 or y1 < y0: continue
        d = (Y[b] - Y[c]) * (X[a] - X[c]) + (X[c] - X[b]) * (Y[a] - Y[c])
        if abs(d) < 1e-9: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((Y[b] - Y[c]) * (gx - X[c]) + (X[c] - X[b]) * (gy - Y[c])) / d
        w1 = ((Y[c] - Y[a]) * (gx - X[c]) + (X[a] - X[c]) * (gy - Y[c])) / d
        w2 = 1 - w0 - w1
        ins = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not ins.any(): continue
        z = w0 * Z[a] + w1 * Z[b] + w2 * Z[c]
        sub = zb[y0:y1 + 1, x0:x1 + 1]; upd = ins & (z > sub)
        if not upd.any(): continue
        attr = w0[..., None] * A[a] + w1[..., None] * A[b] + w2[..., None] * A[c]
        sub[upd] = z[upd]; buf[y0:y1 + 1, x0:x1 + 1][upd] = attr[upd]; mk[y0:y1 + 1, x0:x1 + 1][upd] = True
    col = buf[..., 0:3]; n = buf[..., 3:6]; n = n / np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-6)
    aoo = buf[..., 6:7]; emi = buf[..., 7:8]; spc = buf[..., 8:9]
    nrm = lambda v: np.array(v) / np.linalg.norm(v)
    key, fill, rimd = nrm([-0.5, 0.65, 0.6]), nrm([0.7, 0.2, 0.4]), nrm([0.2, 0.35, -0.9])
    lam = lambda L: np.clip(n @ L, 0, 1)[..., None]
    hemi = 0.30 + 0.25 * (n[..., 1:2] * 0.5 + 0.5)
    lit = col * (hemi * aoo * np.array([0.85, 0.9, 1.1]) + lam(key) * np.array([1.0, 0.92, 0.82]) * (0.6 + 0.4 * aoo) + lam(fill) * np.array([0.45, 0.55, 0.85]) * 0.28)
    lit += (lam(rimd) ** 1.5) * np.array([0.35, 0.65, 1.0]) * 0.55 * aoo
    H = nrm(key + np.array([0, 0, 1.0])); lit += (np.clip(n @ H, 0, 1)[..., None] ** 30) * spc * 0.9
    lit = lit * (1 - emi) + (col * (0.78 + 0.60 * lam(key) + 0.25 * lam(fill)) * 1.10) * emi
    lit = np.clip(lit, 0, 1.6); lit = lit / (1 + 0.15 * lit); lit = np.clip(lit * 1.10, 0, 1)
    yy = np.linspace(0, 1, S)[:, None, None]; xx = np.linspace(-1, 1, S)[None, :, None]
    bg = (1 - yy) * np.array([0.03, 0.05, 0.11]) + yy * np.array([0.07, 0.10, 0.20]); bg = bg + 0.05 * np.clip(1 - (xx ** 2 + (yy - 0.55) ** 2 * 1.6), 0, 1) * np.array([0.5, 0.6, 1.0])
    bg = np.broadcast_to(bg, (S, S, 3)).copy()
    ring = [R @ np.array([1.25 * math.cos(t), 0.0, 0.8 + 2.9 * math.sin(t)]) for t in np.linspace(0, 2 * math.pi, 60)]
    gl = Image.new("L", (S, S), 0); ImageDraw.Draw(gl).polygon([tuple(proj(q)) for q in ring], fill=255)
    gl = np.asarray(gl.filter(ImageFilter.GaussianBlur(S * 0.03)), float)[..., None] / 255
    bg = bg + gl * np.array([0.55, 0.28, 0.08]) * 0.55
    out = np.where(mk[..., None], lit, bg)
    # bloom on emissive pixels (crystals, eyes)
    src = np.where(mk[..., None], lit * emi * 0.9, 0); simg = Image.fromarray((np.clip(src, 0, 1) * 255).astype(np.uint8))
    b1 = np.asarray(simg.filter(ImageFilter.GaussianBlur(S * 0.006)), float) / 255; b2 = np.asarray(simg.filter(ImageFilter.GaussianBlur(S * 0.022)), float) / 255
    out = out + 0.30 * b1 + 0.50 * b2
    out = np.clip(out, 0, 1) ** (1 / 1.04)
    return Image.fromarray((out * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)

# ------------------------------------------------------------------ main
if __name__ == "__main__":
    hero = build(0.10 if not FAST else 0.14, 5, "hero")
    V, T, Cc, N, *_ = merge(hero)
    write_ply(f"{OUT}/ember_fox_v3.ply", V, T, Cc); write_obj(f"{OUT}/ember_fox_v3.obj", V, T, Cc, N, with_vc=True)
    info = write_color_split(f"{OUT}/roblox_parts", V, T, Cc, N)
    json.dump({"units": "studs", "forward": "-Z", "up": "+Y", "triangles": int(len(T)), "colour_parts": info}, open(f"{OUT}/model_info.json", "w"), indent=1)
    t0 = time.time(); views = []
    for yaw, pitch in ((150, -8), (80, -4), (215, -8)):
        views.append(render(hero, yaw, pitch, size=900, ss=2)); print("rendered", yaw, f"{time.time()-t0:.0f}s")
    sheet = Image.new("RGB", (900 * 3, 900))
    for i, v in enumerate(views): sheet.paste(v, (i * 900, 0))
    sheet.save(f"{OUT}/preview.png"); views[0].save(f"{OUT}/hero_front34.png")
    print("done")
