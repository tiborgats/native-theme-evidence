#!/usr/bin/env python3
"""Reads when Compose shows a button's focus indication from the Android host's MeasureTest.focusVisibility pass
(AH-pass) as the material-3 facts' value, `token.behavior.focus_visible_when` (S4.2's `FocusVisibleWhen`). The
Material facts lane wrote it (2026-11-07, spec S17 *`evidence`*: an analysis output for a value read from images).

Run from the repository root (Python 3.11+, the standard library only):

    python3 docs/evidence/android-host/<run>/analysis/read_focus.py docs/evidence/android-host/<run>/measure

It reads, under that image folder, `focus.toml` (per step, in order: `0-initial`, `1-tap` a real tap, `2-tab` a Tab
key event, `3-tap-again` a second tap; each step's touch mode, the button's focused semantics, the interactions its
source emitted since the step before, and the specimen's PNG, captured 1.5 s after the step) and each step's PNG
(8-bit RGB or RGBA), and writes `focus-visible.toml` into the image folder:

- `[step.<name>]`: `focused`, `in_touch_mode`, `interactions` as read, and `differs_from_initial`, the number of
  pixels in which the step's capture differs from `0-initial`'s (the button at rest);
- `focus_visible_when`: `{ keyboard = {} }` where a tap leaves the button unfocused and drawn as at rest (both
  taps' captures equal the initial one, `Press` and `Release` emitted, no `Focus`), and the Tab key, which leaves
  touch mode, focuses it (`Focus` emitted) and draws it otherwise than at rest (its capture differs): Compose shows
  its focus indication for focus moved by the keyboard and never for a tap. No timeout shows within the capture's
  1.5 s, and the pass changes nothing after it; `{}` is the variant with no timeout (S11).

`input_image` names every file read, as repository paths.
"""

import struct
import sys
import tomllib
import zlib
from pathlib import Path


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


def differing(a, b):
    if a[:2] != b[:2]:
        return a[0] * a[1]
    return sum(1 for ra, rb in zip(a[2], b[2]) for pa, pb in zip(ra, rb) if pa != pb)


def main():
    if len(sys.argv) != 2:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    image = Path(sys.argv[1])
    steps = {s["name"]: s for s in tomllib.loads((image / "focus.toml").read_text())["step"]}
    pngs = {name: read_png(image / s["png"]) for name, s in steps.items()}
    read = ["focus.toml"] + [s["png"] for s in steps.values()]
    lines = ["# Output of analysis/read_focus.py (its docstring is the method), file focus-visible.toml.",
             "# input_image: every file it reads, as a repository path (spec S17 *`evidence`*).",
             "input_image = [" + ", ".join(f'"{image.as_posix()}/{rel}"' for rel in read) + "]"]
    diff = {name: differing(pngs[name], pngs["0-initial"]) for name in steps}
    for name, s in steps.items():
        lines += [f'\n[step."{name}"]', f"focused = {str(s['focused']).lower()}",
                  f"in_touch_mode = {str(s['in_touch_mode']).lower()}",
                  "interactions = [" + ", ".join(f'"{i}"' for i in s["interactions"]) + "]",
                  f"differs_from_initial = {diff[name]}"]
    taps = [steps["1-tap"], steps["3-tap-again"]]
    tab = steps["2-tab"]
    tap_rest = all(not s["focused"] and "Focus" not in s["interactions"] and "Press" in s["interactions"]
                   and "Release" in s["interactions"] for s in taps) and diff["1-tap"] == 0 and diff["3-tap-again"] == 0
    tab_shown = tab["focused"] and not tab["in_touch_mode"] and "Focus" in tab["interactions"] and diff["2-tab"] > 0
    if tap_rest and tab_shown:
        lines.insert(3, "focus_visible_when = { keyboard = {} }")
    (image / "focus-visible.toml").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
