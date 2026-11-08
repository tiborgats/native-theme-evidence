# native-theme-evidence

The measured evidence of [native-theme](https://github.com/tiborgats/native-theme): what the OS probe, the hosts and
the harnesses recorded on GitHub's runner images and in the project's containers, and the committed analyses of those
recordings. native-theme's facts (`docs/facts/`) cite these files; they are kept here, not in the workflow runs,
because GitHub deletes a run's artifacts after 90 days, and not in native-theme itself, so that a clone of the library
does not download them.

## How native-theme pins it

native-theme's `docs/facts/sources.toml` pins one commit of this repository, the `[[source]]` with
`evidence = true` (id `native-theme-evidence`). A citation names a file by its path here, `docs/evidence/...`, and the
project's readers (its checkers, the generators that read evidence and the facts gate) resolve that path in a clean
checkout of this repository whose HEAD is the pinned commit, and fail otherwise: a file is committed evidence when it
is in that commit's tree. `scripts/update_sources.sh` (`--only native-theme-evidence` for this entry alone) checks the
pin out in the project's source cache; `NATIVE_THEME_EVIDENCE` names another checkout (CI's, a worktree's clone).

## What it holds

`docs/evidence/<harness>/<date>-run-<id>/<image>/`, one folder per recorded run and runner image, at the paths it had
in native-theme. Each run folder holds its `README.md` (the run, its commit, the images and what it reported), its
`run.toml` (per image: the preset, the `sources.toml` entry and the OS, and the toolkit where one drew or answered)
and, where the run was analysed, its `analysis/` scripts. Every other file of a run is cited by a fact, a state-model
entry or a vector table, or is an image a cited analysis reads; a run's records named as exempt (`settings.txt`,
`environment.txt`) are kept beside them. native-theme's `scripts/check_fact_citations.py` checks this on every pin.
The runs its plan lists as legacy count as cited until its M4, when the files no fact cites are deleted.
[`docs/evidence/README.md`](docs/evidence/README.md) lists the runs.

## Rules

- A recorded file is not edited after it is added: a later reading is a new run folder.
- The branches follow native-theme's: a native-theme branch that adds evidence commits its runs on a branch of the
  same name here, cut from the commit it pins, and its facts commit moves the pin to that branch's head. The branch
  here is pushed before the commit that pins it.
- When a native-theme branch merges into another, the source's pinned commit is merged here into the target's (a
  fast-forward where one contains the other, else a merge commit, never a rebase or a squash), so every commit a pin
  ever named stays reachable; the merge in native-theme pins the result. A branch here is deleted once merged, or once
  its native-theme branch is deleted unmerged.
- History is never rewritten: a file is deleted by a new commit, never by a force push.

## Licence

As native-theme: MIT, Apache-2.0 or 0BSD, at your option ([`LICENSE-MIT`](LICENSE-MIT),
[`LICENSE-APACHE`](LICENSE-APACHE), [`LICENSE-0BSD`](LICENSE-0BSD)).
