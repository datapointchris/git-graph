"""The timeline algebra — that any sequence is expressible, and that it refuses nonsense."""

import pytest

from git_graph.events import CatchUp
from git_graph.events import Commit
from git_graph.events import Land
from git_graph.events import Open
from git_graph.events import generate
from git_graph.history import GitHistory


def texts(timeline) -> list[str]:
    history = GitHistory()
    generate(timeline, history)
    return [command.text for command in history.commands]


def test_a_branch_can_be_opened_off_another_branch():
    """Stacked pull requests and nested feature branches are this, and nothing else."""
    commands = texts((Open('api'), Open('cli', base='api')))
    assert 'git checkout -q -b feature/cli feature/api' in commands


def test_a_branch_opened_without_a_base_comes_off_the_trunk():
    assert 'git checkout -q -b feature/api main' in texts((Open('api'),))


def test_referring_to_a_branch_no_event_opened_names_the_feature():
    with pytest.raises(ValueError, match='never opened'):
        texts((Land('never opened'),))


def test_referring_to_a_branch_that_already_landed_names_the_feature():
    with pytest.raises(ValueError, match='api'):
        texts((Open('api'), Land('api'), CatchUp('api')))


def test_each_commit_writes_its_own_file_unless_told_otherwise():
    """A file nobody else writes never conflicts, which is why a conflict has to be asked for."""
    commands = texts((Open('api'), Commit(on='api', n=3, message='api')))
    written = {text.split('> ')[-1] for text in commands if text.startswith('printf')}
    assert len(written) == 3


def test_commits_can_be_pointed_at_one_shared_file():
    commands = texts((Open('api'), Commit(on='api', touches='config.txt', content='limit = 1')))
    assert [text for text in commands if text.endswith('> config.txt')]


def test_a_contested_file_makes_the_catch_up_resolve():
    """Nothing conflicts unless both sides wrote the same path, so the resolution only appears then."""
    quiet = texts((Open('api'), Commit(on='api'), Commit(), CatchUp('api')))
    contested = texts(
        (
            Open('api'),
            Commit(on='api', touches='config.txt', content='a'),
            Commit(touches='config.txt', content='b'),
            CatchUp('api'),
        )
    )
    assert not [text for text in quiet if 'rebase --continue' in text]
    assert [text for text in contested if 'rebase --continue' in text]


def test_every_event_carries_its_own_options():
    """The reason the algebra is open-ended: two branches in one history can differ."""
    from git_graph.history import CatchUpStyle

    commands = texts(
        (
            Open('api'),
            Open('cli'),
            Commit(),
            CatchUp('api', CatchUpStyle.rebase),
            CatchUp('cli', CatchUpStyle.merge),
        )
    )
    assert [text for text in commands if 'git rebase' in text]
    assert [text for text in commands if 'git merge --no-edit' in text]
