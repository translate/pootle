#!/usr/bin/env python

"""Top-level tests using urllib2 to check interaction with servers
This uses test_cmdlineserver / test_service / test_apache (which are for different webservers)
ServerTester is mixed in with the different server tests below to generate the required tests"""

from Pootle import test_create
from Pootle import test_cmdlineserver
from Pootle import potree
from Pootle import projects
import zipfile
from translate.misc import wStringIO
import urllib
import urllib2
import os
import re

try:
    import cookielib
except ImportError:
    # fallback for python before 2.4
    cookielib = None
    import ClientCookie

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    # Written by Wade Leftwich
    # Submitted to ASPN Cookbook
    # Available at the following URL: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/146306
    # As far as I can tell, this code is public domain
    # Copied my Walter Leibbrandt from jToolkit's web/postMultipart.py
    import mimetypes

    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % (mimetypes.guess_type(filename)[0] or 'application/octet-stream'))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

class ServerTester:
    """Tests things directly against the socket of the server. Requires self.baseaddress."""

    setup_class = test_create.TestCreate.setup_class

    # Utility Methods
    ##################

    def fetch_page(self, relative_url):
        """Utility method that fetches a page from the webserver installed in the service."""
        url = "%s%s" % (self.baseaddress, relative_url)
        print "Fetching: ", url
        stream = self.urlopen(url)
        contents = stream.read()
        return contents

    def login(self):
        """Utility method that calls the login method with username and password."""
        return self.fetch_page("?islogin=1&username=%s&password=" % (self.testuser.username))

    def logout(self):
        """Utility method that calls the logout method."""
        return self.fetch_page("?islogout=1")

    def post_request(self, relative_url, contents, headers):
        """Utility method that posts a request to the webserver installed in the service."""
        url = "%s/%s" % (self.baseaddress, relative_url)
        print "posting to", url
        post_request = urllib2.Request(url, contents, headers)
        stream = self.urlopen(post_request)
        response = stream.read()
        return response

    # Setup and teardown methods
    #############################
    def setup_cookies(self):
        """Setup cookie-handler."""
        if cookielib:
            self.cookiejar = cookielib.CookieJar()
            self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
            self.urlopen = self.opener.open
        else:
            self.urlopen = ClientCookie.urlopen

    def setup_database(self, method):
        """Create a new database to test with."""
        import os, md5
        from dbclasses import Language, Project, User
        from initdb import attempt, configDB

        self.alchemysess = configDB(self.prefs.Pootle)

        # Populate database with test data
        testproject = Project(u"testproject")
        testproject.fullname = u"Pootle Unit Tests"
        testproject.description = "Test Project for verifying functionality"
        testproject.checkstyle = "standard"
        testproject.localfiletype = "po"
        attempt(self.alchemysess, testproject)

        zxx = Language("zxx")
        zxx.fullname = u'Test Language'
        zxx.nplurals = '1'
        zxx.pluralequation ='0'
        attempt(self.alchemysess, zxx)

        adminuser = User(u"adminuser")
        adminuser.name=u"Administrator"
        adminuser.activated="True"
        adminuser.passwdhash=md5.new("").hexdigest()
        adminuser.logintype="hash"
        adminuser.siteadmin=True
        attempt(self.alchemysess, adminuser)

        normaluser = User(u"normaluser")
        normaluser.name=u"Norman the Normal User"
        normaluser.activated="True"
        normaluser.passwdhash=md5.new("").hexdigest()
        normaluser.logintype="hash"
        normaluser.siteadmin=False
        attempt(self.alchemysess, normaluser)

        self.alchemysess.flush()

    def setup_prefs(self, method):
        """Sets up any extra preferences required."""
        from dbclasses import User
        if hasattr(method, "userprefs"):
            if method.userprefs['rights.siteadmin']:
                self.testuser = self.alchemysess.query(User).filter(User.username == u'adminuser').first()
            else:
                self.testuser = self.alchemysess.query(User).filter(User.username == u'normaluser').first()

            for key, value in method.userprefs.iteritems():
                self.prefs.setvalue("Pootle.users.%s.%s" % (self.testuser.username, key), value)
        else:
            self.testuser = self.alchemysess.query(User).filter(User.username == u'normaluser').first()
        self.alchemysess.close()

    def setup_testproject_dir(self, perms=None):
        """Sets up a blank test project directory."""
        projectname = "testproject"
        lang = "zxx"
        projectdir = os.path.join(self.podir, projectname)

        os.mkdir(projectdir)
        podir = os.path.join(projectdir, lang)
        os.mkdir(podir)
        if perms:
            prefsfile = file(os.path.join(projectdir, lang, "pootle-%s-%s.prefs" % (projectname, lang)), 'w')
            prefsfile.write("# Prefs file for Pootle unit tests\nrights:\n  %s = '%s'\n" % (self.testuser.username, perms))
            prefsfile.close()
        language_page = self.fetch_page("%s/%s/" % (lang, projectname))

        assert "Test Language" in language_page
        assert "0 files, 0/0 words (0%) translated" in language_page
        return podir

    def teardown_method(self, method):
      self.cookiejar.clear()
      pass

    # Test methods
    ###############
    def test_login(self):
        """Checks that login works and sets cookies."""
        # make sure we start logged out
        contents = self.fetch_page("")
        assert "Log in" in contents

        # check login leads us to a normal page
        contents = self.login()
        assert "Log in" not in contents

        # check login is retained on next fetch
        contents = self.fetch_page("")
        assert "Log in" not in contents

    def test_logout(self):
        """Checks that logout works after logging in."""
        # make sure we start logged in
        contents = self.login()
        assert "Log out" in contents

        # check login leads us to a normal page
        contents = self.logout()
        assert "Log in" in contents

    def test_non_admin_rights(self):
        """Checks that, without admin rights, we can't access the admin screen."""

        contents = self.fetch_page("admin/")
        assert "You must log in to administer Pootle" in contents

        contents = self.login()
        assert not '<a href="/admin/">Admin</a>' in contents

        contents = self.fetch_page("admin/")
        assert "You do not have the rights to administer pootle" in contents
    test_non_admin_rights.userprefs = {"rights.siteadmin": False}

    def test_admin_rights(self):
        """Checks that admin rights work properly."""
        contents = self.login()
        adminlink = '<a href="/admin/">Admin</a>' in contents
        assert adminlink

        contents = self.fetch_page("admin/")
        admintitle = "<title>Pootle Admin Page</title>" in contents
        assert admintitle
    test_admin_rights.userprefs = {"rights.siteadmin": True}

    def test_add_project(self):
        """Checks that we can add a project successfully."""
        self.login()

        projects_list = self.fetch_page("admin/projects.html")
        testproject_present = '<a href="../projects/testproject/admin.html">testproject</a>' in projects_list
        assert testproject_present

        testproject2_present = '<a href="../projects/testproject2/admin.html">testproject2</a>' in projects_list
        assert not testproject2_present
        assert projects_list.count(""""selected" value="po""") == 1

        add_dict = {
            "newprojectcode": "testproject2",
            "newprojectname": "Test Project 2",
            "newprojectdescription": "Test Project Addition",
            "newprojectfiletype": "xliff",
            "changeprojects": "Save changes"
        }
        add_args = "&".join(["%s=%s" % (key, urllib.quote_plus(value)) for key, value in add_dict.items()])
        add_url = "admin/projects.html?" + add_args
        add_result = self.fetch_page(add_url)
        testproject2_present = '<a href="../projects/testproject2/admin.html">testproject2</a>' in add_result
        assert testproject2_present

        projects_list = self.fetch_page("admin/projects.html")
        # The asserts below may fail if output framework changes, html checking does not checking the 'selected' value,
        # but instead relying on the projected 'value' in the project's name
        assert """projectfiletype-testproject" value="po">""" in projects_list
        assert """projectfiletype-testproject2" value="xliff">""" in projects_list
    test_add_project.userprefs = {"rights.siteadmin": True}

    def test_add_project_language(self):
        """Tests that we can add a language to a project, then access its page when there are no files."""
        self.login()

        language_list = self.fetch_page("projects/testproject/index.html")
        assert "Test Language" not in language_list
        assert "Pootle Unit Tests" in language_list

        project_admin = self.fetch_page("projects/testproject/admin.html")
        assert '<option value="zxx">Test Language: zxx</option>' in project_admin

        add_dict = {
            "newlanguage": "zxx",
            "doaddlanguage": "Add Language"
        }
        add_args = "&".join(["%s=%s" % (key, urllib.quote_plus(value)) for key, value in add_dict.items()])
        add_language = self.fetch_page("projects/testproject/admin.html?" + add_args)
        assert "Test Language" in add_language

        language_page = self.fetch_page("zxx/testproject/")
        assert "Test Language" in language_page
        assert "Pootle Unit Tests" in language_page
        assert "0 files, 0/0 words (0%) translated" in language_page
    test_add_project_language.userprefs = {"rights.siteadmin": True}

    def test_upload_new_file(self):
        """Tests that we can upload a new file into a project."""
        self.login()

        # XXX: Don't move the following line below the call to self.post_request(), because it is dependant on this call.
        podir = self.setup_testproject_dir(perms="view, translate, admin")
        fields = [("doupload", "Upload File")]
        pocontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        files = [("uploadfile", "test_upload.po", pocontents)]
        content_type, upload_contents = encode_multipart_formdata(fields, files)
        headers = {"Content-Type": content_type, "Content-Length": len(upload_contents)}
        response = self.post_request("zxx/testproject/", upload_contents, headers)
        assert ' href="test_upload.po?' in response

        pofile_storename = os.path.join(podir, "test_upload.po")
        assert os.path.isfile(pofile_storename)
        assert open(pofile_storename).read() == pocontents

        pocontents_download = self.fetch_page("zxx/testproject/test_upload.po")
        assert pocontents_download == pocontents

    def test_upload_new_xliff_file(self):
        """Tests that we can upload a new XLIFF file into a project."""
        self.login()

        # XXX: Don't move the following line below the call to self.post_request(), because it is dependant on this call.
        podir = self.setup_testproject_dir(perms="view, translate, admin")
        xliffcontents = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1">
    <file datatype="po" original="test_upload.po" source-language="en-US">
        <body>
            <trans-unit id="1" xml:space="preserve">
                <source>test</source>
                <target state="translated">rest</target>
                <context-group name="po-reference" purpose="location">
                    <context context-type="sourcefile">test.c</context>
                </context-group>
            </trans-unit>
        </body>
    </file>
</xliff>'''
        fields = [("doupload", "Upload File")]
        files = [("uploadfile", "test_upload.xlf", xliffcontents)]
        content_type, upload_contents = encode_multipart_formdata(fields, files)
        headers = {"Content-Type": content_type, "Content-Length": len(upload_contents)}
        response = self.post_request("zxx/testproject/", upload_contents, headers)
        assert ' href="test_upload.po?' in response

        pofile_storename = os.path.join(podir, "test_upload.po")
        assert os.path.isfile(pofile_storename)
        assert open(pofile_storename).read() == xliffcontents
        # Well, since it is a new file, it actually now is an xliff file...
        #pocontents_download = self.fetch_page("zxx/testproject/test_upload.po")
        #pocontents_expected = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        #assert pocontents_download == pocontents_expected

    def test_upload_suggestions(self):
        """Tests that we can upload when we only have suggest rights."""
        self.login()

        podir = self.setup_testproject_dir(perms="view, suggest")
        tree = potree.POTree(self.prefs.Pootle, self.server)
        project = projects.TranslationProject("zxx", "testproject", tree)
        po1contents = '#: test.c\nmsgid "test"\nmsgstr ""\n'
        open(os.path.join(podir, "test_upload.po"), "w").write(po1contents)

        fields = [("doupload", "Upload File")]
        pocontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        files = [("uploadfile", "test_upload.po", pocontents)]
        content_type, upload_contents = encode_multipart_formdata(fields, files)
        headers = {"Content-Type": content_type, "Content-Length": len(upload_contents)}
        response = self.post_request("zxx/testproject/", upload_contents, headers)
        assert ' href="test_upload.po?' in response
        # Check that the orignal file didn't take the new suggestion.
        # We test with 'in' since the header is added
        assert po1contents in self.fetch_page("zxx/testproject/test_upload.po")

        suggestions_content = open(os.path.join(podir, "test_upload.po.pending"), 'r').read()
        assert 'msgstr "rest"' in suggestions_content
    test_upload_suggestions.userprefs = {"rights.siteadmin": False}

    def test_upload_overwrite(self):
        """Tests that we can overwrite a file in a project."""
        self.login()

        podir = self.setup_testproject_dir(perms="view, translate, overwrite")
        tree = potree.POTree(self.prefs.Pootle, self.server)
        project = projects.TranslationProject("zxx", "testproject", tree)
        po1contents = '#: test.c\nmsgid "test"\nmsgstr ""\n'
        open(os.path.join(podir, "test_upload.po"), "w").write(po1contents)

        fields = [("doupload", "Upload File"),("dooverwrite", "No")]
        pocontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        files = [("uploadfile", "test_upload.po", pocontents)]
        content_type, upload_contents = encode_multipart_formdata(fields, files)
        headers = {"Content-Type": content_type, "Content-Length": len(upload_contents)}
        response = self.post_request("zxx/testproject/", upload_contents, headers)
        assert ' href="test_upload.po?' in response
        # Now we only test with 'in' since the header is added
        assert pocontents in self.fetch_page("zxx/testproject/test_upload.po")
        firstpofile = self.fetch_page("zxx/testproject/test_upload.po")

        fields = [("doupload", "Upload File"),("dooverwrite", "Yes")]
        pocontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n#: test.c\nmsgid "azoozoo"\nmsgstr ""'
        files = [("uploadfile", "test_upload.po", pocontents)]
        content_type, upload_contents = encode_multipart_formdata(fields, files)
        headers = {"Content-Type": content_type, "Content-Length": len(upload_contents)}
        response = self.post_request("zxx/testproject/", upload_contents, headers)
        assert pocontents == self.fetch_page("zxx/testproject/test_upload.po")

    def test_upload_new_archive(self):
        """Tests that we can upload a new archive of files into a project."""
        self.login()

        podir = self.setup_testproject_dir(perms="view, translate, admin")
        po1contents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        po2contents = '#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n'

        archivefile = wStringIO.StringIO()
        archive = zipfile.ZipFile(archivefile, "w", zipfile.ZIP_DEFLATED)
        archive.writestr("test.po", po1contents)
        archive.writestr("frog.po", po2contents)
        archive.close()

        fields = [("doupload", "Upload File")]
        files = [("uploadfile", "upload.zip", archivefile.getvalue())]
        content_type, upload_contents = encode_multipart_formdata(fields, files)
        headers = {"Content-Type": content_type, "Content-Length": len(upload_contents)}
        response = self.post_request("zxx/testproject/", upload_contents, headers)

        for filename, contents in [("test.po", po1contents), ("frog.po", po2contents)]:
            assert (' href="%s?' % filename) in response

            pofile_storename = os.path.join(podir, filename)
            assert os.path.isfile(pofile_storename)
            assert open(pofile_storename).read() == contents

            pocontents_download = self.fetch_page("zxx/testproject/%s" % filename)
            assert pocontents_download == contents

    def test_upload_over_file(self):
        """Tests that we can upload a new version of a file into a project."""
        self.login()

        podir = self.setup_testproject_dir(perms="view, translate")
        tree = potree.POTree(self.prefs.Pootle, self.server)
        project = projects.TranslationProject("zxx", "testproject", tree)
        po1contents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n'
        open(os.path.join(podir, "test_existing.po"), "w").write(po1contents)
        po2contents = '#: test.c\nmsgid "test"\nmsgstr "rested"\n\n#: toad.c\nmsgid "slink"\nmsgstr "stink"\n'

        fields = [("doupload", "Upload File")]
        files = [("uploadfile", "test_existing.po", po2contents)]
        content_type, upload_contents = encode_multipart_formdata(fields, files)
        headers = {"Content-Type": content_type, "Content-Length": len(upload_contents)}
        response = self.post_request("zxx/testproject/?editing=1", upload_contents, headers)
        assert ' href="test_existing.po?' in response

        # NOTE: this is what we do currently: any altered strings become suggestions.
        # It may be a good idea to change this
        mergedcontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n\n#: toad.c\nmsgid "slink"\nmsgstr "stink"\n'
        suggestedcontents = '#: test.c\nmsgid ""\n"_: suggested by adminuser\\n"\n"test"\nmsgstr "rested"\n'
        pofile_storename = os.path.join(podir, "test_existing.po")
        assert os.path.isfile(pofile_storename)
        assert open(pofile_storename).read().find(mergedcontents) >= 0

        pendingfile_storename = os.path.join(podir, "test_existing.po.pending")
        assert os.path.isfile(pendingfile_storename)
        assert open(pendingfile_storename).read().find(suggestedcontents) >= 0

        pocontents_download = self.fetch_page("zxx/testproject/test_existing.po")
        assert pocontents_download.find(mergedcontents) >= 0
    test_upload_over_file.userprefs = {"rights.siteadmin": True}

    def test_upload_xliff_over_file(self):
        """Tests that we can upload a new version of a XLIFF file into a project."""
        self.login()

        podir = self.setup_testproject_dir(perms="view, translate")
        tree = potree.POTree(self.prefs.Pootle, self.server)
        project = projects.TranslationProject("zxx", "testproject", tree)
        pocontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n'
        open(os.path.join(podir, "test_existing.po"), "w").write(pocontents)

        xlfcontents = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1">
    <file datatype="po" original="test_existing.po" source-language="en-US">
        <body>
            <trans-unit id="1" xml:space="preserve" approved="yes">
                <source>test</source>
                <target state="translated">rested</target>
                <context-group name="po-reference" purpose="location">
                    <context context-type="sourcefile">test.c</context>
                </context-group>
            </trans-unit>
            <trans-unit id="2" xml:space="preserve" approved="yes">
                <source>slink</source>
                <target state="translated">stink</target>
                <context-group name="po-reference" purpose="location">
                    <context context-type="sourcefile">toad.c</context>
                </context-group>
            </trans-unit>
        </body>
    </file>
</xliff>'''
        fields = [("doupload", "Upload File")]
        files = [("uploadfile", "test_existing.xlf", xlfcontents)]
        content_type, upload_contents = encode_multipart_formdata(fields, files)
        headers = {"Content-Type": content_type, "Content-Length": len(upload_contents)}
        response = self.post_request("zxx/testproject/?editing=1", upload_contents, headers)
        assert ' href="test_existing.po?' in response

        # NOTE: this is what we do currently: any altered strings become suggestions.
        # It may be a good idea to change this
        mergedcontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n\n#: toad.c\nmsgid "slink"\nmsgstr "stink"\n'
        suggestedcontents = '#: test.c\nmsgid ""\n"_: suggested by adminuser\\n"\n"test"\nmsgstr "rested"\n'
        pofile_storename = os.path.join(podir, "test_existing.po")
        assert os.path.isfile(pofile_storename)
        assert open(pofile_storename).read().find(mergedcontents) >= 0

        pendingfile_storename = os.path.join(podir, "test_existing.po.pending")
        assert os.path.isfile(pendingfile_storename)
        assert open(pendingfile_storename).read().find(suggestedcontents) >= 0

        pocontents_download = self.fetch_page("zxx/testproject/test_existing.po")
        assert pocontents_download.find(mergedcontents) >= 0
    test_upload_xliff_over_file.userprefs = {"rights.siteadmin": True}

    def test_submit_translation(self):
        """Tests that we can upload a new file into a project."""
        self.login()

        podir = self.setup_testproject_dir(perms="view, translate")
        pofile_storename = os.path.join(podir, "test_upload.po")
        pocontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        open(pofile_storename, "w").write(pocontents)

        expected_pocontents = '#: test.c\nmsgid "test"\nmsgstr "restrain"\n'
        fields = {"orig-pure0.0": "test", "trans0": "restrain", "submit0": "submit", "pofilename": "test_upload.po"}
        content_type, post_contents = encode_multipart_formdata(fields.items(), [])
        headers = {"Content-Type": content_type, "Content-Length": len(post_contents)}
        translatepage = self.post_request("zxx/testproject/test_upload.po?translate=1&editing=1", post_contents, headers)

        tree = potree.POTree(self.prefs.Pootle, self.server)
        project = projects.TranslationProject("zxx", "testproject", tree)
        pofile = project.getpofile("test_upload.po")
        assert str(pofile.units[1]) == expected_pocontents

    def test_submit_plural_translation(self):
        """Tests that we can submit a translation with plurals."""
        self.login()

        podir = self.setup_testproject_dir(perms="view, translate")
        pofile_storename = os.path.join(podir, "test_upload.po")
        pocontents = 'msgid "singular"\nmsgid_plural "plural"\nmsgstr[0] "enkelvoud string"\nmsgstr[1] "meervoud boodskap"\n'
        open(pofile_storename, "w").write(pocontents)

        expected_pocontents = 'msgid "singular"\nmsgid_plural "plural"\nmsgstr[0] "enkelvoud"\nmsgstr[1] "meervoud"\n'
        fields = {"orig-pure0.0": "singular", "trans0.0": "enkelvoud", "trans0.1": "meervoud", "submit0": "submit", "pofilename": "test_upload.po"}
        content_type, post_contents = encode_multipart_formdata(fields.items(), [])
        headers = {"Content-Type": content_type, "Content-Length": len(post_contents)}
        translatepage = self.post_request("zxx/testproject/test_upload.po?translate=1&editing=1", post_contents, headers)

        tree = potree.POTree(self.prefs.Pootle, self.server)
        project = projects.TranslationProject("zxx", "testproject", tree)
        pofile = project.getpofile("test_upload.po")
        assert str(pofile.units[1]) == expected_pocontents

    def test_submit_plural_to_singular_lang(self):
        """Tests that we can submit a translation with plurals to a language without plurals."""
        self.login()

        podir = self.setup_testproject_dir(perms="view, translate")
        pofile_storename = os.path.join(podir, "test_upload.po")
        pocontents = 'msgid "singular"\nmsgid_plural "plural"\nmsgstr[0] "enkelvoud string"\n'
        open(pofile_storename, "w").write(pocontents)

        expected_pocontents = 'msgid "singular"\nmsgid_plural "plural"\nmsgstr[0] "enkelvoud"\n'
        fields = {"orig-pure0.0": "singular", "trans0.0": "enkelvoud", "submit0": "submit", "pofilename": "test_upload.po"}
        content_type, post_contents = encode_multipart_formdata(fields.items(), [])
        headers = {"Content-Type": content_type, "Content-Length": len(post_contents)}
        translatepage = self.post_request("zxx/testproject/test_upload.po?translate=1&editing=1", post_contents, headers)

        tree = potree.POTree(self.prefs.Pootle, self.server)
        project = projects.TranslationProject("zxx", "testproject", tree)
        pofile = project.getpofile("test_upload.po")
        assert str(pofile.units[1]) == expected_pocontents

    def test_submit_fuzzy(self):
        """Tests that we can mark a unit as fuzzy."""
        self.login()

        podir = self.setup_testproject_dir(perms="view, translate")
        pofile_storename = os.path.join(podir, "test_fuzzy.po")
        pocontents = '#: test.c\nmsgid "fuzzy"\nmsgstr "wuzzy"\n'
        open(pofile_storename, "w").write(pocontents)

        # Fetch the page and check that the fuzzy checkbox is NOT checked.
        translatepage = self.fetch_page("zxx/testproject/test_fuzzy.po?translate=1&editing=1")
        assert '<input class="fuzzycheck" accesskey="f" type="checkbox" name="fuzzy0" id="fuzzy0" />' in translatepage

        fields = {"orig-pure0.0": "fuzzy", "trans0": "wuzzy", "submit0": "submit", "fuzzy0": "on", "pofilename": "test_fuzzy.po"}
        content_type, post_contents = encode_multipart_formdata(fields.items(), [])
        headers = {"Content-Type": content_type, "Content-Length": len(post_contents)}
        translatepage = self.post_request("zxx/testproject/test_fuzzy.po?translate=1&editing=1", post_contents, headers)

        # Fetch the page again and check that the fuzzy checkbox IS checked.
        translatepage = self.fetch_page("zxx/testproject/test_fuzzy.po?translate=1&editing=1")
        assert '<input checked="checked" name="fuzzy0" accesskey="f" type="checkbox" id="fuzzy0" class="fuzzycheck" />' in translatepage

        tree = potree.POTree(self.prefs.Pootle, self.server)
        project = projects.TranslationProject("zxx", "testproject", tree)
        pofile = project.getpofile("test_fuzzy.po")
        expected_pocontents = '#: test.c\n#, fuzzy\nmsgid "fuzzy"\nmsgstr "wuzzy"\n'
        assert str(pofile.units[1]) == expected_pocontents
        assert pofile.units[1].isfuzzy()

        # Submit the translation again, without the fuzzy checkbox checked
        fields = {"orig-pure0.0": "fuzzy", "trans0": "wuzzy", "submit0": "submit", "pofilename": "test_fuzzy.po"}
        content_type, post_contents = encode_multipart_formdata(fields.items(), [])
        headers = {"Content-Type": content_type, "Content-Length": len(post_contents)}
        translatepage = self.post_request("zxx/testproject/test_fuzzy.po?translate=1&editing=1", post_contents, headers)

        # Fetch the page once more and check that the fuzzy checkbox is NOT checked.
        translatepage = self.fetch_page("zxx/testproject/test_fuzzy.po?translate=1&editing=1")
        assert '<input class="fuzzycheck" accesskey="f" type="checkbox" name="fuzzy0" id="fuzzy0" />' in translatepage
        tree = potree.POTree(self.prefs.Pootle, self.server)
        project = projects.TranslationProject("zxx", "testproject", tree)
        pofile = project.getpofile("test_fuzzy.po")
        assert not pofile.units[1].isfuzzy()

    def test_submit_translator_comments(self):
        """Tests that we can edit translator comments."""
        self.login()

        podir = self.setup_testproject_dir(perms="view, translate")
        pofile_storename = os.path.join(podir, "test_upload.po")
        pocontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        open(pofile_storename, "w").write(pocontents)

        expected_pocontents = '# Some test comment\n# test comment line 2\n#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        fields = {"orig-pure0.0": "test", "trans0": "rest", "translator_comments0": "Some test comment\ntest comment line 2", "submit0": "submit", "pofilename": "test_upload.po"}
        content_type, post_contents = encode_multipart_formdata(fields.items(), [])
        headers = {"Content-Type": content_type, "Content-Length": len(post_contents)}
        translatepage = self.post_request("zxx/testproject/test_upload.po?translate=1&editing=1", post_contents, headers)

        tree = potree.POTree(self.prefs.Pootle, self.server)
        project = projects.TranslationProject("zxx", "testproject", tree)
        pofile = project.getpofile("test_upload.po")
        assert str(pofile.units[1]) == expected_pocontents

    def test_navigation_url_parameters(self):
        """Tests that the navigation urls (next/end etc) has the necessary parameters."""
        self.login()

        podir = self.setup_testproject_dir(perms="view, translate")
        pofile_storename = os.path.join(podir, "test_nav_url.po")
        pocontents = '#: test.c\nmsgid "test1"\nmsgstr "rest"\n'
        pocontents += '\nmsgid "test2"\nmsgstr "rest2"\n'
        pocontents += '\nmsgid "test3"\nmsgstr "rest2"\n'
        pocontents += '\nmsgid "test4"\nmsgstr "rest2"\n'
        pocontents += '\nmsgid "test5"\nmsgstr "rest2"\n'
        pocontents += '\nmsgid "test6"\nmsgstr "rest2"\n'
        pocontents += '\nmsgid "test7"\nmsgstr "rest2"\n'
        pocontents += '\nmsgid "test8"\nmsgstr "rest2"\n'
        pocontents += '\nmsgid "test9"\nmsgstr "rest2"\n'
        pocontents += '\nmsgid "test10"\nmsgstr "rest2"\n'
        pocontents += '\nmsgid "test11"\nmsgstr "rest2"\n'
        open(pofile_storename, "w").write(pocontents)

        # Mozootle can't currently use preferences set like this, so commented
        # out for now:
        #self.prefs.setvalue("Pootle.users.testuser.viewrows", 1)
        translatepage = self.fetch_page("zxx/testproject/test_nav_url.po?translate=1&view=1")
        patterns = re.findall('<a href=".(.*)".*Next 1.*</a>', translatepage)
        parameters = patterns[0].split('&amp;')
        assert 'pofilename=test_nav_url.po' in parameters
        assert 'item=10' in parameters

    def test_search(self):
        """Test the searching functionality when results are and are not expected."""
        self.login()

        # Create initial .po file
        podir = self.setup_testproject_dir(perms='view')
        pofile_storename = os.path.join(podir, "test_upload.po")
        pocontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        open(pofile_storename, "w").write(pocontents)

        test_translation_string = '<div class="translation-text">test</div>'
        # Test for existing results
        fields = {
            'searchtext': 'test',
            'pofilename': 'test_upload.po',
            'source': '1'
        }
        content_type, post_contents = encode_multipart_formdata(fields.items(), [])
        headers = { 'Content-Type': content_type, 'Content-Length': len(post_contents) }
        translatepage = self.post_request('zxx/testproject/translate.html', post_contents, headers)
        assert test_translation_string in translatepage

        # Test for empty result
        fields = {
            'searchtext': 'test',
            'pofilename': 'test_upload.po',
            'target': '1'
        }
        content_type, post_contents = encode_multipart_formdata(fields.items(), [])
        headers = { 'Content-Type': content_type, 'Content-Length': len(post_contents) }
        translatepage = self.post_request('zxx/testproject/translate.html', post_contents, headers)
        assert test_translation_string not in translatepage

def MakeServerTester(baseclass):
    """Makes a new Server Tester class using the base class to setup webserver etc."""
    class TestServer(baseclass, ServerTester):
        def setup_method(self, method):
            ServerTester.setup_database(self, method)
            ServerTester.setup_prefs(self, method)
            baseclass.setup_method(self, method)
            ServerTester.setup_cookies(self)
    return TestServer

TestServerCmdLine = MakeServerTester(test_cmdlineserver.TestCmdlineServer)
# TestServerService = MakeServerTester(test_service.TestjLogbookService)
# TestServerApache = MakeServerTester(test_apache.TestApachejLogbook)

