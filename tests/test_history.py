"""Every assertion here reads `GitHistory.commands`, which is the tool's real output.

The engine generates shell commands and executes nothing until `execute_commands()`, so
the command list is the argv the run would issue — spying on it tests what was built
without building a repo to find out.
"""

from git_graph.main import DEFAULT_BRANCH
from git_graph.main import GitHistory


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


def test_no_generated_command_mentions_master():
    history = GitHistory()
    history.init_git_repo()
    history.commit(msg='FIRST COMMIT', branch=DEFAULT_BRANCH)
    history.feature('experiment 01')
    history.final_commit()
    assert not [command for command in history.commands if 'master' in command]
