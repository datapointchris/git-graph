from main import GitHistory, MergeFlags
from dataclasses import dataclass

@dataclass
class GitHistoryScenario:
    name: str
    merge_flags: set[MergeFlags]
    history: GitHistory
    