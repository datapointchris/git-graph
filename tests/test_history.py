"""Every assertion here reads `GitHistory.commands`, which is the tool's real output.

The engine generates shell commands and executes nothing until `execute_commands()`, so
the command list is the argv the run would issue — spying on it tests what was built
without building a repo to find out.
"""

import pytest

from git_graph.main import DEFAULT_BRANCH
from git_graph.main import SYNTHETIC_AUTHOR_EMAIL
from git_graph.main import CatchUpStyle
from git_graph.main import GitHistory
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
    assert f'git config user.email "{SYNTHETIC_AUTHOR_EMAIL}"' in history.commands


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


def test_no_generated_command_mentions_master():
    history = GitHistory()
    history.init_git_repo()
    history.commit(msg='FIRST COMMIT', branch=DEFAULT_BRANCH)
    history.feature('experiment 01')
    history.final_commit()
    assert not [command for command in history.commands if 'master' in command]
