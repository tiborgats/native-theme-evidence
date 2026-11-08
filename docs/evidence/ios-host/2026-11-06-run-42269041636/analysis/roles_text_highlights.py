#!/usr/bin/env python3
"""Reads the text selection and find highlights of the iOS host's run 42269041636 (tools/ios-host, measure mode, the
`roles` pass) into the values the colour-role facts cite.

Run from the repository root, once per image folder:

    python3 -I docs/evidence/ios-host/2026-11-06-run-42269041636/analysis/roles_text_highlights.py \
        docs/evidence/ios-host/2026-11-06-run-42269041636/ios-host-macos-26

Reads, per appearance (light, dark), the crops of three scenes over opaque black and opaque white
(measure1/screen/<appearance>/<scene>/<part>/{black,white}/text.png): `text_selection/focused` (a UITextView first
responder with characters 0-8 selected), `text_selection/unfocused` (a text view that is not first responder, the same
selection set) and `find/default` (a text view with UIFindInteraction's navigator up and "find" searched: 3 results,
the second highlighted); measure1/index.toml's `[[scene_read]]` for those facts; and measure-differ-levels.txt, to
check that no crop it reads differs between the pass's two runs (`differ` below). Writes
<folder>/roles_text_highlights.toml. Needs Pillow.

Method. Each pixel is solved as one layer from its value over black (B) and over white (W), per channel
a = 1 - (W - B) / 255 and F = B / a (the host's solve.swift model, solved/measure1.toml `model`); the pixel's alpha is
the mean of the channels' a (none where it is at most 0.002: transparent), its colour F rounded to 8 bits, clamped to
0..255. Colours are written `#rrggbbaa`.
- `[text_selection.<appearance>]`: `highlight` the commonest solved colour among the partly covered pixels
  (0 < alpha < 255) whose channels spread by more than 20 levels (the highlight is the crop's one chromatic
  translucent paint), `highlight_pixels` their number; `highlight_box` the bounding box (x0, y0, x1, y1, crop pixels)
  of the pixels within 3 levels of it in every channel and the alpha; `selected_glyph` the commonest solved colour of
  the opaque pixels (alpha at least 253) inside that box (the selected characters drawn over the highlight; the
  selection grabbers, which are not glyphs, are the other opaque colour there), `selected_glyph_pixels` their number.
- `[text_selection_unfocused.<appearance>]`: `chromatic_pixels` the number of solved pixels whose channels spread by
  more than 2 levels (the focused crop's highlight and grabbers are chromatic), and `selection` "absent" where it is 0
  (no selection is drawn in a text view that is not first responder), else "drawn".
- `[find.<appearance>]`: `current_match` the commonest solved opaque colour whose channels spread by more than 20
  levels (the highlighted result's box), `current_match_pixels` its number; `transparent_pixels` the number of solved
  transparent pixels (where the find dimming leaves the other results uncovered, over the light appearance's clear text
  view), and the scene's `result_count` and `highlighted_result_index` as the index records them.
"""
import sys
import tomllib
from collections import Counter
from pathlib import Path

from PIL import Image

SCENES = (("text_selection", "focused"), ("text_selection", "unfocused"), ("find", "default"))


def solve(b, w):
    a = sum(1 - (w[i] - b[i]) / 255 for i in range(3)) / 3
    if a <= 0.002:
        return None
    return tuple(round(min(255, max(0, b[i] / a))) for i in range(3)) + (round(a * 255),)


def hexa(c):
    return "#" + "".join(f"{v:02x}" for v in c)


def spread(c):
    return max(c[:3]) - min(c[:3])


def read_crop(folder, appearance, scene, part):
    paths = {bd: folder / "measure1" / "screen" / appearance / scene / part / bd / "text.png" for bd in ("black", "white")}
    bi = Image.open(paths["black"]).convert("RGB")
    wi = Image.open(paths["white"]).convert("RGB")
    if bi.size != wi.size:
        raise SystemExit(f"{paths['black']}: size differs from the white crop's")
    w, h = bi.size
    bp, wp = bi.load(), wi.load()
    solved = {(x, y): solve(bp[x, y], wp[x, y]) for x in range(w) for y in range(h)}
    return paths, solved


def main():
    folder = Path(sys.argv[1])
    root = Path.cwd()
    index = tomllib.loads((folder / "measure1" / "index.toml").read_text())
    differ_file = folder / "measure-differ-levels.txt"
    differ = differ_file.read_text()
    inputs = [folder / "measure1" / "index.toml", differ_file]
    out = []
    for appearance in ("light", "dark"):
        for scene, part in SCENES:
            paths, solved = read_crop(folder, appearance, scene, part)
            for p in paths.values():
                inputs.append(p)
                rel = "./screen/" + str(p.relative_to(folder / "measure1" / "screen"))
                if rel + ":" in differ:
                    raise SystemExit(f"{p}: differs between the runs ({differ_file})")
            vals = [v for v in solved.values() if v]
            if (scene, part) == ("text_selection", "focused"):
                partial = Counter(v for v in vals if 0 < v[3] < 255 and spread(v) > 20)
                hl, n = partial.most_common(1)[0]
                pts = [p for p, v in solved.items() if v and all(abs(v[i] - hl[i]) <= 3 for i in range(4))]
                box = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
                inside = Counter(v for (x, y), v in solved.items()
                                 if v and v[3] >= 253 and box[0] <= x <= box[2] and box[1] <= y <= box[3])
                glyph, gn = inside.most_common(1)[0]
                out.append(f"[text_selection.{appearance}]")
                out.append(f'highlight = "{hexa(hl)}"')
                out.append(f"highlight_pixels = {n}")
                out.append(f"highlight_box = [{', '.join(str(v) for v in box)}]")
                out.append(f'selected_glyph = "{hexa(glyph)}"')
                out.append(f"selected_glyph_pixels = {gn}")
            elif (scene, part) == ("text_selection", "unfocused"):
                chroma = sum(1 for v in vals if spread(v) > 2)
                out.append(f"[text_selection_unfocused.{appearance}]")
                out.append(f"chromatic_pixels = {chroma}")
                out.append(f'selection = "{"absent" if chroma == 0 else "drawn"}"')
            else:
                opaque = Counter(v for v in vals if v[3] == 255 and spread(v) > 20)
                cm, cn = opaque.most_common(1)[0]
                transparent = sum(1 for v in solved.values() if v is None)
                read = next(s for s in index["scene_read"]
                            if s["scene"] == "find" and s["appearance"] == appearance and s["backdrop"] == "system")
                out.append(f"[find.{appearance}]")
                out.append(f'current_match = "{hexa(cm)}"')
                out.append(f"current_match_pixels = {cn}")
                out.append(f"transparent_pixels = {transparent}")
                out.append(f"result_count = {read['find_result_count']}")
                out.append(f"highlighted_result_index = {read['find_highlighted_result_index']}")
            out.append("")
    head = [f"# Output of analysis/roles_text_highlights.py (its docstring is the method) over {folder}.",
            "input_image = ["] + [f'    "{p.relative_to(root) if p.is_absolute() else p}",' for p in sorted(set(inputs))] + ["]", ""]
    (folder / "roles_text_highlights.toml").write_text("\n".join(head + out))


if __name__ == "__main__":
    main()
