# Claude Code - git-graph Development Context

Universal rules — git safety, commit conventions, testing, comments, tool preferences — live in
`~/.claude/CLAUDE.md` and are not restated here.

**This file contains ONLY git-graph-specific rules and patterns.**

## What this repo is for

Build synthetic git histories under different branching strategies, so the resulting graph can be
**looked at** instead of argued about. It exists to answer questions like "what does rebasing to
catch up and merging to land actually produce, six features in?" — questions no amount of reading
the git docs settles, because the answer is a shape.

It is a throwaway-repo generator, not a git wrapper. Nothing here is meant to run against a repo
that holds work.

## Everything Destroys a Repo (⚠️ CRITICAL)

Every path ends in `rm -rf .git`. A target directory must carry a `.git-graph-sandbox` marker
before anything runs, and three separate places check for it:

- `prepare_sandbox()` — creates the directory and marker, and refuses `$HOME`, this repo, any
  directory containing this repo, and any non-empty directory with no marker.
- `run_destructive()` — gates the KeyboardInterrupt cleanup, which bypasses `self.commands` and so
  would otherwise bypass every other guard.
- The preamble of the generated `git-commands.sh` — **the one that matters.** That file holds the
  command as a plain line and runs wherever it is invoked from, which is how this repo's own
  `.git` was deleted once.

Never add a destructive path that does not check `in_sandbox()`, and never weaken
`prepare_sandbox` to "only refuse if it's a git repo" — a scratch directory full of unrelated
files is not safe to `rm -rf` inside either.

## Architecture: generate, then execute

`GitHistory` accumulates shell commands into `self.commands` and executes nothing until
`execute_commands()`. That split is the whole design and is worth preserving:

- `dry_run=True` prints the commands without running them, so a strategy can be inspected as text.
- `interactive=True` steps through, pausing at each commit and merge.
- `write_commands_to_file()` emits the run as a re-runnable script.

Anything new — a rebase verb, a catch-up step — should add commands to that list rather than
shelling out directly, or it silently loses all three modes.

## Determinism is load-bearing, not a nicety

Every commit is generated with fixed content, a fixed message, and dates from a clock that
advances one minute per commit. That is what lets `compare` say two scenarios produced the *same
objects* rather than merely the same shape — and it is the entire basis of the worktree answer.

Four ways to break it silently, none of which any test names directly, so check for them by hand:

- **Reading the wall clock.** `authored()` and `committed()` pin `GIT_AUTHOR_DATE` and
  `GIT_COMMITTER_DATE`. Any command that creates a commit without going through one of them takes
  the current time and its hash stops being reproducible.
- **Randomness.** The generator used Faker; it does not any more, and it must not again.
- **Naming a branch in a commit message.** A commit made on a branch and fast-forwarded onto the
  trunk *is* the same commit. Put the branch in the message and it stops being one, which is
  exactly the fact `worktree-land` vs `commit-to-main` exists to demonstrate.
- **Iterating a set.** Merge flags are sorted before rendering, for the same reason.

`committed()` pins only the committer date, because a replay keeps its author. That is what makes
a rebased commit's new hash attributable to its new parent rather than to the clock.

## Scenarios are a name and a timeline, and options live on the event

`Open`, `Commit`, `CatchUp`, `Land`, `Restack`, `Merge`, `CherryPick`, `Revert`, `Push`, `Abandon`,
`Tag`, `Note` — each carries its own options. An earlier design put the catch-up style and the
landing button on the *scenario*, which made exactly five comparisons expressible: a history where
one branch rebases and another merges could not be written down at all. Add capability by adding
an event, never by adding a field to `Scenario`.

`Open(feature, base=...)` is the whole of stacked pull requests and nested branches — a branch off
a branch is the general case with the default filled in, not a special case.

The timeline is **data, not a callable**, because a scenario has to be listable and readable
without being run.

Two rules the shipped scenarios protect, both easy to break by adding a "reasonable" one:

- **Vary one thing at a time** in any pair meant to be compared, and set `compare_with` so the
  listing points at the partner. A scenario varying two things answers neither question.
- **Every `CatchUp` needs real trunk movement before it.** A catch-up with nothing to absorb is a
  no-op git reports as "already up to date", and a timeline full of those compares two strategies
  on a history where neither acts.

`catch_up()` deliberately writes no annotating commit. Whether a catch-up leaves a commit behind is
the thing being measured, and a marker the tool wrote would appear in both shapes.

## Conflict stops are measured, never predicted

The walker decides *whether* resolution steps are needed — it knows which files both sides wrote.
It does not decide how many: resolving a rebase in the branch's favour conflicts once and then
applies cleanly, while resolving it the other way conflicts on every commit. The rounds emitted
are an upper bound, and `probe_stop()` — written inverted, so it *fails* while git is still
waiting — is the measurement.

`Command` therefore carries two separate flags. `tolerate_failure` means the run carries on;
`conflict_point` means failing here is the number being reported. Collapsing them counts every
harmless failure as a conflict.

During a **rebase**, `--ours` is the branch being replayed *onto* and `--theirs` is your own work —
the reverse of a merge. `conflict-keep-trunk` exists to show it, and it empties the branch.

## Two models of merging live here, on purpose

`MergeFlags` + the `Merge` event model **git's local verbs**. `LandStyle` + the `Land` event model
**GitHub's three buttons plus a fast-forward push**, which are not the same thing — and the graph that
matters is the one in the repo.

## Where things live

`history.py` is the engine and the only place that emits a command. `events.py` is the algebra and
the walker. `scenarios.py` is the catalogue. `fingerprint.py` measures a built repo at four depths.
`render.py` is the visual layer and deliberately wraps git's own `--graph` rather than laying out a
DAG — the drawing you are shown is the one you will see in your own terminal. `main.py` is the
typer app.

Two conventions shaped this surface and are worth keeping. A flag never decides whether a command
writes, so `show` is the dry run, `build` is the write, and no `--dry-run` exists to contradict a
verb. And stdout carries data only, so a build narrates to **stderr** with git's own stdout relayed
there too, because `compare --json` has to parse.

`process.py` is the boundary: every subprocess in the package goes through it, including the reads
`fingerprint.py` makes of a built repo. There are no sanctioned exceptions, and a test asserts it.
