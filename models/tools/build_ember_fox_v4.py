#!/usr/bin/env python3
"""Ember Fox v4: cute chibi Roblox-cartoon fox (big glossy eyes, blush, soft shading, small gems) (numpy + PIL only).
Style reference: faceted low-poly creature with glowing crystal spikes, striped markings, big expressive head.
Units: studs. Faces -Z (Roblox LookVector), Y up.
Usage: python3 build_ember_fox_v4.py OUT_DIR [--fast]
"""
import json, math, os, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
OUT = sys.argv[1] if len(sys.argv) > 1 else "ember_fox_v4"
FAST = "--fast" in sys.argv
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(11)

# ------------------------------------------------------------------ SDF anatomy (cute chibi proportions)
G = dict(body=0, neck=1, head=2, snout=3, ear=4, legF=5, legH=6, tail=7, cheek=8, ruff=9)
PRIMS = []
def P_(g, a, b, ra, rb, scale=(1, 1, 1), k=0.2): PRIMS.append((G[g], np.array(a, float), np.array(b, float), ra, rb, np.array(scale, float), k))

P_("body", (0,1.02,-0.20), (0,0.98,0.45), .64, .60, k=0.0)
P_("body", (0,0.98,0.45), (0,0.95,0.80), .60, .55, k=0.30)
P_("ruff", (0,0.80,-0.62), (0,0.72,-0.50), .42, .40, k=0.25)
P_("neck", (0,1.40,-0.55), (0,1.75,-0.85), .52, .50, k=0.30)
P_("head", (0,1.96,-0.95), (0,1.88,-1.15), .95, .88, k=0.25)
P_("snout",(0,1.70,-1.78), (0,1.64,-2.00), .30, .24, k=0.20)
for s in (-1, 1):
    P_("cheek", (s*.60,1.66,-1.10), (s*.68,1.60,-1.22), .38, .34, k=0.20)
    P_("ear",   (s*.52,2.62,-.85), (s*.84,3.40,-.76), .40, .16, scale=(1,1,2.0), k=0.10)
    P_("legF", (s*.34,.82,-.35), (s*.34,.32,-.42), .31, .26, k=0.20)
    P_("legF", (s*.34,.32,-.42), (s*.34,.15,-.52), .26, .28, k=0.10)
    P_("legH", (s*.40,.86,.46), (s*.38,.36,.56), .37, .29, k=0.20)
    P_("legH", (s*.38,.36,.56), (s*.38,.15,.50), .29, .30, k=0.10)
tail_pts = [((0,1.02,.78),.26), ((0,1.08,1.35),.50), ((0,1.42,1.95),.62), ((0,1.92,2.30),.56), ((0,2.42,2.46),.44), ((0,2.84,2.46),.30)]
for i in range(len(tail_pts) - 1):
    P_("tail", tail_pts[i][0], tail_pts[i+1][0], tail_pts[i][1], tail_pts[i+1][1], k=0.28 if i == 0 else 0.20)

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


# ------------------------------------------------------------------ painting (soft, friendly)
C = lambda h: np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], float) / 255
ORANGE, LIGHT, DEEP, CREAM, BROWN, NOSE = C("#FF8420"), C("#FFA24A"), C("#EE6414"), C("#FFF4E0"), C("#7A4528"), C("#2A1A1A")
BLUSH = C("#FF8FA3")
GLOW_LO, GLOW_HI = C("#FF8A2A"), C("#FFE27A")
def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a * (1 - t[..., None]) + b * t[..., None]
def hashnoise(P, f):
    s = np.sin(P @ np.array([12.9898, 78.233, 37.719]) * f) * 43758.5453
    return s - np.floor(s)

def paint(P, N, g):
    n = len(P); x, y, z = P[:, 0], P[:, 1], P[:, 2]
    isg = lambda *ids: np.isin(g, [G[i] for i in ids]).astype(float)
    T = lambda c: np.tile(c, (n, 1))
    col = lerp(T(ORANGE), T(LIGHT), np.clip(N[:, 1], 0, 1) * 0.6)
    ft = (z * 1.5 + y * 1.4) % 1.0                                          # soft tail stripes only
    stripe_tail = sstep(0.0, 0.10, ft) * sstep(0.46, 0.34, ft) * isg("tail")
    col = lerp(col, T(DEEP), sstep(1.4, 2.3, z) * isg("tail") * 0.55)
    cream = np.zeros(n); mx = np.maximum
    cream = mx(cream, sstep(-0.05, -0.35, N[:, 1]) * isg("body", "legF", "legH", "ruff", "neck"))
    cream = mx(cream, isg("ruff", "cheek"))
    cream = mx(cream, isg("head") * sstep(1.86, 1.62, y))
    cream = mx(cream, isg("snout"))
    cream = mx(cream, isg("ear") * sstep(-0.02, -0.40, N[:, 2]) * sstep(2.72, 2.88, y) * sstep(3.32, 3.18, y))
    cream = mx(cream, isg("tail") * sstep(2.34, 2.62, y))
    col = lerp(col, T(CREAM), cream)
    dark = isg("ear") * sstep(3.30, 3.42, y) * 0.8
    dark = mx(dark, isg("legF", "legH") * sstep(0.40, 0.20, y))
    col = lerp(col, T(BROWN), dark)
    for s in (-1, 1):                                                       # pink blush
        d = np.linalg.norm((P - np.array([s * .70, 1.72, -1.52])) * np.array([1.0, 1.5, 1.0]), axis=1)
        col = lerp(col, T(BLUSH), sstep(0.30, 0.14, d) * 0.85 * isg("head", "cheek"))
    return np.clip(col, 0, 1), np.zeros(n)

def ao_at(P, N, h=0.12):
    occ = 0
    for i, w in ((1, 1.0), (2, 0.5), (3, 0.25)):
        occ += w * np.maximum(i * h - sdf(P + N * i * h), 0) / (i * h)
    return np.clip(1 - 0.6 * occ / 1.75, 0.55, 1)

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
    def add(approx, dirhint, L, r, blend=0.5, sides=5, snap=True):
        p, n = project_to_surface(approx) if snap else (np.array(approx, float), np.array([0, 1, 0.0]))
        d = np.array(dirhint, float); d /= np.linalg.norm(d); d = d * (1 - blend) + n * blend; d /= np.linalg.norm(d)
        V, F, Cc = crystal(p - n * 0.05, d, L, r, sides, twist=rng.random() * 0.8)
        out.append((V, orient_out(V, F), Cc))
    for z in (-0.15, 0.15, 0.45, 0.72):                                      # four small gems on the back
        add((0, 1.9, z), (0, 0.9, 0.45), 0.40 + 0.08 * math.sin(math.pi * (z + 0.15) / 0.9), 0.115, 0.5)
    tip = np.array([0, 2.92, 2.46])                                           # small flame-gem cluster on the tail
    for hint, L, r in (((0, 1, 0), 0.92, 0.20), ((0.55, 1, 0.1), 0.68, 0.16), ((-0.55, 1, 0.1), 0.68, 0.16), ((0, 0.7, 0.8), 0.50, 0.13), ((0, 0.7, -0.8), 0.50, 0.13)):
        add(tip, hint, L, r, 0.0, 5, snap=False)
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
    BLACK = C("#120A0C")
    for s in (-1, 1):
        ex, ey, ez = s * .40, 1.91, -1.86
        smooth(*ell((ex, ey, ez), (.22, .27, .12), (0, 0, -s*5), 12, 16), BLACK, spec=0.9)                    # huge glossy eye
        smooth(*ell((ex - s*.07, ey + .10, ez - .10), (.095, .105, .045), (0, 0, 0), 8, 10), C("#FFFFFF"), emit=0.9, spec=1.0)   # big sparkle
        smooth(*ell((ex + s*.08, ey - .11, ez - .10), (.045, .05, .03), (0, 0, 0), 6, 8), C("#FFFFFF"), emit=0.9, spec=1.0)      # small sparkle
        smooth(*ell((ex + s*.02, ey - .02, ez - .105), (.15, .19, .035), (0, 0, 0), 8, 10), C("#3B2420"), spec=0.6)             # warm brown iris ring
    smooth(*ell((0, 1.73, -2.19), (.125, .095, .10), (0, 0, 0), 8, 12), C("#241415"), spec=0.9)               # button nose
    smooth(*ell((-.04, 1.775, -2.27), (.035, .02, .02), (0, 0, 0), 5, 6), C("#FFFFFF"), emit=0.6, spec=1.0)  # nose shine
    # tiny smile: two arcs under the nose
    for s in (-1, 1):
        for t in np.linspace(0.0, 1.0, 7):
            x = s * (0.015 + 0.15 * t); y = 1.585 - 0.045 * math.sin(math.pi * t * 0.85) + 0.02 * t
            base = np.array([x, y - 0.03, -2.12])
            p, n = project_to_surface(base)
            smooth(*ell(p + n * 0.012, (.03, .03, .024), (0, 0, 0), 4, 6), C("#3B2420"))
        # little whisker dots
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
    V, T = surface_nets(res, lo=(-1.3, -0.1, -2.6), hi=(1.3, 4.0, 3.6))
    V = laplace(V, T, smooth_it, 0.5)
    N = grad(V); T = fix_winding(V, T, N)
    g = labels(V); col, emit = paint(V, N, g); ao = ao_at(V, N)
    parts = [dict(V=V, T=T, C=col, N=N, ao=ao, emit=emit, spec=np.full(len(V), 0.08), flat=False)]      # smooth, soft body
    for (cV, cF, cC) in crystals():
        parts.append(dict(V=cV, T=cF, C=cC, N=None, ao=np.ones(len(cV)), emit=np.full(len(cV), 0.55), spec=np.full(len(cV), 0.7), flat=True))
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

PALETTE = {"orange": ORANGE, "light_orange": LIGHT, "deep_orange": DEEP, "cream": CREAM, "brown": BROWN, "blush_pink": BLUSH, "nose_eye_black": C("#120A0C"), "eye_ring": C("#3B2420"), "white": C("#FFFFFF"), "crystal_orange": GLOW_LO, "crystal_yellow": GLOW_HI}
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
    json.dump({"note": "Import all .obj files with the same origin; set each MeshPart.Color3 to color_rgb. Use Neon material for crystal_*; use SmoothPlastic with high reflectance for the eyes.", "parts": info}, open(f"{dirpath}/colors.json", "w"), indent=1)
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
    key, fill, rimd = nrm([-0.45, 0.70, 0.60]), nrm([0.7, 0.3, 0.5]), nrm([0.2, 0.40, -0.9])
    lam = lambda L: np.clip(n @ L, 0, 1)[..., None]
    hemi = 0.44 + 0.22 * (n[..., 1:2] * 0.5 + 0.5)
    lit = col * (hemi * aoo * np.array([0.85, 0.9, 1.1]) + lam(key) * np.array([1.0, 0.96, 0.90]) * 0.78 * (0.55 + 0.45 * aoo) + lam(fill) * np.array([1.0, 0.90, 0.82]) * 0.20)
    lit += (lam(rimd) ** 1.5) * np.array([1.0, 0.9, 0.8]) * 0.22 * aoo
    H = nrm(key + np.array([0, 0, 1.0])); lit += (np.clip(n @ H, 0, 1)[..., None] ** 30) * spc * 0.9
    lit = lit * (1 - emi) + (col * (0.78 + 0.60 * lam(key) + 0.25 * lam(fill)) * 1.10) * emi
    lit = np.clip(lit, 0, 1.6); lit = lit / (1 + 0.10 * lit); lit = np.clip(lit * 1.04, 0, 1)
    yy = np.linspace(0, 1, S)[:, None, None]; xx = np.linspace(-1, 1, S)[None, :, None]
    bg = (1 - yy) * np.array([0.74, 0.86, 1.00]) + yy * np.array([0.96, 0.93, 0.98])
    bg = bg + 0.10 * np.clip(1 - (xx ** 2 + (yy - 0.55) ** 2 * 1.4), 0, 1) * np.array([1.0, 0.95, 0.8])
    bg = np.broadcast_to(bg, (S, S, 3)).copy()
    ring = [R @ np.array([1.25 * math.cos(t), 0.0, 0.55 + 2.5 * math.sin(t)]) for t in np.linspace(0, 2 * math.pi, 60)]
    gl = Image.new("L", (S, S), 0); ImageDraw.Draw(gl).polygon([tuple(proj(q)) for q in ring], fill=255)
    gl = np.asarray(gl.filter(ImageFilter.GaussianBlur(S * 0.022)), float)[..., None] / 255
    bg = bg * (1 - 0.30 * gl)
    out = np.where(mk[..., None], lit, bg)
    # bloom on emissive pixels (crystals, eyes)
    src = np.where(mk[..., None], lit * emi * 0.9, 0); simg = Image.fromarray((np.clip(src, 0, 1) * 255).astype(np.uint8))
    b1 = np.asarray(simg.filter(ImageFilter.GaussianBlur(S * 0.006)), float) / 255; b2 = np.asarray(simg.filter(ImageFilter.GaussianBlur(S * 0.022)), float) / 255
    out = out + 0.22 * b1 + 0.30 * b2
    out = np.clip(out, 0, 1) ** (1 / 1.04)
    return Image.fromarray((out * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)

# ------------------------------------------------------------------ main
if __name__ == "__main__":
    hero = build(0.075 if not FAST else 0.12, 4, "hero")
    V, T, Cc, N, *_ = merge(hero)
    write_ply(f"{OUT}/ember_fox_v4.ply", V, T, Cc); write_obj(f"{OUT}/ember_fox_v4.obj", V, T, Cc, N, with_vc=True)
    info = write_color_split(f"{OUT}/roblox_parts", V, T, Cc, N)
    json.dump({"units": "studs", "forward": "-Z", "up": "+Y", "triangles": int(len(T)), "colour_parts": info}, open(f"{OUT}/model_info.json", "w"), indent=1)
    t0 = time.time(); views = []
    for yaw, pitch in ((150, -8), (80, -4), (215, -8)):
        views.append(render(hero, yaw, pitch, size=900, ss=2)); print("rendered", yaw, f"{time.time()-t0:.0f}s")
    sheet = Image.new("RGB", (900 * 3, 900))
    for i, v in enumerate(views): sheet.paste(v, (i * 900, 0))
    sheet.save(f"{OUT}/preview.png"); views[0].save(f"{OUT}/hero_front34.png")
    print("done")
