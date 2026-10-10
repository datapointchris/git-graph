"""`git-graph update` and the update notice share one pyselfupdate config.

Run in-process, unlike test_cli.py, because the release lookup is replaced rather than reached.
"""

from typer.testing import CliRunner

from git_graph import main

runner = CliRunner()


def test_update_installs_the_published_release(monkeypatch):
    calls = []
    monkeypatch.setattr(main, 'run_update', lambda config, **kwargs: calls.append((config, kwargs)))

    result = runner.invoke(main.app, ['update', '--check'])

    assert result.exit_code == 0
    config, kwargs = calls[0]
    assert (config.tool, config.owner) == ('git-graph', 'datapointchris')
    assert kwargs == {'check_only': True}


def test_update_does_not_also_print_the_update_notice(monkeypatch):
    # The notice would name the release the command is already installing.
    monkeypatch.setattr(main, 'run_update', lambda config, **kwargs: None)
    notices = []
    monkeypatch.setattr(main, 'notify', notices.append)

    runner.invoke(main.app, ['update'])
    runner.invoke(main.app, ['scenarios', 'list', '--json'])

    assert notices == [main.UPDATE_CONFIG]
