import sys
import md5

from django.conf import settings
from django.db import connection
from django.test import utils
from django.core.management import call_command
from django.contrib.auth.models import User
from pootle_app.translation_project import scan_translation_projects
from py import test


def setup_test_environment(verbosity, interactive):
    utils.setup_test_environment()
    old_db_name = settings.DATABASE_NAME
    test_db_name = connection.creation.create_test_db(verbosity, autoclobber=not interactive)
    call_command('initdb', verbosity=verbosity)
    scan_translation_projects()
    create_test_users()
    # Pretend it's a production environment.
    settings.DEBUG = False
    return (old_db_name, test_db_name)
    
def teardown_test_environment(verbosity, interactive, old_db_name):
    connection.creation.destroy_test_db(old_db_name, verbosity)
    utils.teardown_test_environment()

def create_test_users():
    nonpriv = User(username=u"nonpriv",
                  first_name="Non privileged test user",
                  is_active=True)
    nonpriv.password = md5.new("nonpriv").hexdigest()
    nonpriv.save()
                  
def run_tests(test_labels, verbosity=1, interactive=True, extra_tests=[]):
    # Prepare django for testing.
    (old_db_name, test_db_name) = setup_test_environment(verbosity, interactive)
    
    pytest_argv = []
    if hasattr(settings, 'PYTEST_ARGS'):
        pytest_argv.extend(settings.PYTEST_ARGS)
        
    # Everything after '--' is passed to nose.
    if '--' in sys.argv:
        hyphen_pos = sys.argv.index('--')
        pytest_argv.extend(sys.argv[hyphen_pos + 1:])
        
    if verbosity >= 1:
        print ' '.join(pytest_argv)

    test.config.parse(pytest_argv)
    pytest_session = test.config.initsession()
    failures = pytest_session.main()
    # Clean up django.
    teardown_test_environment(verbosity, interactive, old_db_name)
    return len(failures)
