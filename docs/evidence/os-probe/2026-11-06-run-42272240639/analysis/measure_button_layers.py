#!/usr/bin/env python3
"""Measures the buttons' layers of the os-probe button passes of run 42272240639 (macOS 26.7.2 in its macos-26 job,
macOS 15.8.2 in its macos-15 job) and writes the values the macOS facts cite (docs/facts/macos/button.toml), as S17's
analysis output. It is run 41006842699's analysis/measure_button_layers.py with its per-button measurement unchanged
but for the image's colour (`icon`, below)
(the functions from `read_png` to `emit`, copied as they are; that script's docstring states each value's rule:
`drawn_box`, `fill`, `fill_share`, `stroke`, `stroke_<side>`, `edge_<side>`, `corner_<corner>`, `label`, `icon`,
`drawn_only_content`, `shadow`, `shadow_pixels`), applied to this run's passes and sheets; it writes no focus, caret,
geometry or derivation part (the run's focus pass is under the red accent only, its caret a recording, and its
geometry is the earlier run's). The facts lane wrote it (2026-11-06).

Run from the repository root (Python 3.11+, the standard library only), once per image folder:

    python3 docs/evidence/os-probe/2026-11-06-run-42272240639/analysis/measure_button_layers.py [IMAGE]

IMAGE is `os-probe-macos-26` (the default: macos-tahoe's) or `os-probe-macos-15` (macos-monterey's).

What it reads, under the image folder (the probe's method texts are in each probe.toml, `[macos.button_pass]`
`mode_method`, `method`, `backdrops`, `layer_method`):

- <pass>/probe.toml of the passes `button-pass` (key: the window key and main, the application active),
  `button-pass-key-not-main` (the sheet key and not main), `button-pass-main-not-key` (main and not key),
  `button-pass-inactive-increase-contrast-on` (the application inactive, the sheet neither key nor main, Increase
  Contrast on): each button's frame in its layer and its cell's title and image rects, as the earlier script reads
  them, and `key_at_capture` and the `isKeyWindow`/`NSApp_isActive` reads, which it requires to be the pass's mode;
- each pass's settings.txt, where the pass writes a setting (`button-pass-inactive-increase-contrast-on`): it requires
  `write increaseContrast true: exit 0` and `read back: 1`, so the pass ran with Increase Contrast on; a pass that
  changes none says `no setting changed: the image's`, which it requires too (each text a line's start);
- the layers `<pass>/<appearance>/[<sheet>/]<state>-layer.png`, for the states normal, pressed, disabled and
  disabled_pressed (`disabled_pressed`: `setEnabled: NO` and `highlight: YES` together, U91): in the key pass the
  sheets `default_a`, `default_b`, `default_c` (each style with the Return key equivalent, the window's default
  button cell: U92) and `image_a`, `image_b`, `image_c` (the symbol image beside the title, U99), and of the plain
  sheets (`push`, `styles_a`, `styles_b`, `styles_c`, whose other layers run 41006842699 holds) only
  `disabled_pressed`; in the three other passes the plain sheets, every state (U93);
- with each layer, its `<state>-over-grey.png`, the capture over the grey backdrop (`[…<appearance>.<state>.over_grey]`,
  `backdrop_raw` #808080ff, which it requires), as run 41006842699's script reads its Increase Contrast pass's: the
  probe's own `check_grey` finds many of this run's layers not one linear overlay (its `max_byte_delta` and
  `pixels_over_2` per button, over the button's whole region), so each value read from a layer is checked at the
  pixels it is read from against that capture: `fill_grey_delta`, `label_grey_delta`, `icon_grey_delta`, the largest
  byte difference of the layer composited over #808080 and the capture at the fill's, the label's and the icon's
  pixels (that script's rule, `grey_delta`, unchanged), and, added here (the macOS tie-break round 7, 2026-11-08),
  `edge_grey_delta` at the eight pixels `stroke_<side>` and `edge_<side>` are read from (the first two from each side's
  edge along the box's middle row or column) and `shadow_grey_delta` at the pixels `shadow` is read from (the frame
  grown by 6 px, outside the frame). The grey captures were brought from the run's artifact (byte for byte; each
  layer they belong to is the committed one byte for byte) by the tie-break, which re-ran this script and
  tiebreak_corners.py: every other key of the output is unchanged.

The image's colour (the macOS tie-break round 8, 2026-11-10; the register's U751). The earlier script's rule reads
`icon` as it reads `label`: the pixels of the largest alpha in the rect, or the pixel farthest from an opaque fill. The
image is the symbol "star" at 9 pt (mini), 11 pt (small) and 13 pt (regular and up), whose strokes cover no whole
pixel: this run's symbols pass reads the glyph's largest coverage as 0.63 to 0.74 at 1 pixel a point and otherwise at 2
(`symbols/probe.toml`, `size_symbol_renders.<scale>.glyph.max_coverage`). So that reading is the paint's alpha times
the glyph's coverage, from one to four pixels, and it follows the symbol's point size: over no fill and over a
translucent fill its straight RGB is the paint's and its alpha a lower bound of the paint's; over an opaque fill the
picked pixel is the fill mixed with the paint, so neither. This script therefore writes `icon` only where the layer
itself shows a fully covered pixel of opaque paint (`covered`): an alpha of 255 where the fill is absent or
translucent, or, over an opaque fill, a picked pixel of #000000 or #ffffff where the fill is not that colour (a mix
of the fill and a paint reaches a channel's end only at full coverage of an opaque paint). Every other reading is
written as `icon_peak`, with `icon_pixels` and `icon_grey_delta` as before, and no fact cites it. `label` is
unchanged: the title's reading does not follow the control size.

The colours' error bound (S17 *Fields*, ADD-A141), which a fact's tolerance may not exceed. A layer pixel's straight
colour and alpha are the probe's solve from the captures over black and over white, each read to one 8-bit level, and
one level of a composite is 1/alpha levels of the straight channel beneath it: `fill`, and `label` and `icon` where the
fill is absent or opaque (the layer's own pixel), hold to floor(1/alpha) levels a channel, alpha the value's own (1
level from an alpha of 128/255 up). Where the fill is translucent, `label` and `icon` are solved a second time from
the layer's pixel and the fill (colour (P - F (1 - alpha)) / alpha, the earlier script's rule): one level of P alone
is 1/alpha levels of the result and the fill's level adds to it, so that solve's bound is no smaller than
floor(1/alpha); S17 states none for it, and the facts carry at most floor(1/alpha) there too.

It writes `layers-<pass>-<sheet>.toml` into the image folder (pass: key, key_not_main, main_not_key,
inactive_contrast), per `<pass>.<sheet>.<appearance>.<state>.<button>` the earlier script's values, and
`input_image`, every file it read. It exits 1, writing nothing, when a file it needs is missing or not as expected.
"""

import struct
import sys
import tomllib
import zlib
from collections import Counter
from math import sqrt
from pathlib import Path

IMAGE = sys.argv[1] if len(sys.argv) > 1 else "os-probe-macos-26"
if IMAGE not in ("os-probe-macos-26", "os-probe-macos-15"):
    print(f"measure_button_layers: unknown image folder {IMAGE!r}", file=sys.stderr)
    sys.exit(2)
RUN = f"docs/evidence/os-probe/2026-11-06-run-42272240639/{IMAGE}"
# pass name: (folder, sheets with every state, sheets with disabled_pressed only, (isKeyWindow, NSApp isActive),
#             the settings.txt lines required)
PASSES = {
    "key": ("button-pass", ("default_a", "default_b", "default_c", "image_a", "image_b", "image_c"),
            ("push", "styles_a", "styles_b", "styles_c"), (True, True), None),
    "key_not_main": ("button-pass-key-not-main", ("push", "styles_a", "styles_b", "styles_c"), (), (True, True),
                     ("no setting changed",)),
    "main_not_key": ("button-pass-main-not-key", ("push", "styles_a", "styles_b", "styles_c"), (), (False, True),
                     ("no setting changed",)),
    "inactive_contrast": ("button-pass-inactive-increase-contrast-on", ("push", "styles_a", "styles_b", "styles_c"),
                          (), (False, False), ("write increaseContrast true: exit 0", "read back: 1")),
}
APPEARANCES = ("aqua", "darkAqua")
STATES = ("normal", "pressed", "disabled", "disabled_pressed")
SIDES = ("top", "right", "bottom", "left")
CORNERS = ("top_left", "top_right", "bottom_right", "bottom_left")


class Bad(Exception):
    pass


def read_png(path: Path):
    """(width, height, rows of (r, g, b, a)) of an 8-bit, non-interlaced RGB or RGBA PNG."""
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
    width, height, depth, colour, _, _, interlace = ihdr
    if depth != 8 or colour not in (2, 6) or interlace != 0:
        raise Bad(f"{path}: depth {depth}, colour type {colour}, interlace {interlace}: not read here")
    bpp = 4 if colour == 6 else 3
    raw = zlib.decompress(idat)
    stride = width * bpp
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(height):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 0xFF
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 0xFF
        elif f == 3:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + (a + prev[x]) // 2) & 0xFF
        elif f == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[x] = (line[x] + pred) & 0xFF
        elif f != 0:
            raise Bad(f"{path}: filter {f}")
        rows.append([tuple(line[x:x + bpp]) + ((255,) if bpp == 3 else ()) for x in range(0, stride, bpp)])
        prev = line
    return width, height, rows


class Layer:
    def __init__(self, path: Path, origin=(0, 0)):
        self.w, self.h, self.rows = read_png(path)
        self.ox, self.oy = origin

    def px(self, x, y):
        x, y = x - self.ox, y - self.oy
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.rows[y][x]
        return (0, 0, 0, 0)


def hexa(p):
    return "#%02x%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in p)


def near(p, q, d):
    return all(abs(a - b) <= d for a, b in zip(p, q))


def same_paint(p, q, d=3):
    """Two straight pixels the same colour and alpha within d levels; two nearly transparent pixels are equal."""
    if p[3] < 8 and q[3] < 8:
        return True
    return near(p, q, d)


def drawn_box(layer, fr):
    x0, y0, w, h = fr
    xs, ys, n = [], [], 0
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if layer.px(x, y)[3] >= 4:
                xs.append(x)
                ys.append(y)
                n += 1
    if not n:
        return None
    return (min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, n)


def mode_fill(layer, box):
    x0, y0, w, h = box[:4]
    pix = [layer.px(x, y) for y in range(y0 + 2, y0 + h - 2) for x in range(x0 + 2, x0 + w - 2)]
    if not pix:
        return None, 0.0, []
    m, _ = Counter(pix).most_common(1)[0]
    share = sum(1 for p in pix if near(p, m, 2)) / len(pix)
    return m, share, [(x, y) for y in range(y0 + 2, y0 + h - 2) for x in range(x0 + 2, x0 + w - 2)
                      if near(layer.px(x, y), m, 2)]


def edges(layer, box, fill):
    x0, y0, w, h = box[:4]
    cx, cy = x0 + w // 2, y0 + h // 2
    lines = {"top": [(cx, y0), (cx, y0 + 1)], "bottom": [(cx, y0 + h - 1), (cx, y0 + h - 2)],
             "left": [(x0, cy), (x0 + 1, cy)], "right": [(x0 + w - 1, cy), (x0 + w - 2, cy)]}
    out = {}
    for side, (a, b) in lines.items():
        e0, e1 = layer.px(*a), layer.px(*b)
        if fill is None:
            if e0[3] < 8 and e1[3] < 8:
                cls = "absent"
            elif e1[3] < 8:
                cls = {"width": 1, "edge": hexa(e0)}
            else:
                cls = "unclassified"
        else:
            at_cov = (e0[3] <= fill[3] + 3) and (e0[3] < 8 or near(e0[:3], fill[:3], 3))
            if same_paint(e1, fill) and (same_paint(e0, fill) or at_cov):
                cls = "absent"
            elif same_paint(e1, fill):
                cls = {"width": 1, "edge": hexa(e0)}
            else:
                cls = "unclassified"
        out[side] = (cls, [hexa(e0), hexa(e1)])
    return out


def row_median(vals):
    v = sorted(vals)
    return v[len(v) // 2] if v else None


def corner_profile(layer, box, corner):
    x0, y0, w, h = box[:4]
    top = corner.startswith("top")
    left = corner.endswith("left")
    half = w // 2
    prof, flat = [], 0
    for i in range(min(40, (h + 1) // 2)):
        y = y0 + i if top else y0 + h - 1 - i
        alphas = [layer.px(x, y)[3] for x in range(x0, x0 + w) if layer.px(x, y)[3] >= 8]
        med = row_median(alphas)
        if not med:
            prof.append(float(half))
            continue
        inset = 0.0
        for j in range(half):
            x = x0 + j if left else x0 + w - 1 - j
            cov = min(1.0, max(0.0, layer.px(x, y)[3] / med))
            if cov >= 0.98:
                break
            inset += 1.0 - cov
        prof.append(inset)
        if inset < 0.02:
            flat += 1
            if flat >= 2:
                break
        else:
            flat = 0
    return prof


def row_area(r, i):
    """The area a circle of radius r in a corner leaves uncovered in pixel row i (from the corner's edge)."""
    s = 0.0
    for k in range(16):
        y = i + (k + 0.5) / 16
        if y < r:
            s += r - sqrt(max(0.0, r * r - (r - y) * (r - y)))
    return s / 16


def fit(prof):
    best = None
    for step in range(1, 161):
        r = step * 0.25
        sse = sum((row_area(r, i) - m) ** 2 for i, m in enumerate(prof))
        if best is None or sse < best[1]:
            best = (r, sse)
    return best[0], sqrt(best[1] / len(prof))


def colour_of(layer, rect, fill):
    """The title's or image's colour (see the docstring), or None."""
    x0, y0, w, h = rect
    pix = [layer.px(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w)]
    if not pix:
        return None, 0
    if fill is None:
        amax = max(p[3] for p in pix)
        if amax < 8:
            return None, 0
        top = [p for p in pix if p[3] >= amax - 2]
        return hexa([sum(p[c] for p in top) / len(top) for c in range(3)] + [amax]), len(top)
    fa = fill[3] / 255
    if fill[3] >= 250:
        far = max(pix, key=lambda p: sum((p[c] - fill[c]) ** 2 for c in range(3)))
        if sum((far[c] - fill[c]) ** 2 for c in range(3)) < 48 ** 2:
            return None, 0
        return hexa(list(far[:3]) + [255]), 1
    sol = []
    for p in pix:
        a = p[3] / 255
        if a <= fa + 2 / 255:
            continue
        al = (a - fa) / (1 - fa)
        col = [(p[c] / 255 * a - fill[c] / 255 * fa * (1 - al)) / al for c in range(3)]
        sol.append((al, col))
    if not sol:
        return None, 0
    amax = max(s[0] for s in sol)
    top = [s for s in sol if s[0] >= amax - 2 / 255]
    col = [255 * sum(s[1][c] for s in top) / len(top) for c in range(3)]
    return hexa(col + [255 * amax]), len(top)


def covered(col, fill):
    """Whether a colour `colour_of` read is a fully covered pixel of opaque paint (the docstring's rule for `icon`)."""
    if fill is not None and fill[3] >= 250:
        return col[:7] in ("#000000", "#ffffff") and hexa(fill)[:7] != col[:7]
    return col[7:9] == "ff"


def shadow(layer, fr):
    x0, y0, w, h = fr
    n = 0
    for y in range(y0 - 6, y0 + h + 6):
        for x in range(x0 - 6, x0 + w + 6):
            if x0 <= x < x0 + w and y0 <= y < y0 + h:
                continue
            if layer.px(x, y)[3] >= 3:
                n += 1
    return n


def grey_delta(layer, grey, pts):
    d = 0
    for x, y in pts:
        p, g = layer.px(x, y), grey.px(x, y)
        a = p[3] / 255
        for c in range(3):
            d = max(d, abs(p[c] * a + 128 * (1 - a) - g[c]))
    return round(d, 3)


def toml_val(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return '"' + v + '"'
    if isinstance(v, list):
        return "[" + ", ".join(toml_val(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{k} = {toml_val(x)}" for k, x in v.items()) + " }"
    raise Bad(f"value {v!r}")


def measure_button(layer, fr, cell, grey):
    out = {}
    box = drawn_box(layer, fr)
    if box is None:
        out["fill"] = "absent"
        out["stroke"] = "absent"
        out["shadow"] = "absent" if shadow(layer, fr) == 0 else "drawn"
        return out
    out["drawn_box"] = list(box)
    m, share, fill_pts = mode_fill(layer, box)
    fill = None
    if m is None or m[3] < 3:
        out["fill"] = "absent"
    elif share < 0.35:
        out["fill"] = "non_uniform"
        out["fill_share"] = round(share, 3)
    else:
        fill = m
        out["fill"] = hexa(m)
        out["fill_share"] = round(share, 3)
        if grey is not None:
            out["fill_grey_delta"] = grey_delta(layer, grey, fill_pts)
    fx, fy = fr[0], fr[1]
    content = [(fx + int(r[0]) - 1, fy + int(r[1]) - 1, int(r[2]) + 2, int(r[3]) + 2)
               for r in (cell.get("cell_titleRectForBounds_xywh"), cell.get("cell_imageRectForBounds_xywh"))
               if r and r[2] > 0 and r[3] > 0]
    label_only = fill is None and out["fill"] == "absent" and any(
        c[0] <= box[0] and c[1] <= box[1] and box[0] + box[2] <= c[0] + c[2] and box[1] + box[3] <= c[1] + c[3]
        for c in content)
    if label_only:
        out["drawn_only_content"] = True
        out["stroke"] = "absent"
    elif out["fill"] != "non_uniform":
        es = edges(layer, box, fill)
        if grey is not None:
            out["edge_grey_delta"] = grey_delta(layer, grey, edge_points(box))
        if all(c == "absent" for c, _ in es.values()):
            out["stroke"] = "absent"
        for side in SIDES:
            cls, e = es[side]
            out[f"edge_{side}"] = e
            if out.get("stroke") != "absent":
                out[f"stroke_{side}"] = cls
    if fill is not None:
        for c in CORNERS:
            prof = corner_profile(layer, box, c)
            r, rms = fit(prof)
            spelled = ({"full": {"maximum_px": "absent"}} if abs(r - min(box[2], box[3]) / 2) <= 0.75
                       else f"{r:g}px")
            out[f"corner_{c}"] = {"insets_px": [round(v, 3) for v in prof], "radius_px": r,
                                  "rms_px": round(rms, 3), "radius": spelled}
    for name, key in (("label", "cell_titleRectForBounds_xywh"), ("icon", "cell_imageRectForBounds_xywh")):
        rect = cell.get(key)
        if not rect or rect[2] <= 0 or rect[3] <= 0:
            continue
        r = (fx + int(rect[0]), fy + int(rect[1]), int(rect[2]), int(rect[3]))
        col, n = colour_of(layer, r, fill if out["fill"] not in ("absent", "non_uniform") else None)
        if out["fill"] == "non_uniform" or col is None:
            continue
        peak = name == "icon" and not covered(col, fill if out["fill"] not in ("absent", "non_uniform") else None)
        out[f"{name}_peak" if peak else name] = col
        out[f"{name}_pixels"] = n
        if grey is not None:
            pts = [(x, y) for y in range(r[1], r[1] + r[3]) for x in range(r[0], r[0] + r[2])
                   if layer.px(x, y)[3] >= 0.9 * max(layer.px(xx, yy)[3] for yy in range(r[1], r[1] + r[3])
                                                     for xx in range(r[0], r[0] + r[2]))]
            out[f"{name}_grey_delta"] = grey_delta(layer, grey, pts)
    n = shadow(layer, fr)
    out["shadow"] = "absent" if n == 0 else "drawn"
    out["shadow_pixels"] = n
    if grey is not None:
        out["shadow_grey_delta"] = grey_delta(layer, grey, ring_points(fr))
    return out


def edge_points(box):
    """The pixels `edges` reads: the first two from each side's edge along the box's middle row or column."""
    x0, y0, w, h = box[:4]
    cx, cy = x0 + w // 2, y0 + h // 2
    return [(cx, y0), (cx, y0 + 1), (cx, y0 + h - 1), (cx, y0 + h - 2),
            (x0, cy), (x0 + 1, cy), (x0 + w - 1, cy), (x0 + w - 2, cy)]


def ring_points(fr):
    """The pixels `shadow` reads: the frame grown by 6 px, outside the frame."""
    x0, y0, w, h = fr
    return [(x, y) for y in range(y0 - 6, y0 + h + 6) for x in range(x0 - 6, x0 + w + 6)
            if not (x0 <= x < x0 + w and y0 <= y < y0 + h)]


def emit(lines, path, table):
    lines.append(f"[{path}]")
    for k, v in table.items():
        lines.append(f"{k} = {toml_val(v)}")
    lines.append("")


FILES = {}


def out_file(name):
    return FILES.setdefault(name, {"lines": [], "images": []})


FILES = {}


def out_file(name):
    return FILES.setdefault(name, {"lines": [], "images": []})


def main():
    root = Path(RUN)
    for pname, (pdir, full, dp_only, (want_key, want_active), settings) in PASSES.items():
        probe_rel = f"{RUN}/{pdir}/probe.toml"
        probe = tomllib.loads((root / pdir / "probe.toml").read_text())
        bp = probe["macos"]["button_pass"]
        sheets = bp["sheets"]
        set_rel = None
        if settings is not None:
            text = (root / pdir / "settings.txt").read_text()
            for need in settings:
                if not any(line.startswith(need) for line in text.splitlines()):
                    raise Bad(f"{pdir}/settings.txt: no line {need!r}")
            set_rel = f"{RUN}/{pdir}/settings.txt"
        for sheet in full + dp_only:
            s = sheets[sheet]
            f = out_file(f"layers-{pname}-{sheet}")
            f["images"].append(probe_rel)
            if set_rel:
                f["images"].append(set_rel)
            for ap in APPEARANCES:
                for st in (STATES if sheet in full else ("disabled_pressed",)):
                    cap = s[ap][st]
                    if cap.get("isKeyWindow_before") is not want_key or cap.get("isKeyWindow_after") is not want_key \
                            or cap.get("NSApp_isActive_before") is not want_active \
                            or cap.get("NSApp_isActive_after") is not want_active:
                        raise Bad(f"{pdir} {sheet} {ap} {st}: the window or application state is not the pass's")
                    lay = cap["layer"]
                    rel = Path(pdir) / lay["file"]
                    layer = Layer(root / rel)
                    f["images"].append(f"{RUN}/{rel}")
                    og = cap.get("over_grey")
                    if not isinstance(og, dict) or og.get("backdrop_raw") != "#808080ff":
                        raise Bad(f"{pdir} {sheet} {ap} {st}: no capture over #808080ff")
                    grel = Path(pdir) / og["file"]
                    grey = Layer(root / grel)
                    f["images"].append(f"{RUN}/{grel}")
                    for b, bt in lay["buttons"].items():
                        res = measure_button(layer, bt["frame_px_xywh"], s["buttons"][b], grey)
                        emit(f["lines"], f"{pname}.{sheet}.{ap}.{st}.{b}", res)
    for name, f in FILES.items():
        head = [f"# Output of analysis/measure_button_layers.py (its docstring is the method), file {name}.toml.",
                "# input_image: every file this part reads (layers, their captures over grey, the probe.toml files",
                "# whose frames and cell rects it takes, and the pass's settings.txt where it checks the pass's setting).",
                "input_image = ["]
        head += [f'    "{x}",' for x in dict.fromkeys(f["images"])] + ["]", ""]
        (root / f"{name}.toml").write_text("\n".join(head + f["lines"]), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except (Bad, OSError, KeyError) as e:
        print(f"measure_button_layers: {e}", file=sys.stderr)
        sys.exit(1)
