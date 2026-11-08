#!/usr/bin/env python3
"""Reads the WinUI host's run 1 (`frames.toml` and the recordings it names) as the windows-11 facts' values: the
accent button's and the dialog's default button's box, stroke, focus offset and label font, the caret's width and
secondary caret, the text-rendering settings, the per-language font fallbacks, the colour space of a brush
transition and the scroll into view's duration. The Windows facts lane wrote it (2026-11-07, spec S17 *`evidence`*:
an analysis output for values computed from values a harness read, and for values read from images).

Run from the repository root (Python 3.11+, the standard library only):

    python3 docs/evidence/winui-host/<run>/analysis/read_host.py docs/evidence/winui-host/<run>/winui-host-windows-11-arm

It reads, under that image folder, `frames.toml` (its tables named below), `text-default.png`,
`motion-caret_ltr.png`, `motion-caret_mixed.png`, `motion-caret_mixed_end.png` (each the recording's distinct
frames side by side, 160 px wide each, as the `[[motion]]` table's `screen_rect` gives), and
`motion-color_space_red_to_translucent_blue.csv`, `motion-color_space_translucent_green_to_red.csv`,
`motion-color_space_black_to_white.csv` (every recorded frame's `distinct_index` and its `centre` pixel). It writes
`analysis.toml` into the image folder:

- `[button.primary]` from `[defaults]`' `accent_button_*` (a Button whose Style is AccentButtonStyle) and
  `[button.dialog_default]` from the `[[dialog.button]]` that is the dialog's `default_button` (`PrimaryButton`, its
  style AccentButtonStyle); the host's Thickness strings are `left,top,right,bottom`. Per side:
  `padding_<side>_px = Padding.<side> + BorderThickness.<side>` (S2.11's box: the model's padding is measured from the
  box, the stroke taking no layout space, while WinUI lays the content inside BorderThickness and Padding; the
  shared button facts state the same sum, docs/facts/windows/button.toml), `stroke_<side>_width_px =
  BorderThickness.<side>`, `focus_offset_<side>_px = -FocusVisualMargin.<side> - FocusVisualPrimaryThickness.<side>`
  (the margin sets the ring's outer edge, the model's offset is to its inner edge, the ring as wide as the primary
  thickness, `token.focus.width`); `label_font_family`, `label_font_size_px`, `label_font_weight` are the label
  TextBlock's FontFamily, FontSize (px, WinUI's unit) and FontWeight. A side whose four values the host did not
  read as numbers is left out.
- `[caret]`: per recording, the columns where consecutive distinct frames differ (the caret blinking on and off;
  every other pixel is unchanged), as `<recording>_columns`, and the runs of adjacent such columns,
  `<recording>_carets`. `width_px` is the number of columns of a run where every recording has one run of one width;
  `secondary` is `"absent"` where `caret_mixed_end` (the caret at the end of `abc אבג`, after the right-to-left run,
  a position with two visual places in a left-to-right field) has one run, so one caret is drawn.
- `[text_rendering]`: `text-default.png`'s pixels other than white, `grey` where the three channels are equal and
  `coloured` otherwise (checked against `[[text_capture]]`' counts); `antialiasing` is `"grayscale"` where coloured is
  0 and grey is not, `"subpixel"` where coloured is not 0. `subpixel_order` maps `[directwrite]`'s
  `default_pixel_geometry` (`RGB` to `"rgb"`, `BGR` to `"bgr"`, `FLAT` to `"none"`); `gamma` and `contrast` are its
  `default_gamma` and `default_enhanced_contrast` (ClearType's enhanced contrast), each written only where the
  monitor's parameters (`monitor_*`) equal the defaults; `grayscale_enhanced_contrast` is recorded beside them.
- `[fallbacks]`: `per_language`, per `[[font_fallback]]` whose `base_family` is `Segoe UI Variable` (WinUI's
  default family) and whose sample is its locale's first (the en-US emoji and symbol samples are no language's
  text), the locale and the families its runs map to (each run's family, before ` Regular`/the style, in run order,
  each once). `same_as_no_base` is true where the entries with no base family give the same map.
- `[color_space]`: per recording, each distinct frame's centre pixel against the colour a transition from `from` to
  `to` (the `[[motion]]` table's) draws over white at progress t, under three interpolations: `straight` (each
  8-bit channel and the alpha interpolated apart, then composited over white), `premultiplied` (each channel times
  its alpha, and the alpha, interpolated apart, then composited) and `oklab` (L, a, b and the straight alpha
  interpolated apart, back to sRGB, then composited); per frame the t of 0..1 in steps of 1/2000 that fits best,
  and per recording and interpolation the largest channel difference left (`<recording>_<space>_worst`, 8-bit
  levels). `space` names the one interpolation that fits every recording within 2 levels while every other fails
  some recording by more: `straight` is the model's `straight_srgb8` (S2.7: straight 8-bit channels; its
  truncation toward zero lies within this precision), `premultiplied` its `premultiplied_srgb`, `oklab` its `oklab`.
- `[scroll_into_view]`: the passes `scroll_into_view_focus` and `scroll_into_view_focus_next` (a TextBox below the
  ScrollViewer's view focused by keyboard); `duration_ms` is 0 where each pass's `view_events` hold no inertial view
  change (`inertial True`) and one `changed` event, not intermediate: the view moves to its final offset in one
  step.

`input_image` names every file read, as repository paths.
"""

import csv
import math
import struct
import sys
import tomllib
import zlib
from pathlib import Path

CARETS = ("caret_ltr", "caret_mixed", "caret_mixed_end")
SPACES = ("color_space_red_to_translucent_blue", "color_space_translucent_green_to_red",
          "color_space_black_to_white")
SIDES = ("left", "top", "right", "bottom")   # a XAML Thickness string's order
PIXEL_GEOMETRY = {"RGB": "rgb", "BGR": "bgr", "FLAT": "none"}


def read_png(path):
    """(width, height, rows of (r, g, b[, a]) tuples) of an 8-bit RGB or RGBA, non-interlaced PNG."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    i, idat, head = 8, b"", None
    while i < len(data):
        n = struct.unpack(">I", data[i:i + 4])[0]
        kind, chunk = data[i + 4:i + 8], data[i + 8:i + 8 + n]
        if kind == b"IHDR":
            head = struct.unpack(">IIBBBBB", chunk)
        elif kind == b"IDAT":
            idat += chunk
        i += 12 + n
    w, h, depth, colour, _, _, interlace = head
    if depth != 8 or colour not in (2, 6) or interlace != 0:
        raise ValueError(f"{path}: not 8-bit RGB(A), non-interlaced")
    bpp = 4 if colour == 6 else 3
    raw, stride, pos = zlib.decompress(idat), w * bpp, 0
    prev, rows = bytearray(stride), []
    for _ in range(h):
        filt = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if filt == 1:
                line[x] = (line[x] + a) & 255
            elif filt == 2:
                line[x] = (line[x] + b) & 255
            elif filt == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif filt == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append([tuple(line[x * bpp:x * bpp + bpp]) for x in range(w)])
        prev = line
    return w, h, rows


def thickness(s):
    """A XAML Thickness string `l,t,r,b` as {side: number}, or None."""
    try:
        parts = [float(p) for p in str(s).split(",")]
    except ValueError:
        return None
    return dict(zip(SIDES, parts)) if len(parts) == 4 else None


def num(x):
    return int(x) if float(x).is_integer() else x


def button_lines(name, padding, border, margin, primary, family, size, weight):
    out = [f"\n[button.{name}]"]
    p, b, m, f = thickness(padding), thickness(border), thickness(margin), thickness(primary)
    for side in ("top", "right", "bottom", "left"):
        if p and b:
            out.append(f"padding_{side}_px = {num(p[side] + b[side])}")
    for side in ("top", "right", "bottom", "left"):
        if b:
            out.append(f"stroke_{side}_width_px = {num(b[side])}")
    for side in ("top", "right", "bottom", "left"):
        if m and f:
            out.append(f"focus_offset_{side}_px = {num(-m[side] - f[side])}")
    out += [f'label_font_family = "{family}"', f"label_font_size_px = {num(size)}",
            f"label_font_weight = {int(weight)}"]
    return out


def srgb_to_linear(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c):
    c = min(max(c, 0.0), 1.0)
    return 255 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)


def to_oklab(rgb):
    r, g, b = (srgb_to_linear(c) for c in rgb)
    l_ = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m_ = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)


def from_oklab(lab):
    lo, a, b = lab
    l_ = (lo + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (lo - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (lo - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (linear_to_srgb(4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_),
            linear_to_srgb(-1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_),
            linear_to_srgb(-0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_))


def drawn(fr, to, t, space):
    """The colour over white at progress t, as 8-bit channels (unrounded)."""
    fa, ta = fr[3] / 255, to[3] / 255
    a = fa + (ta - fa) * t
    if space == "straight":
        rgb = [f + (g - f) * t for f, g in zip(fr[:3], to[:3])]
        return [a * c + (1 - a) * 255 for c in rgb]
    if space == "premultiplied":
        return [f * fa + (g * ta - f * fa) * t + (1 - a) * 255 for f, g in zip(fr[:3], to[:3])]
    lf, lt = to_oklab(fr[:3]), to_oklab(to[:3])
    rgb = from_oklab([f + (g - f) * t for f, g in zip(lf, lt)])
    return [a * c + (1 - a) * 255 for c in rgb]


def hexrgb(s):
    s = s.lstrip("#")
    return [int(s[i:i + 2], 16) for i in range(0, len(s), 2)]


def argb(s):
    """`#aarrggbb` (the host's colour form) as (r, g, b, a)."""
    a, r, g, b = hexrgb(s)
    return (r, g, b, a)


def main():
    if len(sys.argv) != 2:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    image = Path(sys.argv[1])
    frames = tomllib.loads((image / "frames.toml").read_text())
    motion = {m["name"]: m for m in frames["motion"]}
    read = ["frames.toml", "text-default.png"] + [f"motion-{n}.png" for n in CARETS] + \
        [f"motion-{n}.csv" for n in SPACES]
    lines = ["# Output of analysis/read_host.py (its docstring is the method), file analysis.toml.",
             "# input_image: every file it reads, as a repository path (spec S17 *`evidence`*).",
             "input_image = [" + ", ".join(f'"{image.as_posix()}/{rel}"' for rel in read) + "]"]

    d = frames["defaults"]
    lines += button_lines("primary", d["accent_button_padding"], d["accent_button_border_thickness"],
                          d["accent_button_focus_visual_margin"], d["accent_button_focus_visual_primary_thickness"],
                          d["accent_button_label_font_family"], d["accent_button_label_font_size"],
                          d["accent_button_label_font_weight"])
    default = frames["dialog"]["default_button"] + "Button"
    for b in frames["dialog"]["button"]:
        if b["name"] == default and b["style_is_accent_button_style"] is True:
            lines += button_lines("dialog_default", b["button_padding"], b["button_border_thickness"],
                                  b["button_focus_visual_margin"], b["button_focus_visual_primary_thickness"],
                                  b["button_label_font_family"], b["button_label_font_size"],
                                  b["button_label_font_weight"])

    lines.append("\n[caret]")
    widths, runs_end = set(), None
    for n in CARETS:
        w, h, rows = read_png(image / f"motion-{n}.png")
        fw = motion[n]["screen_rect"]["width"]
        count = w // fw
        cols = sorted({x for k in range(count - 1) for y in range(h) for x in range(fw)
                       if rows[y][k * fw + x] != rows[y][(k + 1) * fw + x]})
        runs = []
        for x in cols:
            if runs and x == runs[-1][1] + 1:
                runs[-1][1] = x
            else:
                runs.append([x, x])
        lines.append(f"{n}_columns = {cols}")
        lines.append(f"{n}_carets = {len(runs)}")
        widths |= {b - a + 1 for a, b in runs}
        if len(runs) != 1:
            widths.add(None)
        if n == "caret_mixed_end":
            runs_end = len(runs)
    if len(widths) == 1 and None not in widths:
        lines.append(f"width_px = {widths.pop()}")
    if runs_end == 1:
        lines.append('secondary = "absent"')

    lines.append("\n[text_rendering]")
    _, _, rows = read_png(image / "text-default.png")
    grey = coloured = 0
    for row in rows:
        for px in row:
            r, g, b = px[:3]
            if (r, g, b) == (255, 255, 255):
                continue
            if r == g == b:
                grey += 1
            else:
                coloured += 1
    cap = frames["text_capture"][0]
    lines.append(f"grey_pixels = {grey}")
    lines.append(f"coloured_pixels = {coloured}")
    lines.append(f"matches_host_counts = {str(grey == cap['grey_pixels'] and coloured == cap['coloured_pixels']).lower()}")
    if coloured == 0 and grey > 0:
        lines.append('antialiasing = "grayscale"')
    elif coloured > 0:
        lines.append('antialiasing = "subpixel"')
    dw = frames["directwrite"]
    same = all(dw[f"default_{k}"] == dw[f"monitor_{k}"] for k in
               ("gamma", "enhanced_contrast", "pixel_geometry", "grayscale_enhanced_contrast"))
    lines.append(f"monitor_equals_default = {str(same).lower()}")
    if same and dw["default_pixel_geometry"] in PIXEL_GEOMETRY:
        lines.append(f'subpixel_order = "{PIXEL_GEOMETRY[dw["default_pixel_geometry"]]}"')
    if same:
        lines.append(f"gamma = {dw['default_gamma']!r}")
        lines.append(f"contrast = {dw['default_enhanced_contrast']!r}")
        lines.append(f"grayscale_enhanced_contrast = {dw['default_grayscale_enhanced_contrast']!r}")

    def fallback_map(base):
        out, seen = {}, set()
        for f in frames["font_fallback"]:
            if f["base_family"] != base or f["locale"] in seen:
                continue
            seen.add(f["locale"])
            fams = []
            for run in f["runs"]:
                fam = run.split(" -> ", 1)[1].split(" (weight", 1)[0]
                fam = fam[:-len(" Regular")] if fam.endswith(" Regular") else fam
                if fam not in fams:
                    fams.append(fam)
            out[f["locale"]] = fams
        return out

    per_language = fallback_map("Segoe UI Variable")
    lines.append("\n[fallbacks]")
    lines.append(f"same_as_no_base = {str(per_language == fallback_map('')).lower()}")
    entries = ", ".join(f'"{k}" = [' + ", ".join(f'"{v}"' for v in vs) + "]" for k, vs in per_language.items())
    lines.append("per_language = { " + entries + " }")

    lines.append("\n[color_space]")
    fits = {"straight": True, "premultiplied": True, "oklab": True}
    fails = {k: False for k in fits}
    for n in SPACES:
        fr, to = argb(motion[n]["from"]), argb(motion[n]["to"])
        seen, pixels = set(), []
        with (image / f"motion-{n}.csv").open() as fh:
            for row in csv.DictReader(fh):
                if row["distinct_index"] not in seen:
                    seen.add(row["distinct_index"])
                    pixels.append(hexrgb(row["centre"]))
        for space in fits:
            worst = 0.0
            for px in pixels:
                best = min(max(abs(c - p) for c, p in zip(drawn(fr, to, i / 2000, space), px))
                           for i in range(2001))
                worst = max(worst, best)
            lines.append(f"{n}_{space}_worst = {round(worst, 3)!r}")
            if worst > 2:
                fits[space] = False
                fails[space] = True
    fitting = [s for s, ok in fits.items() if ok]
    if len(fitting) == 1 and all(fails[s] for s in fits if s not in fitting):
        lines.append(f'space = "{ {"straight": "straight_srgb8", "premultiplied": "premultiplied_srgb", "oklab": "oklab"}[fitting[0]] }"')

    lines.append("\n[scroll_into_view]")
    one_step = True
    for n in ("scroll_into_view_focus", "scroll_into_view_focus_next"):
        ev = motion[n]["view_events"]
        changed = [e for e in ev if " changed " in e]
        inertial = [e for e in ev if "inertial True" in e]
        ok = not inertial and len(changed) == 1 and "intermediate False" in changed[0]
        lines.append(f"{n}_one_step = {str(ok).lower()}")
        one_step = one_step and ok
    if one_step:
        lines.append("duration_ms = 0")

    (image / "analysis.toml").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
