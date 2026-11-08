#!/usr/bin/env python3
"""Reads the iPad focus pass of the iOS host's run 42275053139 (tools/ios-host, `focus` mode, Full Keyboard Access on)
into the values the facts cite: the focus halo UIKit draws around a focused button, and the button's own readings while
focused.

Run from the repository root, once per image folder:

    python3 -I docs/evidence/ios-host/2026-11-06-run-42275053139/analysis/press_focus.py \
        docs/evidence/ios-host/2026-11-06-run-42275053139/ios-host-macos-26

Reads the folder's focus1/index.toml (a `[[render]]` per cell: the button's frame in its cell, `is_focused`, its
configuration as `updated(for:)` resolves it, its title font and colour, its view tree) and, for each of UIKit's own
specimens (the configuration styles at medium and the system type; not the `+focusable_subclass` copies), its two crops
of the simulator's screenshot over the system background, focus1/screen/<appearance>/<specimen>/<size>/system/
normal.png and focused.png (the cell's pixels at the screen's scale, 2 on the iPad). Writes <folder>/press_focus.toml.
Needs Pillow.

Coordinates: the crop is the cell; the button's frame in device pixels is frame_pt times the scale, its edges X0, Y0
(left, top) and X1, Y1 (right, bottom), each a whole pixel in this run. A pixel "differs" where the focused crop's RGB
differs from the normal crop's.

`[halo.<appearance>.<specimen>]`, the focus halo, read on the frame's centre lines (the row through the frame's
vertical centre and the column through its horizontal centre), where the halo's band crosses each straight edge:
- `color`: the focused crop's commonest colour among the differing pixels of the four crossings, `#rrggbb` (the
  pixels the band covers fully);
- on each side, the run of differing pixels that contains the frame's edge pixel (the left side: the run on the
  centre row containing X0; the right: containing X1 - 1; top and bottom likewise on the centre column): its outer end
  and its inner end. `width` is the run's length (the four runs' lengths agree, else `width = "unread"`), and
  `offset_<side>` the distance from the frame's edge to the run's inner end, outward positive (S2.10: to the ring's
  inner edge), both divided by the scale (points, the model's px). Where the bezel under the band has the halo's colour
  (filled on iOS 18 in the light appearance), the inner pixels do not differ, so the run reads short: such a side is
  read only from specimens whose band covers no bezel of that colour, and `width`, `offset_*` are written only where
  all four runs end on pixels that are not the halo's colour in the normal crop (else "unread").
- `solid`: true where every pixel of the band's middle line along its straight stretches has the halo's colour (no
  dash): the column of each side run's middle pixel from Y0 + e to Y1 - e, and the row of the top and bottom runs'
  middle pixels from X0 + e to X1 - e, e the largest corner radius of the view tree in pixels plus the band's width
  (so the corners are left out; a capsule has no straight vertical stretch); "unread" where no stretch remains.
- `outside_max_levels`: the largest per-channel difference among differing pixels farther than one pixel outside the
  band's outer box (X0, Y0, X1, Y1 grown by the band's outer distance), 0 where there is none: a halo with a shadow
  or glow would differ there. `outside_pixels` their count.
- `centre_unchanged`: true where no pixel differs inside the frame shrunk by the band's inner distance plus 1 pixel
  and, horizontally, by r (the corners' extent): the button's own drawing is the same focused and not.

`[cells.<appearance>.<specimen>]`, from the focused `[[render]]` (configuration styles only):
- `is_focused`, `can_become_focused`: UIKit's answers in the focused cell;
- `same_as_normal`: true where the focused cell's configuration, title font, title colour and view tree equal the
  normal cell's (key by key);
- `padding_top`, `padding_left`, `padding_bottom`, `padding_right`: `content_insets_pt` (top, leading, bottom,
  trailing; left to right, so leading is left), points;
- `icon_placement`: `image_placement`; `icon_text_gap`: `image_padding_pt`; `subtitle_gap`: `title_padding_pt`;
- `font_family`, `font_size`: the title font's family and point size;
- `opacity`: the button view's alpha times its layer's opacity (view tree path "0").

`[token.<appearance>]`: the halo's readings where every specimen of the appearance gives the same one (else
"unread"): `color`, `width`, `offset_top`, `offset_right`, `offset_bottom`, `offset_left`, `kind` ("ring" where
every specimen's halo is a band on all four sides and its centre is unchanged), `dash` ("solid" where every specimen's
band is solid), `shadow` ("absent" where no specimen differs farther than one pixel outside its band).
"""
import sys
import tomllib
from collections import Counter
from pathlib import Path

from PIL import Image


def toml_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return repr(round(v, 4))
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    raise TypeError(v)


def runs(flags):
    out = []
    for i, f in enumerate(flags):
        if f:
            if out and out[-1][1] == i - 1:
                out[-1][1] = i
            else:
                out.append([i, i])
    return out


def run_containing(rs, i):
    for r in rs:
        if r[0] <= i <= r[1]:
            return r
    return None


def main(folder):
    folder = Path(folder)
    index = folder / "focus1" / "index.toml"
    d = tomllib.loads(index.read_text())
    sc = d["screen"]["scale"]
    renders = {(r["appearance"], r["specimen"], r["state"]): r for r in d["render"]}
    inputs = [str(index)]
    halo, cells = {}, {}
    for (app, spec, state), f in sorted(renders.items()):
        if state != "focused" or "focusable_subclass" in spec:
            continue
        n = renders[(app, spec, "normal")]
        fp = folder / "focus1" / f["screen"]
        np_ = folder / "focus1" / n["screen"]
        inputs += [str(np_), str(fp)]
        a = Image.open(np_).convert("RGB")
        b = Image.open(fp).convert("RGB")
        W, H = b.size
        fr = f["frame_pt"]
        X0, Y0 = round(fr[0] * sc), round(fr[1] * sc)
        X1, Y1 = round((fr[0] + fr[2]) * sc), round((fr[1] + fr[3]) * sc)
        cy, cx = (Y0 + Y1) // 2, (X0 + X1) // 2
        diff = lambda x, y: a.getpixel((x, y)) != b.getpixel((x, y))
        row = runs([diff(x, cy) for x in range(W)])
        col = runs([diff(cx, y) for y in range(H)])
        left, right = run_containing(row, X0), run_containing(row, X1 - 1)
        top, bottom = run_containing(col, Y0), run_containing(col, Y1 - 1)
        h = {}
        crossing = []
        for r, horiz in ((left, True), (right, True), (top, False), (bottom, False)):
            if r:
                crossing += [((x, cy) if horiz else (cx, x)) for x in range(r[0], r[1] + 1)]
        color = Counter(b.getpixel(p) for p in crossing).most_common(1)[0][0] if crossing else None
        h["color"] = "#%02x%02x%02x" % color if color else "unread"
        ok = all((left, right, top, bottom))
        if ok:
            # the run's inner end must not border a pixel of the halo's colour in the normal crop
            inner_px = [(left[1] + 1, cy), (right[0] - 1, cy), (cx, top[1] + 1), (cx, bottom[0] - 1)]
            ok = all(a.getpixel(p) != color for p in inner_px)
        lengths = {r[1] - r[0] + 1 for r in (left, right, top, bottom) if r}
        if ok and len(lengths) == 1:
            wpx = lengths.pop()
            h["width"] = wpx / sc
            h["offset_left"] = -(left[1] + 1 - X0) / sc
            h["offset_right"] = -(X1 - right[0]) / sc
            h["offset_top"] = -(top[1] + 1 - Y0) / sc
            h["offset_bottom"] = -(Y1 - bottom[0]) / sc
            outer = X0 - left[0]
            inner = left[1] + 1 - X0
            rad = max([v.get("corner_radius_pt", 0.0) for v in f["view"]] + [0.0]) * sc
            ext = int(rad) + wpx
            mid_l, mid_r = (left[0] + left[1]) // 2, (right[0] + right[1]) // 2
            mid_t, mid_b = (top[0] + top[1]) // 2, (bottom[0] + bottom[1]) // 2
            line = [(mid_l, y) for y in range(Y0 + ext, Y1 - ext)] + [(mid_r, y) for y in range(Y0 + ext, Y1 - ext)]
            line += [(x, mid_t) for x in range(X0 + ext, X1 - ext)] + [(x, mid_b) for x in range(X0 + ext, X1 - ext)]
            h["solid"] = all(b.getpixel(q) == color for q in line) if line else "unread"
            out = []
            for y in range(H):
                for x in range(W):
                    if x < X0 - outer - 1 or x >= X1 + outer + 1 or y < Y0 - outer - 1 or y >= Y1 + outer + 1:
                        if diff(x, y):
                            out.append(max(abs(p - q) for p, q in zip(a.getpixel((x, y)), b.getpixel((x, y)))))
            h["outside_pixels"] = len(out)
            h["outside_max_levels"] = max(out, default=0)
            changed = 0
            for y in range(Y0 + inner + 1, Y1 - inner - 1):
                for x in range(int(X0 + max(rad, inner + 1)), int(X1 - max(rad, inner + 1))):
                    changed += diff(x, y)
            h["centre_unchanged"] = changed == 0
        else:
            for k in ("width", "offset_left", "offset_right", "offset_top", "offset_bottom"):
                h[k] = "unread"
        halo.setdefault(app, {})[spec] = h
        if f["kind"] == "configuration":
            c = f["configuration"]
            keys = ("configuration", "title_font", "title_color", "view")
            ci = c["content_insets_pt"]
            cells.setdefault(app, {})[spec] = {
                "is_focused": f["is_focused"],
                "can_become_focused": f["can_become_focused"],
                "same_as_normal": all(f[k] == n[k] for k in keys),
                "padding_top": ci[0], "padding_left": ci[1], "padding_bottom": ci[2], "padding_right": ci[3],
                "icon_placement": c["image_placement"],
                "icon_text_gap": c["image_padding_pt"],
                "subtitle_gap": c["title_padding_pt"],
                "font_family": f["title_font"]["family"],
                "font_size": f["title_font"]["size_pt"],
                "opacity": f["view"][0]["alpha"] * f["view"][0]["layer_opacity"],
            }
    token = {}
    for app, specs in halo.items():
        t = {}
        for k in ("color", "width", "offset_top", "offset_right", "offset_bottom", "offset_left"):
            vals = {s[k] for s in specs.values() if s.get(k) != "unread"}
            t[k] = vals.pop() if len(vals) == 1 else "unread"
        read = [s for s in specs.values() if s.get("width") != "unread"]
        t["kind"] = "ring" if read and all(s["centre_unchanged"] is True for s in read) else "unread"
        t["dash"] = "solid" if read and all(s["solid"] is True for s in read) else "unread"
        t["shadow"] = "absent" if read and all(s["outside_pixels"] == 0 for s in read) else "unread"
        t["specimens_read"] = len(read)
        t["specimens"] = len(specs)
        token[app] = t
    lines = [f"# Output of analysis/press_focus.py (its docstring is the method) over {folder}.", "input_image = ["]
    lines += [f"    {toml_value(p)}," for p in inputs] + ["]", ""]
    for app in sorted(token):
        lines.append(f"[token.{app}]")
        lines += [f"{k} = {toml_value(v)}" for k, v in token[app].items()] + [""]
    for app in sorted(halo):
        for spec in sorted(halo[app]):
            lines.append(f"[halo.{app}.{spec}]")
            lines += [f"{k} = {toml_value(v)}" for k, v in halo[app][spec].items()] + [""]
    for app in sorted(cells):
        for spec in sorted(cells[app]):
            lines.append(f"[cells.{app}.{spec}]")
            lines += [f"{k} = {toml_value(v)}" for k, v in cells[app][spec].items()] + [""]
    (folder / "press_focus.toml").write_text("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1])
