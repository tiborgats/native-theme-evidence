#!/usr/bin/env python3
"""Reads the pressed bar button items of the iOS host's run 42275570795 (tools/ios-host, `press` mode: a real touch
held on each item of a UIToolbar while the screenshot was taken) into the values the facts cite. iOS 18 only: on iOS 26
the bar items are hosted by SwiftUI on a Liquid Glass platter and the view tree holds none of their parts.

Run from the repository root:

    python3 -I docs/evidence/ios-host/2026-11-06-run-42275570795/analysis/press_bar_items.py \
        docs/evidence/ios-host/2026-11-06-run-42275570795/ios-host-macos-15

Reads the folder's press1/index.toml: each `[[render]]` of a bar item (`specimen` `bar_*`, state `pressed`, over the
system background), its view tree as read while the touch was held (`held_until_screenshot`), and the `[[motion]]` table
of the same page and cell (phase `press`: every layer that is animated, transformed or not opaque, sampled from 0 to
1 s after the touch went down). Writes <folder>/press_bar_items.toml.

`[items.<appearance>.<specimen>]`, per bar item:
- `held`: `held_until_screenshot` and `state_applied` both true (the touch was down at the capture);
- `content_class`: the class of the item's content view, the UIButtonLabel (a title) or the UIImageView (a glyph)
  under the item's _UIButtonBarButton (view tree path 0.1.0.1, the toolbar's content view's first item);
- `content_opacity`: the product, over the content view and each of its ancestors up to the toolbar (path 0), of the
  layer's `layer_opacity` (a UIView's `alpha` is its layer's opacity: the item is read only where the two agree on
  every view of the chain, else it is left out);
- `fill`: the content's colour as drawn: the label's `text_color` (a title) or the image view's `tint` (a glyph), its
  alpha multiplied by `content_opacity`, `#rrggbbaa` (each channel the read's 8-bit hex, the alpha rounded to 8 bits);
- `opacity`: the item view's own opacity, the _UIButtonBarButton's `layer_opacity` (the dimming is the content's, not
  the item's);
- `font_family`, `font_size`: the label's font family and point size (a title only);
- `steady`: true where every press-phase motion sample of the page and cell records the content's layer at
  `content_opacity` (to 1e-3) and no animation on it: the pressed look holds from the touch on, it is no transition's
  midpoint.
"""
import sys
import tomllib
from pathlib import Path


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


def main(folder):
    folder = Path(folder)
    index = folder / "press1/index.toml"
    d = tomllib.loads(index.read_text())
    out = {}
    for r in d["render"]:
        if not r["specimen"].startswith("bar_") or r["state"] != "pressed" or r["backdrop"] != "system":
            continue
        views = {v["path"]: v for v in r["view"]}
        item = views.get("0.1.0.1")
        if item is None or item["class"] != "_UIButtonBarButton":
            continue
        content = [v for p, v in views.items() if p.startswith("0.1.0.1.") and v["class"] in ("UIButtonLabel", "UIImageView")]
        if len(content) != 1:
            continue
        c = content[0]
        op, p, agree = 1.0, c["path"], True
        while True:
            v = views[p]
            agree = agree and abs(float(v["alpha"]) - float(v["layer_opacity"])) <= 1e-6
            op *= float(v["layer_opacity"])
            if p == "0":
                break
            p = p.rsplit(".", 1)[0]
        if not agree:
            continue
        colour = (c["text_color"] if c["class"] == "UIButtonLabel" else c["tint"])["hex"].lstrip("#")
        a = int(colour[6:8], 16) / 255 * op
        rec = {
            "held": str(r["held_until_screenshot"]) == "True" and str(r["state_applied"]) == "True",
            "content_class": c["class"],
            "content_opacity": op,
            "fill": "#" + colour[:6] + f"{round(a * 255):02x}",
            "opacity": float(item["layer_opacity"]),
        }
        if c["class"] == "UIButtonLabel":
            rec["font_family"] = c["font"]["family"]
            rec["font_size"] = float(c["font"]["size_pt"])
        page = f"{r['appearance']}/{r['specimen']}/{r['size']}"
        cell = f"{r['backdrop']}/{r['state']}"
        steady = None
        for m in d["motion"]:
            if m["page"] != page or m["cell"] != cell or m["phase"] != "press":
                continue
            steady = True
            for s in m["samples"]:
                lay = [l for l in s.get("layers", []) if l["layer"] == c["path"]]
                anim = [a_ for a_ in s.get("animations", []) if a_["layer"] == c["path"]]
                if anim or len(lay) != 1 or abs(float(lay[0]["opacity"]) - op) > 1e-3:
                    steady = False
        rec["steady"] = bool(steady)
        out.setdefault(r["appearance"], {})[r["specimen"]] = rec
    lines = [f"# Output of analysis/press_bar_items.py (its docstring is the method) over {folder.as_posix()}.",
             f'input_image = "{index.as_posix()}"', ""]
    for app in sorted(out):
        for spec in sorted(out[app]):
            lines.append(f"[items.{app}.{spec}]")
            lines += [f"{k} = {toml_value(v)}" for k, v in out[app][spec].items()]
            lines.append("")
    (folder / "press_bar_items.toml").write_text("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1])
