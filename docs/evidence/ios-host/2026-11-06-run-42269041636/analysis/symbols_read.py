#!/usr/bin/env python3
"""Reads the symbol configurations of the iOS host's run 42269041636 (tools/ios-host, `Measure.swift`'s `symbols`
pass) into the values the facts cite.

Run from the repository root, once per image folder:

    python3 -I docs/evidence/ios-host/2026-11-06-run-42269041636/analysis/symbols_read.py \
        docs/evidence/ios-host/2026-11-06-run-42269041636/ios-host-macos-26

Reads the folder's measure1/index.toml and writes <folder>/symbols_read.toml. Nothing is computed beyond reading the
strings UIKit's descriptions print; every value is spelled as a fact's value for its key (S11):

- `[buttons.<style>.<size>.<specimen>]`: `[[button_symbol]]`'s configuration buttons (each `UIButton.Configuration`
  style at every `buttonSize`; `<specimen>` `image` an image with a title, `icon_only` an image alone,
  `indicator_popup` the pop-up indicator, `pop_up` the pop-up button), read from the button's first image view (the
  one drawing the symbol): `symbol` the symbol's name in the image's description (`symbol(system: <name>)`);
  `text_style` and `point_size` (a number, in points, which are logical px) the `textStyle=` and `pointSize=` of the
  image view's `preferredSymbolConfiguration` description, where it names one; `size` (a number, in points, which are
  logical px) the symbol's point size: `point_size` where the configuration names one, else, for a `textStyle`, the
  point size of the font UIKit gives that text style at the run's content size category (`screen.
  preferred_content_size_category`, L), read from `[[font_style]]`'s entries at category `large` whose font's own
  `text_style` is that style (the `tight` variant gives the `Short` styles: `UICTFontTextStyleShortSubhead` 15,
  `UICTFontTextStyleShortBody` 17), as `UIImageSymbolConfiguration.h` declares a text style's configuration a Dynamic
  Type size configuration; no `size` where neither is named; `scale` its `scale=` (`S`/`Small` →
  "small", `M`/`Medium` → "medium", `L`/`Large` → "large", UIImageSymbolScale's names); `weight` "absent" where the
  configuration names no `weight=` (UIKit then sets no symbol weight), else `weight_name` the name it prints and no
  `weight` (a symbol weight's name, not a drawn face's weight: ADD-A136 states a font weight from the face, and the run
  reads no face); `rendering_mode` "template" where the image's description says `renderingMode=automatic(template)`
  or `alwaysTemplate`, "original" where it says `alwaysOriginal` or `automatic(original)`; `axes = {}`,
  `symbolic_colors = {}` where the configuration names nothing beyond `textStyle`, `pointSize`, `weight` and `scale`
  (no hierarchical or palette colours, no variable value); and, for the `image` and `icon_only` specimens:
  `symbol_variants = []` where the drawn symbol's name equals the name of the configuration's image the host set
  (`configuration_image`: UIKit added no `.fill`, `.circle`, … variant), `glyph = "absent"` where the button's
  `currentImage` is absent and its image view draws the configuration's own image (the image is the application's;
  UIKit adds no symbol of its own).
- `[defaults.<style>]`: `[[configuration_default]]`'s new configuration of each style
  (`UIButton.Configuration.<style>()`, no property set): `default_size` its `buttonSize` as the model's size, medium
  being the model's `regular` (UIButtonConfiguration.h's `UIButtonConfigurationSize`, the state models' cited mapping;
  mini, small and large keep their names).
- `[types.<type>]`: the buttons with no configuration (`UIButton(type:)`: `system` with an image the host set,
  `info_light`, `info_dark`, `detail_disclosure`, `contact_add`, `close`), read from the image view drawing a symbol
  (close's first image view is its anonymous circle): the same keys, and `glyph_name` the symbol UIKit set as
  `currentImage` where the host set none (`system` sets the host's image: `glyph = "absent"`, `symbol_variants = []`
  where the drawn symbol is the one the host set, `star`).
- `[contexts.<appearance>.<root>.<symbol>]`: the `symbol_contexts` scene's controls that place a symbol of their own
  (a UIToolbar's items, a navigation bar's items and back indicator, a tab bar's items, a list cell, a segmented
  control, a search bar), the first image view in the view tree's order drawing each symbol (`<symbol>` its name
  with `.` written `_`): the same keys, and `fill` the image view's `tint` (`#rrggbbaa`, the view tree's
  `tint.hex`), where it states one in sRGB hex.
"""
import re
import sys
import tomllib
from pathlib import Path

SCALES = {"S": "small", "Small": "small", "M": "medium", "Medium": "medium", "L": "large", "Large": "large"}
KNOWN = {"textStyle", "pointSize", "weight", "scale"}
TYPES = {"system", "info_light", "info_dark", "detail_disclosure", "contact_add", "close"}


def symbol_name(desc):
    m = re.search(r"symbol\(system: ([^)]*)\)", desc or "")
    return m.group(1) if m else None


def rendering(desc):
    m = re.search(r"renderingMode=([A-Za-z]+(?:\([a-z]+\))?)", desc or "")
    if not m:
        return None
    r = m.group(1)
    if r in ("automatic(template)", "alwaysTemplate"):
        return "template"
    if r in ("automatic(original)", "alwaysOriginal"):
        return "original"
    return None


def config(desc):
    """The preferred symbol configuration's description as key=value pairs, and whether it names anything else."""
    out, other = {}, False
    if not isinstance(desc, str) or desc == "absent":
        return None, False
    for part in [p.strip() for p in desc.split(",")]:
        if part in ("", "(null)"):
            continue
        if "=" in part:
            k, v = part.split("=", 1)
            if k in KNOWN:
                out[k] = v
                continue
        other = True
    return out, other


SIZES = {}
BUTTON_SIZES = {"medium": "regular", "mini": "mini", "small": "small", "large": "large"}


def read_view(v):
    rec = {}
    name = symbol_name(v.get("image"))
    if name is None:
        return None
    rec["symbol"] = name
    cfg, other = config(v.get("preferred_symbol_configuration"))
    if cfg is not None:
        if "textStyle" in cfg:
            rec["text_style"] = cfg["textStyle"]
        if "pointSize" in cfg:
            rec["point_size"] = float(cfg["pointSize"])
            rec["size"] = float(cfg["pointSize"])
        elif cfg.get("textStyle") in SIZES:
            rec["size"] = SIZES[cfg["textStyle"]]
        if cfg.get("scale") in SCALES:
            rec["scale"] = SCALES[cfg["scale"]]
        if "weight" in cfg:
            rec["weight_name"] = cfg["weight"]
        else:
            rec["weight"] = "absent"
        if not other:
            rec["axes"] = {}
            rec["symbolic_colors"] = {}
    rm = rendering(v.get("image"))
    if rm:
        rec["rendering_mode"] = rm
    return rec


def toml_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return repr(v) if v != int(v) else repr(float(int(v)))
    if isinstance(v, int):
        return str(v)
    if isinstance(v, dict):
        return "{}" if not v else "{ " + ", ".join(f"{k} = {toml_value(x)}" for k, x in v.items()) + " }"
    if isinstance(v, list):
        return "[" + ", ".join(toml_value(x) for x in v) + "]"
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def main(folder):
    folder = Path(folder)
    rel = folder.resolve().relative_to(Path.cwd().resolve()).as_posix()
    index = tomllib.loads((folder / "measure1/index.toml").read_text())
    assert index["screen"]["preferred_content_size_category"].endswith("L"), index["screen"]["preferred_content_size_category"]
    for f in index["font_style"]:
        if f["category"] == "large" and isinstance(f["font"], dict):
            ts, size = f["font"]["text_style"], float(f["font"]["size_pt"])
            assert SIZES.get(ts, size) == size, ts
            SIZES[ts] = size
    tables = []
    for c in index["configuration_default"]:
        if c["source"].startswith("a new configuration"):
            tables.append((f"defaults.{c['style']}", {"default_size": BUTTON_SIZES[c["button_size"]]}))
    for b in index["button_symbol"]:
        style, size, variant = b["style"], b["size"], b["variant"]
        views = [v for v in b["image_views"] if symbol_name(v.get("image"))]
        if not views:
            continue
        rec = read_view(views[0])
        if style in TYPES:
            if b["current_image"] != "absent" and style != "system":
                rec["glyph_name"] = symbol_name(b["current_image"])
            if style == "system" and symbol_name(b["current_image"]) == rec["symbol"] == "star":
                rec["glyph"] = "absent"
                rec["symbol_variants"] = []
            tables.append((f"types.{style}", rec))
            continue
        if variant in ("image", "icon_only"):
            cfg_name = symbol_name(b.get("configuration_image"))
            if cfg_name is not None and cfg_name == rec["symbol"]:
                rec["symbol_variants"] = []
                if b["current_image"] == "absent":
                    rec["glyph"] = "absent"
        tables.append((f"buttons.{style}.{size}.{variant}", rec))
    for s in index["scene_read"]:
        if s["scene"] != "symbol_contexts":
            continue
        for v in s["view"]:
            if not v.get("image_is_symbol"):
                continue
            rec = read_view(v)
            if rec is None:
                continue
            tint = v.get("tint")
            if isinstance(tint, dict) and "hex" in tint:
                rec["fill"] = tint["hex"]
            tables.append((f"contexts.{s['appearance']}.{v['root']}.{rec['symbol'].replace('.', '_')}", rec))
    out = [f"# Output of analysis/symbols_read.py (its docstring is the method) over {rel}.",
           f'input_image = ["{rel}/measure1/index.toml"]', ""]
    seen = set()
    for name, rec in tables:
        if name in seen:
            continue
        seen.add(name)
        out.append(f"[{name}]")
        for k, v in rec.items():
            out.append(f"{k} = {toml_value(v)}")
        out.append("")
    (folder / "symbols_read.toml").write_text("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1])
