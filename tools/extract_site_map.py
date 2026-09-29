#!/usr/bin/env python3
"""
Extract feeder linework from a vector site-map PDF (e.g. 12kV distribution drawings)
into a JSON "site map" file that kml_media_reconciler.html can georeference.

    pip install pymupdf
    python extract_site_map.py "distribution-drawing.pdf" [--page 1] [--dpi 72] [--min-len 40]
                               [--label "0,0,255=Feeder A" --label "0,255,0=Feeder B" ...]

Output: <pdf name>.sitemap.json containing
  page size, a PNG render of the page (base64) for picking control points,
  and one group per (stroke colour, line width) with all its polylines in PDF points.
Groups are named from --label if given, else from legend text found next to a colour swatch,
else "colour rgb(...)". Names can be edited later in the tool.
Black, white and grey linework (roads, text, symbols, borders) is skipped by default.
"""
import argparse, base64, json, os, re, sys
try:
    import pymupdf
except ImportError:
    import fitz as pymupdf  # older installs

ap = argparse.ArgumentParser()
ap.add_argument("pdf")
ap.add_argument("--page", type=int, default=1)
ap.add_argument("--dpi", type=int, default=72, help="render resolution of the background image (72 = 1 px per PDF point)")
ap.add_argument("--min-len", type=float, default=40, help="drop colour groups whose total line length (pt) is below this")
ap.add_argument("--min-path", type=float, default=2.0, help="drop individual paths shorter than this (pt), i.e. symbols")
ap.add_argument("--keep-grey", action="store_true", help="keep black/grey/white linework as groups too")
ap.add_argument("--label", action="append", default=[], help="r,g,b=Name  (or r,g,b@width=Name)")
ap.add_argument("-o", "--out")
ap.add_argument("--name", help="display name for the site map (default: PDF file name)")
a = ap.parse_args()

doc = pymupdf.open(a.pdf)
pg = doc[a.page - 1]
W, H = pg.rect.width, pg.rect.height

def rgb(c):
    return tuple(int(round(x * 255)) for x in c)

def is_grey(c):
    return max(c) - min(c) < 20

labels = {}
for l in a.label:
    k, _, name = l.partition("=")
    col, _, wd = k.partition("@")
    labels[(tuple(int(x) for x in col.split(",")), float(wd) if wd else None)] = name.strip()

# ---- legend guess: colour swatches (short horizontal lines) with text to their right
words = pg.get_text("words")
legend_guess = {}
for p in pg.get_drawings():
    if p.get("color") is None:
        continue
    r = p["rect"]
    if not (20 <= r.width <= 120 and r.height <= 4):
        continue
    c = rgb(p["color"])
    if is_grey(c):
        continue
    ymid = (r.y0 + r.y1) / 2
    txt = " ".join(w[4] for w in sorted(words, key=lambda w: w[0]) if abs((w[1] + w[3]) / 2 - ymid) < 6 and r.x1 < w[0] < r.x1 + 260)
    txt = txt.strip()
    if txt and c not in legend_guess and len(txt) > 3:
        legend_guess[c] = txt

# ---- collect polylines per (colour, width)
groups = {}
for p in pg.get_drawings():
    col = p.get("color")
    if col is None:
        continue
    c = rgb(col)
    if is_grey(c) and not a.keep_grey:
        continue
    wd = round(p.get("width") or 0, 1)
    key = (c, wd)
    g = groups.setdefault(key, {"color": c, "width": wd, "paths": [], "len": 0.0})
    cur = []
    def flush():
        global cur
        if len(cur) >= 2:
            L = sum(((cur[i][0] - cur[i - 1][0]) ** 2 + (cur[i][1] - cur[i - 1][1]) ** 2) ** 0.5 for i in range(1, len(cur)))
            if L >= a.min_path:
                g["paths"].append([[round(x, 1), round(y, 1)] for x, y in cur]); g["len"] += L
        cur = []
    for it in p["items"]:
        op = it[0]
        if op == "l":
            p1, p2 = it[1], it[2]
            if cur and abs(cur[-1][0] - p1.x) < 0.05 and abs(cur[-1][1] - p1.y) < 0.05:
                cur.append((p2.x, p2.y))
            else:
                flush(); cur = [(p1.x, p1.y), (p2.x, p2.y)]
        elif op == "c":  # bezier: keep end points only (feeders are straight)
            p1, p4 = it[1], it[4]
            if cur and abs(cur[-1][0] - p1.x) < 0.05 and abs(cur[-1][1] - p1.y) < 0.05:
                cur.append((p4.x, p4.y))
            else:
                flush(); cur = [(p1.x, p1.y), (p4.x, p4.y)]
        else:  # rectangles / quads are symbols
            flush()
    flush()

out_groups = []
for (c, wd), g in sorted(groups.items(), key=lambda kv: -kv[1]["len"]):
    if g["len"] < a.min_len or not g["paths"]:
        continue
    name = labels.get((c, wd)) or labels.get((c, None)) or legend_guess.get(c) or f"colour rgb({c[0]},{c[1]},{c[2]})" + (f" w{wd}" if wd else "")
    out_groups.append({"key": f"{c[0]},{c[1]},{c[2]}@{wd}", "name": name, "color": list(c), "width": wd,
                       "totalLen": round(g["len"]), "pathCount": len(g["paths"]), "paths": g["paths"]})

pix = pg.get_pixmap(dpi=a.dpi)
png_b64 = base64.b64encode(pix.tobytes("png")).decode()

result = {
    "kind": "sitemap", "version": 1,
    "name": a.name or os.path.splitext(os.path.basename(a.pdf))[0],
    "source": (a.name or os.path.basename(a.pdf)), "page": a.page,
    "pageWidth": W, "pageHeight": H,
    "imageDpi": a.dpi, "imageWidth": pix.width, "imageHeight": pix.height, "imagePng": png_b64,
    "groups": out_groups,
    "controlPoints": [], "exclusions": [],
}
out = a.out or os.path.splitext(a.pdf)[0] + ".sitemap.json"
with open(out, "w") as fh:
    json.dump(result, fh)
print(f"{out}: {len(out_groups)} colour groups, image {pix.width}x{pix.height}", file=sys.stderr)
for g in out_groups:
    print(f"  {g['name']:45s} rgb{tuple(g['color'])} w{g['width']}  paths={g['pathCount']} len={g['totalLen']}", file=sys.stderr)
