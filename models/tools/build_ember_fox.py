#!/usr/bin/env python3
"""Procedural low-poly Ember Fox (numpy + PIL only).
Outputs per-part OBJ files, a combined OBJ+MTL, parts.json (colours, pivots) and a 3-view preview PNG.
Units are studs. The fox faces -Z (Roblox LookVector). Y is up.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

OUT = sys.argv[1] if len(sys.argv) > 1 else "ember_fox"
os.makedirs(OUT, exist_ok=True)

def rot(rx=0, ry=0, rz=0):
    a, b, c = map(math.radians, (rx, ry, rz))
    Rx = np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
    Ry = np.array([[math.cos(b),0,math.sin(b)],[0,1,0],[-math.sin(b),0,math.cos(b)]])
    Rz = np.array([[math.cos(c),-math.sin(c),0],[math.sin(c),math.cos(c),0],[0,0,1]])
    return Rz @ Ry @ Rx

def ellipsoid(center, radii, rotation=(0,0,0), taper=None, n_lat=8, n_lon=12):
    """taper=(axis_dir, strength): shrinks cross-section toward +local-Y (ear/flame tips)."""
    verts = [[0, 1, 0]]
    for i in range(1, n_lat):
        v = math.pi * i / n_lat
        for j in range(n_lon):
            u = 2 * math.pi * j / n_lon
            verts.append([math.sin(v)*math.cos(u), math.cos(v), math.sin(v)*math.sin(u)])
    verts.append([0, -1, 0])
    V = np.array(verts, dtype=float)
    if taper is not None:
        t = (V[:, 1] + 1) / 2                      # 0 bottom .. 1 top
        s = 1 - taper * t
        V[:, 0] *= s; V[:, 2] *= s
    V = V * np.array(radii)
    V = V @ rot(*rotation).T + np.array(center)
    F = []
    for j in range(n_lon):                          # top fan
        F.append([0, 1 + j, 1 + (j + 1) % n_lon])
    for i in range(n_lat - 2):                      # rings
        a = 1 + i * n_lon; b = 1 + (i + 1) * n_lon
        for j in range(n_lon):
            j2 = (j + 1) % n_lon
            F.append([a + j, b + j, b + j2]); F.append([a + j, b + j2, a + j2])
    last = len(V) - 1; base = 1 + (n_lat - 2) * n_lon
    for j in range(n_lon):                          # bottom fan
        F.append([last, base + (j + 1) % n_lon, base + j])
    F = np.array(F)
    # orient every triangle outward (parts are convex)
    c = V.mean(axis=0)
    for k, (a, b, d) in enumerate(F):
        n = np.cross(V[b] - V[a], V[d] - V[a])
        if np.dot(n, (V[a] + V[b] + V[d]) / 3 - c) < 0:
            F[k] = [a, d, b]
    return V, F

PARTS = []
def part(name, color, *a, **k):
    V, F = ellipsoid(*a, **k); PARTS.append((name, color, V, F))

ORANGE, DORANGE, CREAM = "#F08A24", "#D9651C", "#FFF1D6"
BROWN, WHITE, NOSE, YEL, FLAME = "#3A2318", "#FFFFFF", "#2A1A14", "#FFC93C", "#FF7A1A"

part("body",      ORANGE, (0,1.15,0.1), (0.78,0.68,1.15), n_lat=9, n_lon=14)
part("chest",     CREAM,  (0,0.98,-0.62), (0.55,0.5,0.55), n_lat=6, n_lon=10)
part("head",      ORANGE, (0,1.95,-1.05), (0.9,0.78,0.78), n_lat=10, n_lon=16)
part("muzzle",    CREAM,  (0,1.72,-1.72), (0.4,0.3,0.36), n_lat=6, n_lon=10)
part("nose",      NOSE,   (0,1.8,-2.04), (0.11,0.09,0.09), n_lat=4, n_lon=6)
for s, side in ((-1,"L"),(1,"R")):
    part(f"eye_{side}",       BROWN, (s*0.38,2.02,-1.68), (0.2,0.25,0.11), n_lat=6, n_lon=10)
    part(f"eye_shine_{side}", WHITE, (s*0.34,2.1,-1.77),  (0.07,0.085,0.045), n_lat=4, n_lon=6)
    part(f"ear_{side}",       ORANGE,(s*0.55,2.85,-0.95), (0.3,0.7,0.15), rotation=(0,0,-s*14), taper=0.55, n_lat=6, n_lon=8)
    part(f"ear_inner_{side}", CREAM, (s*0.55,2.78,-1.06), (0.17,0.45,0.07), rotation=(0,0,-s*14), taper=0.55, n_lat=5, n_lon=8)
    part(f"cheek_{side}",     CREAM, (s*0.62,1.72,-1.35), (0.28,0.26,0.28), n_lat=5, n_lon=8)
for fx, side in ((-1,"L"),(1,"R")):
    for fz, end in ((-0.62,"F"),(0.78,"B")):
        part(f"leg_{side}{end}",  DORANGE, (fx*0.44,0.48,fz), (0.22,0.5,0.25), n_lat=6, n_lon=8)
        part(f"paw_{side}{end}",  CREAM,   (fx*0.44,0.1,fz-0.04), (0.25,0.12,0.3), n_lat=4, n_lon=8)
# bushy tail: overlapping chain along an upward arc, ending in a two-layer flame
part("tail_1", ORANGE,  (0,1.2,1.2),  (0.38,0.4,0.62), rotation=(-30,0,0), n_lat=6, n_lon=10)
part("tail_2", ORANGE,  (0,1.62,1.78),(0.48,0.52,0.66), rotation=(-50,0,0), n_lat=7, n_lon=12)
part("tail_3", DORANGE, (0,2.15,2.2), (0.5,0.56,0.62), rotation=(-70,0,0), n_lat=7, n_lon=12)
part("flame_outer", FLAME, (0,2.95,2.42), (0.46,0.86,0.4), rotation=(-12,0,0), taper=0.78, n_lat=7, n_lon=10)
part("flame_inner", YEL,   (0,2.88,2.38), (0.25,0.56,0.22), rotation=(-12,0,0), taper=0.78, n_lat=6, n_lon=8)

def vnormals(V, F):
    N = np.zeros_like(V)
    for a, b, c in F:
        n = np.cross(V[b]-V[a], V[c]-V[a]); N[a]+=n; N[b]+=n; N[c]+=n
    L = np.linalg.norm(N, axis=1, keepdims=True); L[L==0]=1
    return N / L

def write_obj(path, items, mtl_name=None):
    with open(path, "w") as f:
        if mtl_name: f.write(f"mtllib {mtl_name}\n")
        off = 0
        for name, color, V, F in items:
            N = vnormals(V, F)
            f.write(f"o {name}\n")
            if mtl_name: f.write(f"usemtl mat_{color[1:]}\n")
            for v in V: f.write("v %.4f %.4f %.4f\n" % tuple(v))
            for n in N: f.write("vn %.4f %.4f %.4f\n" % tuple(n))
            for a, b, c in F:
                f.write("f %d//%d %d//%d %d//%d\n" % (a+1+off,a+1+off,b+1+off,b+1+off,c+1+off,c+1+off))
            off += len(V)

os.makedirs(f"{OUT}/parts", exist_ok=True)
for name, color, V, F in PARTS:
    write_obj(f"{OUT}/parts/{name}.obj", [(name, color, V, F)])
write_obj(f"{OUT}/ember_fox_combined.obj", PARTS, "ember_fox.mtl")
with open(f"{OUT}/ember_fox.mtl", "w") as f:
    for col in sorted({c for _, c, _, _ in PARTS}):
        r, g, b = (int(col[i:i+2], 16)/255 for i in (1, 3, 5))
        f.write(f"newmtl mat_{col[1:]}\nKd {r:.3f} {g:.3f} {b:.3f}\nKa 0 0 0\nKs 0 0 0\nd 1\n\n")
manifest = {"unit": "studs", "faces": "-Z", "up": "+Y",
            "parts": [{"name": n, "color": c, "pivot": [round(float(x),3) for x in V.mean(axis=0)], "triangles": int(len(F)), "vertices": int(len(V))} for n, c, V, F in PARTS]}
json.dump(manifest, open(f"{OUT}/parts.json", "w"), indent=1)
tris = sum(len(F) for *_, F in PARTS)

# ---------- preview render: z-buffer, smooth shading, 2x supersample ----------
def render(yaw, pitch=-14, size=640, ss=2):
    S = size * ss
    zbuf = np.full((S, S), -1e9); rgb = np.zeros((S, S, 3)); bg = np.array([248, 246, 252], float)
    mask = np.zeros((S, S), bool)
    R = rot(pitch, yaw, 0)
    allv = np.vstack([V for _, _, V, _ in PARTS]); lo, hi = allv.min(0), allv.max(0); ctr = (lo + hi) / 2
    scale = S * 0.62 / max(hi[1]-lo[1], (hi[0]-lo[0]) * 1.0, (hi[2]-lo[2]) * 0.8)
    L = np.array([0.45, 0.75, 0.55]); L /= np.linalg.norm(L)
    for name, col, V, F in PARTS:
        P = (V - ctr) @ R.T; N = vnormals(V, F) @ R.T
        base = np.array([int(col[i:i+2], 16) for i in (1, 3, 5)], float)
        X = S/2 + P[:,0]*scale; Y = S*0.52 - P[:,1]*scale; Z = P[:,2]
        for a, b, c in F:
            fn = np.cross(P[b]-P[a], P[c]-P[a])
            if fn[2] <= 0: continue
            x0, x1 = int(max(0, math.floor(min(X[[a,b,c]])))), int(min(S-1, math.ceil(max(X[[a,b,c]]))))
            y0, y1 = int(max(0, math.floor(min(Y[[a,b,c]])))), int(min(S-1, math.ceil(max(Y[[a,b,c]]))))
            if x1 < x0 or y1 < y0: continue
            gx, gy = np.meshgrid(np.arange(x0, x1+1)+0.5, np.arange(y0, y1+1)+0.5)
            d = (Y[b]-Y[c])*(X[a]-X[c]) + (X[c]-X[b])*(Y[a]-Y[c])
            if abs(d) < 1e-9: continue
            w0 = ((Y[b]-Y[c])*(gx-X[c]) + (X[c]-X[b])*(gy-Y[c])) / d
            w1 = ((Y[c]-Y[a])*(gx-X[c]) + (X[a]-X[c])*(gy-Y[c])) / d
            w2 = 1 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not inside.any(): continue
            z = w0*Z[a] + w1*Z[b] + w2*Z[c]
            sub = zbuf[y0:y1+1, x0:x1+1]
            upd = inside & (z > sub)
            if not upd.any(): continue
            n = (w0[...,None]*N[a] + w1[...,None]*N[b] + w2[...,None]*N[c])
            n /= np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-9)
            lam = np.clip(n @ L, 0, 1)
            shade = 0.48 + 0.52 * lam
            rim = 0.35 * np.clip(1 - n[...,2], 0, 1) ** 2
            colr = np.clip(base[None,None,:] * shade[...,None] + 255 * 0.25 * rim[...,None], 0, 255)
            sub[upd] = z[upd]
            rgb[y0:y1+1, x0:x1+1][upd] = colr[upd]
            mask[y0:y1+1, x0:x1+1][upd] = True
    out = np.where(mask[...,None], rgb, bg[None,None,:])
    return Image.fromarray(out.astype(np.uint8)).resize((size, size), Image.LANCZOS)

views = [render(150), render(90), render(210), render(0)]
sheet = Image.new("RGB", (640 * 4, 640), (248, 246, 252))
for i, v in enumerate(views): sheet.paste(v, (i * 640, 0))
sheet.save(f"{OUT}/preview.png")
print(f"parts={len(PARTS)} triangles={tris} -> {OUT}")
