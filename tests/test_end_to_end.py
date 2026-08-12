"""Runs generated commands through real git, which is the only place the tool is proved.

The command-list tests assert what was built and nothing in them notices a command git
rejects — a malformed flag, a branch that does not exist yet, an identity git refuses to
commit without. Those only surface by running it.
"""

import os
import subprocess
from pathlib import Path

import pytest

from git_graph.main import DEFAULT_BRANCH
from git_graph.main import GitHistory
from git_graph.main import MergeFlags


def git(sandbox: Path, *args: str) -> str:
    """Read from a built sandbox, failing the test on any git error."""
    result = subprocess.run(['git', '-C', str(sandbox), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


@pytest.fixture(autouse=True)
def restore_working_directory():
    """Insurance against a run that dies before `__exit__` and strands pytest in a sandbox."""
    origin = Path.cwd()
    yield
    os.chdir(origin)


def build(target: Path, **kwargs) -> None:
    with GitHistory(target_dir=target, **kwargs) as history:
        history.commit(msg='FIRST COMMIT', branch=DEFAULT_BRANCH)
        history.feature('experiment 01')
        history.final_commit()
        history.execute_commands()


def test_generated_history_builds_a_real_repo(tmp_path):
    sandbox = tmp_path / 'sandbox'

    build(sandbox, merge_flags={MergeFlags.no_ff})

    assert git(sandbox, 'rev-parse', '--abbrev-ref', 'HEAD') == DEFAULT_BRANCH
    assert git(sandbox, 'rev-list', '--count', '--merges', 'HEAD') == '1'
    assert git(sandbox, 'status', '--porcelain') == ''


def test_a_landed_feature_branch_is_gone_and_its_commits_are_not(tmp_path):
    sandbox = tmp_path / 'sandbox'

    build(sandbox, merge_flags={MergeFlags.no_ff})

    assert 'feature/experiment-01' not in git(sandbox, 'branch', '--list')
    assert 'regular commit' in git(sandbox, 'log', '--format=%s')


def test_the_working_directory_is_restored_after_a_run(tmp_path):
    origin = Path.cwd()

    build(tmp_path / 'sandbox')

    assert Path.cwd() == origin


def test_two_runs_build_side_by_side_rather_than_nesting(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    build(Path('first'))
    build(Path('second'))

    assert (tmp_path / 'first' / '.git').is_dir()
    assert (tmp_path / 'second' / '.git').is_dir()
    assert not (tmp_path / 'first' / 'second').exists()
