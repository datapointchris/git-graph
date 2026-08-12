"""Runs generated commands through real git, which is the only place the tool is proved.

The command-list tests assert what was built and nothing in them notices a command git
rejects — a malformed flag, a branch that does not exist yet, an identity git refuses to
commit without. Those only surface by running it.
"""

import os
import subprocess
from pathlib import Path

import pytest

from git_graph.history import DEFAULT_BRANCH
from git_graph.history import CatchUpStyle
from git_graph.history import GitHistory
from git_graph.history import LandStyle
from git_graph.history import MergeFlags
from git_graph.scenarios import DEFAULT_TIMELINE
from git_graph.scenarios import SCENARIOS
from git_graph.scenarios import CatchUp
from git_graph.scenarios import Land
from git_graph.scenarios import find


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


def build_with_landing(target: Path, style: LandStyle) -> None:
    """One feature, with the trunk moving under it, landed by the matching GitHub button."""
    with GitHistory(target_dir=target) as history:
        history.commit(msg='FIRST COMMIT', branch=DEFAULT_BRANCH)
        branch = history.start_branch('experiment 01')
        history.advance(DEFAULT_BRANCH, commits=1)
        history.land(branch, style)
        history.execute_commands()


@pytest.mark.parametrize('style', list(LandStyle))
def test_landing_removes_the_branch_and_leaves_the_trunk_checked_out(tmp_path, style):
    sandbox = tmp_path / 'sandbox'

    build_with_landing(sandbox, style)

    assert git(sandbox, 'rev-parse', '--abbrev-ref', 'HEAD') == DEFAULT_BRANCH
    assert git(sandbox, 'branch', '--list', 'feature/*') == ''


def test_the_merge_button_leaves_the_branch_as_a_visible_bubble(tmp_path):
    sandbox = tmp_path / 'sandbox'

    build_with_landing(sandbox, LandStyle.merge)

    assert git(sandbox, 'rev-list', '--count', '--merges', DEFAULT_BRANCH) == '1'
    assert '[feature/experiment-01]' in git(sandbox, 'log', '--format=%s', DEFAULT_BRANCH)


def test_the_squash_button_keeps_the_changes_and_discards_the_commits(tmp_path):
    sandbox = tmp_path / 'sandbox'

    build_with_landing(sandbox, LandStyle.squash)

    subjects = git(sandbox, 'log', '--format=%s', DEFAULT_BRANCH)
    assert git(sandbox, 'rev-list', '--count', '--merges', DEFAULT_BRANCH) == '0'
    assert '[feature/experiment-01]' not in subjects
    assert '(#1)' in subjects


def test_the_rebase_button_keeps_the_commits_and_discards_the_branch(tmp_path):
    sandbox = tmp_path / 'sandbox'

    build_with_landing(sandbox, LandStyle.rebase)

    assert git(sandbox, 'rev-list', '--count', '--merges', DEFAULT_BRANCH) == '0'
    assert '[feature/experiment-01]' in git(sandbox, 'log', '--format=%s', DEFAULT_BRANCH)


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


def build_scenario(target: Path, name: str) -> None:
    with GitHistory(target_dir=target) as history:
        find(name).generate(history)
        history.execute_commands()


def timeline_events(kind) -> int:
    return len([event for event in DEFAULT_TIMELINE if isinstance(event, kind)])


@pytest.mark.parametrize('scenario', SCENARIOS, ids=lambda scenario: scenario.name)
def test_every_scenario_lands_everything_it_opens(tmp_path, scenario):
    sandbox = tmp_path / scenario.name

    build_scenario(sandbox, scenario.name)

    assert git(sandbox, 'branch', '--list', 'feature/*') == ''
    assert git(sandbox, 'rev-parse', '--abbrev-ref', 'HEAD') == DEFAULT_BRANCH


def test_rebasing_to_catch_up_leaves_one_merge_per_landing(tmp_path):
    sandbox = tmp_path / 'sandbox'

    build_scenario(sandbox, 'rebase-catch-up')

    merges = git(sandbox, 'rev-list', '--count', '--merges', DEFAULT_BRANCH)
    assert int(merges) == timeline_events(Land)


def test_merging_to_catch_up_adds_a_merge_per_absorption_on_top(tmp_path):
    """The thicket: every catch-up leaves a crossing in the trunk's history as well."""
    sandbox = tmp_path / 'sandbox'

    build_scenario(sandbox, 'merge-catch-up')

    merges = git(sandbox, 'rev-list', '--count', '--merges', DEFAULT_BRANCH)
    assert int(merges) == timeline_events(Land) + timeline_events(CatchUp)


def test_squashing_to_land_leaves_one_commit_per_feature_and_no_branch_commits(tmp_path):
    sandbox = tmp_path / 'sandbox'

    build_scenario(sandbox, 'squash-land')

    subjects = git(sandbox, 'log', '--format=%s', DEFAULT_BRANCH)
    assert git(sandbox, 'rev-list', '--count', '--merges', DEFAULT_BRANCH) == '0'
    assert '[feature/' not in subjects
    assert len([line for line in subjects.splitlines() if '(#' in line]) == timeline_events(Land)


def test_rebasing_to_land_keeps_every_branch_commit_on_a_linear_trunk(tmp_path):
    sandbox = tmp_path / 'sandbox'

    build_scenario(sandbox, 'rebase-land')

    subjects = git(sandbox, 'log', '--format=%s', DEFAULT_BRANCH)
    assert git(sandbox, 'rev-list', '--count', '--merges', DEFAULT_BRANCH) == '0'
    assert '[feature/' in subjects


def test_two_scenarios_build_side_by_side_and_differ(tmp_path):
    """The comparison the whole tool exists for: same timeline, one variable, two graphs."""
    rebasing = tmp_path / 'rebasing'
    merging = tmp_path / 'merging'

    build_scenario(rebasing, 'rebase-catch-up')
    build_scenario(merging, 'merge-catch-up')

    assert int(git(merging, 'rev-list', '--count', '--merges', DEFAULT_BRANCH)) > int(
        git(rebasing, 'rev-list', '--count', '--merges', DEFAULT_BRANCH)
    )


def test_two_runs_build_side_by_side_rather_than_nesting(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    build(Path('first'))
    build(Path('second'))

    assert (tmp_path / 'first' / '.git').is_dir()
    assert (tmp_path / 'second' / '.git').is_dir()
    assert not (tmp_path / 'first' / 'second').exists()
