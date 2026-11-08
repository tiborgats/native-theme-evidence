#!/usr/bin/env python3
"""Reads whether a UIButton with no image draws an image of its own: the iOS host's render pass (tools/ios-host, the
base specimen set), per image folder.

Run from the repository root, once per image folder:

    python3 -I docs/evidence/ios-host/2026-10-30-run-41020880059/analysis/read_icon_presence.py <image folder>

Reads <folder>/run1/index.toml (the render pass's index: per cell, the specimen, its kind, size, state and backdrop, and
the button's view tree, one table per view with its `class` and `frame_pt`). Writes <folder>/icon_presence.toml.

The cells read: the system-backdrop cells of every specimen that sets no image: the `UIButton.Configuration` styles
alone and with a variant that adds no image (a role, a corner style, a subtitle, a menu, a pop-up indicator; not
`+image_*` and not `+activity_indicator_shown`, whose indicator is an image of its own), and the system type
(`UIButton(type: .system)` with a title, kind `button_type`, specimen `system`), in every size, state and appearance
the pass drew. A cell draws an icon where its view tree holds a view whose class name contains `ImageView` and whose
frame does not contain the title label's whole frame (an image behind the title is the bezel's: the system type draws
its selected state's bezel as a `UIImageView` larger than the button, `image_is_symbol` false), but for a
specimen with the pop-up indicator (`+indicator_popup`), whose indicator is one `UIImageView`: there, an icon is drawn
where the tree holds more than one such view, or one whose frame does not start at or after the title label's
trailing edge (the indicator trails the title). A cell with no view tree (none recorded) is not read.

Output:
- `[specimens.<specimen>]`: `icon` ("absent" where no read cell of the specimen draws an icon, else "drawn"),
  `cells` (the cells read);
- `[no_image]`: `icon` ("absent" where every read cell of every specimen above draws none, else "drawn"), `cells`,
  `specimens` (their number), `kinds` (the cell kinds read).
"""
import sys
import tomllib
from pathlib import Path

folder = Path(sys.argv[1])
index = folder / "run1" / "index.toml"
data = tomllib.load(open(index, "rb"))


def reads(cell):
    sp = cell["specimen"]
    if cell.get("backdrop") != "system" or "view" not in cell:
        return False
    if cell["kind"] == "configuration":
        return "+image_" not in sp and "activity_indicator" not in sp
    return cell["kind"] == "button_type" and sp == "system"


def contains(outer, inner):
    ox, oy, ow, oh = outer
    ix, iy, iw, ih = inner
    return ox <= ix + 0.01 and oy <= iy + 0.01 and ox + ow >= ix + iw - 0.01 and oy + oh >= iy + ih - 0.01


def draws_icon(cell):
    views = cell["view"]
    labels = [v for v in views if "Label" in v["class"]]
    images = [v for v in views if "ImageView" in v["class"]
              and not (labels and contains(v["frame_pt"], labels[0]["frame_pt"]))]
    if "+indicator_popup" not in cell["specimen"]:
        return bool(images)
    if len(images) > 1:
        return True
    if not images:
        return False
    if not labels:
        return True
    lx, _, lw, _ = labels[0]["frame_pt"]
    ix = images[0]["frame_pt"][0]
    return ix < lx + lw - 0.01


specimens = {}
for cell in data["render"]:
    if not reads(cell):
        continue
    s = specimens.setdefault(cell["specimen"], {"cells": 0, "drawn": 0, "kind": cell["kind"]})
    s["cells"] += 1
    s["drawn"] += draws_icon(cell)

out = [f"# Output of analysis/read_icon_presence.py (docs/evidence/ios-host/2026-10-30-run-41020880059/analysis/; "
       f"its docstring is the method) over {folder.as_posix()}.",
       f'input_image = "{index.as_posix()}"', ""]
total = sum(s["cells"] for s in specimens.values())
drawn = sum(s["drawn"] for s in specimens.values())
out += ["[no_image]", f'icon = "{"drawn" if drawn else "absent"}"', f"cells = {total}",
        f"specimens = {len(specimens)}",
        "kinds = [" + ", ".join(f'"{k}"' for k in sorted({s["kind"] for s in specimens.values()})) + "]", ""]
for name in sorted(specimens):
    s = specimens[name]
    out += [f'[specimens."{name}"]', f'icon = "{"drawn" if s["drawn"] else "absent"}"', f"cells = {s['cells']}", ""]
(folder / "icon_presence.toml").write_text("\n".join(out), encoding="utf-8")
print(folder, total, "cells", drawn, "with an icon,", len(specimens), "specimens")
