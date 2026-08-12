# Git-Graph

Build synthetic git histories under different branching strategies, so the resulting graph can be
looked at rather than argued about. Generates the git commands first, then dry-runs, single-steps,
or executes them.

## The sandbox guard

Everything here destroys and rebuilds a repo in the working directory, so a target must carry a
`.git-graph-sandbox` marker file before anything runs. `prepare_sandbox()` creates the directory
and the marker, and refuses `$HOME`, this repo, any directory containing it, and any non-empty
directory that has no marker.

The generated `git-commands.sh` carries the same check in its preamble. That is the one that
matters: the script holds a bare `rm -rf .git` and runs wherever it is invoked from, which is how
this repo's own `.git` was deleted once. If that happens again:

```bash
git init
git remote add origin https://github.com/datapointchris/git-graph.git
```

## Running it

A scenario is one named branching strategy: how an open branch catches up with the trunk, and
which of GitHub's three buttons lands it.

```bash
git-graph scenarios list
git-graph scenarios show rebase-catch-up          # the dry run — prints commands, runs none
git-graph scenarios build rebase-catch-up --target target
git -C target log --graph --oneline --all
```

`show` is the dry run and `build` is the write, so there is no `--dry-run` flag to get wrong.
`build --interactive` steps through, pausing at each commit and merge.

## The comparison

Two scenarios differing in exactly one variable, built side by side into their own sandboxes:

```bash
git-graph scenarios compare rebase-catch-up merge-catch-up --target target
```

```text
┃ scenario        ┃ commits ┃ merges ┃ trunk steps ┃ branches left ┃
│ rebase-catch-up │      19 │      4 │          11 │             1 │
│ merge-catch-up  │      23 │      8 │          11 │             1 │
```

Same timeline, same four interleaved features. Merging to catch up adds a merge commit per
absorption on top of the one per landing — the thicket that argument is usually about, as a
number and as a graph you can open.

`--json` is on every read, and a build keeps its narration on stderr so `compare --json` parses.

## What it approximates, and where that stops

The three landing styles model GitHub's buttons rather than git's local verbs, because the graph
that matters is the one in the repo. GitHub performs the real squash and rebase with its own
committer identity and timestamps; the shape reproduces here and the metadata does not, which is
fine for a comparison about shape. There is no remote, so a rebase needs no force push.
