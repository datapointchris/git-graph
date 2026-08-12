from dataclasses import dataclass

from git_graph.history import GitHistory
from git_graph.history import MergeFlags


@dataclass
class GitHistoryScenario:
    name: str
    merge_flags: set[MergeFlags]
    history: GitHistory
