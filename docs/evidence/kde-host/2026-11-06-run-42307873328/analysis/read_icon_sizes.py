#!/usr/bin/env python3
"""Reads Kirigami's icon size for labels from the KDE render host's run (KH-reads) as the kde-breeze facts' value,
`token.icons.sizes.keyed.for_labels.size`. The KDE facts lane wrote it (2026-11-07, spec S17 *`evidence`*: an
analysis output for a value a harness read into a text file, which the facts cite through it).

Run from the repository root (Python 3.11+, the standard library only):

    python3 docs/evidence/kde-host/<run>/analysis/read_icon_sizes.py docs/evidence/kde-host/<run>

It reads `qml/index.txt` (tools/kde-host/buttons.qml's index: its `icon sizes` line, `sizeForLabels=<n>` as
Kirigami's `Units.iconSizes.sizeForLabels` answered, and the label font's `FontMetrics` height) and
`fonts/fonts.toml` (tools/kde-host/fonts.py: the platform theme's general font, `[[font]]` `name =
"system.general"`, its family, point size and `QFontMetricsF::height()`, `height_f`), and writes `qml/analysis.toml`:

- `size_for_labels_px`: the index's `sizeForLabels`;
- `general_font`, `general_font_height_px`: the general font as `QFontInfo` resolved it and its `QFontMetricsF`
  height: Kirigami keeps the application font's metrics as a `QFontMetricsF` (kirigami@6.31.0
  src/platform/units.cpp:35, :53, and :275 on a font change), whose `height()` is a `qreal`;
- `rounded_icon_size_input_px`: that height as `roundedIconSize(int size)` receives it from `sizeForLabels()`'s
  `roundedIconSize(m_units->d->fontMetrics.height())` (units.cpp:297, :322-326), the `qreal` converted to `int` by
  truncation toward zero (C++'s floating-integral conversion; 17.6875 is 17), not `QFontMetrics::height()`'s integer
  height (18 for the same font), which Kirigami does not read;
- `rounded_icon_size_px`: that function applied to the input (units.cpp:297-319: below 16 the size, below 22 16,
  below 32 22, below 48 32, below 64 48, else the size), and `consistent`, true where it equals the index's value.

Corrected 2026-11-08 (native-theme's KDE round 6): the first version read `QFontMetrics::height()`'s `height`, 18,
as the input; the value, 16, is the same either way.

`input_image` names every file read, as repository paths.
"""

import re
import sys
import tomllib
from pathlib import Path


def rounded_icon_size(size):
    for bound, value in ((16, None), (22, 16), (32, 22), (48, 32), (64, 48)):
        if size < bound:
            return size if value is None else value
    return size


def main():
    if len(sys.argv) != 2:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    run = Path(sys.argv[1])
    index = (run / "qml/index.txt").read_text()
    fonts = tomllib.loads((run / "fonts/fonts.toml").read_text())
    lines = ["# Output of analysis/read_icon_sizes.py (its docstring is the method), file qml/analysis.toml.",
             "# input_image: every file it reads, as a repository path (spec S17 *`evidence`*).",
             f'input_image = ["{run.as_posix()}/qml/index.txt", "{run.as_posix()}/fonts/fonts.toml"]']
    m = re.search(r"^icon sizes .*\bsizeForLabels=(\d+)\b", index, re.M)
    general = next((f for f in fonts["font"] if f.get("name") == "system.general"), None)
    if m:
        lines.append(f"size_for_labels_px = {int(m.group(1))}")
    if general:
        lines.append(f'general_font = "{general["resolved_family"]} {general["resolved_point_size_f"]!r}pt"')
        size = int(general["height_f"])  # C++'s qreal-to-int conversion truncates toward zero, as int() does
        lines.append(f"general_font_height_px = {general['height_f']!r}")
        lines.append(f"rounded_icon_size_input_px = {size}")
        lines.append(f"rounded_icon_size_px = {rounded_icon_size(size)}")
    if m and general:
        size = int(general["height_f"])
        lines.append(f"consistent = {str(rounded_icon_size(size) == int(m.group(1))).lower()}")
    (run / "qml/analysis.toml").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
