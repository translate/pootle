import sys
import md5
import tempfile
import shutil
import os

import os
ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import sys
sys.path.append(ROOT_DIR)

from django.conf import settings
from django.db import connection
from django.test import utils
from django.core.management import call_command
from django.contrib.auth.models import User
from pootle_app.models.translation_project import scan_translation_projects
from py import test


class TestEnv(object):
    def __init__(self, verbosity, interactive):
        self.verbosity = verbosity
        self.interactive = interactive
        
        utils.setup_test_environment()
        self.create_test_podir()
        self.create_test_db()
        self.create_test_users()
        
        scan_translation_projects()
        # Pretend it's a production environment.
        settings.DEBUG = False
        
            
    def __del__(self):
        self.teardown_test_db()
        utils.teardown_test_environment()
        self.teardown_test_podir()


    def create_test_db(self):
        self.old_db_name = settings.DATABASE_NAME
        self.test_db_name = connection.creation.create_test_db(self.verbosity, autoclobber=not self.interactive)
        call_command('initdb', verbosity=self.verbosity)


    def create_test_podir(self):
        self.oldpodir = settings.PODIRECTORY
        self.testpodir = tempfile.mkdtemp()
        settings.PODIRECTORY = self.testpodir
        
        gnu = os.path.join(self.testpodir, "terminology")
        os.mkdir(gnu)
        potfile = file(os.path.join(gnu, "terminology.pot"), 'w')
        potfile.write('#: test.c\nmsgid "test"\nmsgstr ""\n')
        potfile.close()
        pofile = file(os.path.join(gnu, "ar.po"), 'w')
        pofile.write('#: test.c\nmsgid "test"\nmsgstr "rest"\n')
        pofile.close()

        nongnu = os.path.join(self.testpodir, "pootle")
        os.mkdir(nongnu)
        nongnu_ar = os.path.join(nongnu, "ar")
        os.mkdir(nongnu_ar)
        nongnu_ja = os.path.join(nongnu, "ja")
        os.mkdir(nongnu_ja)
        nongnu_af = os.path.join(nongnu, "af")
        os.mkdir(nongnu_af)
        pofile = file(os.path.join(nongnu_af, "pootle.po"), 'w')
        pofile.write('''#: fish.c
msgid "fish"
msgstr ""

#: test.c
msgid "test"
msgstr "rest"

''')
        pofile.close()
        


    def create_test_users(self):
        nonpriv = User(username=u"nonpriv",
                       first_name="Non privileged test user",
                       is_active=True)
        nonpriv.password = md5.new("nonpriv").hexdigest()
        nonpriv.save()


    def teardown_test_podir(self):
        settings.PODIRECTORY = self.oldpodir
        shutil.rmtree(self.testpodir)
    
    def teardown_test_db(self):
        connection.creation.destroy_test_db(self.old_db_name, self.verbosity)

        
def run_tests(test_labels, verbosity=1, interactive=True, extra_tests=[]):
    # Prepare django for testing.
    testenv = TestEnv(verbosity, interactive)
    
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
    #del(testenv)
    
    return len(failures)
