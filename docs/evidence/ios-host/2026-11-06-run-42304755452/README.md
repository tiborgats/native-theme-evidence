# iOS host, run 42304755452 (2026-11-06)

[The run](https://github.com/tiborgats/native-theme/actions/runs/42304755452): `os-probe.yml`'s ios-host job with
`ios_host_passes=render,press` and `ios_host_settings=button_shapes`, the measurement campaign's IP-a11y pass under
Button Shapes. The harness is `tools/ios-host` on `v0.8.0-tools-ios-m2` at `8baca1fe`: `run.sh` writes
com.apple.Accessibility's `ButtonShapesEnabled` (`simctl spawn defaults write`, exit 0, run.txt) after the simulator's
boot, then runs the render pass (the base specimen set, as in run 41020880059) and the press pass twice each, compares
and solves them.

| Folder | Preset | Runner | Xcode, SDK | Simulator |
|---|---|---|---|---|
| `ios-host-macos-15/` | `ios-13` | macOS 15.8.2 (24H232) | Xcode 16.4 (16F6), iphonesimulator 18.5 (22F76) | iOS 18.6 (22G86), iPhone 16 Pro |
| `ios-host-macos-26/` | `ios-26` | macOS 26.6.2 (25G83) | Xcode 26.6 (17F113), iphonesimulator 26.5 (23F81a) | iOS 26.5 (23F77), iPhone 17 Pro |

Kept here, per image folder: `run1/index.toml` (its `[motion]` records what UIAccessibility reported:
`button_shapes = true`), `solved/run1.toml`, `differ-levels.txt`, `press1/index.toml`, the press pass's medium crops of
the non-glass styles and the render pass's crops they are compared with (`press1/screen/…`, `run1/screen/…`), both
render runs' activity indicator crops over black and white (`run1/screen/…`, `run2/screen/…`), and
`cond_read_buttons.toml`, the output of `analysis/cond_read_buttons.py` over them (its docstring is the method; it
names each file it reads as `input_image`). The full run (the other crops, the drawings, the screenshots, the solved
layers, the second runs, the SDK headers and the logs) stays in the run's CI artifacts until GitHub deletes them; this
run is not on `v0.8.0-tools-ios-m2`, its files here were taken from those artifacts.

What the run shows (each job's run.txt): both render runs and both press runs finished `ok` on both images. The render
runs differ in 676 of 10,631 files on iOS 18 (352 outside `draw/`) and 1,424 of 15,871 on iOS 26 (830 outside
`draw/`): the activity indicator, which never stops, and on iOS 26 Liquid Glass, bar items and back buttons; compare.swift
accepts them on both images (exit 0). The press runs differ in 1 file on iOS 18 (the index) and 9 on iOS 26, accepted.
The facts read no crop that differs between the runs (the analysis marks such a cell unread).
