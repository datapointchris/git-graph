"""The catalogue: one named history per git strategy or command worth seeing the shape of.

A scenario is a name and a timeline, nothing else. Where two scenarios exist to be compared
they are built from one shared timeline with a single argument changed, so the difference in
the result is attributable — `compare` reports a scenario pair as not like-for-like when their
timelines differ in more than that, because a table of numbers cannot tell you which of two
changes caused them.
"""

from dataclasses import dataclass
from dataclasses import replace

from git_graph.events import Abandon
from git_graph.events import CatchUp
from git_graph.events import CherryPick
from git_graph.events import Commit
from git_graph.events import Land
from git_graph.events import Merge
from git_graph.events import Note
from git_graph.events import Open
from git_graph.events import Push
from git_graph.events import Restack
from git_graph.events import Revert
from git_graph.events import Tag
from git_graph.events import Timeline
from git_graph.events import generate
from git_graph.history import CatchUpStyle
from git_graph.history import GitHistory
from git_graph.history import LandStyle
from git_graph.history import MergeFlags
from git_graph.history import Resolution


@dataclass(frozen=True)
class Scenario:
    name: str
    group: str
    teaches: str
    timeline: Timeline
    compare_with: str = ''
    """The scenario this one is built to be read beside, when there is an obvious partner."""

    def generate(self, history: GitHistory) -> None:
        generate(self.timeline, history)

    def commands(self) -> list[str]:
        """The whole run as text, generated without a sandbox or anything on disk."""
        history = GitHistory()
        history.generate_preamble()
        self.generate(history)
        return [command.text for command in history.commands]


def interleaved(catch_up: CatchUpStyle, land: LandStyle) -> Timeline:
    """Four features whose lifetimes overlap, because a strategy only shows itself under overlap.

    Every catch-up here follows real trunk movement — an ordinary commit, or another feature
    landing. A catch-up with nothing to absorb is a no-op git reports as "already up to date",
    and a timeline full of those compares two strategies on a history where neither acts.
    """
    return (
        Open('session token refresh'),
        Commit(on='session token refresh', n=2, message='session token refresh'),
        Commit(n=2, message='unrelated trunk work'),
        CatchUp('session token refresh', catch_up),
        Open('split config loader'),
        Commit(on='split config loader', n=2, message='split config loader'),
        Commit(message='typo in the readme'),
        Land('session token refresh', land),
        CatchUp('split config loader', catch_up),
        Open('retry on timeout'),
        Commit(on='retry on timeout', n=2, message='retry on timeout'),
        Commit(message='bump a dependency'),
        Land('split config loader', land),
        CatchUp('retry on timeout', catch_up),
        Open('drop legacy exporter'),
        Commit(on='drop legacy exporter', n=2, message='drop legacy exporter'),
        Land('retry on timeout', land),
        CatchUp('drop legacy exporter', catch_up),
        Land('drop legacy exporter', land),
    )


def contested(catch_up: CatchUpStyle, resolve: Resolution) -> Timeline:
    """One file, written by both sides. The only way anything here can conflict.

    Two branch commits rewrite it, so a rebase replaying them stops once per commit while a
    merge absorbing them stops once — the trade choosing between them is actually made against,
    and a cost the finished graph does not record anywhere.
    """
    return (
        Open('rate limiter'),
        Commit(on='rate limiter', message='raise the limit', touches='config.txt', content='limit = 100'),
        Commit(on='rate limiter', message='raise it further', touches='config.txt', content='limit = 200'),
        Commit(message='lower the limit on the trunk', touches='config.txt', content='limit = 50'),
        CatchUp('rate limiter', catch_up, resolve=resolve),
        Land('rate limiter'),
    )


def stacked(base_land: LandStyle, fix: bool) -> Timeline:
    """A branch opened off another branch, and what happens to it when its base lands.

    The child still carries the base's commits. Whether that is fine or a mess depends entirely
    on how the base landed: a merge puts those exact commits on the trunk, so the child rebases
    onto history it already shares. Squash and rebase both put the *content* there under new
    identities, so replaying the child re-applies changes that are already present.

    `git rebase --onto` is the repair, and it is the whole reason `Restack` is its own event:
    it tells git which commits are the child's own, instead of leaving it to work that out from
    a base that no longer exists.
    """
    repair = (Restack('cli', old_base='api-base'),) if fix else (CatchUp('cli', CatchUpStyle.rebase),)
    return (
        Open('api'),
        Commit(on='api', n=2, message='api'),
        # Tagged before the child opens, because landing the base deletes its branch — and
        # `rebase --onto` needs to name where the child's own commits start, which by then is
        # a ref nothing else remembers.
        Tag('api-base'),
        Open('cli', base='api'),
        Commit(on='cli', n=2, message='cli'),
        Commit(message='trunk moves on'),
        Land('api', base_land),
        *repair,
        Land('cli'),
    )


WORKTREE_WORK = Commit(message='refresh the session token', touches='auth.txt', content='token refreshed')
"""One commit, spelled identically wherever it is made — the control in the worktree comparison.

Same message, same file, same content, and the deterministic clock puts it at the same instant
in both scenarios. Everything that could differ is held fixed, so anything that *does* differ is
the worktree.
"""

TRUNK_WORK = Commit(message='someone else lands first', touches='notes.txt', content='noted')
"""A second fixed commit, so a pair of scenarios can hold two commits identical and vary only order."""

SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        name='rebase-catch-up',
        group='Catching up',
        teaches='Rebase to catch up, merge button to land. One clean bubble per feature.',
        timeline=interleaved(CatchUpStyle.rebase, LandStyle.merge),
        compare_with='merge-catch-up',
    ),
    Scenario(
        name='merge-catch-up',
        group='Catching up',
        teaches='Merge the trunk into the branch instead. One extra crossing per absorption.',
        timeline=interleaved(CatchUpStyle.merge, LandStyle.merge),
        compare_with='rebase-catch-up',
    ),
    Scenario(
        name='no-catch-up',
        group='Catching up',
        teaches='Never absorb the trunk. Same counts as rebasing, and a visibly different graph.',
        timeline=interleaved(CatchUpStyle.none, LandStyle.merge),
        compare_with='rebase-catch-up',
    ),
    Scenario(
        name='squash-land',
        group='Landing',
        teaches='Squash button. One commit per feature; the branch commits never reach the trunk.',
        timeline=interleaved(CatchUpStyle.rebase, LandStyle.squash),
        compare_with='rebase-catch-up',
    ),
    Scenario(
        name='rebase-land',
        group='Landing',
        teaches='Rebase button. Every commit kept, no merge commits, one linear trunk.',
        timeline=interleaved(CatchUpStyle.rebase, LandStyle.rebase),
        compare_with='rebase-catch-up',
    ),
    Scenario(
        name='worktree-land',
        group='Worktree',
        teaches='One commit made in a second worktree, landed by fast-forward. Compare hashes with commit-to-main.',
        timeline=(
            Note('git worktree add — a second checkout, sharing one object store with the first'),
            Open('session token refresh', worktree=True),
            replace(WORKTREE_WORK, on='session token refresh'),
            Land('session token refresh', LandStyle.fast_forward),
        ),
        compare_with='commit-to-main',
    ),
    Scenario(
        name='commit-to-main',
        group='Worktree',
        teaches='The same commit, made straight on the trunk. The control for worktree-land.',
        timeline=(WORKTREE_WORK, Push()),
        compare_with='worktree-land',
    ),
    Scenario(
        name='worktree-behind',
        group='Worktree',
        teaches='The same commit, but the trunk moved first — so landing replays it under a new hash.',
        timeline=(
            Open('session token refresh', worktree=True),
            replace(WORKTREE_WORK, on='session token refresh'),
            TRUNK_WORK,
            Push(),
            Land('session token refresh', LandStyle.fast_forward),
        ),
        compare_with='committed-in-order',
    ),
    Scenario(
        name='committed-in-order',
        group='Worktree',
        teaches='The same two commits made straight on the trunk. Same content, same shape, different hashes.',
        timeline=(TRUNK_WORK, WORKTREE_WORK, Push()),
        compare_with='worktree-behind',
    ),
    Scenario(
        name='stacked-on-merge',
        group='Stacked branches',
        teaches='A stacked branch whose base landed as a merge. The child rebases cleanly.',
        timeline=stacked(LandStyle.merge, fix=False),
        compare_with='stacked-on-squash',
    ),
    Scenario(
        name='stacked-on-squash',
        group='Stacked branches',
        teaches='The same stack, base squashed. The child replays commits whose content already landed.',
        timeline=stacked(LandStyle.squash, fix=False),
        compare_with='stacked-on-merge',
    ),
    Scenario(
        name='stacked-restacked',
        group='Stacked branches',
        teaches='The repair: rebase --onto tells git which commits are the child branch’s own.',
        timeline=stacked(LandStyle.squash, fix=True),
        compare_with='stacked-on-squash',
    ),
    Scenario(
        name='conflict-rebase',
        group='Conflicts',
        teaches='Rebasing through a contested file stops once per commit.',
        timeline=contested(CatchUpStyle.rebase, Resolution.theirs),
        compare_with='conflict-merge',
    ),
    Scenario(
        name='conflict-merge',
        group='Conflicts',
        teaches='Merging the same contested file stops once, whatever the branch length.',
        timeline=contested(CatchUpStyle.merge, Resolution.theirs),
        compare_with='conflict-rebase',
    ),
    Scenario(
        name='conflict-keep-trunk',
        group='Conflicts',
        teaches='The same rebase resolved with --ours, which during a rebase means the trunk: the branch is emptied.',
        timeline=contested(CatchUpStyle.rebase, Resolution.ours),
        compare_with='conflict-rebase',
    ),
    Scenario(
        name='cherry-pick',
        group='Rewriting',
        teaches='One commit copied to another branch: same content, new parent, new hash.',
        timeline=(
            Open('hotfix'),
            Commit(on='hotfix', message='patch the leak'),
            Tag('the-fix'),
            CherryPick('the-fix'),
            Land('hotfix', LandStyle.merge),
        ),
    ),
    Scenario(
        name='revert',
        group='Rewriting',
        teaches='Undo that adds an inverse commit rather than removing anything.',
        timeline=(
            Commit(message='the regression'),
            Tag('bad'),
            Commit(message='more work on top'),
            Revert('bad'),
        ),
    ),
    Scenario(
        name='force-push-after-rebase',
        group='Rewriting',
        teaches='Why a rebased branch needs a force push: the replayed commits are new objects.',
        timeline=(
            Open('session token refresh'),
            Commit(on='session token refresh', n=2, message='session token refresh'),
            Push(ref='session token refresh'),
            Commit(n=2, message='trunk moves under it'),
            CatchUp('session token refresh', CatchUpStyle.rebase),
            Note('a plain push is rejected here — the remote holds commits this branch no longer has'),
            Push(ref='session token refresh', force=True),
            Land('session token refresh'),
        ),
    ),
    Scenario(
        name='abandoned-branch',
        group='Rewriting',
        teaches='A branch deleted without landing. Its commits stay in the object store, unreachable.',
        timeline=(
            Open('spike'),
            Commit(on='spike', n=2, message='spike'),
            Commit(message='trunk carries on'),
            Abandon('spike'),
        ),
    ),
    Scenario(
        name='local-merge-verbs',
        group='Landing',
        teaches="git's own merge, no-ff and squash, as distinct from the buttons a pull request offers.",
        timeline=(
            Open('fast forwardable'),
            Commit(on='fast forwardable', message='ff'),
            Merge('fast forwardable'),
            Open('kept as a bubble'),
            Commit(on='kept as a bubble', message='bubble'),
            Merge('kept as a bubble', flags=frozenset({MergeFlags.no_ff})),
        ),
    ),
    Scenario(
        name='long-lived-branch',
        group='Stacked branches',
        teaches='A branch open across several trunk landings, with its own sub-branches merging in.',
        timeline=(
            Open('rewrite the exporter'),
            Commit(on='rewrite the exporter', n=2, message='exporter'),
            Open('exporter schema', base='rewrite the exporter'),
            Commit(on='exporter schema', n=2, message='schema'),
            Land('exporter schema', LandStyle.merge, into='rewrite the exporter'),
            Commit(message='trunk moves'),
            CatchUp('rewrite the exporter', CatchUpStyle.rebase),
            Open('exporter tests', base='rewrite the exporter'),
            Commit(on='exporter tests', n=2, message='tests'),
            Land('exporter tests', LandStyle.merge, into='rewrite the exporter'),
            Land('rewrite the exporter', LandStyle.merge),
        ),
    ),
)


def find(name: str) -> Scenario:
    """Look up a scenario by name, listing the known ones when there is no match."""
    for scenario in SCENARIOS:
        if scenario.name == name:
            return scenario
    known = ', '.join(scenario.name for scenario in SCENARIOS)
    raise ValueError(f'unknown scenario {name!r}. Known scenarios: {known}')


def groups() -> dict[str, list[Scenario]]:
    """Scenarios by what they teach, in catalogue order."""
    ordered: dict[str, list[Scenario]] = {}
    for scenario in SCENARIOS:
        ordered.setdefault(scenario.group, []).append(scenario)
    return ordered
