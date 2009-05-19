import tempfile
import shutil
import os

from django.conf import settings
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth.models import User
from pootle_app.models.translation_project import scan_translation_projects
from pootle_store.models import fs

class PootleTestCase(TestCase):
    """Base TestCase class, set's up a pootle environment with a
    couple of test files and projects"""


    def _setup_test_podir(self):
        self.testpodir = tempfile.mkdtemp()
        settings.PODIRECTORY = self.testpodir
        fs.location = self.testpodir
        
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
        


    def _setup_test_users(self):
        nonpriv = User(username=u"nonpriv",
                       first_name="Non privileged test user",
                       is_active=True)
        nonpriv.set_password("nonpriv")
        nonpriv.save()

    def _teardown_test_podir(self):
        shutil.rmtree(self.testpodir)

    def setUp(self):
        self._setup_test_podir()

        #FIXME: replace initdb with a fixture
        call_command('initdb')
        
        self._setup_test_users()
        scan_translation_projects()

    def tearDown(self):
        self._teardown_test_podir()


    def follow_redirect(self, response):
        """follow a redirect chain until a non redirect response is recieved"""
        new_response = response
        while new_response.status_code in (301, 302, 303, 307):
            scheme, netloc, path, query, fragment = urlparse.urlsplit(new_response['location'])
            new_response = self.client.get(path, QueryDict(query))
        return new_response
    
class AnonTests(PootleTestCase):
    def test_login(self):
        """Checks that login works and sets cookies"""
        response = self.client.get('/')
        self.assertContains(response, "Log in")

        response = self.client.post('/login.html', {'username':'admin', 'password':'admin'})
        self.assertRedirects(response, '/home/')

        
class AdminTests(PootleTestCase):
    def setUp(self):
        super(AdminTest, self).setUp()
        self.client.login(username='admin', password='admin')

    def test_logout(self):
        response = self.client.get('/')
        self.assertContains(response, "Log out")

        response = self.client.get("/logout.html")
        self.assertRedirects(response, '/')

        response = self.client.get('/')
        self.assertContains(response, "Log in")
    

class NonprivTests(PootleTestCase):
    def setUp(self):
        super(AdminTest, self).setUp()
        self.client.login(username='nonpriv', password='nonpriv')
        

        

