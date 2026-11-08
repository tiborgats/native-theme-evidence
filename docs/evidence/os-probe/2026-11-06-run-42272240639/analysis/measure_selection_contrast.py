#!/usr/bin/env python3
"""The Increase Contrast selection solve (U235, and macos-monterey's under U236): run 42215651196's
analysis/measure_selection.py's solve, unchanged (`solve`, `read_png`, `rgba`, `hexa` copied as they are; its docstring
states the method: a glyph colour F of alpha a over two selection backgrounds B1 and B2 composites to C1 and C2, a per
channel 1 - (C1 - C2) / (B1 - B2) on the channels where |B1 - B2| >= 100, averaged; F = (C1 - (1 - a) B1) / a,
clamped and rounded), over two selections drawn under Increase Contrast: the image's accent, read by an earlier run's
`increase-contrast-on` pass, and the red accent (`AppleAccentColor` 0), read by this run's
`increase-contrast-on-accent-red` pass. The facts lane wrote it (2026-11-06).

Run from the repository root (Python 3.11+, the standard library only), once per image folder:

    python3 docs/evidence/os-probe/2026-11-06-run-42272240639/analysis/measure_selection_contrast.py IMAGE

IMAGE is `os-probe-macos-26`, whose first selection is run 41195846264's (macOS 26.6.2: the two selections come from
two builds of macOS 26, 26.6.2 and 26.7.2), or `os-probe-macos-15`, whose first selection is run 42215651196's (macOS
15.8.2, the build of this run's macOS 15 job). It reads both passes' probe.toml `[macos.selection]` (each column's
`r1_<column>_glyph` and `r1_<column>_background` samples of the emphasized row) and this run's pass's
`settings.txt` (it requires `increaseContrast` and `AppleAccentColor` written and read back as 1 and 0) and captures
`renders/selection/<appearance>-emphasized.png` (`samples_match`: every sample's `raw` equals the capture's pixel at
its `pixel_xy`). It writes `selection-contrast.toml` into this run's image folder: per appearance,
`foreground_inactive` (secondaryLabelColor), `disabled_foreground` (tertiaryLabelColor) and `link` (linkColor) as
`#rrggbbaa`, with each channel's alpha (`solve.<column>.channel_alphas`), and the backgrounds the two passes drew.
"""

import struct
import sys
import tomllib
import zlib
from pathlib import Path

COLUMNS = (("foreground_inactive", "secondaryLabelColor"), ("disabled_foreground", "tertiaryLabelColor"),
           ("link", "linkColor"))
FIRST = {"os-probe-macos-26": "docs/evidence/os-probe/2026-10-31-run-41195846264/os-probe-macos-26/increase-contrast-on",
         "os-probe-macos-15": "docs/evidence/os-probe/2026-11-06-run-42215651196/os-probe-macos-15/increase-contrast-on"}
RUN = "docs/evidence/os-probe/2026-11-06-run-42272240639"


def read_png(path: Path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    pos, idat, ihdr = 8, b"", None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
    width, height, depth, colour, _, _, interlace = ihdr
    if depth != 8 or colour not in (2, 6) or interlace != 0:
        raise ValueError(f"{path}: not an 8-bit non-interlaced RGB(A) PNG")
    bpp = 4 if colour == 6 else 3
    raw, stride = zlib.decompress(idat), width * bpp
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(height):
        f, line = raw[i], bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 0xFF
            elif f == 2:
                line[x] = (line[x] + b) & 0xFF
            elif f == 3:
                line[x] = (line[x] + (a + b) // 2) & 0xFF
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else (b if pb <= pc else c))) & 0xFF
            elif f != 0:
                raise ValueError(f"{path}: filter {f}")
        rows.append([tuple(line[x:x + bpp]) + ((255,) if bpp == 3 else ()) for x in range(0, stride, bpp)])
        prev = line
    return width, height, rows


def rgba(s):
    s = s.lstrip("#")
    return tuple(int(s[k:k + 2], 16) for k in range(0, 8, 2))


def hexa(c):
    return "#" + "".join(f"{v:02x}" for v in c)


def off_segment(p, o, s):
    """The largest channel distance of p from the segment o..s."""
    d = [s[k] - o[k] for k in range(3)]
    n = sum(v * v for v in d)
    t = 0.0 if n == 0 else max(0.0, min(1.0, sum((p[k] - o[k]) * d[k] for k in range(3)) / n))
    return max(abs(p[k] - (o[k] + t * d[k])) for k in range(3))


def solve(c1, b1, c2, b2):
    alphas = [1 - (c1[k] - c2[k]) / (b1[k] - b2[k]) for k in range(3) if abs(b1[k] - b2[k]) >= 100]
    a = sum(alphas) / len(alphas)
    f = [max(0, min(255, round((c1[k] - (1 - a) * b1[k]) / a))) for k in range(3)]
    return tuple(f) + (round(255 * a),), alphas


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in FIRST:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    image = sys.argv[1]
    second = f"{RUN}/{image}/increase-contrast-on-accent-red"
    text = Path(f"{second}/settings.txt").read_text().splitlines()
    for need in ("write increaseContrast true: exit 0", "write AppleAccentColor 0: exit 0"):
        if need not in text:
            raise SystemExit(f"{second}/settings.txt: no line {need!r}")
    if text[text.index("write increaseContrast true: exit 0") + 1] != "read back: 1" or \
            text[text.index("write AppleAccentColor 0: exit 0") + 1] != "read back: 0":
        raise SystemExit(f"{second}/settings.txt: a setting did not read back")
    inputs = [f"{FIRST[image]}/probe.toml", f"{second}/probe.toml", f"{second}/settings.txt"]
    s1 = tomllib.loads(Path(inputs[0]).read_text())["macos"]["selection"]
    s2 = tomllib.loads(Path(inputs[1]).read_text())["macos"]["selection"]
    lines = ["# Output of analysis/measure_selection_contrast.py (its docstring is the method), file selection-contrast.toml.",
             "# input_image: every file it reads, as a repository path (spec S17 *`evidence`*)."]
    body = []
    for ap in ("aqua", "darkAqua"):
        run = s2[ap]["emphasized"]
        png = f"{second}/{run['file']}"
        inputs.append(png)
        _, _, rows = read_png(Path(png))
        match = all(rows[v["pixel_xy"][1]][v["pixel_xy"][0]] == rgba(v["raw"]) for v in run["samples"].values())
        m, r = s1[ap]["emphasized"]["samples"], run["samples"]
        body.append(f"\n[selection_contrast.{ap}]")
        body.append(f"samples_match = {'true' if match else 'false'}")
        body.append(f'background_first = "{m["r1_labelColor_background"]["raw"]}"')
        body.append(f'background_second = "{r["r1_labelColor_background"]["raw"]}"')
        sol = []
        for key, column in COLUMNS:
            c, a = solve(rgba(m[f"r1_{column}_glyph"]["raw"]), rgba(m[f"r1_{column}_background"]["raw"]),
                         rgba(r[f"r1_{column}_glyph"]["raw"]), rgba(r[f"r1_{column}_background"]["raw"]))
            body.append(f'{key} = "{hexa(c)}"')
            sol.append(f"\n[selection_contrast.{ap}.solve.{column}]\nchannel_alphas = [{', '.join(repr(round(v, 4)) for v in a)}]")
        body += sol
    lines.append("input_image = [" + ", ".join(f'"{i}"' for i in inputs) + "]")
    out = Path(f"{RUN}/{image}/selection-contrast.toml")
    out.write_text("\n".join(lines + body) + "\n")
    tomllib.loads(out.read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
