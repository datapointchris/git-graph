"""The subprocess boundary, and the guard that keeps it the only one."""

from pathlib import Path

import pytest

from git_graph import process


def test_only_the_boundary_module_starts_a_process():
    """An undocumented boundary is one a later change walks straight past, so a test holds it."""
    package = Path(process.__file__).parent
    offenders = [module.name for module in package.glob('*.py') if module.name != 'process.py' and 'subprocess.' in module.read_text()]
    assert offenders == []


def test_a_shell_string_runs_as_a_shell_line():
    assert process.run('exit 3').returncode == 3


def test_a_sequence_runs_without_a_shell():
    """`echo $HOME` unexpanded proves no shell saw it — the safe form for anything with a path in it."""
    result = process.run(['echo', '$HOME'], capture_stdout=True)
    assert result.stdout.strip() == '$HOME'


def test_streams_are_captured_only_when_asked_for():
    result = process.run('echo out', capture_stdout=True)
    assert result.stdout.strip() == 'out'
    assert result.stderr is None


def test_check_raises_where_a_wrong_answer_would_be_worse_than_none():
    with pytest.raises(Exception, match='exit status 3'):
        process.run('exit 3', check=True)


def test_a_command_that_does_not_return_gives_up():
    """The failure no caller would have guarded for itself: a git verb that opens an editor.

    Asserted with a sleep rather than a real blocking read, because pytest hands the child a
    stdin that is already at EOF — every read returns instantly and the case cannot be staged
    from inside the suite. What is under test is that the ceiling exists and fires.
    """
    with pytest.raises(Exception, match='timed out'):
        process.run('sleep 5', timeout=1)
