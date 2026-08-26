from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as installed_version


def _tool_version() -> str:
    """This build's version, or 'unknown' from a source checkout.

    Read from the installed distribution rather than a constant here, so
    whatever bumps `pyproject.toml` owns the only copy. A second constant is
    bumped by nothing: logsift reached 0.1.3 and typos 1.0.0 while each went on
    reporting 0.1.0, because semantic-release writes `version_toml` and touches
    no other file.

    The argument is the distribution name, which is not the package directory —
    this package is `git_graph` and the distribution is `git-graph`.

    A checkout that was never installed has no metadata and says so rather than
    inventing a number.
    """
    try:
        return installed_version('git-graph')
    except PackageNotFoundError:
        return 'unknown'


__version__ = _tool_version()
