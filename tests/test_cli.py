"""The CLI, driven as a real process.

Run out-of-process on purpose. The contract another program depends on is the exit code and
the stdout/stderr split, and neither is observable from a function call — a build narrating
onto stdout parses as valid Python and breaks every caller of `--json`.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import typer

from git_graph.main import confirm_destroying
from git_graph.main import resolve
from git_graph.scenarios import SCENARIOS


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, '-m', 'git_graph', *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_no_arguments_shows_help_rather_than_an_error():
    """Exit 2 is typer's own no_args_is_help code, which every Python CLI on the fleet returns."""
    result = run()
    assert result.returncode == 2
    assert 'scenarios' in result.stdout
    assert result.stderr == ''


def test_a_bare_resource_shows_its_verbs():
    result = run('scenarios')
    assert result.returncode == 2
    assert 'compare' in result.stdout
    assert 'build' in result.stdout


def test_version_is_one_line_naming_the_tool():
    result = run('--version')
    assert result.returncode == 0
    assert result.stdout.startswith('git-graph ')
    assert len(result.stdout.strip().splitlines()) == 1


def test_list_json_carries_every_scenario():
    result = run('scenarios', 'list', '--json')
    assert result.returncode == 0
    assert [record['name'] for record in json.loads(result.stdout)] == [scenario.name for scenario in SCENARIOS]


def test_show_is_the_dry_run_and_writes_nothing(tmp_path):
    result = run('scenarios', 'show', 'rebase-catch-up', '--json', cwd=tmp_path)
    assert result.returncode == 0
    assert json.loads(result.stdout)['commands']
    assert list(tmp_path.iterdir()) == []


def test_an_unknown_scenario_is_a_usage_error():
    result = run('scenarios', 'show', 'does-not-exist')
    assert result.returncode == 2
    assert result.stdout == ''


def test_an_unknown_scenario_names_the_known_ones():
    with pytest.raises(typer.BadParameter, match='rebase-catch-up'):
        resolve('does-not-exist')


def test_comparing_a_scenario_with_itself_is_a_usage_error(tmp_path):
    result = run('scenarios', 'compare', 'rebase-catch-up', 'rebase-catch-up', '--target', str(tmp_path / 'out'))
    assert result.returncode == 2
    assert not (tmp_path / 'out').exists()


def test_building_over_an_existing_sandbox_needs_force_when_not_a_terminal(tmp_path):
    target = tmp_path / 'sandbox'

    first = run('scenarios', 'build', 'squash-land', '--target', str(target))
    blocked = run('scenarios', 'build', 'squash-land', '--target', str(target))

    assert first.returncode == 0
    assert blocked.returncode == 2


def test_refusing_a_rebuild_names_the_flag_that_would_allow_it(tmp_path):
    """Asserted at the source: the same message read back off stderr is rich's rendering of it,
    which colours the flag into `-` plus `-force` on a runner and not on a workstation."""
    target = tmp_path / 'sandbox'
    target.mkdir()
    (target / 'already-here').touch()

    with pytest.raises(typer.BadParameter, match='--force'):
        confirm_destroying(target, force=False)


def test_an_empty_target_is_rebuilt_without_asking(tmp_path):
    target = tmp_path / 'sandbox'
    target.mkdir()

    confirm_destroying(target, force=False)


def test_force_rebuilds_an_existing_sandbox(tmp_path):
    target = tmp_path / 'sandbox'

    run('scenarios', 'build', 'squash-land', '--target', str(target))
    rebuilt = run('scenarios', 'build', 'squash-land', '--target', str(target), '--force')

    assert rebuilt.returncode == 0


def test_interactive_without_a_terminal_is_a_usage_error(tmp_path):
    target = tmp_path / 'sandbox'

    result = run('scenarios', 'build', 'squash-land', '--target', str(target), '--interactive')

    assert result.returncode == 2
    assert not target.exists()


@pytest.mark.parametrize('command', [('scenarios', 'list'), ('scenarios', 'show', 'rebase-catch-up')])
def test_a_read_puts_only_its_data_on_stdout(command):
    result = run(*command, '--json')
    assert json.loads(result.stdout)


def test_a_build_keeps_its_narration_off_stdout(tmp_path):
    """The one a function-call test cannot see: git's own output inherits the process's stdout."""
    result = run(
        'scenarios',
        'compare',
        'rebase-catch-up',
        'merge-catch-up',
        '--target',
        str(tmp_path / 'out'),
        '--json',
    )

    assert result.returncode == 0
    assert set(json.loads(result.stdout)) == {'rebase-catch-up', 'merge-catch-up'}
    assert 'git init' in result.stderr


def test_comparing_two_scenarios_measures_both(tmp_path):
    result = run(
        'scenarios',
        'compare',
        'rebase-catch-up',
        'merge-catch-up',
        '--target',
        str(tmp_path / 'out'),
        '--json',
    )

    shapes = json.loads(result.stdout)
    assert shapes['merge-catch-up']['merges'] > shapes['rebase-catch-up']['merges']
    assert (tmp_path / 'out' / 'rebase-catch-up' / '.git').is_dir()
    assert (tmp_path / 'out' / 'merge-catch-up' / '.git').is_dir()


def test_a_build_leaves_the_rerunnable_script_behind(tmp_path):
    target = tmp_path / 'sandbox'

    run('scenarios', 'build', 'rebase-land', '--target', str(target))

    script = target / 'git-commands.sh'
    assert script.is_file()
    assert script.read_text().startswith('#!/usr/bin/env bash')
