"""Scenario generation, asserted on the command list rather than on a built repo.

The shapes each scenario actually produces are in `test_end_to_end.py`, which builds them.
"""

from pathlib import Path

import pytest

from git_graph.history import CatchUpStyle
from git_graph.history import GitHistory
from git_graph.history import LandStyle
from git_graph.scenarios import DEFAULT_TIMELINE
from git_graph.scenarios import SCENARIOS
from git_graph.scenarios import AdvanceTrunk
from git_graph.scenarios import CatchUp
from git_graph.scenarios import Land
from git_graph.scenarios import OpenBranch
from git_graph.scenarios import Scenario
from git_graph.scenarios import find


def events_of(kind) -> int:
    return len([event for event in DEFAULT_TIMELINE if isinstance(event, kind)])


@pytest.mark.parametrize('scenario', SCENARIOS, ids=lambda scenario: scenario.name)
def test_every_scenario_generates_a_runnable_command_list(scenario):
    commands = scenario.commands()
    assert commands[0].startswith('rm ')
    assert 'git init -b main' in commands


@pytest.mark.parametrize('scenario', SCENARIOS, ids=lambda scenario: scenario.name)
def test_every_scenario_opens_and_lands_the_same_features(scenario):
    commands = scenario.commands()
    opened = [command for command in commands if command.startswith('git checkout -b ')]
    deleted = [command for command in commands if command.startswith('git branch -')]
    assert len(opened) == events_of(OpenBranch)
    assert len(deleted) == events_of(Land)


def test_the_timeline_moves_the_trunk_under_every_open_branch():
    """A catch-up with nothing to absorb compares two strategies on a history where neither acts."""
    assert events_of(AdvanceTrunk) > 0
    assert events_of(CatchUp) == events_of(OpenBranch)


def test_rebasing_to_catch_up_emits_no_merge_for_the_catch_up():
    commands = find('rebase-catch-up').commands()
    assert len([command for command in commands if command.startswith('git rebase')]) == events_of(CatchUp)


def test_merging_to_catch_up_emits_one_merge_per_catch_up():
    commands = find('merge-catch-up').commands()
    catch_up_merges = [command for command in commands if command == 'git merge --no-edit main']
    assert len(catch_up_merges) == events_of(CatchUp)


def test_not_catching_up_emits_neither():
    commands = find('no-catch-up').commands()
    assert not [command for command in commands if command.startswith('git rebase')]
    assert not [command for command in commands if command == 'git merge --no-edit main']


def test_generating_commands_touches_nothing_on_disk(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    commands = find('rebase-catch-up').commands()

    assert commands
    assert list(tmp_path.iterdir()) == []


def test_an_unknown_scenario_names_the_known_ones():
    with pytest.raises(ValueError, match='rebase-catch-up'):
        find('does-not-exist')


def test_landing_a_feature_no_event_opened_names_the_feature():
    scenario = Scenario(
        name='broken',
        description='Lands a branch that was never opened.',
        catch_up=CatchUpStyle.none,
        land=LandStyle.merge,
        timeline=(Land('never opened'),),
    )
    with pytest.raises(ValueError, match='never opened'):
        scenario.generate(GitHistory(target_dir=Path('unused')))


def test_scenario_names_are_unique():
    names = [scenario.name for scenario in SCENARIOS]
    assert len(names) == len(set(names))
