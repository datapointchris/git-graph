"""Every assertion here reads `GitHistory.commands`, which is the tool's real output.

The engine generates shell commands and executes nothing until `execute_commands()`, so
the command list is the argv the run would issue — spying on it tests what was built
without building a repo to find out.
"""

from git_graph.main import DEFAULT_BRANCH
from git_graph.main import SYNTHETIC_AUTHOR_EMAIL
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


def test_no_generated_command_mentions_master():
    history = GitHistory()
    history.init_git_repo()
    history.commit(msg='FIRST COMMIT', branch=DEFAULT_BRANCH)
    history.feature('experiment 01')
    history.final_commit()
    assert not [command for command in history.commands if 'master' in command]
