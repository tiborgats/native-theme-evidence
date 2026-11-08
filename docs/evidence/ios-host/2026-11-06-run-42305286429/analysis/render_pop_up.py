#!/usr/bin/env python3
"""Reads the pop-up buttons of the iOS host's run 42305286429 (tools/ios-host, `ios_host_set=popup`) into the values
the combo_box facts cite (CB-1, ADD-A127; the ledger's U173, U175, U257).

Run from the repository root, once per image folder:

    python3 -I docs/evidence/ios-host/2026-11-06-run-42305286429/analysis/render_pop_up.py \
        docs/evidence/ios-host/2026-11-06-run-42305286429/ios-host-macos-26

Reads the folder's run1/index.toml (the render pass's index: per cell, the button's frame, intrinsic size, its
`UIButton.Configuration` as `updated(for:)` resolves it, and its view tree with each view's frame in the button's
coordinates and each label's text) and run1/sync/done (the pages whose margin check failed after five retakes: the
button overflowed its cell there, so no cell of such a page is read). Writes <folder>/render_pop_up.toml.

The specimens: each configuration style with a menu as its primary action, `changesSelectionAsPrimaryAction` and the
pop-up indicator, under two selections ("One", `selected_first`; "Two longer", `selected_second`) at its own
(intrinsic) width (`width_own`), at 200 points (`width_wide`) and at 60 points (`width_narrow`), at medium (the
model's `regular`), over the system background, normal state. Only the system-background, normal-state cell of each
specimen is read; a specimen whose page is in run1/sync/done is `unread`. The borderless and bordered styles are left
out (they read as plain, gray, tinted and filled in run 41020880059, analysis.toml `same.pairs`); the glass styles
are read for their geometry only (the view tree's frames), as the existing combo_box facts read glass.

Per `[pop_up.<appearance>.<style>]`, all lengths in points (UIKit's logical unit, the facts' px):
- `own.<selection>`: `width` (the button's frame width), `row` (the content row the frame holds: the configuration's
  leading and trailing content insets, the title label's frame width, the gap from the label's frame to the
  indicator image view's, the indicator's frame width), `slack` (`width` less `row`), and the title label's padding
  inside the content box: `label_padding_top` (the label's top less the top inset), `label_padding_bottom` (the
  frame's height less the bottom inset less the label's bottom), `label_padding_left` (the label's left less the
  leading inset; the capture is left to right), `label_padding_right` (0 where the gap above is measured from the
  label's frame, as the facts' `label_arrow_gap` is: the content's space ends at the label's frame).
- `content_width`: "shown" where, for both selections at the own width, `slack` is 0 to 0.01 point and the two widths
  differ (the frame follows the shown title alone), else "unread".
- `content_slack`: the selections' common `slack` (rounded to 0.001) where `content_width` is "shown", else "unread".
- `label_padding_<side>`: the selections' common value, else "unread".
- `wide.<selection>`: at 200 points, the label's left and the indicator's left (where the spare width goes).
- `narrow.<selection>`: at 60 points, `label_text` (the label's text), `label_height` and `one_line_height` (the label's
  height at the own width), `lines` (`label_height` over `one_line_height`, rounded), and `frame_height`.
- `elision`: "none" where, at 60 points, for every selection read, the label holds the whole title (its text the
  shown title) over more lines than one and the button's frame grows to hold it (its height the label's plus the top
  and bottom insets, to 0.01 point): UIKit wraps the title and cuts none of it; else "unread".
"""
import sys
import tomllib
from pathlib import Path

EPS = 0.01
STYLES = ["plain", "gray", "tinted", "filled", "glass", "prominent_glass", "clear_glass", "prominent_clear_glass"]
TITLE = {"selected_first": "One", "selected_second": "Two longer"}


def r3(x):
    x = round(x, 3)
    return 0.0 if x == 0 else x


def main():
    folder = Path(sys.argv[1])
    root = Path.cwd()
    rel = folder.resolve().relative_to(root.resolve()).as_posix()
    index = tomllib.loads((folder / "run1/index.toml").read_text())
    failed = set()
    for line in (folder / "run1/sync/done").read_text().splitlines():
        if ": " in line and "margin pixels differ" in line:
            failed.add(line.split(": ", 1)[0])           # <appearance>/<specimen>/<size>
    cells = {}
    for x in index["render"]:
        if x["backdrop"] != "system" or x["state"] != "normal" or "pop_up" not in x["specimen"]:
            continue
        if x["style"] not in STYLES:
            continue
        key = (x["appearance"], x["style"], x["variant"]["pop_up"], x["variant"]["width"])
        page = f"{x['appearance']}/{x['specimen']}/{x['size']}"
        cells[key] = (x, page in failed)

    out = {}
    for (app, style, sel, width), (x, bad) in sorted(cells.items()):
        o = out.setdefault(app, {}).setdefault(style, {})
        if bad:
            o.setdefault(width, {})[sel] = {"unread": "its page failed the margin check (run1/sync/done)"}
            continue
        ins = x["configuration"]["content_insets_pt"]        # top, leading, bottom, trailing
        fw, fh = x["frame_pt"][2], x["frame_pt"][3]
        labels = [v for v in x["view"] if v["class"] == "UILabel"]
        images = [v for v in x["view"] if v["class"] == "UIImageView"]
        if len(labels) != 1 or len(images) != 1:
            o.setdefault(width, {})[sel] = {"unread": "not one label and one image view"}
            continue
        lx, ly, lw, lh = labels[0]["frame_pt"]
        ix, iy, iw, ih = images[0]["frame_pt"]
        rec = {"label_text": labels[0].get("text", ""), "label_left": lx, "label_width": lw, "label_height": lh,
               "indicator_left": ix, "indicator_width": iw, "frame_width": fw, "frame_height": fh}
        if width == "own":
            gap = ix - (lx + lw)
            row = ins[1] + lw + gap + iw + ins[3]
            rec.update(width=fw, row=r3(row), slack=r3(fw - row),
                       label_padding_top=r3(ly - ins[0]), label_padding_bottom=r3(fh - ins[2] - (ly + lh)),
                       label_padding_left=r3(lx - ins[1]), label_padding_right=0.0)
        o.setdefault(width, {})[sel] = rec

    for app, styles in out.items():
        for style, o in styles.items():
            own = o.get("own", {})
            ok = (len(own) == 2 and all("unread" not in r for r in own.values()))
            if ok and all(abs(r["slack"]) <= EPS for r in own.values()) and \
                    own["selected_first"]["width"] != own["selected_second"]["width"]:
                o["content_width"] = "shown"
                o["content_slack"] = r3(own["selected_first"]["slack"])
            else:
                o["content_width"] = o["content_slack"] = "unread"
            for side in ("top", "bottom", "left", "right"):
                vals = {r[f"label_padding_{side}"] for r in own.values() if "unread" not in r}
                o[f"label_padding_{side}"] = vals.pop() if ok and len(vals) == 1 else "unread"
            narrow = o.get("narrow", {})
            read = [(s, r) for s, r in narrow.items() if "unread" not in r]
            el = "unread"
            if read and ok:
                good = True
                for s, r in read:
                    one = own[s]["label_height"]
                    r["one_line_height"] = one
                    r["lines"] = round(r["label_height"] / one)
                    top = own[s]["frame_height"] - own[s]["label_height"]     # the insets around one line
                    good &= (r["label_text"] == TITLE[s] and r["lines"] > 1
                             and abs(r["frame_height"] - (r["label_height"] + top)) <= EPS)
                el = "none" if good else "unread"
            o["elision"] = el

    def val(v):
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return repr(float(v)) if isinstance(v, float) else str(v)
        return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'

    lines = [f"# Output of analysis/render_pop_up.py (its docstring is the method) over {rel}.",
             "input_image = [", f'    "{rel}/run1/index.toml",', f'    "{rel}/run1/sync/done",', "]", ""]
    for app, styles in sorted(out.items()):
        for style, o in sorted(styles.items()):
            lines.append(f"[pop_up.{app}.{style}]")
            for k in ("content_width", "content_slack", "label_padding_top", "label_padding_right",
                      "label_padding_bottom", "label_padding_left", "elision"):
                lines.append(f"{k} = {val(o[k])}")
            lines.append("")
            for width in ("own", "wide", "narrow"):
                for sel, r in sorted(o.get(width, {}).items()):
                    lines.append(f"[pop_up.{app}.{style}.{width}.{sel}]")
                    lines += [f"{k} = {val(v)}" for k, v in r.items()]
                    lines.append("")
    (folder / "render_pop_up.toml").write_text("\n".join(lines))
    tomllib.loads((folder / "render_pop_up.toml").read_text())


main()
