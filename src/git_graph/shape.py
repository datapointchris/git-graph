"""Measuring a built sandbox, so two graphs can be compared as numbers and not only by eye.

Looking at the graph is still the point — this is what makes the difference statable. Two
scenarios that differ in one variable produce two of these, and the fields are chosen for
what a reader of the repo would actually notice.
"""

import subprocess
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

from git_graph.history import DEFAULT_BRANCH


@dataclass(frozen=True)
class Shape:
    commits: int
    merges: int
    trunk_steps: int
    branches: int

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def git_output(sandbox: Path, *args: str) -> str:
    """Read from a built sandbox. Raises rather than returning a wrong number on git's error."""
    result = subprocess.run(['git', '-C', str(sandbox), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def measure(sandbox: Path, branch: str = DEFAULT_BRANCH) -> Shape:
    """Count what the trunk looks like after a scenario built it.

    `trunk_steps` follows first parents only, which is the history you read when you look at
    the trunk rather than at everything that ever reached it — the number that separates a
    trunk you can scan from one you cannot.
    """
    branch_lines = [line for line in git_output(sandbox, 'branch', '--list').splitlines() if line.strip()]
    return Shape(
        commits=int(git_output(sandbox, 'rev-list', '--count', branch)),
        merges=int(git_output(sandbox, 'rev-list', '--count', '--merges', branch)),
        trunk_steps=int(git_output(sandbox, 'rev-list', '--count', '--first-parent', branch)),
        branches=len(branch_lines),
    )
