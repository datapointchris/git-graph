# Claude Code - git-graph Development Context

Universal rules — git safety, commit conventions, testing, comments, tool preferences — live in
`~/.claude/CLAUDE.md`, and how the fleet builds Python lives in `~/dev/standards/python.md`.
Neither is restated here.

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

## Scenarios are the unit of comparison

A scenario is one catch-up style plus one landing button plus a timeline, in `scenarios.py`. The
timeline is **data, not a callable**, because a scenario has to be listable and readable without
being run — `scenarios show` prints every command a build would issue and issues none of them.

Two rules the shipped scenarios exist to protect, both of which are easy to break by adding a
"reasonable" one:

- **Vary one axis at a time.** `rebase-catch-up`, `merge-catch-up` and `no-catch-up` differ only in
  the catch-up; `rebase-catch-up`, `squash-land` and `rebase-land` differ only in the button. A
  scenario varying both answers neither question.
- **Every `CatchUp` needs real trunk movement before it** — an `AdvanceTrunk`, or another feature
  landing. A catch-up with nothing to absorb is a no-op git reports as "already up to date", and a
  timeline full of those compares two strategies on a history where neither does anything.

`catch_up()` deliberately writes no annotating commit, unlike `feature()`, which commits the
command text so the graph shows it. Whether a catch-up leaves a commit behind is the thing being
measured, and a marker the tool wrote would appear in both shapes.

## Two models of merging live here, on purpose

`MergeFlags` + `feature()` model **git's local verbs**. `LandStyle` + `land()` model **GitHub's
three buttons**, which are not the same thing — and the graph that matters is the one in the repo.
Neither replaces the other; `feature()` also carries the nested-branch case (`InnerFeature`) that
the scenario timeline cannot yet express.

## The CLI is the front door

`main.py` is the typer app, `history.py` is the engine. The standard is `~/dev/standards/cli-design.md`
and two of its rules already shaped this surface: `show` is the dry run and `build` is the write, so
no `--dry-run` flag exists to contradict a verb; and a build narrates to **stderr** with git's own
stdout relayed there too, because `compare --json` has to parse.
