"""The one place this package leaves the process.

Every subprocess goes through `run`, and the three callers that need it want three different
error postures — a generated command whose failure is data, a cleanup that reports nothing,
and a read that must raise rather than return a wrong number. Those are arguments here rather
than three separate calls to `subprocess.run`, because an undocumented boundary is one a later
change walks straight past. `tests/test_process.py` asserts nothing else in the package starts
a process.

The timeout is the part no caller would have added on its own. Every command here is a git
operation on a small synthetic repo and finishes in milliseconds, so the only way one blocks
is by waiting on input nobody is going to type — a merge that opens an editor because a
`--no-edit` was forgotten will sit there until the terminal is closed.
"""

import subprocess
from collections.abc import Sequence

COMMAND_TIMEOUT_SECONDS = 120


def run(
    command: str | Sequence[str],
    *,
    capture_stdout: bool = False,
    capture_stderr: bool = False,
    check: bool = False,
    timeout: int = COMMAND_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    """Run a command, as a shell line when given a string and directly when given a sequence.

    Streams are captured only where a caller has something to do with them. git's own stderr is
    normally left to flow to the terminal, because it is where git explains a conflict and that
    explanation is the most useful thing on the screen during a build.
    """
    return subprocess.run(
        command,
        shell=isinstance(command, str),
        stdout=subprocess.PIPE if capture_stdout else None,
        stderr=subprocess.PIPE if capture_stderr else None,
        text=True,
        check=check,
        timeout=timeout,
    )
