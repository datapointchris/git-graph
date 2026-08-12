"""The comparison ladder, and the property everything above it rests on: determinism."""

import pytest

from git_graph.fingerprint import Sameness
from git_graph.fingerprint import canonical_order
from git_graph.scenarios import SCENARIOS


def test_canonical_order_never_reads_a_hash_value():
    """Two graphs of the same shape must walk in corresponding order, or nothing is comparable."""
    ours = {'a': ['b'], 'b': ['c', 'd'], 'c': [], 'd': []}
    theirs = {'z': ['y'], 'y': ['x', 'w'], 'x': [], 'w': []}
    assert [ours_key for ours_key in canonical_order(ours, ['a'])] == ['a', 'b', 'c', 'd']
    assert [theirs_key for theirs_key in canonical_order(theirs, ['z'])] == ['z', 'y', 'x', 'w']


def test_the_same_scenario_built_twice_is_the_same_repository(tmp_path, build):
    """The keystone. Without it every comparison stops at "same shape" and can go no deeper."""
    _, first, _ = build('rebase-catch-up', tmp_path / 'one')
    _, second, _ = build('rebase-catch-up', tmp_path / 'two')
    assert first.level(second) is Sameness.identical


def test_a_worktree_leaves_no_trace_in_the_repository(tmp_path, build):
    """The whole answer to what a worktree does: nothing a repository can see."""
    _, worktree, _ = build('worktree-land', tmp_path / 'worktree')
    _, direct, _ = build('commit-to-main', tmp_path / 'direct')
    assert worktree.level(direct) is Sameness.identical


def test_replaying_work_keeps_the_shape_and_changes_the_hashes(tmp_path, build):
    _, replayed, _ = build('worktree-behind', tmp_path / 'replayed')
    _, in_order, _ = build('committed-in-order', tmp_path / 'in-order')
    assert replayed.level(in_order) is Sameness.objects


def test_counts_alone_cannot_tell_two_strategies_apart(tmp_path, build):
    """The reason the ladder exists: these two agree on every number and look nothing alike."""
    _, rebased, _ = build('rebase-catch-up', tmp_path / 'rebased')
    _, never, _ = build('no-catch-up', tmp_path / 'never')
    assert rebased.counts == never.counts
    assert rebased.level(never) is Sameness.topology


def test_merging_to_catch_up_costs_a_merge_commit_per_absorption(tmp_path, build):
    _, rebased, _ = build('rebase-catch-up', tmp_path / 'rebased')
    _, merged, _ = build('merge-catch-up', tmp_path / 'merged')
    assert merged.counts.merges > rebased.counts.merges
    assert rebased.level(merged) is Sameness.counts


@pytest.mark.parametrize('scenario', SCENARIOS, ids=lambda scenario: scenario.name)
def test_every_scenario_builds_and_can_be_measured(tmp_path, build, scenario):
    _, fingerprint, _ = build(scenario.name, tmp_path / scenario.name)
    assert fingerprint.counts.commits >= 1
    assert fingerprint.topology
