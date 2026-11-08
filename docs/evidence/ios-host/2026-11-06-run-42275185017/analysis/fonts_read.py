#!/usr/bin/env python3
"""Reads the iOS host's fonts pass (run 42275185017, tools/ios-host `Measure.swift`, the `fonts` pass) into the values
the iOS facts cite: the text styles' fonts and their tight, loose and emphasized variants, the configuration buttons'
title and subtitle text, the system button's title, the emoji font and the text antialiasing. The iOS facts lane wrote
it (M1b round 3, 2026-11-07; spec S17 *`evidence`*: an analysis output for values decided from read values).

Run from the repository root, once per image folder (Python 3.11+, the standard library only):

    python3 -I docs/evidence/ios-host/2026-11-06-run-42275185017/analysis/fonts_read.py \
        docs/evidence/ios-host/2026-11-06-run-42275185017/ios-host-macos-26

It reads the folder's `measure1/index.toml` only and writes `fonts_read.toml` beside `measure1/`, its top-level
`input_image` naming that file. Every key below is written only where its rule holds (no key: not decided here).
Lengths are unitless, in points (a logical pixel on iOS, spec S17); the axis tags are the OpenType four-letter tags of
the variation's numeric identifiers (`opsz` 1869640570, `wght` 2003265652, `wdth` 2003072104, as the run's README
gives them).

The variation (`CTFontCopyVariation`, the index's `variation`) lists only the axes the font sets away from their
defaults: `title1` at 28 pt, whose optical size equals the `opsz` axis's default of 28, is the one regular style with
no `opsz` entry, and every other regular style's `opsz` entry is present and differs from 28. So an axis the variation
does not list is at the default the font's own axis list gives (`variation_axes`, `NSCTVariationAxisDefaultValue`);
an axis the font does not list at all is not read.

`[styles.<style>.<variant>]`, one per `[[font_style]]` (each text style at the large category, the default, as
`preferredFont(forTextStyle:)` gives it, `regular`, and with `traitTightLeading`, `traitLooseLeading` and `traitBold`
added to its descriptor, `tight`, `loose` and `bold`; `italic` is not read here):
- `family`: the font's family name; `size`: its point size; `name`, `text_style`, `symbolic_traits`: for the record.
- `weight`: the face's weight as the variation draws it (spec batch ADD-A136: the drawn face's weight, not the
  weight trait): the variation's `wght` value, or the `wght` axis's default where the variation lists none; rounded to
  a whole number (S2.8's `u16`) only where it is within 0.01 of one. `weight_trait` records UIFont's trait.
- `style = "normal"`: the font's slant trait is 0 and its symbolic traits hold no italic bit (bit 0,
  `UIFontDescriptorTraitItalic`).
- `axes`, a table: `opsz = "follows_size"` where the descriptor's optical size attribute is `"auto"` (Core Text
  sizes the optical axis to the point size) and the font's `opsz` value (the variation's, or the axis default where it
  lists none) equals the point size clamped to the `opsz` axis's minimum and maximum, within 0.01; written only where
  every axis the variation lists is so accounted for, `wght` being `font.weight`'s route and never an axis (S2.8, S12).
- `features`, an empty table: the descriptor's feature settings are `"absent"` (no feature set beyond the font's own
  defaults).
- `line_height`: the font's ascender less its descender plus its leading, the line advance TextKit lays it out with
  (the method of run 41020880059's `text_styles`), to 0.001.

`[button_titles.<appearance>.<row>.<label>]` (the `button_titles` scene: `UIButton.Configuration` buttons at
`buttonSize` medium titled "Button", `plain`, `gray`, `tinted`, `filled` and, on iOS 26, `glass` and `prominent_glass`;
`filled` with a subtitle; `filled` at most 100 points wide with an overlong word, a long title and a long subtitle;
and `UIButton(type: .system)` titled "Button", row `system`), `<label>` `title` or `subtitle`, read from the
button's view tree (`[[scene_read.view]]`: each UILabel's (or UIButtonLabel's, the system type's) text, font, `number_of_lines`, `line_break_mode`,
`attributed_text`, frame) and, for the title, the scene's `<row>_title_*` reads:
- `font_from`: the `[[font_style]]` or `[[font_role]]` entry whose font has the label's font name, point size, text
  style and symbolic traits, the one whose descriptor the run read (the labels' own reads carry no variation; only
  `filled`'s title has `filled_title_font_detail`, which is checked to equal that entry's variation); `style`, `axes`
  and `features` by the rules above, from that entry.
- `line_height = "auto"` (spec S2.8: the font's own line spacing) where the label's frame height equals, rounded up
  to a device pixel (1/3 pt), `n·(ascender − descender) + (n − 1)·leading` for a whole number of lines `n` ≥ 1 (lines
  laid out at the font's own advance, the last without its leading); `lines` records `n`. The subtitle's positive
  leading tells this from `n·(ascender − descender + leading)`.
- `decoration = "absent"`: no run of the label's attributed text holds an underline or strikethrough attribute
  (`NSUnderline`, `NSStrikethrough`); the run's environment has Button Shapes off.
- `case = "mixed"`: the label's text equals the title the specimen set ("Button", "Subtitle", or the long texts),
  so no case transform applies.
- `elision`, `wrap`, `max_lines` from the label's `line_break_mode` and `number_of_lines`: `by_word_wrapping` with 0
  lines is `elision = "none"`, `wrap = "word_char"`, `max_lines = "none"` (NSLineBreakByWordWrapping wraps at word
  boundaries and breaks a word that does not fit a line inside it, which `wrap_evidence` shows: the overlong word, one
  word, laid out on `overlong_word_lines` lines); `by_truncating_middle` with 1 line is `elision = "middle"`,
  `wrap = "none"`, `max_lines = 1`. Any other mode is not decided.

`[fallbacks] emoji_family`: the family Core Text picks for the emoji "😀" from the body font
(`[[font_for_string]]`, `CTFontCreateForString`).

`[rendering] antialiasing = "grayscale"`: every `text_rendering` capture (body, caption 1 and large title text over
the system background, black and white, light and dark) whose crop holds more than two colours (the text is visible)
has no pixel whose chroma exceeds 2 levels (`pixels.chroma_over_2` 0: no subpixel colour fringes), and holds more than
two colours (edge pixels between the text's and the backdrop's colours: antialiased, not aliased); each capture
settled over two screenshots.
"""
import math
import sys
import tomllib
from pathlib import Path

TAGS = {1869640570: "opsz", 2003265652: "wght", 2003072104: "wdth", 1196572996: "GRAD"}
SCALE = 3


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def axis_defaults(entry):
    out = {}
    for a in entry.get("variation_axes", []) or []:
        if isinstance(a, dict) and num(a.get("NSCTVariationAxisIdentifier")):
            out[TAGS.get(int(a["NSCTVariationAxisIdentifier"]), str(int(a["NSCTVariationAxisIdentifier"])))] = a
    return out


def variation(entry):
    v = entry.get("variation")
    if not isinstance(v, dict):
        return None
    return {TAGS.get(int(k), k): val for k, val in v.items()}


def decide_font(entry):
    """style, axes, features, weight from a [[font_style]] or [[font_role]] entry (rules in the docstring)."""
    out = {}
    font = entry.get("font", {})
    axes = axis_defaults(entry)
    var = variation(entry)
    st = font.get("symbolic_traits")
    if font.get("slant") == 0.0 and isinstance(st, int) and not (st & 1):
        out["style"] = "normal"
    if var is not None and "wght" in axes:
        w = var.get("wght", axes["wght"].get("NSCTVariationAxisDefaultValue"))
        if num(w) and abs(w - round(w)) <= 0.01:
            out["weight"] = int(round(w))
    size = font.get("size_pt")
    if (var is not None and entry.get("optical_size_attribute") == "auto" and "opsz" in axes and num(size)
            and set(var) <= {"opsz", "wght"}):
        a = axes["opsz"]
        o = var.get("opsz", a.get("NSCTVariationAxisDefaultValue"))
        lo, hi = a.get("NSCTVariationAxisMinimumValue"), a.get("NSCTVariationAxisMaximumValue")
        if num(o) and num(lo) and num(hi) and abs(o - min(hi, max(lo, size))) <= 0.01:
            out["axes"] = {"opsz": "follows_size"}
    if entry.get("feature_settings") == "absent":
        out["features"] = {}
    return out


def ceil_px(x):
    return math.ceil(x * SCALE - 1e-6) / SCALE


def lines_auto(font, height):
    a, d, l = font.get("ascender_pt"), font.get("descender_pt"), font.get("leading_pt")
    if not all(num(x) for x in (a, d, l, height)):
        return None
    for n in range(1, 40):
        if abs(ceil_px(n * (a - d) + (n - 1) * l) - height) <= 0.01:
            return n
    return None


def toml_val(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(round(v, 4))
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, list):
        return "[" + ", ".join(toml_val(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{k} = {toml_val(x)}" for k, x in v.items()) + " }" if v else "{}"
    raise ValueError(v)


def font_key(font):
    return (font.get("name"), font.get("size_pt"), font.get("text_style"), font.get("symbolic_traits"))


TITLES = {"filled_overlong_word": "Supercalifragilisticexpialidocious", "filled_long_title": "A long title of several words"}
SUBTITLES = {"filled_subtitle": "Subtitle", "filled_long_subtitle": "A long subtitle of several words"}


def main():
    if len(sys.argv) != 2:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    image = Path(sys.argv[1])
    src = image / "measure1" / "index.toml"
    d = tomllib.loads(src.read_text())
    tables = {}

    entries = {}
    for e in d.get("font_style", []):
        if e.get("variant") == "italic" or "font" not in e:
            continue
        f = e["font"]
        r = {"family": f["family"], "size": f["size_pt"], "name": f["name"], "text_style": f.get("text_style"),
             "symbolic_traits": f.get("symbolic_traits"), "weight_trait": f.get("weight")}
        r.update(decide_font(e))
        if all(num(f.get(k)) for k in ("ascender_pt", "descender_pt", "leading_pt")):
            r["line_height"] = round(f["ascender_pt"] - f["descender_pt"] + f["leading_pt"], 3)
        tables[f"styles.{e['style']}.{e['variant']}"] = r
        entries.setdefault(font_key(f), ("font_style", e))
    for e in d.get("font_role", []):
        if "font" in e:
            entries.setdefault(font_key(e["font"]), ("font_role", e))

    overlong_lines = {}
    for read in d.get("scene_read", []):
        if read.get("scene") != "button_titles":
            continue
        app = read["appearance"]
        detail = read.get("filled_title_font_detail")
        detail_var = None
        if isinstance(detail, str):
            detail_var = tomllib.loads(detail).get("variation")
        labels = {}
        for v in read.get("view", []):
            if v.get("class") in ("UILabel", "UIButtonLabel") and isinstance(v.get("font"), dict):
                labels.setdefault(v["root"], []).append(v)
        for row, views in labels.items():
            views.sort(key=lambda v: v["frame_pt"][1])
            for idx, v in enumerate(views):
                part = "title" if idx == 0 else "subtitle"
                font = v["font"]
                r = {"text": v.get("text")}
                src_entry = entries.get(font_key(font))
                if src_entry is not None:
                    kind, e = src_entry
                    i = d[kind].index(e)
                    r["font_from"] = f"{kind}.{i}"
                    dec = decide_font(e)
                    if row == "filled" and part == "title" and detail_var is not None:
                        r["font_detail_variation_equal"] = detail_var == e.get("variation")
                        if not r["font_detail_variation_equal"]:
                            dec = {}
                    for k in ("style", "axes", "features"):
                        if k in dec:
                            r[k] = dec[k]
                n = lines_auto(font, v["frame_pt"][3])
                if n is not None:
                    r["lines"] = n
                    r["line_height"] = "auto"
                attrs = v.get("attributed_text") or []
                if isinstance(attrs, list) and not any(
                        k.startswith("NSUnderline") or k.startswith("NSStrikethrough") for a in attrs for k in a):
                    if d["environment"].get("button_shapes") is False:
                        r["decoration"] = "absent"
                expected = (TITLES.get(row, "Button") if part == "title" else SUBTITLES.get(row))
                if expected is not None and v.get("text") == expected:
                    r["case"] = "mixed"
                mode, lines = v.get("line_break_mode"), v.get("number_of_lines")
                r["line_break_mode"], r["number_of_lines"] = mode, lines
                if mode == "by_word_wrapping" and lines == 0:
                    r.update({"elision": "none", "wrap": "word_char", "max_lines": "none"})
                elif mode == "by_truncating_middle" and lines == 1:
                    r.update({"elision": "middle", "wrap": "none", "max_lines": 1})
                if row == "filled_overlong_word" and part == "title" and n is not None:
                    overlong_lines[app] = n
                tables[f"button_titles.{app}.{row}.{part}"] = r
    for app, n in overlong_lines.items():
        tables[f"button_titles.{app}.wrap_evidence"] = {
            "overlong_word": TITLES["filled_overlong_word"], "overlong_word_lines": n,
            "broken_inside_word": n > 1}

    emoji = [s for s in d.get("font_for_string", []) if s.get("script") == "emoji"]
    if len(emoji) == 1:
        tables["fallbacks"] = {"emoji_family": emoji[0]["picked_family_name"],
                               "emoji_postscript_name": emoji[0]["picked_postscript_name"]}

    caps = [c for c in d.get("capture", []) if c.get("scene") == "text_rendering"]
    visible = [c for c in caps if c["pixels"]["distinct_colors"] > 2]
    if caps and visible and all(c["pixels"]["chroma_over_2"] == 0 and c.get("settled") for c in visible):
        tables["rendering"] = {"antialiasing": "grayscale", "captures": len(caps), "text_visible": len(visible),
                               "chroma_over_2_total": sum(c["pixels"]["chroma_over_2"] for c in visible),
                               "min_distinct_colors": min(c["pixels"]["distinct_colors"] for c in visible)}

    lines = ["# Output of analysis/fonts_read.py (its docstring is the method), file fonts_read.toml.",
             "# input_image: every file it reads, as a repository path (spec S17 *`evidence`*).",
             f"input_image = [{toml_val(src.as_posix())}]"]
    for head, r in tables.items():
        lines.append(f"\n[{head}]")
        for k, v in r.items():
            if v is None:
                continue
            lines.append(f"{k} = {toml_val(v)}")
    out = image / "fonts_read.toml"
    out.write_text("\n".join(lines) + "\n")
    tomllib.loads(out.read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
