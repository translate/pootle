import tempfile
import shutil
import urlparse
import os

from django.conf import settings
from django.test import TestCase
from django.http import QueryDict
from django.core.management import call_command
from django.contrib.auth.models import User
from pootle_app.models.translation_project import scan_translation_projects
from pootle_store.models import fs

def formset_dict(data):
    """convert human readable POST dictionary into brain dead django formset dictionary"""
    new_data = {'form-TOTAL_FORMS': len(data), 'form-INITIAL_FORMS': 0}
    for i in range(len(data)):
        for key, value in data[i].iteritems():
            new_data["form-%d-%s" % (i, key)] = value
    return new_data

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

        response = self.client.post('/accounts/login/', {'username':'admin', 'password':'admin'})
        self.assertRedirects(response, '/accounts/admin/')

    def test_admin_not_logged(self):
        """checks that admin pages are not accessible without login"""
        response = self.client.get("/admin/")
        self.assertRedirects(response, 'http://testserver/accounts/login/?message=You+must+log+in+to+administer+Pootle.')

        
class AdminTests(PootleTestCase):
    def setUp(self):
        super(AdminTests, self).setUp()
        self.client.login(username='admin', password='admin')

    def test_logout(self):
        """tests login and logout links"""
        response = self.client.get('/')
        self.assertContains(response, "Log out")

        response = self.client.get("/accounts/logout/")
        self.assertRedirects(response, '/')

        response = self.client.get('/')
        self.assertContains(response, "Log in")

    def test_admin_rights(self):
        """checks that admin user can access admin pages"""
        response = self.client.get('/')
        self.assertContains(response, "<a href='/admin/'>Admin</a>")
        response = self.client.get('/admin/')
        self.assertContains(response, '<title>Pootle Admin Page</title>')        

    def test_add_project(self):
        """Checks that we can add a project successfully."""
    
        response = self.client.get("/admin/projects.html")
        self.assertContains(response, "<a href='/projects/pootle/admin.html'>pootle</a>")
        self.assertContains(response, "<a href='/projects/terminology/admin.html'>terminology</a>")

        add_dict = {
            "code": "testproject",                                       
            "localfiletype": "xlf",                                     
            "fullname": "Test Project",                                
            "checkstyle": "standard",
            "treestyle": "gnu",
            }
    
        response = self.client.post("/admin/projects.html", formset_dict([add_dict]))
        self.assertContains(response, "<a href='/projects/testproject/admin.html'>testproject</a>")
    
        # check for the actual model
        from pootle_app.models import Project
        testproject = Project.objects.get(code="testproject")
        
        self.assertTrue(testproject)
        self.assertEqual(testproject.fullname, add_dict['fullname'])
        self.assertEqual(testproject.checkstyle, add_dict['checkstyle'])
        self.assertEqual(testproject.localfiletype, add_dict['localfiletype'])
        self.assertEqual(testproject.treestyle, add_dict['treestyle'])

    def test_add_project_language(self):
        """Tests that we can add a language to a project, then access
        its page when there are no files."""
        from pootle_app.models import Language, Project
        fish = Language(code="fish", fullname="fish")
        fish.save()
            
        response = self.client.get("/projects/pootle/admin.html")
        self.assertContains(response, "fish")

        project = Project.objects.get(code='pootle')
        add_dict = {
            "language": fish.id,
            "project": project.id,
            }
        response = self.client.post("/projects/pootle/admin.html", formset_dict([add_dict]))
        self.assertContains(response, '/fish/pootle/')
        
        response = self.client.get("/fish/")
        self.assertContains(response, 'fish</title>')
        self.assertContains(response, '<a href="pootle/">Pootle</a>')
        self.assertContains(response, "1 project,  0% translated")


class NonprivTests(PootleTestCase):
    def setUp(self):
        super(NonprivTests, self).setUp()
        self.client.login(username='nonpriv', password='nonpriv')
        
    def test_non_admin_rights(self):
        """checks that non privileged users cannot access admin pages"""
        response = self.client.get('/admin/')
        self.assertRedirects(response, 'http://testserver/accounts/nonpriv/?message=You+do+not+have+the+rights+to+administer+Pootle.')
        
        

