"""What the built repos actually show — the findings each scenario exists to produce."""

import subprocess
from pathlib import Path

import pytest

from git_graph.scenarios import SCENARIOS
from git_graph.scenarios import find


def git(sandbox: Path, *args: str) -> str:
    result = subprocess.run(['git', '-C', str(sandbox), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def test_scenario_names_are_unique():
    names = [scenario.name for scenario in SCENARIOS]
    assert len(names) == len(set(names))


def test_every_declared_partner_exists():
    """A `compare with` naming nothing is a dead end printed on every listing."""
    for scenario in SCENARIOS:
        if scenario.compare_with:
            assert find(scenario.compare_with)


def test_an_unknown_scenario_names_the_known_ones():
    with pytest.raises(ValueError, match='rebase-catch-up'):
        find('does-not-exist')


def test_generating_commands_touches_nothing_on_disk(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert find('rebase-catch-up').commands()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('name', ['rebase-catch-up', 'squash-land', 'rebase-land', 'conflict-rebase'])
def test_a_landed_branch_is_gone_and_the_trunk_is_checked_out(tmp_path, build, name):
    sandbox, _, _ = build(name, tmp_path / name)
    assert git(sandbox, 'branch', '--list', 'feature/*') == ''
    assert git(sandbox, 'rev-parse', '--abbrev-ref', 'HEAD') == 'main'


def test_squashing_keeps_the_changes_and_discards_the_commits(tmp_path, build):
    sandbox, fingerprint, _ = build('squash-land', tmp_path / 'squash')
    subjects = git(sandbox, 'log', '--format=%s', 'main')
    assert fingerprint.counts.merges == 0
    assert 'session token refresh 1' not in subjects
    assert '(#1)' in subjects


def test_rebasing_to_land_keeps_every_commit_on_a_linear_trunk(tmp_path, build):
    sandbox, fingerprint, _ = build('rebase-land', tmp_path / 'rebase')
    assert fingerprint.counts.merges == 0
    assert 'session token refresh 1' in git(sandbox, 'log', '--format=%s', 'main')


def test_a_rebase_stops_and_a_merge_stops_once(tmp_path, build):
    """The cost the finished graph records nowhere, which is why the run is measured too."""
    _, _, rebasing = build('conflict-rebase', tmp_path / 'rebase')
    _, _, merging = build('conflict-merge', tmp_path / 'merge')
    assert rebasing.stops >= 1
    assert merging.stops == 1


def test_resolving_a_rebase_toward_the_trunk_discards_the_branch(tmp_path, build):
    """`--ours` during a rebase means the branch you are replaying onto, not your own work."""
    kept, _, _ = build('conflict-rebase', tmp_path / 'kept')
    lost, _, _ = build('conflict-keep-trunk', tmp_path / 'lost')
    assert 'limit = 200' in git(kept, 'show', 'main:config.txt')
    assert 'limit = 50' in git(lost, 'show', 'main:config.txt')


def test_a_cherry_pick_copies_content_under_a_new_hash(tmp_path, build):
    sandbox, _, _ = build('cherry-pick', tmp_path / 'cherry')
    subjects = git(sandbox, 'log', '--all', '--format=%s')
    assert subjects.count('patch the leak') == 2


def test_a_revert_adds_an_inverse_rather_than_removing_anything(tmp_path, build):
    sandbox, _, _ = build('revert', tmp_path / 'revert')
    subjects = git(sandbox, 'log', '--format=%s', 'main')
    assert 'the regression' in subjects
    assert 'Revert' in subjects


def test_an_abandoned_branch_leaves_its_commits_unreachable(tmp_path, build):
    sandbox, fingerprint, _ = build('abandoned-branch', tmp_path / 'abandoned')
    assert 'spike' not in git(sandbox, 'log', '--all', '--format=%s')
    assert fingerprint.counts.branches == 1


def test_a_stacked_branch_still_lands_after_its_base_is_squashed(tmp_path, build):
    sandbox, _, _ = build('stacked-on-squash', tmp_path / 'stacked')
    assert git(sandbox, 'branch', '--list', 'feature/*') == ''
    assert 'cli 1' in git(sandbox, 'log', '--format=%s', 'main')
