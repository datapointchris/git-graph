# Git-Graph

Build synthetic git histories from named scenarios, so the graph each one produces can be looked
at rather than argued about. Generates the git commands first, then prints, single-steps, or
executes them.

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

A scenario is a name and a timeline: a sequence of git operations — open a branch, commit, catch
up, land, cherry-pick, force-push — each carrying its own options. Every option lives on the
event rather than on the scenario, so a history where one branch rebases and another merges is as
writable as one that treats them alike.

```bash
git-graph scenarios list                          # grouped by what each one teaches
git-graph scenarios show worktree-land            # the timeline; --commands for every git line
git-graph scenarios build conflict-rebase --target target
```

`show` is the dry run and `build` is the write, so there is no `--dry-run` flag to get wrong.
`build --interactive` steps through, pausing at each commit and merge.

## The comparison

`compare` builds two scenarios into their own sandboxes and reports the **first level at which
they differ**, going deeper only as long as it has to:

| level | means |
| --- | --- |
| `counts` | different sizes |
| `topology` | same numbers, different graph |
| `trees` | same graph, different content |
| `objects` | same content, different commit hashes — the work was replayed, not moved |
| `identical` | the same repository, down to the hashes |

The last two only mean anything because the generator is deterministic: fixed content, fixed
messages, and a clock that advances one minute per commit rather than reading the wall. Two
scenarios doing the same work produce byte-identical hashes, so a hash that *does* differ differs
for a reason worth naming.

```bash
git-graph scenarios compare worktree-land commit-to-main --target target
```

```text
IDENTICAL
Identical repositories, down to the commit hashes.
```

That is the whole answer to what a worktree does to a repository: nothing. A second checkout
shares one object store, and landing by fast-forward creates no commit of its own, so one commit
stays one commit and the history is indistinguishable from having typed it on the trunk. Move the trunk first
(`compare worktree-behind committed-in-order`) and the verdict drops to `objects`, with a table
naming every commit that kept its content and changed its hash.

Counts alone would have called the first pair identical *and* called `rebase-catch-up` and
`no-catch-up` identical, which they are not — they agree on every number and produce visibly
different graphs. That is why the ladder exists.

## Conflicts, and the cost that is not in the graph

A commit writes a file of its own unless a scenario points two of them at the same path, which is
the only way anything here can conflict. `build` then reports **stops** — the number of times git
handed the run back for a human to repair.

That number is nowhere in the finished repository. Rebasing through a contested file stops once
per commit; merging the same file stops once, however long the branch. Two comparable shapes,
very different costs to reach.

`conflict-keep-trunk` shows the trap in git's own vocabulary: during a *rebase*, `--ours` is the
branch you are replaying onto rather than your own work, so resolving that way empties the branch
entirely.

`--json` is on every read, and a build keeps its narration on stderr so `compare --json` parses.

## What it approximates, and where that stops

The three landing styles model GitHub's buttons rather than git's local verbs, because the graph
that matters is the one in the repo. GitHub performs the real squash and rebase with its own
committer identity and timestamps; the shape reproduces here and the metadata does not, which is
fine for a comparison about shape.

There is a real remote — a bare repo inside the sandbox — because a fast-forward landing pushes,
and because the reason a rebased branch needs a force push is that the replayed commits are new
objects rather than the same ones moved.
