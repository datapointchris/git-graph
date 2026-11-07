"""Building a scenario chdirs into its sandbox, so every test that builds one shares this."""

import os
import subprocess
from pathlib import Path

import pytest

from git_graph.fingerprint import Fingerprint
from git_graph.fingerprint import measure
from git_graph.history import GitHistory
from git_graph.scenarios import find

GIT_REPOSITORY_VARIABLES = subprocess.run(
    ['git', 'rev-parse', '--local-env-vars'], capture_output=True, text=True, check=True
).stdout.split()
"""The variables git exports into the processes it launches, `GIT_DIR` and `GIT_INDEX_FILE` among them.

A hook or a `git rebase --exec` run from a linked worktree hands them to the suite. `GIT_DIR`
outranks the working directory, so a build's `git init`, `git config` and `rm -rf .git` would act
on the repository being committed rather than the sandbox.
"""


@pytest.fixture(autouse=True)
def clear_git_repository_variables(monkeypatch):
    for name in GIT_REPOSITORY_VARIABLES:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def restore_working_directory():
    """Insurance against a run that dies before `__exit__` and strands pytest in a sandbox."""
    origin = Path.cwd()
    yield
    os.chdir(origin)


@pytest.fixture
def build():
    """Build a named scenario into a directory and hand back where it went and what it made."""

    def _build(name: str, target: Path) -> tuple[Path, Fingerprint, GitHistory]:
        with GitHistory(target_dir=target) as history:
            find(name).generate(history)
            history.execute_commands()
            sandbox = history.target_dir
        return sandbox, measure(sandbox), history

    return _build
