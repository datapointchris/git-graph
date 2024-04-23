from dataclasses import dataclass

from main import GitHistory, MergeFlags


@dataclass
class GitHistoryScenario:
    name: str
    merge_flags: set[MergeFlags]
    history: GitHistory
