"""The command tree, walked: every command shows an example, and every command the tool prints exists."""

import json
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import typer
from typer.testing import CliRunner

from git_graph.main import app
from git_graph.scenarios import SCENARIOS

REPO = Path(__file__).parent.parent
TREE = typer.main.get_command(app)


def subcommands(command: Any) -> dict[str, Any] | None:
    """A group's commands by name, or None for a leaf."""
    return getattr(command, 'commands', None)


def walk(command: Any, path: tuple[str, ...] = ()) -> Iterator[tuple[tuple[str, ...], Any]]:
    yield path, command
    for name, child in (subcommands(command) or {}).items():
        yield from walk(child, (*path, name))


def test_every_command_carries_an_example():
    """An agent lifting an invocation from --help has only the flag list without one."""
    lacking = [' '.join(path) or '(root)' for path, command in walk(TREE) if 'Examples:' not in (command.help or '')]
    assert lacking == []


def test_every_command_answers_help():
    runner = CliRunner()
    failing = [path for path, _ in walk(TREE) if runner.invoke(app, [*path, '--help']).exit_code != 0]
    assert failing == []


# A command printed for a person to run. In the source: a line that starts with it, a code span,
# or after a `label: `. In the README: a shell fence line or a code span. Prose such as "a
# git-graph sandbox" is none of those. A word running into a `/` or `.` is a path, not a verb.
WORDS = r'((?: [a-z][\w-]*(?![\w/.-]))+)'
PRINTED_IN_SOURCE = re.compile(rf"(?:^[ \t]*'?[ \t]*|`|: )git-graph{WORDS}", re.MULTILINE)
SHELL_FENCE = re.compile(r'^```(?:bash|sh)\n(.*?)^```', re.MULTILINE | re.DOTALL)
PRINTED_IN_FENCE = re.compile(rf'^git-graph{WORDS}', re.MULTILINE)
PRINTED_IN_SPAN = re.compile(rf'`git-graph{WORDS}')


def printed_commands() -> Iterator[tuple[str, list[str]]]:
    for source in sorted((REPO / 'src' / 'git_graph').glob('*.py')):
        for match in PRINTED_IN_SOURCE.finditer(source.read_text()):
            yield source.name, match.group(1).split()
    readme = (REPO / 'README.md').read_text()
    for fence in SHELL_FENCE.finditer(readme):
        for match in PRINTED_IN_FENCE.finditer(fence.group(1)):
            yield 'README.md', match.group(1).split()
    for match in PRINTED_IN_SPAN.finditer(readme):
        yield 'README.md', match.group(1).split()


def test_every_command_it_prints_is_in_the_command_tree():
    """A hint naming a renamed command sends its reader to an error. The walk stops at a leaf,
    so the scenario names after it are arguments rather than commands."""
    missing = []
    walked = 0
    for source, words in printed_commands():
        walked += 1
        command = TREE
        for word in words:
            children = subcommands(command)
            if children is None:
                break
            if word not in children:
                missing.append(f'{source}: git-graph {" ".join(words)}')
                break
            command = children[word]

    assert walked > 20
    assert missing == []


def test_every_read_prints_one_json_document_on_stdout():
    """Run out of process, because a read narrating onto stdout is visible only there."""
    reads = [
        (path, command)
        for path, command in walk(TREE)
        if getattr(command, 'rich_help_panel', None) == 'Reading' and any('--json' in param.opts for param in command.params)
    ]
    assert reads
    for path, command in reads:
        arguments = [SCENARIOS[0].name for param in command.params if param.param_type_name == 'argument' and param.required]
        result = subprocess.run(
            [sys.executable, '-m', 'git_graph', *path, *arguments, '--json'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, path
        assert json.loads(result.stdout), path
