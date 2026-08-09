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

Scenarios are configured in `git_graph/main.py` under `__main__`. `dry_run=True` prints the
commands without executing, and `interactive=True` steps through them pausing at each commit and
merge.
