#!/usr/bin/env python

"""Top-level tests using urllib2 to check interaction with servers
This uses test_cmdlineserver / test_service / test_apache (which are for different webservers)
ServerTester is mixed in with the different server tests below to generate the required tests"""

from Pootle import test_create
from Pootle import test_cmdlineserver
from Pootle import potree
from Pootle import projects
from jToolkit.web import postMultipart
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

class ServerTester:
    """Tests things directly against the socket of the server. Requires self.baseaddress"""
    setup_class = test_create.TestCreate.setup_class

    def setup_cookies(self):
        """handle cookies etc"""
        if cookielib:
            self.cookiejar = cookielib.CookieJar()
            self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
            self.urlopen = self.opener.open
        else:
            self.urlopen = ClientCookie.urlopen

    def setup_prefs(self, method):
        """sets up any extra preferences required..."""
        if hasattr(method, "userprefs"):
            for key, value in method.userprefs.iteritems():
                self.prefs.setvalue("Pootle.users.testuser." + key, value)

    def fetch_page(self, relative_url):
        """Fetches a page from the webserver installed in the service"""
        url = "%s/%s" % (self.baseaddress, relative_url)
        print "fetching", url
        stream = self.urlopen(url)
        contents = stream.read()
        return contents

    def post_request(self, relative_url, contents, headers):
        """Posts a request to the webserver installed in the service"""
        url = "%s/%s" % (self.baseaddress, relative_url)
        print "posting to", url
        post_request = urllib2.Request(url, contents, headers)
        stream = self.urlopen(post_request)
        response = stream.read()
        return response

    def login(self):
        """calls the login method with username and password"""
        return self.fetch_page("?islogin=1&username=testuser&password=")

    def test_login(self):
        """checks that login works and sets cookies"""
        contents = self.login()
        # check login leads us to a normal page
        assert "Log In" not in contents
        # check login is retained on next fetch
        contents = self.fetch_page("")
        assert "Log In" not in contents

    def test_non_admin_rights(self):
        """checks that without admin rights we can't access the admin screen"""
        contents = self.login()
        adminlink = '<a href="/admin/">Admin</a>' in contents
        assert not adminlink
        contents = self.fetch_page("admin/")
        denied = "You do not have the rights to administer pootle" in contents
        assert denied

    def test_admin_rights(self):
        """checks that admin rights work properly"""
        contents = self.login()
        adminlink = '<a href="/admin/">Admin</a>' in contents
        assert adminlink
        contents = self.fetch_page("admin/")
        admintitle = "<title>Pootle Admin Page</title>" in contents
        assert admintitle
    test_admin_rights.userprefs = {"rights.siteadmin": True}

    def test_add_project(self):
        """checks that we can add a project successfully"""
        self.login()
        projects_list = self.fetch_page("admin/projects.html")
        testproject_present = '<a href="../projects/testproject/admin.html">testproject</a>' in projects_list
        assert testproject_present
        testproject2_present = '<a href="../projects/testproject2/admin.html">testproject2</a>' in projects_list
        assert not testproject2_present
        assert projects_list.count(""""selected" value="po""") == 1
        add_dict = {"newprojectcode": "testproject2", "newprojectname": "Test Project 2",
            "newprojectdescription": "Test Project Addition","newprojectfiletype": "xliff", "changeprojects": "Save changes"}
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
        """tests that we can add a language to a project, then access its page when there are no files"""
        self.login()
        language_list = self.fetch_page("projects/testproject/")
        assert "Test Language" not in language_list
        assert "Pootle Unit Tests" in language_list
        project_admin = self.fetch_page("projects/testproject/admin.html")
        assert '<option value="zxx">Test Language</option>' in project_admin
        add_dict = {"newlanguage": "zxx", "doaddlanguage": "Add Language"}
        add_args = "&".join(["%s=%s" % (key, urllib.quote_plus(value)) for key, value in add_dict.items()])
        add_language = self.fetch_page("projects/testproject/admin.html?" + add_args)
        assert "Test Language" in add_language
        language_page = self.fetch_page("zxx/testproject/")
        assert "Test Language" in language_page
        assert "Pootle Unit Tests" in language_page
        assert "0 files, 0/0 words (0%) translated" in language_page
    test_add_project_language.userprefs = {"rights.siteadmin": True}

    def setup_testproject_dir(self):
        """Sets up a blank test project directory"""
        projectdir = os.path.join(self.podir, "testproject")
        os.mkdir(projectdir)
        podir = os.path.join(projectdir, "zxx")
        os.mkdir(podir)
        language_page = self.fetch_page("zxx/testproject/")
        assert "Test Language" in language_page
        assert "Pootle Unit Tests" in language_page
        assert "0 files, 0/0 words (0%) translated" in language_page
        return podir

    def test_upload_new_file(self):
        """tests that we can upload a new file into a project"""
        self.login()
        podir = self.setup_testproject_dir()
        fields = [("doupload", "Upload File")]
        pocontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        files = [("uploadfile", "test_upload.po", pocontents)]
        content_type, upload_contents = postMultipart.encode_multipart_formdata(fields, files)
        headers = {"Content-Type": content_type, "Content-Length": len(upload_contents)}
        response = self.post_request("zxx/testproject/", upload_contents, headers)
        assert ' href="test_upload.po?' in response
        pofile_storename = os.path.join(podir, "test_upload.po")
        assert os.path.isfile(pofile_storename)
        assert open(pofile_storename).read() == pocontents
        pocontents_download = self.fetch_page("zxx/testproject/test_upload.po")
        assert pocontents_download == pocontents

    def test_upload_new_xlifffile(self):
        """tests that we can upload a new xliff file into a project"""
        self.login()
        podir = self.setup_testproject_dir()
        fields = [("doupload", "Upload File")]
        xliffcontents = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1"><file datatype="po" original="test_upload.po" source-language="en-US"><body><trans-unit id="1" xml:space="preserve"><source>test</source><target state="translated">rest</target><context-group name="po-reference" purpose="location"><context context-type="sourcefile">test.c</context></context-group></trans-unit></body></file></xliff>'''
        pocontents_expected = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        files = [("uploadfile", "test_upload.xlf", xliffcontents)]
        content_type, upload_contents = postMultipart.encode_multipart_formdata(fields, files)
        headers = {"Content-Type": content_type, "Content-Length": len(upload_contents)}
        response = self.post_request("zxx/testproject/", upload_contents, headers)
        assert ' href="test_upload.po?' in response
        pofile_storename = os.path.join(podir, "test_upload.po")
        assert os.path.isfile(pofile_storename)
        assert open(pofile_storename).read() == xliffcontents
        # Well, since it is a new file, it actually now is an xliff file...
#                pocontents_download = self.fetch_page("zxx/testproject/test_upload.po")
#                assert pocontents_download == pocontents_expected

    def test_upload_new_archive(self):
        """tests that we can upload a new archive of files into a project"""
        self.login()
        podir = self.setup_testproject_dir()
        fields = [("doupload", "Upload File")]
        po1contents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        po2contents = '#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n'
        archivefile = wStringIO.StringIO()
        archive = zipfile.ZipFile(archivefile, "w", zipfile.ZIP_DEFLATED)
        archive.writestr("test.po", po1contents)
        archive.writestr("frog.po", po2contents)
        archive.close()
        files = [("uploadfile", "upload.zip", archivefile.getvalue())]
        content_type, upload_contents = postMultipart.encode_multipart_formdata(fields, files)
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
        """tests that we can upload a new version of a file into a project"""
        self.login()
        podir = self.setup_testproject_dir()
        tree = potree.POTree(self.prefs.Pootle)
        project = projects.TranslationProject("zxx", "testproject", tree)
        po1contents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n'
        open(os.path.join(podir, "test_existing.po"), "w").write(po1contents)
        po2contents = '#: test.c\nmsgid "test"\nmsgstr "rested"\n\n#: toad.c\nmsgid "slink"\nmsgstr "stink"\n'
        fields = [("doupload", "Upload File")]
        files = [("uploadfile", "test_existing.po", po2contents)]
        content_type, upload_contents = postMultipart.encode_multipart_formdata(fields, files)
        headers = {"Content-Type": content_type, "Content-Length": len(upload_contents)}
        response = self.post_request("zxx/testproject/?editing=1", upload_contents, headers)
        # NOTE: this is what we do currently, any altered strings become suggestions.
        # It may be a good idea to change this
        mergedcontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n\n#: toad.c\nmsgid "slink"\nmsgstr "stink"\n'
        suggestedcontents = '#: test.c\nmsgid ""\n"_: suggested by testuser\\n"\n"test"\nmsgstr "rested"\n'
        assert ' href="test_existing.po?' in response
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
        """tests that we can upload a new version of a file into a project"""
        self.login()
        podir = self.setup_testproject_dir()
        tree = potree.POTree(self.prefs.Pootle)
        project = projects.TranslationProject("zxx", "testproject", tree)
        pocontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n'
        open(os.path.join(podir, "test_existing.po"), "w").write(pocontents)
        xlfcontents = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1">
 
<file datatype="po" original="test_existing.po" source-language="en-US"><body>
<trans-unit id="1" xml:space="preserve">
 <source>test</source>
 <target state="translated">rested</target>
 <context-group name="po-reference" purpose="location">
  <context context-type="sourcefile">test.c</context>
 </context-group>
</trans-unit>
<trans-unit id="2" xml:space="preserve">
 <source>slink</source>
 <target state="translated">stink</target>
 <context-group name="po-reference" purpose="location">
  <context context-type="sourcefile">toad.c</context>
 </context-group>
 </trans-unit>
</body></file></xliff>
'''
        fields = [("doupload", "Upload File")]
        files = [("uploadfile", "test_existing.xlf", xlfcontents)]
        content_type, upload_contents = postMultipart.encode_multipart_formdata(fields, files)
        headers = {"Content-Type": content_type, "Content-Length": len(upload_contents)}
        response = self.post_request("zxx/testproject/?editing=1", upload_contents, headers)
        # NOTE: this is what we do currently, any altered strings become suggestions.
        # It may be a good idea to change this
        mergedcontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n\n#: toad.c\nmsgid "slink"\nmsgstr "stink"\n'
        suggestedcontents = '#: test.c\nmsgid ""\n"_: suggested by testuser\\n"\n"test"\nmsgstr "rested"\n'
        assert ' href="test_existing.po?' in response
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
        """tests that we can upload a new file into a project"""
        self.login()
        podir = self.setup_testproject_dir()
        pofile_storename = os.path.join(podir, "test_upload.po")
        pocontents = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        open(pofile_storename, "w").write(pocontents)
        expected_pocontents = '#: test.c\nmsgid "test"\nmsgstr "restrain"\n'
        fields = {"orig-pure0.0": "test", "trans0": "restrain", "submit0": "submit", "pofilename": "test_upload.po"}
        content_type, post_contents = postMultipart.encode_multipart_formdata(fields.items(), [])
        headers = {"Content-Type": content_type, "Content-Length": len(post_contents)}
        translatepage = self.post_request("zxx/testproject/test_upload.po?translate=1&editing=1", post_contents, headers)
        tree = potree.POTree(self.prefs.Pootle)
        project = projects.TranslationProject("zxx", "testproject", tree)
        pofile = project.getpofile("test_upload.po")
        assert str(pofile.units[1]) == expected_pocontents

    def test_submit_fuzzy(self):
        """tests that we can mark a unit as fuzzy"""
        self.login()
        podir = self.setup_testproject_dir()
        pofile_storename = os.path.join(podir, "test_fuzzy.po")
        pocontents = '#: test.c\nmsgid "fuzzy"\nmsgstr "wuzzy"\n'
        open(pofile_storename, "w").write(pocontents)
        expected_pocontents = '#: test.c\n#, fuzzy\nmsgid "fuzzy"\nmsgstr "wuzzy"\n'

        # Fetch the page and check that the fuzzy checkbox is NOT checked.
        translatepage = self.fetch_page("zxx/testproject/test_fuzzy.po?translate=1&editing=1")
        assert '<input accesskey="f" type="checkbox" name="fuzzy0" />' in translatepage

        fields = {"orig-pure0.0": "fuzzy", "trans0": "wuzzy", "submit0": "submit", "fuzzy0": "on", "pofilename": "test_fuzzy.po"}
        content_type, post_contents = postMultipart.encode_multipart_formdata(fields.items(), [])
        headers = {"Content-Type": content_type, "Content-Length": len(post_contents)}
        translatepage = self.post_request("zxx/testproject/test_fuzzy.po?translate=1&editing=1", post_contents, headers)

        # Fetch the page again and check that the fuzzy checkbox IS checked.
        translatepage = self.fetch_page("zxx/testproject/test_fuzzy.po?translate=1&editing=1")
        assert '<input type="checkbox" accesskey="f" checked="checked" name="fuzzy0" />' in translatepage

        tree = potree.POTree(self.prefs.Pootle)
        project = projects.TranslationProject("zxx", "testproject", tree)
        pofile = project.getpofile("test_fuzzy.po")
        assert str(pofile.units[1]) == expected_pocontents
        assert pofile.units[1].isfuzzy()

        # Submit the translation again, without the fuzzy checkbox checked
        fields = {"orig-pure0.0": "fuzzy", "trans0": "wuzzy", "submit0": "submit", "pofilename": "test_fuzzy.po"}
        content_type, post_contents = postMultipart.encode_multipart_formdata(fields.items(), [])
        headers = {"Content-Type": content_type, "Content-Length": len(post_contents)}
        translatepage = self.post_request("zxx/testproject/test_fuzzy.po?translate=1&editing=1", post_contents, headers)

        # Fetch the page once more and check that the fuzzy checkbox is NOT checked.
        translatepage = self.fetch_page("zxx/testproject/test_fuzzy.po?translate=1&editing=1")
        assert '<input accesskey="f" type="checkbox" name="fuzzy0" />' in translatepage
        tree = potree.POTree(self.prefs.Pootle)
        project = projects.TranslationProject("zxx", "testproject", tree)
        pofile = project.getpofile("test_fuzzy.po")
        assert not pofile.units[1].isfuzzy()
        
    def test_navigation_url_parameters(self):
        """tests that the navigation urls (next/end etc) has the necessary parameters"""
        self.login()
        podir = self.setup_testproject_dir()
        pofile_storename = os.path.join(podir, "test_nav_url.po")
        pocontents = '#: test.c\nmsgid "test1"\nmsgstr "rest"\n'
        pocontents += '\n#. Second Unit\nmsgid "test2"\nmsgstr "rest2"\n'
        open(pofile_storename, "w").write(pocontents)
        self.prefs.setvalue("Pootle.users.testuser.viewrows", 1)        
        translatepage = self.fetch_page("zxx/testproject/test_nav_url.po?translate=1&view=1")
        patterns = re.findall('<a href=".(.*)".*Next 1.*</a>', translatepage)
        parameters = patterns[0].split('&amp;')
        assert 'pofilename=test_nav_url.po' in parameters
        assert 'item=1' in parameters

def MakeServerTester(baseclass):
    """Makes a new Server Tester class using the base class to setup webserver etc"""
    class TestServer(baseclass, ServerTester):
        def setup_method(self, method):
            ServerTester.setup_prefs(self, method)
            baseclass.setup_method(self, method)
            ServerTester.setup_cookies(self)
    return TestServer

TestServerCmdLine = MakeServerTester(test_cmdlineserver.TestCmdlineServer)
# TestServerService = MakeServerTester(test_service.TestjLogbookService)
# TestServerApache = MakeServerTester(test_apache.TestApachejLogbook)

