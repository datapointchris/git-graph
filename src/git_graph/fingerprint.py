"""Measuring a built repo at four depths, so a comparison can say *where* two histories diverge.

Counts alone cannot answer the question. `rebase-catch-up` and `no-catch-up` agree on every
number and produce visibly different graphs, so a tool that stopped at counting would report
"no difference" for two histories that look nothing alike. Run
`git-graph scenarios compare rebase-catch-up no-catch-up` to see it.

The four levels, each strictly finer than the last:

1. **counts** — how much is there
2. **topology** — the shape of the graph, independent of every hash
3. **trees** — the content each commit holds
4. **objects** — the commit hashes themselves

The interesting verdicts are the last two. *Same trees, different objects* is a rebase or a
cherry-pick: identical work, new identities. *Same objects* means two scenarios did not merely
resemble each other, they produced the same repository — which is the strongest thing that can
be said about a worktree, and it is only sayable because the generator is deterministic.
"""

import enum
import hashlib
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

from git_graph import process
from git_graph.history import DEFAULT_BRANCH


class Sameness(enum.StrEnum):
    """The first level at which two repos disagree, or `identical` when they never do."""

    counts = 'counts'
    topology = 'topology'
    trees = 'trees'
    objects = 'objects'
    identical = 'identical'


VERDICTS: dict[Sameness, str] = {
    Sameness.counts: 'Different sizes — the histories are not the same length or shape.',
    Sameness.topology: 'Same numbers, different graph. The counts coincide; the shapes do not.',
    Sameness.trees: 'Same graph, different content. The commits hold different files.',
    Sameness.objects: 'Same graph, same content, different commit hashes — the work was replayed, not moved.',
    Sameness.identical: 'Identical repositories, down to the commit hashes.',
}
"""Prose keyed by verdict, so the sentence lives in one table and nothing compares sentences."""


@dataclass(frozen=True)
class Counts:
    commits: int
    merges: int
    trunk_steps: int
    branches: int
    tags: int


@dataclass(frozen=True)
class Fingerprint:
    counts: Counts
    topology: str
    trees: str
    objects: str

    def as_dict(self) -> dict:
        return {'counts': asdict(self.counts), 'topology': self.topology, 'trees': self.trees, 'objects': self.objects}

    def level(self, other: 'Fingerprint') -> Sameness:
        """The first level at which this repo and another disagree."""
        if self.counts != other.counts:
            return Sameness.counts
        if self.topology != other.topology:
            return Sameness.topology
        if self.trees != other.trees:
            return Sameness.trees
        if self.objects != other.objects:
            return Sameness.objects
        return Sameness.identical


def git_output(sandbox: Path, *args: str) -> str:
    """Read from a built sandbox, raising rather than returning a wrong number on git's error."""
    result = process.run(['git', '-C', str(sandbox), *args], capture_stdout=True, capture_stderr=True, check=True)
    return result.stdout.strip()


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def tips(sandbox: Path) -> list[tuple[str, str]]:
    """Every ref and what it points at, ordered by name so the traversal below is reproducible."""
    listing = git_output(sandbox, 'for-each-ref', '--format=%(refname) %(objectname)', '--sort=refname')
    return [(name, sha) for name, sha in (line.split(' ', 1) for line in listing.splitlines() if line)]


def parent_map(sandbox: Path) -> dict[str, list[str]]:
    listing = git_output(sandbox, 'rev-list', '--all', '--parents')
    return {parts[0]: parts[1:] for parts in (line.split() for line in listing.splitlines() if line)}


def tree_map(sandbox: Path) -> dict[str, str]:
    listing = git_output(sandbox, 'log', '--all', '--format=%H %T')
    return {commit: tree for commit, tree in (line.split(' ', 1) for line in listing.splitlines() if line)}


def canonical_order(parents: dict[str, list[str]], ref_tips: list[str]) -> list[str]:
    """Every commit, in an order derived from the graph rather than from any hash.

    Depth-first from each ref in name order, first parent first. Nothing about the ordering
    reads a hash's value, so two repos with the same shape and different hashes walk their
    commits in corresponding order — which is what lets the fingerprints below be compared at
    all.
    """
    order: list[str] = []
    seen: set[str] = set()
    stack = list(reversed(ref_tips))
    while stack:
        commit = stack.pop()
        if commit in seen:
            continue
        seen.add(commit)
        order.append(commit)
        stack.extend(reversed(parents.get(commit, [])))
    return order


def measure(sandbox: Path, trunk: str = DEFAULT_BRANCH) -> Fingerprint:
    """Fingerprint a built repo at all four levels."""
    refs = tips(sandbox)
    parents = parent_map(sandbox)
    trees = tree_map(sandbox)
    order = canonical_order(parents, [sha for _, sha in refs])
    position = {commit: index for index, commit in enumerate(order)}

    structure = [f'{position[commit]}<-{",".join(str(position[p]) for p in parents.get(commit, []))}' for commit in order]
    named = [f'{name}@{position[sha]}' for name, sha in refs]
    local_branches = [name for name, _ in refs if name.startswith('refs/heads/')]

    return Fingerprint(
        counts=Counts(
            commits=int(git_output(sandbox, 'rev-list', '--count', trunk)),
            merges=int(git_output(sandbox, 'rev-list', '--count', '--merges', trunk)),
            trunk_steps=int(git_output(sandbox, 'rev-list', '--count', '--first-parent', trunk)),
            branches=len(local_branches),
            tags=len([name for name, _ in refs if name.startswith('refs/tags/')]),
        ),
        topology=digest('|'.join(structure + named)),
        trees=digest('|'.join(trees.get(commit, '') for commit in order)),
        objects=digest('|'.join(order)),
    )


def graph(sandbox: Path, colour: bool = True) -> str:
    """git's own graph drawing — the thing you would actually look at in a terminal."""
    return git_output(
        sandbox,
        '-c',
        'log.date=short',
        'log',
        '--graph',
        '--all',
        f'--color={"always" if colour else "never"}',
        '--format=%C(auto)%h%d %s',
    )


def commit_list(sandbox: Path) -> list[tuple[str, str, str]]:
    """(short hash, subject, tree) for every commit, in the hash-independent canonical order."""
    parents = parent_map(sandbox)
    order = canonical_order(parents, [sha for _, sha in tips(sandbox)])
    detail = {
        commit: (short, subject, tree)
        for commit, short, subject, tree in (
            line.split('\x1f') for line in git_output(sandbox, 'log', '--all', '--format=%H\x1f%h\x1f%s\x1f%T').splitlines()
        )
    }
    return [detail[commit] for commit in order if commit in detail]


def rehomed(first: Path, second: Path) -> list[tuple[str, str, str]]:
    """(subject, hash here, hash there) for work both repos hold under different identities.

    The answer to "what did the rebase actually do". Matching on the tree rather than the hash
    is the whole trick: a replayed commit keeps its content exactly and changes its name, so
    tree equality finds the same work while hash inequality is the thing being reported.
    """
    ours = {tree: (short, subject) for short, subject, tree in commit_list(first)}
    theirs = {tree: (short, subject) for short, subject, tree in commit_list(second)}
    return [(ours[tree][1], ours[tree][0], theirs[tree][0]) for tree in ours.keys() & theirs.keys() if ours[tree][0] != theirs[tree][0]]


def only_in(first: Path, second: Path) -> list[str]:
    """Commit subjects the first repo has and the second does not."""
    theirs = {subject for _, subject, _ in commit_list(second)}
    return [subject for _, subject, _ in commit_list(first) if subject not in theirs]


def shared_trees(first: Path, second: Path) -> tuple[set[str], set[str]]:
    """Tree hashes each repo holds that the other does not — content present in only one.

    Trees rather than commits, because a rebase changes every commit hash while preserving
    every tree. Comparing commits would report a rebased history as wholly different work,
    which is the opposite of what happened.
    """
    ours = set(tree_map(first).values())
    theirs = set(tree_map(second).values())
    return ours - theirs, theirs - ours
