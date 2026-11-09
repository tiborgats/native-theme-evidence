#!/usr/bin/env python3
"""Reads the WinUI host's run 1 (`frames.toml` and the recordings it names) as the windows-11 facts' values: the
accent button's and the dialog's default button's box, stroke, focus offset and label font, the caret's width and
secondary caret, the text-rendering settings, the per-language font fallbacks, the colour space of a brush
transition, the scroll into view's duration, and (with the text-scale run) the curve WinUI scales a font size by. The
Windows facts lane wrote it (2026-11-07, spec S17 *`evidence`*: an analysis output for values computed from values a
harness read, and for values read from images); `[text_scale]` added 2026-11-09 (the ledger's U701, ADD-A145).

Run from the repository root (Python 3.11+, the standard library only):

    python3 docs/evidence/winui-host/<run>/analysis/read_host.py docs/evidence/winui-host/<run>/winui-host-windows-11-arm

It reads, under that image folder, `frames.toml` (its tables named below), `text-default.png`,
`motion-caret_ltr.png`, `motion-caret_mixed.png`, `motion-caret_mixed_end.png` (each the recording's distinct
frames side by side, 160 px wide each, as the `[[motion]]` table's `screen_rect` gives), and
`motion-color_space_red_to_translucent_blue.csv`, `motion-color_space_translucent_green_to_red.csv`,
`motion-color_space_black_to_white.csv` (every recorded frame's `distinct_index` and its `centre` pixel), and the
text-scale run's `text-scale/frames.toml` and `text-scale/text-text_scale.png`. It writes `analysis.toml` into the
image folder:

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
- `[text_scale]`: the `[[text]]` TextBlocks of run 1's pass `default` (`[system]` `ui_settings_text_scale_factor`
  1, `base_factor`) and of the text-scale run's pass `text_scale` (`factor`, the same key, 1.5), paired by
  `font_size` (`sizes_px`; each pair the same family and weight, `is_text_scale_factor_enabled` true and
  `line_height` 0, WinUI's auto line height). A TextBlock's auto height is the font's line spacing times the size it
  is drawn at, so the size the text-scale run drew is `implied_px = size * height(factor) / height(base_factor)`
  (`actual_size.height`). That rests on run 1's heights being one multiple of their sizes: `base_height_per_px_spread`
  is the largest less the smallest of `height / size`, and is required to put the largest implied size off by no
  more than the tolerance (`spread * max(implied_px) <= tolerance_px`). The widths are not used: each TextBlock holds
  its own text, so run 1 cannot show a width to be proportional to the size. Each candidate is a member of the
  model's `TextScaling` (spec S9.4) and gives the size at the factor: `linear`, the size times the factor (S9.4: "a
  product"); `dynamic_type`, the size unchanged (S9.4: under `DynamicType` the factor is not read, the content-size
  category alone scales, and a Windows text-scale factor names none); `android_non_linear` and `win_ui`, the rows of
  native-theme's vector tables at factor 1.5 (VECTOR_ROWS: `android_non_linear.tsv`, generated from Android's
  `FontScaleConverter` through its public API, which has no row at 68 px, listed in
  `android_non_linear_unevaluated_px`; `win_ui.tsv`, generated from WinUI's `TextFormatting::GetScaledFontSize`
  compiled unchanged). `<candidate>_worst_px` is the largest `|implied_px - candidate|` over the sizes it has a value
  for. `tolerance_px` is 0.001: the heights are single-precision values (2^-24 relative each) and a table's rows are
  printed to a float's shortest form, so an implied size near 71 px carries an error of the order of 1e-5 px; 0.001
  is a hundred times that. `least_separation_px` is how far the candidates lie apart at these sizes: for each two,
  the largest difference at a size both have a value for, and of those the smallest; it must exceed twice the
  tolerance, so no two candidates can both fit. `fitting` lists the candidates within the tolerance. The captures: run 1's
  `text-default.png` and the text-scale run's `text-text_scale.png` are each their pass's panel (`[[text_capture]]`'s
  `panel_bounds` at 0,0, the PNG's size), so a TextBlock's `bounds` are pixel coordinates in it;
  `<base_|>capture_ink_outside_bounds` counts the non-white pixels overlapping no TextBlock's bounds (each pixel
  the unit square at its coordinates), and `capture_grey_pixels`, `capture_coloured_pixels` and
  `capture_matches_host_counts` are the text-scale capture's, as `[text_rendering]`'s are run 1's. `curve` names the
  member where exactly one candidate fits, every other misses by more than the tolerance, the spread and the
  separation hold, and no drawn pixel of either capture lies outside the bounds (the drawn text is the frames'
  layout); otherwise it is not written and `fitting` states what fits.

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

# [text_scale]'s candidates from native-theme's vector tables, the rows at factor 1.5 (native-theme at 73b5fc33,
# v0.8.0-rc1): size px -> result px. android_non_linear.tsv:242-246, :265, :267, :272 (`size font_scale result`,
# `FontScaleConverter.forScale(1.5).convertSpToDp`; no row at 68 px); win_ui.tsv:538-561 (`size factor result`,
# `TextFormatting::GetScaledFontSize`), the rows at 10, 12, 14, 16, 18, 20, 28, 40 and 68 px.
VECTOR_FACTOR = 1.5
VECTOR_ROWS = {
    "android_non_linear": {10.0: 15.0, 12.0: 18.0, 14.0: 22.0, 16.0: 23.0, 18.0: 24.0, 20.0: 26.0,
                           28.0: 29.333334, 40.0: 40.0},
    "win_ui": {10.0: 15.870462, 12.0: 17.622662, 14.0: 19.413149, 16.0: 21.23166, 18.0: 23.071577,
               20.0: 24.928377, 28.0: 32.471066, 40.0: 43.986294, 68.0: 71.26509},
}
TEXT_SCALE_TOLERANCE_PX = 0.001


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


def capture_ink(png, texts, panel):
    """(non-white pixels overlapping no TextBlock's bounds, grey pixels, coloured pixels) of a capture of the panel,
    or None where the PNG is not the panel's size at 0,0."""
    w, h, rows = read_png(png)
    if (panel["x"], panel["y"], panel["width"], panel["height"]) != (0, 0, w, h):
        return None
    boxes = [(t["bounds"]["x"], t["bounds"]["y"], t["bounds"]["x"] + t["bounds"]["width"],
              t["bounds"]["y"] + t["bounds"]["height"]) for t in texts]
    outside = grey = coloured = 0
    for y in range(h):
        for x in range(w):
            r, g, b = rows[y][x][:3]
            if (r, g, b) == (255, 255, 255):
                continue
            if r == g == b:
                grey += 1
            else:
                coloured += 1
            if not any(x0 < x + 1 and x < x1 and y0 < y + 1 and y < y1 for x0, y0, x1, y1 in boxes):
                outside += 1
    return outside, grey, coloured


def text_scale_lines(image, frames):
    """`[text_scale]` (the docstring's method)."""
    scaled = tomllib.loads((image / "text-scale" / "frames.toml").read_text())
    base_factor = frames["system"]["ui_settings_text_scale_factor"]
    factor = scaled["system"]["ui_settings_text_scale_factor"]
    base = [t for t in frames["text"] if t["pass"] == "default"]
    drawn_scaled = [t for t in scaled["text"] if t["pass"] == "text_scale"]
    out = ["\n[text_scale]", f"base_factor = {float(base_factor)!r}", f"factor = {float(factor)!r}"]
    keys = ("font_family", "font_weight", "is_text_scale_factor_enabled", "line_height")
    paired = (base_factor == 1 and factor == VECTOR_FACTOR and len(base) == len(drawn_scaled) > 0 and
              all(a["font_size"] == b["font_size"] and all(a[k] == b[k] for k in keys) and
                  a["is_text_scale_factor_enabled"] is True and a["line_height"] == 0
                  for a, b in zip(base, drawn_scaled)))
    out.append(f"paired = {str(paired).lower()}")
    if not paired:
        return out
    sizes = [a["font_size"] for a in base]
    implied = [s * b["actual_size"]["height"] / a["actual_size"]["height"]
               for s, a, b in zip(sizes, base, drawn_scaled)]
    per_px = [a["actual_size"]["height"] / s for s, a in zip(sizes, base)]
    spread = max(per_px) - min(per_px)
    out.append("sizes_px = [" + ", ".join(repr(num(s)) for s in sizes) + "]")
    out.append("implied_px = [" + ", ".join(repr(round(v, 6)) for v in implied) + "]")
    out.append(f"base_height_per_px_spread = {float(f'{spread:.3g}')!r}")
    out.append(f"tolerance_px = {TEXT_SCALE_TOLERANCE_PX!r}")
    candidates = {
        "linear": {s: s * factor for s in sizes},
        "dynamic_type": {s: s for s in sizes},
        "android_non_linear": {s: VECTOR_ROWS["android_non_linear"][s] for s in sizes
                               if s in VECTOR_ROWS["android_non_linear"]},
        "win_ui": {s: VECTOR_ROWS["win_ui"][s] for s in sizes if s in VECTOR_ROWS["win_ui"]},
    }
    fitting = []
    for name, values in candidates.items():
        worst = max(abs(v - values[s]) for s, v in zip(sizes, implied) if s in values)
        out.append(f"{name}_worst_px = {float(f'{worst:.3g}')!r}")
        missing = [s for s in sizes if s not in values]
        if missing:
            out.append(f"{name}_unevaluated_px = [" + ", ".join(repr(num(s)) for s in missing) + "]")
        if worst <= TEXT_SCALE_TOLERANCE_PX:
            fitting.append(name)
    names = list(candidates)
    separation = min(max(abs(candidates[p][s] - candidates[q][s]) for s in sizes
                         if s in candidates[p] and s in candidates[q])
                     for i, p in enumerate(names) for q in names[i + 1:])
    out.append(f"least_separation_px = {round(separation, 6)!r}")
    out.append("fitting = [" + ", ".join(f'"{n}"' for n in fitting) + "]")

    base_capture = frames["text_capture"][0]
    capture = scaled["text_capture"][0]
    base_ink = capture_ink(image / base_capture["png"], base, base_capture["panel_bounds"])
    ink = capture_ink(image / "text-scale" / capture["png"], drawn_scaled, capture["panel_bounds"])
    if base_ink is None or ink is None:
        out.append("captures_are_panels = false")
        return out
    out.append(f"base_capture_ink_outside_bounds = {base_ink[0]}")
    out.append(f"capture_ink_outside_bounds = {ink[0]}")
    out.append(f"capture_grey_pixels = {ink[1]}")
    out.append(f"capture_coloured_pixels = {ink[2]}")
    out.append(f"capture_matches_host_counts = "
               f"{str(ink[1] == capture['grey_pixels'] and ink[2] == capture['coloured_pixels']).lower()}")
    if (len(fitting) == 1 and spread * max(implied) <= TEXT_SCALE_TOLERANCE_PX and
            separation > 2 * TEXT_SCALE_TOLERANCE_PX and base_ink[0] == 0 and ink[0] == 0):
        out.append(f'curve = "{fitting[0]}"')
    return out


def main():
    if len(sys.argv) != 2:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    image = Path(sys.argv[1])
    frames = tomllib.loads((image / "frames.toml").read_text())
    motion = {m["name"]: m for m in frames["motion"]}
    read = ["frames.toml", "text-default.png"] + [f"motion-{n}.png" for n in CARETS] + \
        [f"motion-{n}.csv" for n in SPACES] + ["text-scale/frames.toml", "text-scale/text-text_scale.png"]
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

    lines += text_scale_lines(image, frames)

    (image / "analysis.toml").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
