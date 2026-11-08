#!/usr/bin/env python3
"""The corner measurement of run 41006842699's analysis/tiebreak_corners.py, unchanged (the functions from `read_png`
to `quarter`, copied as they are; that script's docstring states the method: the corner square per corner, the
circular fit `fit_px` and `rms`, `area_px`, `spread_px`, and `radius` as a fact spells it, or "unfit"), applied to the
button layers of run 42272240639 (macOS 26.7.2, macOS 15.8.2) that this run's analysis/measure_button_layers.py
measured. The facts lane wrote it (2026-11-06).

Run from the repository root (Python 3.11+, the standard library only), after measure_button_layers.py, once per
image folder:

    python3 docs/evidence/os-probe/2026-11-06-run-42272240639/analysis/tiebreak_corners.py [IMAGE]

It reads, under the image folder (`os-probe-macos-26`, the default, or `os-probe-macos-15`), each
`layers-<pass>-<sheet>.toml` measure_button_layers.py wrote (each button's `drawn_box`, `fill` and `stroke_<side>`)
and the layer PNGs it names in its `input_image`, and writes `tiebreak-corners.toml`, per
`<pass>.<sheet>.<appearance>.<state>.<button>` where `fill` is a colour (or the outline rule holds), as the earlier
script does.

It exits 1, writing nothing, when a file it needs is missing or not as expected.
"""

import struct
import sys
import tomllib
import zlib
from math import pi, sqrt
from pathlib import Path

IMAGE = sys.argv[1] if len(sys.argv) > 1 else "os-probe-macos-26"
if IMAGE not in ("os-probe-macos-26", "os-probe-macos-15"):
    print(f"tiebreak_corners: unknown image folder {IMAGE!r}", file=sys.stderr)
    sys.exit(2)
RUN = Path(f"docs/evidence/os-probe/2026-11-06-run-42272240639/{IMAGE}")
APPEARANCES = ("aqua", "darkAqua")
CORNERS = ("top_left", "top_right", "bottom_right", "bottom_left")
SAMPLES = 16


class Bad(Exception):
    pass


def read_png(path: Path):
    """(width, height, rows of (r, g, b, a)) of an 8-bit, non-interlaced RGBA PNG."""
    if not path.is_file():
        raise Bad(f"{path}: missing")
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise Bad(f"{path}: not a PNG")
    pos, idat, ihdr = 8, b"", None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
    if ihdr is None:
        raise Bad(f"{path}: no IHDR")
    width, height, depth, ctype, _, _, interlace = ihdr
    if depth != 8 or ctype != 6 or interlace != 0:
        raise Bad(f"{path}: not 8-bit non-interlaced RGBA")
    raw = zlib.decompress(idat)
    stride, bpp = width * 4, 4
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(height):
        ftype = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if ftype == 1:
                line[x] = (line[x] + a) & 255
            elif ftype == 2:
                line[x] = (line[x] + b) & 255
            elif ftype == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif ftype == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
            elif ftype != 0:
                raise Bad(f"{path}: filter {ftype}")
        rows.append([tuple(line[x:x + 4]) for x in range(0, stride, 4)])
        prev = line
    return width, height, rows


def circle_coverage(r: float, n: int):
    """Coverage of each pixel of an n x n corner square (the corner at (0, 0)) by a circular corner of radius r."""
    g = [(k + 0.5) / SAMPLES for k in range(SAMPLES)]
    out = []
    for y in range(n):
        # per sample row, the corner's edge: x >= r - sqrt(r^2 - (r - py)^2) is inside (above the circle's centre)
        edges = []
        for sy in g:
            py = y + sy
            edges.append(r - sqrt(max(r * r - (r - py) ** 2, 0.0)) if py < r else 0.0)
        row = []
        for x in range(n):
            inside = 0
            for e in edges:
                for sx in g:
                    if x + sx >= e:
                        inside += 1
            row.append(inside / (SAMPLES * SAMPLES))
        out.append(row)
    return out


_COVER = {}


def cover(r: float, n: int):
    key = (round(r, 2), n)
    if key not in _COVER:
        _COVER[key] = circle_coverage(key[0], n)
    return _COVER[key]


def corner_square(rows, box, corner, n):
    """The n x n pixels at a corner of the box, flipped so the corner is at (0, 0)."""
    x0, y0, w, h = box
    out = []
    for j in range(n):
        y = y0 + j if corner.startswith("top") else y0 + h - 1 - j
        line = []
        for i in range(n):
            x = x0 + i if corner.endswith("left") else x0 + w - 1 - i
            line.append(rows[y][x])
        out.append(line)
    return out


def fit_corner(square, fill, n, outline=False):
    fr, fg, fb, fa = fill
    pts = []
    for j in range(n):
        inside = False
        for i in range(n):
            r, g, b, a = square[j][i]
            if outline and inside:
                pts.append((j, i, 1.0))
                continue
            if a > fa + 3 or (a >= fa / 2 and max(abs(r - fr), abs(g - fg), abs(b - fb)) > 8):
                continue
            if outline and a >= fa / 2:
                inside = True
            pts.append((j, i, min(a / fa, 1.0)))
    masked = n * n - len(pts)
    if not pts:
        return None
    missing = sum(1 - c for _, _, c in pts)
    area = sqrt(missing / (1 - pi / 4))
    best = None
    steps = int(n / 0.05) + 1
    for k in range(steps):
        r = k * 0.05
        cv = cover(r, n)
        err = sum((cv[j][i] - c) ** 2 for j, i, c in pts)
        if best is None or err < best[1]:
            best = (r, err)
    rms = sqrt(best[1] / len(pts))
    return {"fit_px": round(best[0], 2), "rms": round(rms, 4), "area_px": round(area, 3), "masked": masked}


def parse_fill(s):
    if not isinstance(s, str) or not s.startswith("#") or len(s) != 9:
        return None
    v = [int(s[k:k + 2], 16) for k in (1, 3, 5, 7)]
    return tuple(v) if v[3] >= 3 else None


def quarter(v: float) -> str:
    q = round(v * 4) / 4
    if q < 0.375:
        return "0px"
    t = f"{q:.2f}".rstrip("0").rstrip(".")
    return f"{t}px"


def main() -> int:
    out = {}
    images = []
    try:
        for lp in sorted(RUN.glob("layers-*.toml")):
            doc = tomllib.loads(lp.read_text())
            pngs = {p for p in doc["input_image"] if p.endswith("-layer.png")}
            (pname,) = [k for k in doc if k != "input_image"]
            for sheet, apps in doc[pname].items():
                for app in APPEARANCES:
                    for state, buttons in apps[app].items():
                        sub = "" if sheet == "push" else f"{sheet}/"
                        (img,) = [p for p in pngs if p.endswith(f"/{app}/{sub}{state}-layer.png")]
                        _, _, rows = read_png(Path(img))
                        images.append(img)
                        for button, m in buttons.items():
                            fill = parse_fill(m.get("fill"))
                            outline = False
                            strokes = [m.get(f"stroke_{side}") for side in ("top", "right", "bottom", "left")]
                            if fill is None and m.get("fill") == "absent" and all(
                                    isinstance(st, dict) and st.get("width") == 1 for st in strokes) and len(
                                    {st["edge"] for st in strokes}) == 1:
                                fill, outline = parse_fill(strokes[0]["edge"]), True
                            if fill is None:
                                continue
                            x, y, w, h = m["drawn_box"][:4]
                            n = min(w, h) // 2
                            res = {"box": [x, y, w, h]}
                            if outline:
                                res["read_from"] = "outline"
                            fits = {}
                            for corner in CORNERS:
                                f = fit_corner(corner_square(rows, (x, y, w, h), corner, n), fill, n, outline)
                                if f is None:
                                    break
                                fits[corner] = f
                                res[corner] = f
                            if len(fits) < 4:
                                res["radius"] = "unfit"
                            else:
                                vals = [fits[c]["fit_px"] for c in CORNERS]
                                res["spread_px"] = round(max(vals) - min(vals), 2)
                                half = min(w, h) / 2
                                if not all(fits[c]["rms"] <= 0.06 for c in CORNERS) or res["spread_px"] > 1.0:
                                    res["radius"] = "unfit"
                                elif all(v >= half - 0.75 for v in vals):
                                    res["radius"] = {"full": {"maximum_px": "absent"}}
                                else:
                                    res["radius"] = quarter(sum(vals) / 4)
                            out.setdefault(pname, {}).setdefault(sheet, {}).setdefault(app, {}).setdefault(
                                state, {})[button] = res
    except Bad as e:
        print(f"tiebreak_corners: {e}", file=sys.stderr)
        return 1
    lines = ["# Written by analysis/tiebreak_corners.py (its docstring is the method); do not edit.", "",
             "input_image = ["] + [f'  "{p}",' for p in images] + ["]", ""]

    def val(v):
        if isinstance(v, dict):
            return "{ " + ", ".join(f"{k} = {val(x)}" for k, x in v.items()) + " }"
        if isinstance(v, list):
            return "[" + ", ".join(val(x) for x in v) + "]"
        if isinstance(v, str):
            return f'"{v}"'
        return repr(v)

    for pname, sheets in out.items():
        for sheet, apps in sheets.items():
            for app, states in apps.items():
                for state, buttons in states.items():
                    for button, res in buttons.items():
                        lines.append(f'[{pname}.{sheet}.{app}.{state}."{button}"]')
                        for k, v in res.items():
                            lines.append(f"{k} = {val(v)}")
                        lines.append("")
    (RUN / "tiebreak-corners.toml").write_text("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
