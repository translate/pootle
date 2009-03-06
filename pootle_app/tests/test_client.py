from django.test.client import Client
class Tester:
    def __init__(self):
        self.client = Client()

    def login(self):
        return self.client.post('/login.html', {'username': 'admin', 'password': 'admin'})
        
    def logout(self):
        return self.client.get('/logout.html')
    
    # Test methods
    ###############
    def test_login(self):
        """Checks that login works and sets cookies."""
        # make sure we start logged out
        response = self.client.get('/')
        assert "Log in" in response.content

        # check login leads us to a normal page
        response = self.login()
        assert 'sessionid' in response.cookies.keys()

        # check login is retained on next fetch
        response = self.client.get('/')
        assert "Log in" not in response.content

    def test_logout(self):
        """Checks that logout works after logging in."""
        # make sure we start logged in
        self.login()
        response = self.client.get('/')
        assert "Log out" in response.content

        # check login leads us to a normal page
        self.logout()
        response = self.client.get('/')
        assert "Log in" in response.content
        

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


        
