"""The guards, which are the only part of this tool where being wrong destroys something.

Every path here ends in `rm -rf .git`, and this repo has lost its own once.
"""

from pathlib import Path

import pytest

from git_graph.history import SANDBOX_MARKER
from git_graph.history import in_sandbox
from git_graph.history import prepare_sandbox
from git_graph.history import project_root


def test_the_checkout_is_found_by_its_marker_rather_than_by_position():
    root = project_root()
    assert root is not None
    assert (root / 'pyproject.toml').is_file()


def test_an_installed_build_reports_no_checkout_to_protect(tmp_path):
    """The case that silently broke: counting parents here names the interpreter's lib directory."""
    installed = tmp_path / 'lib' / 'python3.13' / 'site-packages' / 'git_graph' / 'history.py'
    installed.parent.mkdir(parents=True)
    installed.touch()

    assert project_root(installed) is None


def test_the_sandbox_refuses_the_checkout_it_ships_in():
    checkout = project_root()
    assert checkout is not None

    with pytest.raises(SystemExit, match='real work'):
        prepare_sandbox(checkout)


def test_the_sandbox_refuses_a_directory_holding_the_checkout():
    checkout = project_root()
    assert checkout is not None

    with pytest.raises(SystemExit, match='real work'):
        prepare_sandbox(checkout.parent)


def test_the_sandbox_refuses_home():
    with pytest.raises(SystemExit, match='real work'):
        prepare_sandbox(Path.home())


def test_the_sandbox_refuses_a_populated_directory_with_no_marker(tmp_path):
    """Not merely an existing git repo — a scratch directory of unrelated files is not safe either."""
    (tmp_path / 'someone-elses-work.txt').touch()

    with pytest.raises(SystemExit, match=SANDBOX_MARKER):
        prepare_sandbox(tmp_path)


def test_a_fresh_directory_is_created_and_marked(tmp_path):
    sandbox = prepare_sandbox(tmp_path / 'new')

    assert sandbox.is_dir()
    assert (sandbox / SANDBOX_MARKER).is_file()


def test_a_marked_directory_is_reused(tmp_path):
    first = prepare_sandbox(tmp_path / 'again')
    (first / 'left-over.txt').touch()

    assert prepare_sandbox(tmp_path / 'again') == first


def test_in_sandbox_answers_for_the_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert not in_sandbox()

    (tmp_path / SANDBOX_MARKER).touch()
    assert in_sandbox()
