"""The command line: read what a strategy would do, then build it and look at the graph."""

import contextlib
import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from git_graph.history import GitHistory
from git_graph.scenarios import SCENARIOS
from git_graph.scenarios import Scenario
from git_graph.scenarios import find
from git_graph.shape import Shape
from git_graph.shape import measure

ROOT_HELP = (
    'Build synthetic git histories under named branching strategies, so the graph can be looked at '
    'instead of argued about.'
    '\n\n'
    'The noun is always `scenarios`, so a list to show to build loop changes only the verb. Each '
    'scenario names one way of catching up with the trunk and one button for landing it; two that '
    'differ in exactly one of those, built side by side, are the comparison this tool exists for.'
    '\n\n'
    '`show` is the dry run — it prints every command a build would run, and runs none of them. '
    '`build` is the verb that destroys and rebuilds a directory, and it only touches one carrying a '
    '.git-graph-sandbox marker.'
    '\n\n'
    'Run any partial command with no arguments or --help to see what comes next.'
)

DEFAULT_TARGET = Path('target')

app = typer.Typer(name='git-graph', no_args_is_help=True, help=ROOT_HELP)
scenarios_app = typer.Typer(name='scenarios', no_args_is_help=True, help='Named branching strategies and the graphs they build.')
app.add_typer(scenarios_app, name='scenarios')

console = Console(highlight=False)
messages = Console(stderr=True, highlight=False)


class Interactivity:
    """Whether prompting is allowed at all, set once by the root callback."""

    no_input = False


def prompting_allowed() -> bool:
    return not Interactivity.no_input and sys.stdin.isatty()


def print_json(data: object) -> None:
    """Emit JSON to stdout, bypassing Rich markup — the machine-facing half of every read."""
    print(json.dumps(data))


def installed_version() -> str:
    try:
        return importlib.metadata.version('git-graph')
    except importlib.metadata.PackageNotFoundError:
        return 'unknown'


def installed_commit() -> str:
    """The commit this build came from, when uv installed it from a git ref.

    An install that follows a branch reports one version for as long as the branch moves,
    which is the case this answers.
    """
    with contextlib.suppress(importlib.metadata.PackageNotFoundError, OSError, json.JSONDecodeError):
        direct_url = importlib.metadata.distribution('git-graph').read_text('direct_url.json')
        if direct_url:
            return json.loads(direct_url).get('vcs_info', {}).get('commit_id') or ''
    return ''


def show_version(asked: bool) -> None:
    if not asked:
        return
    commit = installed_commit()
    console.print(f'git-graph {installed_version()}{f" @ {commit[:8]}" if commit else ""}')
    raise typer.Exit()


def resolve(name: str) -> Scenario:
    """Look up a scenario, turning an unknown name into a usage error that lists the known ones."""
    try:
        return find(name)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


def scenario_record(scenario: Scenario) -> dict[str, str]:
    return {
        'name': scenario.name,
        'catch_up': str(scenario.catch_up),
        'land': str(scenario.land),
        'description': scenario.description,
    }


def confirm_destroying(target: Path, force: bool) -> None:
    """Gate a rebuild of a directory that already holds one.

    A fresh or empty target needs no confirmation — there is nothing to lose, and the
    sandbox marker already refuses anywhere holding real work.
    """
    if force or not target.exists() or not any(target.iterdir()):
        return
    if not prompting_allowed():
        raise typer.BadParameter(f'{target} already holds a build; pass --force to rebuild it')
    if not typer.confirm(f'Destroy and rebuild {target}?'):
        messages.print('Nothing built.')
        raise typer.Exit(1)


def build_into(scenario: Scenario, target: Path, interactive: bool = False) -> Shape:
    """Generate the scenario, run it in the sandbox, and measure what it left behind."""
    with GitHistory(target_dir=target, interactive=interactive) as history:
        scenario.generate(history)
        history.write_commands_to_file('git-commands.sh')
        history.execute_commands()
        sandbox = history.target_dir
    return measure(sandbox)


def shape_table(title: str, shapes: dict[str, Shape]) -> Table:
    table = Table(title=title, title_justify='left')
    table.add_column('scenario')
    table.add_column('commits', justify='right')
    table.add_column('merges', justify='right')
    table.add_column('trunk steps', justify='right')
    table.add_column('branches left', justify='right')
    for name, shape in shapes.items():
        table.add_row(name, str(shape.commits), str(shape.merges), str(shape.trunk_steps), str(shape.branches))
    return table


@app.callback()
def root(
    version: Annotated[
        bool | None,
        typer.Option('--version', callback=show_version, is_eager=True, help='Show the installed version and exit.'),
    ] = None,
    no_input: Annotated[
        bool,
        typer.Option('--no-input', help='Never prompt; fail naming the flag that would have answered.'),
    ] = False,
) -> None:
    Interactivity.no_input = no_input


@scenarios_app.command('list', rich_help_panel='Reading')
def list_scenarios(
    as_json: Annotated[bool, typer.Option('--json', help='Output as JSON to stdout.')] = False,
) -> None:
    """List the named strategies, and what each one holds fixed."""
    if as_json:
        print_json([scenario_record(scenario) for scenario in SCENARIOS])
        return
    table = Table()
    table.add_column('name')
    table.add_column('catch up')
    table.add_column('land')
    table.add_column('description')
    for scenario in SCENARIOS:
        table.add_row(scenario.name, str(scenario.catch_up), str(scenario.land), scenario.description)
    console.print(table)


@scenarios_app.command('show', rich_help_panel='Reading')
def show(
    name: Annotated[str, typer.Argument(help='Scenario name, as printed by `git-graph scenarios list`.')],
    as_json: Annotated[bool, typer.Option('--json', help='Output as JSON to stdout.')] = False,
) -> None:
    """Show a scenario and every command it would run. This is the dry run; it runs nothing."""
    scenario = resolve(name)
    commands = scenario.commands()
    if as_json:
        print_json(scenario_record(scenario) | {'timeline': [repr(event) for event in scenario.timeline], 'commands': commands})
        return
    console.print(f'[bold]{scenario.name}[/bold] — {scenario.description}')
    console.print(f'catch up by {scenario.catch_up}, land with the {scenario.land} button')
    console.print()
    console.print('[bold]Timeline[/bold]')
    for event in scenario.timeline:
        console.print(f'  {event}')
    console.print()
    console.print(f'[bold]Commands[/bold] ({len(commands)})')
    for command in commands:
        console.print(f'  {command}')


@scenarios_app.command('build', rich_help_panel='Building')
def build(
    name: Annotated[str, typer.Argument(help='Scenario name, as printed by `git-graph scenarios list`.')],
    target: Annotated[Path, typer.Option('--target', help='Directory to destroy and rebuild.')] = DEFAULT_TARGET,
    interactive: Annotated[bool, typer.Option('--interactive', help='Step through, pausing at each commit and merge.')] = False,
    force: Annotated[bool, typer.Option('--force', help='Rebuild a directory that already holds a build, without asking.')] = False,
) -> None:
    """Build a scenario into a sandbox, then look at it with `git -C <target> log --graph`."""
    scenario = resolve(name)
    if interactive and not prompting_allowed():
        raise typer.BadParameter('--interactive needs a terminal; drop it to run the whole scenario through')
    confirm_destroying(target, force)
    shape = build_into(scenario, target, interactive=interactive)
    messages.print(f'Built {scenario.name} in {target}')
    console.print(shape_table(scenario.name, {scenario.name: shape}))


@scenarios_app.command('compare', rich_help_panel='Building')
def compare(
    first: Annotated[str, typer.Argument(help='Scenario name, as printed by `git-graph scenarios list`.')],
    second: Annotated[str, typer.Argument(help='The scenario to build beside it.')],
    target: Annotated[Path, typer.Option('--target', help='Directory to hold both builds, one per scenario.')] = DEFAULT_TARGET,
    force: Annotated[bool, typer.Option('--force', help='Rebuild directories that already hold a build, without asking.')] = False,
    as_json: Annotated[bool, typer.Option('--json', help='Output as JSON to stdout.')] = False,
) -> None:
    """Build two scenarios side by side, each in its own sandbox, and report how the graphs differ."""
    scenarios = [resolve(first), resolve(second)]
    if first == second:
        raise typer.BadParameter('compare two different scenarios; building one twice answers nothing')
    for scenario in scenarios:
        confirm_destroying(target / scenario.name, force)
    shapes = {scenario.name: build_into(scenario, target / scenario.name) for scenario in scenarios}
    if as_json:
        print_json({name: shape.as_dict() for name, shape in shapes.items()})
        return
    console.print(shape_table('Same timeline, one variable changed', shapes))
    for scenario in scenarios:
        console.print(f'git -C {target / scenario.name} log --graph --oneline --all')


def cli() -> None:
    app()
