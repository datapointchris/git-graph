"""A scenario is a named branching strategy plus the history it produces.

The unit of comparison. Two scenarios differ in one variable — how an open branch absorbs
the trunk, which button lands it — and build from the same timeline into separate sandboxes,
so the two graphs can be put side by side. Strategies used to live as commented-out lines
under `__main__`, which meant comparing two of them destroyed the first.

The timeline is deliberately data rather than a function: a scenario has to be listable and
readable without being run, and a callable can only be executed to find out what it does.
"""

from dataclasses import dataclass

from git_graph.history import DEFAULT_BRANCH
from git_graph.history import CatchUpStyle
from git_graph.history import GitHistory
from git_graph.history import LandStyle


@dataclass(frozen=True)
class OpenBranch:
    """Open a feature branch off the trunk, and leave it open."""

    feature: str
    commits: int = 2


@dataclass(frozen=True)
class AdvanceTrunk:
    """Commit straight onto the trunk, moving it under every branch currently open."""

    commits: int = 1


@dataclass(frozen=True)
class CatchUp:
    """Absorb the trunk into an open branch, in whichever style the scenario names."""

    feature: str


@dataclass(frozen=True)
class Land:
    """Land an open branch on the trunk, with whichever button the scenario names."""

    feature: str


type TimelineEvent = OpenBranch | AdvanceTrunk | CatchUp | Land

DEFAULT_TIMELINE: tuple[TimelineEvent, ...] = (
    OpenBranch('session token refresh'),
    AdvanceTrunk(commits=2),
    CatchUp('session token refresh'),
    OpenBranch('split config loader'),
    AdvanceTrunk(),
    Land('session token refresh'),
    CatchUp('split config loader'),
    OpenBranch('retry on timeout'),
    AdvanceTrunk(),
    Land('split config loader'),
    CatchUp('retry on timeout'),
    OpenBranch('drop legacy exporter'),
    Land('retry on timeout'),
    CatchUp('drop legacy exporter'),
    Land('drop legacy exporter'),
)
"""Four features whose lifetimes overlap, because a strategy only shows itself under overlap.

Every catch-up here follows real trunk movement — an `AdvanceTrunk`, or another feature
landing. A catch-up with nothing to absorb is a no-op git reports as "already up to date",
and a timeline full of those compares two strategies on a history where neither does
anything.
"""


def require_open(open_branches: dict[str, str], feature: str) -> str:
    """Resolve a feature to its branch, naming the feature rather than raising a bare KeyError."""
    if feature not in open_branches:
        raise ValueError(f'timeline catches up or lands "{feature}", which no earlier event opened')
    return open_branches[feature]


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    catch_up: CatchUpStyle
    land: LandStyle
    timeline: tuple[TimelineEvent, ...] = DEFAULT_TIMELINE

    def generate(self, history: GitHistory) -> None:
        """Queue this scenario's whole run onto a history, executing nothing."""
        open_branches: dict[str, str] = {}
        history.commit(msg='FIRST COMMIT', branch=DEFAULT_BRANCH)
        for event in self.timeline:
            match event:
                case OpenBranch():
                    open_branches[event.feature] = history.start_branch(event.feature, commits=event.commits)
                case AdvanceTrunk():
                    history.advance(DEFAULT_BRANCH, commits=event.commits)
                case CatchUp():
                    history.catch_up(require_open(open_branches, event.feature), self.catch_up)
                case Land():
                    history.land(require_open(open_branches, event.feature), self.land, title=f'feat: {event.feature}')
                    del open_branches[event.feature]
                case _:
                    raise TypeError(f'{self.name}: timeline holds {event!r}, which is not a timeline event')
        history.command(f'git checkout {DEFAULT_BRANCH}')
        history.final_commit()

    def commands(self) -> list[str]:
        """The whole run as text, generated without a sandbox or anything on disk."""
        history = GitHistory()
        history.generate_preamble()
        self.generate(history)
        return history.commands


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        name='rebase-catch-up',
        description='Rebase to catch up, merge button to land. The fleet workflow.',
        catch_up=CatchUpStyle.rebase,
        land=LandStyle.merge,
    ),
    Scenario(
        name='merge-catch-up',
        description='Merge main into the branch to catch up, merge button to land.',
        catch_up=CatchUpStyle.merge,
        land=LandStyle.merge,
    ),
    Scenario(
        name='no-catch-up',
        description='Never absorb the trunk; land whatever the branch diverged into.',
        catch_up=CatchUpStyle.none,
        land=LandStyle.merge,
    ),
    Scenario(
        name='squash-land',
        description='Rebase to catch up, squash button to land. No branch survives.',
        catch_up=CatchUpStyle.rebase,
        land=LandStyle.squash,
    ),
    Scenario(
        name='rebase-land',
        description='Rebase to catch up, rebase button to land. One linear trunk.',
        catch_up=CatchUpStyle.rebase,
        land=LandStyle.rebase,
    ),
)
"""The two axes, held one at a time.

The first three vary how a branch catches up and land the same way; the first, fourth and
fifth catch up the same way and vary the button. Comparing across both at once answers
neither question.
"""


def find(name: str) -> Scenario:
    """Look up a scenario by name, listing the known ones when there is no match."""
    for scenario in SCENARIOS:
        if scenario.name == name:
            return scenario
    known = ', '.join(scenario.name for scenario in SCENARIOS)
    raise ValueError(f'unknown scenario {name!r}. Known scenarios: {known}')
