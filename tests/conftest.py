"""Building a scenario chdirs into its sandbox, so every test that builds one shares this."""

import os
from pathlib import Path

import pytest

from git_graph.fingerprint import Fingerprint
from git_graph.fingerprint import measure
from git_graph.history import GitHistory
from git_graph.scenarios import find


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
