# iOS host, run 42305286429 (2026-11-06)

[The run](https://github.com/tiborgats/native-theme/actions/runs/42305286429): `os-probe.yml`'s ios-host job with
`ios_host_passes=render` and `ios_host_set=popup`, the measurement campaign's pop-up redo (IP-popup). The harness is
`tools/ios-host` on `v0.8.0-tools-ios-m2` at the run's commit `5246d19e`: the render pass as in run 41020880059,
drawing the pop-up set (`IosHost.swift`, one cell per row): each configuration style (plain, gray, filled and, on iOS
26, glass, with the borderless and bordered styles) with a menu as its primary action,
`changesSelectionAsPrimaryAction` and the pop-up indicator, under two selections ("One" and "Two longer") at its own
width, at 200 points and at 60 points, at medium, in each state, over each backdrop.

| Folder | Preset | Runner | Xcode, SDK | Simulator |
|---|---|---|---|---|
| `ios-host-macos-15/` | `ios-13` | macOS 15.8.2 (24H232) | Xcode 16.4 (16F6), iphonesimulator 18.5 (22F76) | iOS 18.6 (22G86), iPhone 16 Pro |
| `ios-host-macos-26/` | `ios-26` | macOS 26.7.2 (25G332) | Xcode 26.6 (17F113), iphonesimulator 26.5 (23F81a) | iOS 26.5 (23F77), iPhone 17 Pro |

Kept here, per image folder: `run1/index.toml` (each cell's frame, intrinsic size, configuration and view tree, each
label's text), `run1/sync/done` (the pages whose margin check failed), and `render_pop_up.toml`, the output of
`analysis/render_pop_up.py` over them (its docstring is the method). The full run (the crops, drawings, screenshots,
solved layers, the second run, the SDK headers and the logs) stays in the run's CI artifacts until GitHub deletes them;
it is not on `v0.8.0-tools-ios-m2`.

What the run shows (each job's run.txt): both jobs report a failure, as in run 42267206298, but narrower: at 60
points under the longer selection the title wraps over six lines and the button, 134 points tall, overflows its cell
into the page margins, so the margin check fails after five retakes on those pages (`run1/sync/done`: filled and
gray in both appearances on iOS 18, also glass in dark on iOS 26). Every other page passed the checks. On iOS 18 the
two runs are byte-identical (937 files); on iOS 26 they differ only in Liquid Glass crops, and compare.swift accepts
them. The facts read no cell of a page in `run1/sync/done`, and no pixel: only UIKit's own frames and texts, which
are the same in every style, appearance and image.

## What this branch keeps

This branch keeps only the files the facts cite, the files the committed analyses read, and those analyses
(`analysis/`) with their outputs. The full run stays in CI's artifacts until GitHub deletes them;
it is not on `v0.8.0-tools-ios-m2`, and its files here were taken from those artifacts. Kept here:

- `analysis/render_pop_up.py`
- `ios-host-macos-15/render_pop_up.toml`
- `ios-host-macos-15/run1/index.toml`
- `ios-host-macos-15/run1/sync/done`
- `ios-host-macos-26/render_pop_up.toml`
- `ios-host-macos-26/run1/index.toml`
- `ios-host-macos-26/run1/sync/done`
- `run.toml`
