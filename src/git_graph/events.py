"""The timeline algebra: one event per git operation, and the walker that turns it into commands.

Every option lives on the **event**, not on the scenario. An earlier design put the catch-up
style and the landing button on the scenario, which made exactly five comparisons expressible
and nothing else — a history where one branch rebases and another merges could not be written
down at all. Here a scenario is only a name and a sequence, so the algebra bounds what can be
modelled rather than the two axes someone happened to need first.

`Open` taking a `base` is the whole of stacked pull requests and nested feature branches: a
branch off a branch is not a special case, it is the general one with the default filled in.
"""

from dataclasses import dataclass
from dataclasses import field

from git_graph.history import DEFAULT_BRANCH
from git_graph.history import CatchUpStyle
from git_graph.history import GitHistory
from git_graph.history import LandStyle
from git_graph.history import MergeFlags
from git_graph.history import Resolution
from git_graph.history import branch_name

TRUNK = DEFAULT_BRANCH


@dataclass(frozen=True)
class Note:
    """Says something happened that git will not record. The point of the worktree scenarios."""

    text: str

    @property
    def label(self) -> str:
        return f'note: {self.text}'


@dataclass(frozen=True)
class Open:
    """Open a branch. `base` is another feature's name, or None for the trunk."""

    feature: str
    base: str | None = None
    worktree: bool = False

    @property
    def label(self) -> str:
        where = f' off {self.base}' if self.base else ''
        return f'{"worktree new" if self.worktree else "open"} {self.feature}{where}'


@dataclass(frozen=True)
class Commit:
    """Commits on a branch, or on the trunk when `on` is None.

    `touches` names a file other branches may also write, which is the only way a conflict can
    arise: by default every commit gets a file of its own, and a file nobody else writes never
    conflicts with anything.
    """

    on: str | None = None
    n: int = 1
    message: str = 'work'
    touches: str | None = None
    content: str | None = None

    @property
    def label(self) -> str:
        count = f' x{self.n}' if self.n > 1 else ''
        shared = f' touching {self.touches}' if self.touches else ''
        return f'commit on {self.on or TRUNK}{count}{shared}'


@dataclass(frozen=True)
class CatchUp:
    """Absorb the trunk, or another branch, into an open branch."""

    feature: str
    style: CatchUpStyle = CatchUpStyle.rebase
    onto: str | None = None
    resolve: Resolution = Resolution.theirs

    @property
    def label(self) -> str:
        return f'catch up {self.feature} ({self.style})'


@dataclass(frozen=True)
class Restack:
    """`git rebase --onto <new base> <old base> <branch>` — the fix for a stacked branch.

    Its own event rather than a flag on `CatchUp`, because it is a different question: a
    catch-up absorbs commits, a restack changes which commits the branch claims as its own
    history. Reaching for the wrong one is what produces the duplicate-content conflict that
    the stacked scenarios exist to show.
    """

    feature: str
    onto: str | None = None
    old_base: str = ''

    @property
    def label(self) -> str:
        return f'restack {self.feature} onto {self.onto or TRUNK}'


@dataclass(frozen=True)
class Land:
    """Land a branch on the trunk with one of GitHub's buttons, or with `worktree land`."""

    feature: str
    style: LandStyle = LandStyle.merge
    into: str | None = None
    delete: bool = True
    title: str | None = None

    @property
    def label(self) -> str:
        target = f' into {self.into}' if self.into else ''
        verb = 'worktree land' if self.style is LandStyle.fast_forward else f'land ({self.style})'
        return f'{verb} {self.feature}{target}'


@dataclass(frozen=True)
class Merge:
    """git's own merge verb rather than a pull request button, so the two can be compared."""

    source: str
    into: str | None = None
    flags: frozenset[MergeFlags] = field(default_factory=frozenset)

    @property
    def label(self) -> str:
        return f'merge {self.source} into {self.into or TRUNK}'


@dataclass(frozen=True)
class Abandon:
    """Delete a branch that never landed. Its commits become unreachable."""

    feature: str

    @property
    def label(self) -> str:
        return f'abandon {self.feature}'


@dataclass(frozen=True)
class Tag:
    """Name the current commit, so a later event can point at it."""

    name: str

    @property
    def label(self) -> str:
        return f'tag {self.name}'


@dataclass(frozen=True)
class CherryPick:
    """Copy a commit somewhere else. Same content, different parent, therefore a different hash."""

    ref: str
    onto: str | None = None

    @property
    def label(self) -> str:
        return f'cherry-pick {self.ref} onto {self.onto or TRUNK}'


@dataclass(frozen=True)
class Revert:
    """Undo by adding an inverse commit, which is the only undo that leaves history intact."""

    ref: str
    on: str | None = None

    @property
    def label(self) -> str:
        return f'revert {self.ref}'


@dataclass(frozen=True)
class Push:
    """Send a branch to the remote. Forced, when a rebase rewrote what the remote already had."""

    ref: str | None = None
    force: bool = False

    @property
    def label(self) -> str:
        return f'{"force-push" if self.force else "push"} {self.ref or TRUNK}'


type Event = Note | Open | Commit | CatchUp | Restack | Land | Merge | Abandon | Tag | CherryPick | Revert | Push

type Timeline = tuple[Event, ...]


@dataclass
class OpenBranch:
    """What the walker has to remember about a branch to know what could contend with what."""

    branch: str
    base_ref: str
    base_feature: str | None
    files: list[str] = field(default_factory=list)
    absorbed: int = 0


class Walker:
    """Turns a timeline into commands, tracking just enough state to know what *could* conflict.

    It tracks which files each side has written, which is enough to decide whether resolution
    steps are needed at all. It deliberately does not predict how many times git will stop:
    resolving a rebase in the branch's favour conflicts once and then applies cleanly, and the
    same rebase resolved the other way conflicts on every commit. The number of rounds emitted
    is an upper bound; the number reported is what git's exit codes actually said.
    """

    def __init__(self, history: GitHistory):
        self.history = history
        self.branches: dict[str, OpenBranch] = {}
        self.trunk_files: list[str] = []

    def state_for(self, feature: str) -> OpenBranch:
        """The open branch a feature names, or a failure that says which name was wrong.

        Landing removes a branch from this table, so the same message covers both mistakes: a
        feature that was never opened, and one referred to after it has already gone.
        """
        if feature not in self.branches:
            raise ValueError(f'timeline refers to "{feature}", which is not an open branch at that point')
        return self.branches[feature]

    def close(self, feature: str) -> OpenBranch:
        """Take a branch off the open list, because it has landed or been abandoned."""
        state = self.state_for(feature)
        del self.branches[feature]
        return state

    def resolve_ref(self, feature: str | None) -> str:
        if feature is None or feature == TRUNK:
            return TRUNK
        return self.state_for(feature).branch

    def files_since(self, state: OpenBranch) -> set[str]:
        """Files the trunk has written that this branch has not absorbed yet."""
        return set(self.trunk_files[state.absorbed :])

    def conflicts(self, state: OpenBranch) -> int:
        """How many of the branch's own commits rewrite a file the trunk also rewrote.

        Each commit writes a whole file rather than appending, so every one of them collides
        with the trunk's version rather than merging cleanly around it.
        """
        contested = self.files_since(state)
        return len([path for path in state.files if path in contested])

    def walk(self, timeline: Timeline) -> None:
        for event in timeline:
            self.history.begin_step(event.label)
            self.apply(event)

    def apply(self, event: Event) -> None:
        match event:
            case Note():
                return
            case Open():
                base_ref = self.resolve_ref(event.base)
                branch = branch_name(event.feature)
                self.history.open_branch(branch, base_ref)
                self.branches[event.feature] = OpenBranch(
                    branch=branch,
                    base_ref=base_ref,
                    base_feature=event.base,
                    absorbed=len(self.trunk_files),
                )
            case Commit():
                self.commit(event)
            case CatchUp():
                self.catch_up(event)
            case Restack():
                self.restack(event)
            case Land():
                self.land(event)
            case Merge():
                self.history.merge(self.resolve_ref(event.source), self.resolve_ref(event.into), set(event.flags))
            case Abandon():
                state = self.close(event.feature)
                self.history.command(f'git checkout -q {TRUNK}')
                self.history.command(f'git branch -D -q {state.branch}')
            case Tag():
                self.history.tag(event.name)
            case CherryPick():
                self.history.cherry_pick(event.ref, self.resolve_ref(event.onto))
            case Revert():
                self.history.revert(event.ref, self.resolve_ref(event.on))
            case Push():
                self.history.push(self.resolve_ref(event.ref), force=event.force)
            case _:
                raise TypeError(f'{event!r} is not a timeline event')

    def commit(self, event: Commit) -> None:
        ref = self.resolve_ref(event.on)
        self.history.checkout(ref)
        for index in range(event.n):
            path = event.touches or f'work-{self.history.clock:02d}.txt'
            message = event.message if event.n == 1 else f'{event.message} {index + 1}'
            self.history.commit(message, touches=path, content=event.content or message)
            if event.on is None:
                self.trunk_files.append(path)
            else:
                self.state_for(event.on).files.append(path)

    def catch_up(self, event: CatchUp) -> None:
        state = self.state_for(event.feature)
        onto = self.resolve_ref(event.onto)
        contested = self.conflicts(state) if onto == TRUNK else 0
        self.history.catch_up(state.branch, event.style, onto)
        if contested:
            match event.style:
                case CatchUpStyle.rebase:
                    self.history.resolve_rebase(event.resolve, rounds=contested)
                case CatchUpStyle.merge:
                    self.history.resolve_merge(event.resolve, f'Merge {onto} into {state.branch}')
                case CatchUpStyle.none:
                    pass
        if onto == TRUNK:
            state.absorbed = len(self.trunk_files)

    def restack(self, event: Restack) -> None:
        state = self.state_for(event.feature)
        onto = self.resolve_ref(event.onto)
        old_base = event.old_base or state.base_ref
        self.history.command(f'git checkout -q {state.branch}')
        self.history.command(self.history.committed(f'git rebase -q --onto {onto} {old_base} {state.branch}'))
        state.absorbed = len(self.trunk_files)

    def land(self, event: Land) -> None:
        state = self.close(event.feature)
        into = self.resolve_ref(event.into)
        self.history.land(state.branch, event.style, into=into, title=event.title, delete=event.delete)
        if into == TRUNK:
            # The trunk now carries whatever the branch wrote, so an open branch that has not
            # absorbed this landing is contending with those files too.
            self.trunk_files.extend(state.files)


def generate(timeline: Timeline, history: GitHistory) -> None:
    """Queue a whole timeline onto a history, executing nothing."""
    Walker(history).walk(timeline)
