import pytest

from django.core.management import call_command


@pytest.mark.cmd
@pytest.mark.django_db
def test_initdb_noprojects(capfd):
    """Initialise the database with initdb

    Testing without --no-projects would take too long
    """
    call_command('initdb', '--no-projects')
    out, err = capfd.readouterr()
    assert "Successfully populated the database." in out
    assert "Successfully populated the database." in out
    assert "pootle createsuperuser" in out
    assert "Created User: 'nobody'" in err
    assert "Created Directory: '/projects/'" in err
    assert "Created Permission:" in err
    assert "Created PermissionSet:" in err
    assert "Created Language:" in err
