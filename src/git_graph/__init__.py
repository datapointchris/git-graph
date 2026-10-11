from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as installed_version


def _tool_version() -> str:
    """This build's version, or 'unknown' from a source checkout.

    Read from the installed distribution, whose version the release tag sets
    through uv-dynamic-versioning. A constant here would be bumped by nothing.

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
