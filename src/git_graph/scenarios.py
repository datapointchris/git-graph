from dataclasses import dataclass

from git_graph.main import GitHistory
from git_graph.main import MergeFlags


@dataclass
class GitHistoryScenario:
    name: str
    merge_flags: set[MergeFlags]
    history: GitHistory
