"""The command line: read what a strategy would do, build it, then look at what it left behind."""

import contextlib
import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.text import Text

from git_graph import render
from git_graph.fingerprint import VERDICTS
from git_graph.fingerprint import Fingerprint
from git_graph.fingerprint import measure
from git_graph.fingerprint import rehomed
from git_graph.history import GitHistory
from git_graph.scenarios import SCENARIOS
from git_graph.scenarios import Scenario
from git_graph.scenarios import find

ROOT_HELP = (
    'Build synthetic git histories under named strategies, so the graph each one produces can be '
    'looked at instead of argued about.'
    '\n\n'
    'The noun is always `scenarios`, so a list to show to build loop changes only the verb. '
    '`compare` builds two into their own sandboxes and reports where they part company, going '
    'deeper only as long as it has to: how much is there, then the shape of the graph, then the '
    'content, then the commit hashes. Two histories that agree all the way down are the same '
    'repository — which is the whole answer to what a worktree does.'
    '\n\n'
    '`show` is the dry run. It prints every command a build would run and runs none of them; '
    '`build` is the verb that destroys and rebuilds a directory, and only one carrying a '
    '.git-graph-sandbox marker.'
    '\n\n'
    'Run any partial command with no arguments or --help to see what comes next.'
)

DEFAULT_TARGET = Path('target')

app = typer.Typer(name='git-graph', no_args_is_help=True, help=ROOT_HELP)
scenarios_app = typer.Typer(
    name='scenarios',
    no_args_is_help=True,
    help='Named git strategies, the histories they build, and what separates two of them.',
)
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
    """The commit this build came from, when uv installed it from a git ref."""
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


def scenario_record(scenario: Scenario) -> dict:
    return {
        'name': scenario.name,
        'group': scenario.group,
        'teaches': scenario.teaches,
        'compare_with': scenario.compare_with,
        'timeline': [event.label for event in scenario.timeline],
    }


def confirm_destroying(target: Path, force: bool) -> None:
    """Gate a rebuild of a directory that already holds one.

    A fresh or empty target needs no confirmation — there is nothing to lose, and the sandbox
    marker already refuses anywhere holding real work.
    """
    if force or not target.exists() or not any(target.iterdir()):
        return
    if not prompting_allowed():
        raise typer.BadParameter(f'{target} already holds a build; pass --force to rebuild it')
    if not typer.confirm(f'Destroy and rebuild {target}?'):
        messages.print('Nothing built.')
        raise typer.Exit(1)


def build_into(scenario: Scenario, target: Path, interactive: bool = False) -> tuple[Path, Fingerprint, GitHistory]:
    """Generate the scenario, run it in the sandbox, and measure what it left behind."""
    with GitHistory(target_dir=target, interactive=interactive) as history:
        scenario.generate(history)
        history.write_commands_to_file('git-commands.sh')
        history.execute_commands()
        sandbox = history.target_dir
    return sandbox, measure(sandbox), history


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
    """List every scenario, grouped by what looking at it teaches."""
    if as_json:
        print_json([scenario_record(scenario) for scenario in SCENARIOS])
        return
    console.print(render.scenario_table())


@scenarios_app.command('show', rich_help_panel='Reading')
def show(
    name: Annotated[str, typer.Argument(help='Scenario name, as printed by `git-graph scenarios list`.')],
    commands: Annotated[bool, typer.Option('--commands', help='Also print every command a build would run.')] = False,
    as_json: Annotated[bool, typer.Option('--json', help='Output as JSON to stdout.')] = False,
) -> None:
    """Show a scenario's timeline, and optionally every command it would run. Runs nothing."""
    scenario = resolve(name)
    if as_json:
        print_json(scenario_record(scenario) | {'commands': scenario.commands()})
        return
    console.print(f'[bold]{scenario.name}[/bold] — {scenario.teaches}')
    if scenario.compare_with:
        console.print(f'read beside: git-graph scenarios compare {scenario.name} {scenario.compare_with}')
    console.print()
    console.print(render.timeline_table(scenario))
    if commands:
        console.print()
        for command in scenario.commands():
            console.print(f'  {command}')


@scenarios_app.command('build', rich_help_panel='Building')
def build(
    name: Annotated[str, typer.Argument(help='Scenario name, as printed by `git-graph scenarios list`.')],
    target: Annotated[Path, typer.Option('--target', help='Directory to destroy and rebuild.')] = DEFAULT_TARGET,
    interactive: Annotated[bool, typer.Option('--interactive', help='Step through, pausing at each commit and merge.')] = False,
    force: Annotated[bool, typer.Option('--force', help='Rebuild a directory that already holds a build, without asking.')] = False,
    as_json: Annotated[bool, typer.Option('--json', help='Output as JSON to stdout.')] = False,
) -> None:
    """Build a scenario into a sandbox and show the graph it produced."""
    scenario = resolve(name)
    if interactive and not prompting_allowed():
        raise typer.BadParameter('--interactive needs a terminal; drop it to run the whole scenario through')
    confirm_destroying(target, force)
    sandbox, fingerprint, history = build_into(scenario, target, interactive=interactive)

    if as_json:
        print_json(fingerprint.as_dict() | {'stops': history.stops, 'sandbox': str(sandbox)})
        return
    console.print(render.graph_panel(sandbox, f'{scenario.name} — {scenario.teaches}'))
    console.print()
    console.print(render.counts_table({scenario.name: fingerprint}))
    console.print()
    console.print(render.run_report(history.step_summary()))
    console.print()
    console.print(f'git -C {sandbox} log --graph --oneline --all')


@scenarios_app.command('compare', rich_help_panel='Building')
def compare(
    first: Annotated[str, typer.Argument(help='Scenario name, as printed by `git-graph scenarios list`.')],
    second: Annotated[str, typer.Argument(help='The scenario to build beside it.')],
    target: Annotated[Path, typer.Option('--target', help='Directory to hold both builds, one per scenario.')] = DEFAULT_TARGET,
    force: Annotated[bool, typer.Option('--force', help='Rebuild directories that already hold a build, without asking.')] = False,
    as_json: Annotated[bool, typer.Option('--json', help='Output as JSON to stdout.')] = False,
) -> None:
    """Build two scenarios side by side and report the first level at which they differ."""
    if first == second:
        raise typer.BadParameter('compare two different scenarios; building one twice answers nothing')
    scenarios = [resolve(first), resolve(second)]
    for scenario in scenarios:
        confirm_destroying(target / scenario.name, force)

    built = {scenario.name: build_into(scenario, target / scenario.name) for scenario in scenarios}
    sandboxes = {name: sandbox for name, (sandbox, _, _) in built.items()}
    prints = {name: fingerprint for name, (_, fingerprint, _) in built.items()}
    stops = {name: history.stops for name, (_, _, history) in built.items()}
    level = prints[first].level(prints[second])

    if as_json:
        print_json(
            {
                'verdict': level.value,
                'says': VERDICTS[level],
                'scenarios': {name: prints[name].as_dict() | {'stops': stops[name]} for name in prints},
                'rehomed': [
                    {'subject': subject, first: ours, second: theirs}
                    for subject, ours, theirs in rehomed(sandboxes[first], sandboxes[second])
                ],
            }
        )
        return

    panels = [render.graph_panel(sandboxes[name], name) for name in prints]
    console.print(render.side_by_side(console, panels, [render.widest(sandboxes[name]) for name in prints]))
    console.print()
    console.print(render.verdict_panel(level, first, second))
    console.print()
    console.print(render.counts_table(prints))
    if any(stops.values()):
        console.print()
        console.print(Text('stops: ' + ', '.join(f'{name} {count}' for name, count in stops.items())))
        console.print(Text('A stop is a conflict git handed back. The finished graph does not record any of them.'))
    console.print()
    console.print(render.difference_report(sandboxes[first], sandboxes[second], first, second, level))
    console.print()
    for name in prints:
        console.print(f'git -C {sandboxes[name]} log --graph --oneline --all')


def cli() -> None:
    app()
