"""The visual layer: what a scenario did, and where two of them part company.

The graphs are git's own `--graph` drawing rather than a layout engine written here. That is
deliberate and it is the older decision this repo already made — git, lazygit and gitk all draw
it better, and more usefully, the drawing you are shown is the one you will see in your own
terminal afterwards. What is added around it is what git cannot do: two of them side by side,
a verdict naming where they diverge, and the hashes when nothing coarser will separate them.
"""

from pathlib import Path

from rich.columns import Columns
from rich.console import Console
from rich.console import Group
from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from git_graph.fingerprint import VERDICTS
from git_graph.fingerprint import Fingerprint
from git_graph.fingerprint import Sameness
from git_graph.fingerprint import graph
from git_graph.fingerprint import only_in
from git_graph.fingerprint import rehomed
from git_graph.scenarios import Scenario
from git_graph.scenarios import groups

COUNT_FIELDS = ('commits', 'merges', 'trunk_steps', 'branches', 'tags')

FIELD_HELP = {
    'commits': 'every commit reachable from the trunk',
    'merges': 'commits with more than one parent',
    'trunk_steps': 'the trunk read by first parent only — how long it is to scan',
    'branches': 'branches still alive at the end',
    'tags': 'tags left behind',
}


def graph_panel(sandbox: Path, title: str) -> Panel:
    return Panel(Text.from_ansi(graph(sandbox)), title=title, title_align='left', expand=True)


def side_by_side(console: Console, panels: list[Panel], widths: list[int]) -> RenderableType:
    """Two panels across if they fit, stacked if they do not.

    A graph that wraps is not a graph — the lanes stop lining up and the drawing becomes noise.
    Better to stack and scroll than to render something that reads as a different shape.
    """
    if max(widths) * len(panels) + 8 <= console.width:
        return Columns(panels, equal=True, expand=True)
    return Group(*panels)


def widest(sandbox: Path) -> int:
    return max((len(line) for line in graph(sandbox, color=False).splitlines()), default=0)


def scenario_table(highlight: str = '') -> Table:
    """The catalog, grouped by what each scenario teaches."""
    table = Table(show_header=True, header_style='bold', box=None, pad_edge=False)
    table.add_column('name', style='bold')
    table.add_column('teaches')
    table.add_column('compare with')
    for group, members in groups().items():
        table.add_section()
        table.add_row(Text(group, style='bold underline'), '', '')
        for scenario in members:
            style = 'reverse' if scenario.name == highlight else ''
            table.add_row(scenario.name, scenario.teaches, scenario.compare_with, style=style)
    return table


def timeline_table(scenario: Scenario) -> Table:
    table = Table(show_header=True, header_style='bold', box=None, pad_edge=False)
    table.add_column('#', justify='right')
    table.add_column('event')
    for index, event in enumerate(scenario.timeline, start=1):
        table.add_row(str(index), event.label)
    return table


def counts_table(named: dict[str, Fingerprint]) -> Table:
    """Counts for one or more repos, with the rows that differ marked."""
    table = Table(show_header=True, header_style='bold', box=None, pad_edge=False)
    table.add_column('measure')
    for name in named:
        table.add_column(name, justify='right')
    table.add_column('')
    for field in COUNT_FIELDS:
        values = [getattr(fingerprint.counts, field) for fingerprint in named.values()]
        differs = len(set(values)) > 1
        table.add_row(
            field.replace('_', ' '),
            *[str(value) for value in values],
            FIELD_HELP[field] if not differs else f'[bold]differs[/bold] — {FIELD_HELP[field]}',
            style='bold' if differs else '',
        )
    return table


def verdict_panel(level: Sameness, first: str, second: str) -> Panel:
    colors = {
        Sameness.counts: 'red',
        Sameness.topology: 'yellow',
        Sameness.trees: 'yellow',
        Sameness.objects: 'cyan',
        Sameness.identical: 'green',
    }
    body = Text.from_markup(f'[bold]{level.value.upper()}[/bold]\n{VERDICTS[level]}')
    return Panel(body, title=f'{first} vs {second}', title_align='left', border_style=colors[level])


def difference_report(first: Path, second: Path, first_name: str, second_name: str, level: Sameness) -> RenderableType:
    """What actually differs, at whatever depth the verdict says is the interesting one.

    Nothing is printed for a coarse difference beyond the subjects, because at that depth the
    graphs above already show it. The hash table only appears where it is the *only* thing left
    that separates two histories, which is exactly when someone needs to see it.
    """
    parts: list[RenderableType] = []
    if level in (Sameness.counts, Sameness.topology, Sameness.trees):
        for name, here, there in ((first_name, first, second), (second_name, second, first)):
            missing = only_in(here, there)
            if missing:
                parts.append(Text(f'only in {name}: ' + ', '.join(missing)))
    if level is Sameness.objects:
        moved = rehomed(first, second)
        table = Table(show_header=True, header_style='bold', box=None, pad_edge=False)
        table.add_column('same work, committed as')
        table.add_column(first_name)
        table.add_column(second_name)
        for subject, ours, theirs in sorted(moved):
            table.add_row(subject, ours, theirs)
        parts.append(table)
        parts.append(Text(f'{len(moved)} commits hold identical content under different hashes.'))
    if level is Sameness.identical:
        parts.append(Text('Every commit hash matches. These two are the same repository.'))
    return Group(*parts) if parts else Text('')


def run_report(steps: list[tuple[str, int, int]]) -> Table:
    """One row per timeline event: how many commands it took, and how often git stopped.

    The stop column is the reason this exists. It is the cost a conflict actually imposes and
    the finished graph records it nowhere — a rebase and a merge through the same contested
    file leave comparable shapes behind and cost very different amounts to get there.
    """
    table = Table(show_header=True, header_style='bold', box=None, pad_edge=False)
    table.add_column('event')
    table.add_column('commands', justify='right')
    table.add_column('stops', justify='right')
    for label, commands, stops in steps:
        table.add_row(label, str(commands), str(stops) if stops else '', style='bold' if stops else '')
    return table
