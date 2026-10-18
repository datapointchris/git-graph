# git-graph

git-graph builds throwaway git repositories from named scenarios. A scenario is one branching
strategy, played out as a timeline of git operations. The graph it leaves behind can then be looked
at instead of argued about. It answers questions the git documentation cannot settle, because the
answer is a shape. One is what rebasing to catch up and merging to land produce several features
in. Another is whether a commit made in a second worktree lands as the same commit.

It generates sandboxes. It is not a git wrapper. Nothing in it runs against a repository that holds
work. git draws every graph it shows, so the picture is the one `git log --graph` prints in your
own terminal.

## Install

git-graph installs as a uv tool, from a tagged release. It needs Python 3.13 or later, with git on
`PATH`.

```bash
tag=$(git ls-remote --tags --refs --sort=-v:refname https://github.com/datapointchris/git-graph 'v*' | head -1 | cut -d/ -f3)
uv tool install "git+https://github.com/datapointchris/git-graph@$tag"   # the newest release
git-graph --version                                                       # the version, and the commit it was built from
git-graph update --check                                                  # whether a newer release exists
```

`git-graph update` reinstalls the newest release over the current one. It refuses an install from a
local checkout or from a branch, because neither carries a release version to compare. Every other
command checks for a newer release at most once a day. When one exists, it prints one line after
its own output. Setting `NO_AUTO_UPDATE` to any value turns that check off.

## Starting from scratch

```bash
cd "$(mktemp -d)"                                    # builds land in ./target, so start somewhere empty
git-graph scenarios list                             # every scenario, grouped by what it teaches, beside its partner
git-graph scenarios show worktree-land               # its timeline, and the compare that reads it beside its partner
git-graph scenarios show worktree-land --commands    # every git line a build would run; runs none of them
git-graph scenarios build worktree-land              # builds into ./target, draws the graph, prints the git line to see it yourself
git-graph scenarios compare worktree-land commit-to-main --target pair   # proves it worked: IDENTICAL
```

`show` is the dry run. `build` is the write. No flag decides whether a command writes, so there is
no `--dry-run` to forget.

A target that already holds a build is rebuilt only after a yes. `--force` is that yes. Without a
terminal, or under `--no-input`, `build` fails naming `--force` rather than asking. A non-empty
directory with no `.git-graph-sandbox` marker is refused before any question.

`compare` gives each scenario a directory of its own name under its target. Here those are
`pair/worktree-land` and `pair/commit-to-main`.

Every command is a verb under one noun, `scenarios`. Any partial command run with no arguments
prints its help, so the tree is walkable without this file.

## `scenarios list` and `show` — a scenario is a timeline of events, read without running it

```bash
git-graph scenarios list --json                   # name, group, what it teaches, its partner, its timeline
git-graph scenarios show conflict-rebase          # one timeline, event by event
git-graph scenarios show conflict-rebase --json   # the same, with every command it would run
```

A scenario is a name and a timeline. The timeline is a sequence of events. The events are `Open`,
`Commit`, `CatchUp`, `Land`, `Restack`, `Merge`, `CherryPick`, `Revert`, `Push`, `Abandon`, `Tag`
and `Note`. Each event carries its own options. The catch-up style lives on `CatchUp`. The landing
style lives on `Land`. Neither lives on the scenario, so a history where one branch rebases and
another merges is as writable as one that treats them alike.

A branch opened off another branch is an `Open` with a base. Stacked pull requests need no event of
their own.

The timeline is data rather than code. `list` and `show` read it without building anything.
`show --commands` generates every git line with nothing written to disk.

A scenario built to be read beside another names its partner. `show` prints the `compare` command
for the pair. Each pair varies one thing, so its verdict answers one question.

The scenarios are defined in `src/git_graph/scenarios.py`.

## `build` — every command generated first, then run in a sandbox and nowhere else

```bash
git-graph scenarios build rebase-land                  # into ./target, asking first if it holds a build
git-graph scenarios build rebase-land --force --json   # rebuild without asking; counts, fingerprints, stops, path
git -C target log --graph --oneline --all              # the graph it drew, in your own terminal
(cd target && ./git-commands.sh)                       # the same run again, from the script the build wrote
```

A build generates its whole run as text before it executes a line. `show` prints that text.
`build` writes it into the sandbox as `git-commands.sh`, then runs it. Run again inside the
sandbox, the script rebuilds the same repository, down to the hashes. `build --interactive` pauses
after each commit and merge until you type `finish`.

Every build starts with `rm -rf .git` in its target. So a target must carry a `.git-graph-sandbox`
marker before anything runs. `build` creates the directory and the marker. It refuses `$HOME`. It
refuses a non-empty directory with no marker, because a scratch directory of unrelated files is no
safer to delete inside than a repository. Run from a checkout of this repository, it also refuses
the checkout and every directory containing it.

The script carries the same check in its preamble. That check is the one that matters. The script
holds `rm -rf .git` as a plain line. It runs wherever it is invoked from. Outside a sandbox, its
preamble is the only guard. If a checkout's `.git` is ever lost this way, this restores it
without touching a file in the work tree:

```bash
git init -b main
git remote add origin https://github.com/datapointchris/git-graph.git
git fetch origin
git update-ref refs/heads/main origin/main   # the branch, at the last pushed commit
git restore --staged .                       # the index, from that commit; local edits stay as edits
git branch -u origin/main
```

Each sandbox holds a bare repository, `origin.git`, as its remote. Pushing is real rather than
approximated. A fast-forward landing pushes `HEAD` straight to `main`. A rebased branch needs a
force push because its replayed commits are new objects, which only shows with somewhere to push.

Every commit is made as `git-graph <git-graph@localhost>`. A hash that depended on who ran the build
could not be compared.

Stdout carries data only. A build narrates to stderr, git's own output included. That is what lets
`--json` parse on every `scenarios` command.

## `compare` — the first level at which two histories differ, not just whether they do

```bash
git-graph scenarios compare worktree-land commit-to-main         # IDENTICAL
git-graph scenarios compare worktree-behind committed-in-order   # OBJECTS, naming each commit that changed hash
git-graph scenarios compare rebase-catch-up no-catch-up          # TOPOLOGY: the same numbers, a different graph
```

`compare` builds two scenarios into sandboxes of their own. It reports the **first level at which
they differ**, going deeper only as long as it has to:

| level | means |
| --- | --- |
| `counts` | different sizes |
| `topology` | same numbers, different graph |
| `trees` | same graph, different content |
| `objects` | same content, different commit hashes — the work was replayed, not moved |
| `identical` | the same repository, down to the hashes |

The last two levels mean something only because the generator is deterministic. Every commit has
fixed content and a fixed message. Its dates come from a clock that advances one minute per commit
and never reads the system time. Two scenarios doing the same work produce identical hashes. A hash
that does differ differs for a reason worth naming.

`worktree-land` against `commit-to-main` is the whole answer to what a worktree does to a
repository: nothing. A second checkout shares one object store. Landing by fast-forward creates no
commit of its own. One commit stays one commit. The history cannot be told from one typed on the
trunk.

Move the trunk first, as `worktree-behind` does, and the verdict drops to `objects`. The landing
replays the commit onto the new tip under a new hash. A table names every commit that kept its
content and changed its hash.

Counts alone would call `rebase-catch-up` and `no-catch-up` identical. They agree on every number.
Their graphs look nothing alike. That is why the ladder exists.

## Stops — the cost of a conflict, which the finished graph never records

```bash
git-graph scenarios compare conflict-rebase conflict-merge        # a rebase and a merge, through one contested file
git-graph scenarios compare conflict-keep-trunk conflict-rebase   # the same rebase, resolved toward the trunk
```

A commit writes a file of its own unless a scenario points two commits at the same path. That is the
only way anything here can conflict. `build` and `compare` then report **stops**: the times git
handed the run back for a person to repair. That number is nowhere in the finished repository.

A merge presents every conflicting file at once. It stops once, however long the branch. A rebase
replays one commit at a time, so how often it stops depends on the side its resolution keeps.
`conflict-rebase` keeps the branch's side. Its first replayed commit conflicts. The rest apply on
top of that resolution, so it stops once too. Resolved toward the trunk, every contested commit
conflicts again.

`conflict-keep-trunk` is that case. It shows the trap in git's own vocabulary. During a rebase,
`--ours` is the branch being replayed onto, not your own work. Resolving that way discards every
commit the branch made and leaves it empty.

The timeline decides only whether resolution steps are needed. How many stops a run took is
measured from git's exit codes, never predicted.

## GitHub's buttons are modeled by the shape they leave, not by their metadata

`Land` models GitHub's three merge buttons, plus a fast-forward push, rather than git's local
verbs. The graph that matters is the one in the repository after the pull request closes.
`local-merge-verbs` shows git's own merge, as a fast-forward and with `--no-ff`, for contrast.

The merge button is modeled with the merge commit titled by the pull request and carrying its body,
in place of GitHub's default `Merge pull request #N from …` title.

GitHub performs a real squash or rebase with its own committer identity and timestamps. The shape
reproduces here. The metadata does not, which is fine for a comparison about shape.
