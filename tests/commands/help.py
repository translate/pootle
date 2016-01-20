from django.core.management import get_commands
from django.core.management import call_command

import pytest


@pytest.mark.cmd
@pytest.mark.parametrize("command,app", [
    (command, app)
    for command, app in get_commands().iteritems()
    if not app.startswith("django.") and not app.startswith("django_")
])
def test_initdb_help(capfd, command, app):
    """Catch any simple command issues"""
    print "Command: %s, App: %s" % (command, app)
    with pytest.raises(SystemExit):
        call_command(command, '--help')
    out, err = capfd.readouterr()
    assert '--help' in out
