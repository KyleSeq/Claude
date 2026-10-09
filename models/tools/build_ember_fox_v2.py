#!/usr/bin/env python3
"""Ember Fox v2: organic signed-distance model -> surface-nets mesh, painted vertex colours, fur tufts.
numpy + PIL only. Units: studs. Faces -Z (Roblox LookVector), Y up.
Outputs hero + game LODs (PLY with vertex colours, OBJ, colour-split OBJs for Roblox) and preview renders.
Usage: python3 build_ember_fox_v2.py OUT_DIR [--fast]
"""
import json, math, os, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else "ember_fox_v2"
FAST = "--fast" in sys.argv
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)

# ------------------------------------------------------------------ SDF anatomy
G = dict(body=0, neck=1, head=2, snout=3, ear=4, legF=5, legH=6, tail=7, cheek=8, ruff=9, flame=10)
PRIMS = []   # (group, a, b, ra, rb, scale(vec), k)
def P_(g, a, b, ra, rb, scale=(1, 1, 1), k=0.2): PRIMS.append((G[g], np.array(a, float), np.array(b, float), ra, rb, np.array(scale, float), k))

P_("body", (0,1.30,-0.55), (0,1.26,0.15), .60, .50, k=0.0)
P_("body", (0,1.26,0.15), (0,1.22,0.85), .50, .53, k=0.30)
P_("neck", (0,1.55,-0.75), (0,1.90,-1.20), .37, .34, k=0.28)
P_("head", (0,2.00,-1.15), (0,1.92,-1.50), .50, .42, k=0.22)
P_("snout",(0,1.86,-1.62), (0,1.70,-2.34), .28, .10, k=0.16)
P_("ruff", (0,1.12,-0.88), (0,0.96,-0.72), .30, .28, k=0.22)
for s in (-1, 1):
    P_("cheek", (s*.34,1.82,-1.40), (s*.42,1.73,-1.58), .22, .19, k=0.12)
    P_("ear",   (s*.34,2.30,-1.20), (s*.62,3.12,-1.06), .22, .035, scale=(1,1,2.4), k=0.07)
    # front leg: shoulder -> elbow -> wrist -> paw
    P_("legF", (s*.27,1.10,-.52), (s*.27,.72,-.55), .24, .17, k=0.16)
    P_("legF", (s*.27,.72,-.55), (s*.27,.20,-.55), .17, .105, k=0.10)
    P_("legF", (s*.27,.20,-.55), (s*.27,.07,-.72), .095, .12, k=0.10)
    # hind leg (digitigrade): thigh -> hock back -> ankle -> paw
    P_("legH", (s*.31,1.15,.78), (s*.32,.78,.50), .30, .17, k=0.18)
    P_("legH", (s*.32,.78,.50), (s*.30,.55,.96), .17, .11, k=0.10)
    P_("legH", (s*.30,.55,.96), (s*.28,.18,.92), .11, .085, k=0.10)
    P_("legH", (s*.28,.18,.92), (s*.28,.07,.76), .085, .12, k=0.10)
tail_pts = [((0,1.28,.90),.18), ((0,1.35,1.60),.38), ((0,1.52,2.30),.53), ((0,1.88,2.90),.50), ((0,2.42,3.30),.34), ((0,2.95,3.48),.15), ((0,3.35,3.42),.04)]
for i in range(len(tail_pts) - 1):
    P_("tail", tail_pts[i][0], tail_pts[i+1][0], tail_pts[i][1], tail_pts[i+1][1], k=0.25 if i == 0 else 0.15)
P_("flame", (0,3.20,3.46), (0,3.80,3.40), .12, .01, k=0.10)
P_("flame", (-.08,3.12,3.48), (-.24,3.62,3.50), .09, .01, k=0.08)
P_("flame", ( .08,3.12,3.48), ( .24,3.60,3.48), .09, .01, k=0.08)

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

# ------------------------------------------------------------------ painting
C = lambda h: np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], float) / 255
ORANGE, DEEP, CREAM, BROWN, NOSE = C("#E8791E"), C("#C4560F"), C("#FFF0D6"), C("#3A241A"), C("#1E1412")
FLAME_O, FLAME_Y = C("#FF6A14"), C("#FFC93C")
def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a * (1 - t[..., None]) + b * t[..., None]
def hashnoise(P, f):
    s = np.sin(P @ np.array([12.9898, 78.233, 37.719]) * f) * 43758.5453
    return s - np.floor(s)

def paint(P, N, g):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    isg = lambda *ids: np.isin(g, [G[i] for i in ids]).astype(float)
    col = np.tile(ORANGE, (len(P), 1))
    col = lerp(col, np.tile(DEEP, (len(P), 1)), (np.clip(N[:, 1] * 0.5 + 0.5, 0, 1) ** 2) * 0.55)
    cream = np.zeros(len(P))
    mx = np.maximum
    cream = mx(cream, sstep(-0.05, -0.45, N[:, 1]) * isg("body", "legH", "legF", "ruff", "neck"))
    cream = mx(cream, isg("ruff")); cream = mx(cream, isg("cheek"))
    cream = mx(cream, isg("head") * sstep(1.88, 1.74, y))
    cream = mx(cream, isg("snout") * sstep(0.55, 0.0, N[:, 1]))
    cream = mx(cream, isg("body", "neck") * sstep(-0.3, -0.75, N[:, 2]) * sstep(1.50, 1.22, y))
    cream = mx(cream, isg("ear") * sstep(-0.1, -0.5, N[:, 2]) * sstep(2.38, 2.52, y) * sstep(2.80, 2.64, y))
    col = lerp(col, np.tile(CREAM, (len(P), 1)), cream)
    dark = mx(isg("ear") * sstep(0.1, 0.6, N[:, 2]) * sstep(2.34, 2.5, y), isg("ear") * sstep(2.66, 2.86, y))
    dark = mx(dark, isg("legF", "legH") * sstep(0.68, 0.46, y))
    col = lerp(col, np.tile(BROWN, (len(P), 1)), dark)
    col = lerp(col, np.tile(NOSE, (len(P), 1)), isg("snout") * sstep(-2.13, -2.22, z))
    # dark "tear line" from eye to muzzle
    for s in (-1, 1):
        a = np.array([s * .30, 2.0, -1.62]); b = np.array([s * .20, 1.76, -2.05])
        ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
        d = np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
        col = lerp(col, np.tile(BROWN, (len(P), 1)), sstep(0.07, 0.03, d) * isg("head", "snout", "cheek"))
    s_t = np.clip((z - 1.3) / 2.2, 0, 1)
    tc = lerp(np.tile(ORANGE, (len(P), 1)), np.tile(DEEP, (len(P), 1)), sstep(0.1, 0.5, s_t))
    tc = lerp(tc, np.tile(FLAME_O, (len(P), 1)), sstep(0.55, 0.8, s_t))
    tc = lerp(tc, np.tile(FLAME_Y, (len(P), 1)), sstep(0.82, 1.0, s_t))
    col = lerp(col, tc, isg("tail"))
    col = lerp(col, lerp(np.tile(FLAME_O, (len(P), 1)), np.tile(FLAME_Y, (len(P), 1)), sstep(3.2, 3.7, y)), isg("flame"))
    nz = (hashnoise(P, 3.1) * 0.6 + hashnoise(P, 9.7) * 0.4 - 0.5) * 0.14
    col = np.clip(col * (1 + nz[:, None]), 0, 1)
    emit = np.clip(isg("flame") + isg("tail") * sstep(0.55, 0.9, s_t) * 0.9, 0, 1)
    return col, emit

def ao_at(P, N, h=0.11):
    occ = 0
    for i, w in ((1, 1.0), (2, 0.5), (3, 0.25)):
        occ += w * np.maximum(i * h - sdf(P + N * i * h), 0) / (i * h)
    return np.clip(1 - 0.9 * occ / 1.75, 0.30, 1)

# ------------------------------------------------------------------ extra geometry: fur tufts + eyes
def tufts(V, N, col, gv, count, length, base_r=0.04, groups=("cheek", "ruff", "tail"), weight=None):
    gi = np.isin(gv, [G[x] for x in groups]); idx = np.flatnonzero(gi)
    if len(idx) == 0: return None
    pick = rng.choice(idx, size=min(count, len(idx)), replace=False)
    TV, TT, TC, TN, TE = [], [], [], [], []; off = 0
    for i in pick:
        n = N[i]; flow = np.array([0, -0.25, 1.0]);
        if gv[i] == G["tail"]: flow = np.array([0, 0.45, 1.0])
        d = n * 0.22 + flow / np.linalg.norm(flow) * 0.97; d /= np.linalg.norm(d)
        u = np.cross(d, [0, 1, 0]); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-3 else np.array([1, 0, 0]); w = np.cross(d, u)
        L = length * (1.7 if gv[i] == G["tail"] else 1.0) * (0.7 + 0.6 * rng.random()); r = base_r * (0.8 + 0.4 * rng.random())
        ring = [V[i] - n * 0.02 + (u * math.cos(t) + w * math.sin(t)) * r for t in np.linspace(0, 2 * math.pi, 6, endpoint=False)]
        tip = V[i] + d * L
        TV += ring + [tip]
        for j in range(6): TT.append([off + j, off + (j + 1) % 6, off + 6])
        c0 = col[i]; ctip = np.clip(c0 * 1.1 + 0.03, 0, 1)
        TC += [c0] * 6 + [ctip]; TN += [n] * 6 + [d]
        off += 7
    return np.array(TV), np.array(TT), np.array(TC), np.array(TN)

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
    F = np.array(F)
    cen = V.mean(0); A, B, Cc = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    flip = (np.cross(B - A, Cc - A) * ((A + B + Cc) / 3 - cen)).sum(1) < 0
    F[flip] = F[flip][:, [0, 2, 1]]
    return V, F, Nn

def eyes():
    parts = []
    for s in (-1, 1):
        # amber iris, black slit pupil, white catch-light. Sits in the socket on the head surface.
        parts.append((*ell((s*.285, 2.02, -1.76), (.10, .11, .065), (0, 0, -s*18)), C("#FF9E1F"), 0.9, 0.9))
        parts.append((*ell((s*.292, 2.02, -1.805), (.03, .09, .035), (0, 0, -s*18)), C("#0A0605"), 0.0, 1.0))
        parts.append((*ell((s*.25, 2.085, -1.83), (.032, .034, .024), (0, 0, 0), 6, 8), C("#FFFFFF"), 1.0, 1.0))
    return parts

# ------------------------------------------------------------------ build one LOD
def build(res, tuft_count, tuft_len, smooth=1, name="hero"):
    t0 = time.time()
    V, T = surface_nets(res)
    V = laplace(V, T, smooth, 0.45)
    N = grad(V); T = fix_winding(V, T, N)
    g = labels(V); col, emit = paint(V, N, g); ao = ao_at(V, N)
    parts = [dict(V=V, T=T, C=col, N=N, ao=ao, emit=emit, spec=np.zeros(len(V)))]
    tf = tufts(V, N, col, g, tuft_count, tuft_len) if tuft_count else None
    if tf is not None:
        TV, TT, TC, TN = tf
        parts.append(dict(V=TV, T=TT, C=TC, N=TN, ao=np.full(len(TV), 0.95), emit=np.zeros(len(TV)), spec=np.zeros(len(TV))))
    for (EV, EF, EN, ecol, esp, _) in eyes():
        parts.append(dict(V=EV, T=EF, C=np.tile(ecol, (len(EV), 1)), N=EN, ao=np.ones(len(EV)), emit=np.zeros(len(EV)), spec=np.full(len(EV), esp)))
    print(f"[{name}] res={res} verts={sum(len(p['V']) for p in parts)} tris={sum(len(p['T']) for p in parts)} body_tris={len(T)} ({time.time()-t0:.1f}s)")
    return parts, g

def merge(parts):
    off, V, T, Cc, N, ao, em, sp = 0, [], [], [], [], [], [], []
    for p in parts:
        V.append(p["V"]); T.append(p["T"] + off); Cc.append(p["C"]); N.append(p["N"]); ao.append(p["ao"]); em.append(p["emit"]); sp.append(p["spec"]); off += len(p["V"])
    return [np.vstack(x) if x[0].ndim > 1 else np.concatenate(x) for x in (V, T, Cc, N)] + [np.concatenate(ao), np.concatenate(em), np.concatenate(sp)]

# ------------------------------------------------------------------ export
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

PALETTE = {"orange": ORANGE, "deep_orange": DEEP, "cream": CREAM, "brown": BROWN, "flame_orange": FLAME_O, "flame_yellow": FLAME_Y, "amber_eye": C("#FF9E1F"), "white": C("#FFFFFF")}
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
    json.dump({"note": "Import all .obj files with the same origin; set each MeshPart.Color3 to color_rgb.", "parts": info}, open(f"{dirpath}/colors.json", "w"), indent=1)
    return info

# ------------------------------------------------------------------ renderer (z-buffer, smooth shading, AO, rim, soft shadow)
def rot(rx=0, ry=0, rz=0):
    a, b, c = map(math.radians, (rx, ry, rz))
    Rx = np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
    Ry = np.array([[math.cos(b),0,math.sin(b)],[0,1,0],[-math.sin(b),0,math.cos(b)]])
    Rz = np.array([[math.cos(c),-math.sin(c),0],[math.sin(c),math.cos(c),0],[0,0,1]])
    return Rz @ Ry @ Rx

def render(parts, yaw, pitch=-10, size=800, ss=2, focus=None):
    V, T, Cc, N, ao, em, sp = merge(parts)
    S = size * ss
    R = rot(pitch, yaw, 0)
    P0 = V @ R.T
    pmin, pmax = P0.min(0), P0.max(0); pc = (pmin + pmax) / 2
    scale = S * 0.86 / max(pmax[0] - pmin[0], pmax[1] - pmin[1])
    proj = lambda Q: np.stack([S / 2 + (Q[..., 0] - pc[0]) * scale, S * 0.50 - (Q[..., 1] - pc[1]) * scale], -1)
    Pv = P0; Nv = N @ R.T
    XY = proj(Pv); X, Y = XY[:, 0], XY[:, 1]; Z = Pv[:, 2]
    A = np.concatenate([Cc, Nv, ao[:, None], em[:, None], sp[:, None]], 1).astype(np.float32)
    zb = np.full((S, S), -1e9, np.float32); buf = np.zeros((S, S, A.shape[1]), np.float32); mk = np.zeros((S, S), bool)
    a_, b_, c_ = T[:, 0], T[:, 1], T[:, 2]
    fn = np.cross(Pv[b_] - Pv[a_], Pv[c_] - Pv[a_])
    vis = np.flatnonzero(fn[:, 2] > 0)
    for t in vis:
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
    key, fill, rimd = nrm([-0.45, 0.70, 0.55]), nrm([0.65, 0.15, 0.45]), nrm([0.25, 0.45, -0.85])
    lam = lambda L: np.clip(n @ L, 0, 1)[..., None]
    hemi = (0.38 + 0.30 * (n[..., 1:2] * 0.5 + 0.5))
    lit = col * (hemi * aoo * np.array([0.95, 0.95, 1.05]) + lam(key) * np.array([1.0, 0.93, 0.84]) * (0.55 + 0.45 * aoo) + lam(fill) * np.array([0.55, 0.65, 0.85]) * 0.35)
    lit += (lam(rimd) ** 2) * np.array([1.0, 0.82, 0.6]) * 0.35 * aoo
    H = nrm(key + np.array([0, 0, 1.0])); lit += (np.clip(n @ H, 0, 1)[..., None] ** 40) * spc * 1.1
    lit = lit * (1 - emi) + np.clip(col * 1.25 + 0.12, 0, 1) * emi
    # tone map + slight saturation
    lit = np.clip(lit, 0, 1.6); lit = lit / (1 + 0.18 * lit); lit = np.clip(lit * 1.12, 0, 1) ** (1 / 1.05)
    # background: soft vertical gradient + contact shadow
    yy = np.linspace(0, 1, S)[:, None, None]
    bg = (1 - yy) * np.array([0.93, 0.92, 0.97]) + yy * np.array([0.80, 0.80, 0.88]); bg = np.broadcast_to(bg, (S, S, 3)).copy()
    sh = Image.new("L", (S, S), 0); d = ImageDraw.Draw(sh)
    ring = [R @ np.array([1.15 * math.cos(t), 0.0, 0.7 + 2.9 * math.sin(t)]) for t in np.linspace(0, 2 * math.pi, 60)]
    d.polygon([tuple(proj(q)) for q in ring], fill=170)
    sh = np.asarray(sh.filter(ImageFilter.GaussianBlur(S * 0.018)), float)[..., None] / 255
    bg = bg * (1 - 0.35 * sh)
    out = np.where(mk[..., None], lit, bg)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)

# ------------------------------------------------------------------ main
if __name__ == "__main__":
    hero_res = 0.085 if FAST else 0.05
    hero, gh = build(hero_res, tuft_count=900 if FAST else 3200, tuft_len=0.13, smooth=1, name="hero")
    game, gg = build(0.11, tuft_count=0, tuft_len=0, smooth=2, name="game")

    for name, parts in (("hero", hero), ("game", game)):
        V, T, Cc, N, *_ = merge(parts)
        write_ply(f"{OUT}/ember_fox_{name}.ply", V, T, Cc)
        write_obj(f"{OUT}/ember_fox_{name}.obj", V, T, Cc, N, with_vc=True)
    # game LOD without eyes merged split by colour for Roblox MeshParts
    V, T, Cc, N, *_ = merge(game)
    info = write_color_split(f"{OUT}/game_roblox_parts", V, T, Cc, N)
    json.dump({"units": "studs", "forward": "-Z", "up": "+Y",
               "hero_triangles": int(sum(len(p['T']) for p in hero)), "game_triangles": int(sum(len(p['T']) for p in game)),
               "colour_parts": info}, open(f"{OUT}/model_info.json", "w"), indent=1)

    t0 = time.time(); views = []
    for yaw, pitch in ((150, -10), (90, -6), (215, -10)):
        views.append(render(hero, yaw, pitch, size=800, ss=2)); print("rendered view", yaw, f"{time.time()-t0:.0f}s")
    sheet = Image.new("RGB", (800 * 3, 800))
    for i, v in enumerate(views): sheet.paste(v, (i * 800, 0))
    sheet.save(f"{OUT}/preview.png")
    views[0].save(f"{OUT}/hero_front34.png")
    gv = render(game, 150, -10, size=800, ss=2); gv.save(f"{OUT}/game_lod_preview.png")
    print("done")
