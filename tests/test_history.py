"""Every assertion here reads `GitHistory.commands`, which is the tool's real output.

The engine generates shell commands and executes nothing until `execute_commands()`, so
the command list is the argv the run would issue — spying on it tests what was built
without building a repo to find out.
"""

import shlex

import pytest

from git_graph.main import DEFAULT_BRANCH
from git_graph.main import SYNTHETIC_AUTHOR_EMAIL
from git_graph.main import CatchUpStyle
from git_graph.main import GitHistory
from git_graph.main import LandStyle
from git_graph.main import MergeFlags


def test_repo_is_initialised_on_the_default_branch():
    history = GitHistory()
    history.init_git_repo()
    assert f'git init -b {DEFAULT_BRANCH}' in history.commands


def test_feature_branches_from_and_lands_on_the_default_branch():
    history = GitHistory()
    history.feature('experiment 01')
    assert f'git checkout -b feature/experiment-01 {DEFAULT_BRANCH}' in history.commands
    assert f'git checkout {DEFAULT_BRANCH}' in history.commands
    assert 'git merge --no-edit feature/experiment-01' in history.commands


def test_init_writes_an_identity_git_can_commit_with():
    history = GitHistory()
    history.init_git_repo()
    assert [command for command in history.commands if command.startswith('git config user.email') and SYNTHETIC_AUTHOR_EMAIL in command]


def test_merge_flags_are_emitted_in_a_stable_order():
    """Flags come from a set, whose iteration order is arbitrary between processes.

    Sorted order is the only order two runs can agree on, and two generated scripts that
    disagree textually cannot be diffed against each other.
    """
    history = GitHistory(merge_flags={MergeFlags.no_ff, MergeFlags.no_commit})
    history.feature('experiment 01')
    merge = next(command for command in history.commands if command.startswith('git merge'))
    emitted_flags = merge.split()[2:-1]
    assert emitted_flags == sorted(emitted_flags)


def test_start_branch_leaves_the_branch_open_and_names_it():
    history = GitHistory()
    branch = history.start_branch('experiment 01')
    assert branch == 'feature/experiment-01'
    assert f'git checkout -b feature/experiment-01 {DEFAULT_BRANCH}' in history.commands
    assert not [command for command in history.commands if command.startswith('git merge')]


def test_the_trunk_can_advance_while_a_branch_is_open():
    history = GitHistory()
    branch = history.start_branch('experiment 01')
    history.advance(DEFAULT_BRANCH, commits=2)
    assert history.commands.index(f'git checkout -b {branch} {DEFAULT_BRANCH}') < history.commands.index(f'git checkout {DEFAULT_BRANCH}')
    assert len([command for command in history.commands if f'[{DEFAULT_BRANCH}]' in command]) == 2


def test_rebase_catch_up_replays_the_branch_and_records_nothing():
    history = GitHistory()
    history.catch_up('feature/experiment-01', CatchUpStyle.rebase)
    assert history.commands == ['git checkout feature/experiment-01', f'git rebase {DEFAULT_BRANCH}']


def test_merge_catch_up_absorbs_the_trunk_with_a_commit():
    history = GitHistory()
    history.catch_up('feature/experiment-01', CatchUpStyle.merge)
    assert history.commands == ['git checkout feature/experiment-01', f'git merge --no-edit {DEFAULT_BRANCH}']


def test_no_catch_up_touches_the_branch_at_all():
    history = GitHistory()
    history.catch_up('feature/experiment-01', CatchUpStyle.none)
    assert history.commands == []


@pytest.mark.parametrize('style', list(CatchUpStyle))
def test_catch_up_never_writes_a_commit_of_its_own(style):
    """A marker commit would show up in every shape and destroy the comparison."""
    history = GitHistory()
    history.catch_up('feature/experiment-01', style)
    assert not [command for command in history.commands if command.startswith('git commit')]


def test_the_merge_button_leaves_a_merge_commit_and_a_deletable_branch():
    history = GitHistory()
    history.land('feature/experiment-01', LandStyle.merge)
    merge = next(command for command in history.commands if command.startswith('git merge'))
    assert merge.startswith('git merge --no-ff -m ')
    assert 'git branch -d feature/experiment-01' in history.commands


def test_the_squash_button_forces_the_branch_delete():
    """`-d` refuses, because the branch's own commits never reach the trunk."""
    history = GitHistory()
    history.land('feature/experiment-01', LandStyle.squash)
    assert 'git merge --squash feature/experiment-01' in history.commands
    assert 'git branch -D feature/experiment-01' in history.commands


def test_the_rebase_button_replays_then_fast_forwards():
    history = GitHistory()
    history.land('feature/experiment-01', LandStyle.rebase)
    assert history.commands[:4] == [
        'git checkout feature/experiment-01',
        f'git rebase {DEFAULT_BRANCH}',
        f'git checkout {DEFAULT_BRANCH}',
        'git merge --ff-only feature/experiment-01',
    ]


def test_pull_requests_are_numbered_in_the_order_they_land():
    history = GitHistory()
    history.land('feature/one', LandStyle.squash)
    history.land('feature/two', LandStyle.squash)
    subjects = [command for command in history.commands if command.startswith('git commit -m')]
    assert '(#1)' in subjects[0]
    assert '(#2)' in subjects[1]


@pytest.mark.parametrize('style', list(LandStyle))
def test_a_title_that_would_break_the_shell_survives_quoting(style):
    history = GitHistory()
    history.land('feature/experiment-01', style, title="fix: don't break the $SHELL")
    for command in history.commands:
        assert shlex.split(command)


def test_a_quoted_title_reaches_git_intact():
    history = GitHistory()
    history.land('feature/experiment-01', LandStyle.merge, title="fix: don't break the $SHELL")
    merge = next(command for command in history.commands if command.startswith('git merge'))
    assert "fix: don't break the $SHELL" in shlex.split(merge)


def test_no_generated_command_mentions_master():
    history = GitHistory()
    history.init_git_repo()
    history.commit(msg='FIRST COMMIT', branch=DEFAULT_BRANCH)
    history.feature('experiment 01')
    history.final_commit()
    assert not [command for command in history.commands if 'master' in command]
