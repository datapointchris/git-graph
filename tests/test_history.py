"""The engine: what it queues, and the determinism every comparison depends on."""

import shlex

import pytest

from git_graph.history import DEFAULT_BRANCH
from git_graph.history import SYNTHETIC_AUTHOR_EMAIL
from git_graph.history import CatchUpStyle
from git_graph.history import GitHistory
from git_graph.history import LandStyle
from git_graph.history import branch_name


def texts(history: GitHistory) -> list[str]:
    return [command.text for command in history.commands]


def test_repo_is_initialized_on_the_default_branch():
    history = GitHistory()
    history.init_git_repo()
    assert f'git init -b {DEFAULT_BRANCH}' in texts(history)


def test_init_writes_an_identity_git_can_commit_with():
    history = GitHistory()
    history.init_git_repo()
    assert [text for text in texts(history) if text.startswith('git config user.email') and SYNTHETIC_AUTHOR_EMAIL in text]


def test_init_creates_a_remote_to_push_at():
    """Without one, a fast-forward landing cannot be modeled and a force push has nowhere to go."""
    history = GitHistory()
    history.init_git_repo()
    assert [text for text in texts(history) if text.startswith('git init --bare')]
    assert [text for text in texts(history) if text.startswith('git remote add')]


def test_a_commit_pins_both_dates():
    """A hash that moves with the wall clock cannot be compared against anything."""
    history = GitHistory()
    history.commit('work')
    commit = next(text for text in texts(history) if 'git commit' in text)
    assert 'GIT_AUTHOR_DATE=' in commit
    assert 'GIT_COMMITTER_DATE=' in commit


def test_the_clock_advances_so_two_commits_are_never_the_same_instant():
    history = GitHistory()
    history.commit('first')
    history.commit('second')
    stamps = {text.split('GIT_AUTHOR_DATE=')[1].split(' ')[0] for text in texts(history) if 'GIT_AUTHOR_DATE=' in text}
    assert len(stamps) == 2


def test_a_replay_keeps_the_author_and_moves_only_the_committer():
    """What makes a rebased commit's new hash attributable to its new parent and nothing else."""
    history = GitHistory()
    history.catch_up('feature/x', CatchUpStyle.rebase)
    rebase = next(text for text in texts(history) if 'git rebase' in text)
    assert 'GIT_COMMITTER_DATE=' in rebase
    assert 'GIT_AUTHOR_DATE=' not in rebase


def test_a_commit_message_never_names_the_branch_it_was_made_on():
    """A commit fast-forwarded onto the trunk is the same commit, and has to hash the same."""
    history = GitHistory()
    history.commit('refresh the session token')
    commit = next(text for text in texts(history) if 'git commit' in text)
    assert 'feature/' not in commit


def test_the_merge_button_leaves_a_merge_commit_and_a_deletable_branch():
    history = GitHistory()
    history.land('feature/x', LandStyle.merge)
    assert [text for text in texts(history) if '--no-ff' in text]
    assert 'git branch -d -q feature/x' in texts(history)


def test_the_squash_button_forces_the_branch_delete():
    """`-d` refuses, because the branch's own commits never reach the trunk."""
    history = GitHistory()
    history.land('feature/x', LandStyle.squash)
    assert 'git branch -D -q feature/x' in texts(history)


def test_a_fast_forward_landing_pushes_rather_than_merging():
    history = GitHistory()
    history.land('feature/x', LandStyle.fast_forward)
    assert [text for text in texts(history) if text.startswith('git push') and 'HEAD:main' in text]
    assert not [text for text in texts(history) if '--no-ff' in text]


@pytest.mark.parametrize('style', list(LandStyle))
def test_a_title_that_would_break_the_shell_survives_quoting(style):
    history = GitHistory()
    history.land('feature/x', style, title="fix: don't break the $SHELL")
    for command in history.commands:
        assert shlex.split(command.text) or command.text


def test_catch_up_never_writes_a_commit_of_its_own():
    """A marker commit would show up in every shape and destroy the comparison."""
    history = GitHistory()
    history.catch_up('feature/x', CatchUpStyle.rebase)
    assert not [text for text in texts(history) if text.startswith('git commit')]


def test_a_conflict_probe_counts_and_a_tolerated_command_does_not():
    """Collapsing the two would count every harmless failure as a conflict."""
    history = GitHistory()
    history.command('may fail harmlessly', tolerate_failure=True)
    history.probe_stop(history.REBASE_IN_PROGRESS)
    assert [command for command in history.commands if command.conflict_point]
    assert [command for command in history.commands if command.tolerate_failure and not command.conflict_point]


def test_commands_are_attributed_to_the_event_that_queued_them():
    history = GitHistory()
    history.begin_step('open x')
    history.open_branch(branch_name('x'), DEFAULT_BRANCH)
    assert history.commands[-1].step == 'open x'
