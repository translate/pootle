import shutil
import urlparse
import tempfile
import os

from django.conf import settings
from django.test import TestCase
from django.http import QueryDict
from django.core.management import call_command
from django.contrib.auth.models import User

from pootle_translationproject.models import scan_translation_projects
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
        pofile.write(r'''msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\n"
"Report-Msgid-Bugs-To: \n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"X-Generator: Pootle Tests\n"

#: fish.c
msgid "fish"
msgstr ""

#: test.c
msgid "test"
msgstr "rest"

#: fish.c
msgid "%d fish"
msgid_plural "%d fishies"
msgstr[0] ""
msgstr[1] ""
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
