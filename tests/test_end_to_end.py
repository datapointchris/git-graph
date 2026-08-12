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
from git_graph.main import CatchUpStyle
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


def build_with_catch_up(target: Path, style: CatchUpStyle) -> str:
    """Open a branch, move the trunk under it, absorb the trunk. Returns the branch."""
    with GitHistory(target_dir=target) as history:
        history.commit(msg='FIRST COMMIT', branch=DEFAULT_BRANCH)
        branch = history.start_branch('experiment 01')
        history.advance(DEFAULT_BRANCH, commits=2)
        history.catch_up(branch, style)
        history.execute_commands()
    return branch


@pytest.mark.parametrize('style', [CatchUpStyle.rebase, CatchUpStyle.merge])
def test_catching_up_absorbs_the_trunk(tmp_path, style):
    sandbox = tmp_path / 'sandbox'

    branch = build_with_catch_up(sandbox, style)

    assert git(sandbox, 'rev-list', '--count', f'{branch}..{DEFAULT_BRANCH}') == '0'


def test_rebasing_to_catch_up_leaves_the_branch_linear(tmp_path):
    sandbox = tmp_path / 'sandbox'

    branch = build_with_catch_up(sandbox, CatchUpStyle.rebase)

    assert git(sandbox, 'rev-list', '--count', '--merges', branch) == '0'
    assert git(sandbox, 'rev-list', '--count', f'{DEFAULT_BRANCH}..{branch}') == '2'


def test_merging_to_catch_up_leaves_a_merge_commit_on_the_branch(tmp_path):
    """The crossing per absorption that the fleet workflow rejects, in its smallest form."""
    sandbox = tmp_path / 'sandbox'

    branch = build_with_catch_up(sandbox, CatchUpStyle.merge)

    assert git(sandbox, 'rev-list', '--count', '--merges', branch) == '1'
    assert git(sandbox, 'rev-list', '--count', f'{DEFAULT_BRANCH}..{branch}') == '3'


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
