import os
import zipfile

from translate.misc import wStringIO

from pootle.tests import PootleTestCase, formset_dict

from pootle_project.models import Project
from pootle_language.models import Language
from pootle_store.models import Store


class AnonTests(PootleTestCase):
    def test_admin_not_logged(self):
        """checks that admin pages are not accessible without login"""
        response = self.client.get("/admin/")
        self.assertContains(response, '', status_code=403)


class AdminTests(PootleTestCase):
    def setUp(self):
        super(AdminTests, self).setUp()
        self.client.login(username='admin', password='admin')

    def test_admin_rights(self):
        """checks that admin user can access admin pages"""
        response = self.client.get('/')
        self.assertContains(response, "<a href='/admin/'>Admin</a>")
        response = self.client.get('/admin/')
        self.assertContains(response, 'General Settings')

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
        testproject = Project.objects.get(code="testproject")

        self.assertTrue(testproject)
        self.assertEqual(testproject.fullname, add_dict['fullname'])
        self.assertEqual(testproject.checkstyle, add_dict['checkstyle'])
        self.assertEqual(testproject.localfiletype, add_dict['localfiletype'])
        self.assertEqual(testproject.treestyle, add_dict['treestyle'])

    def test_add_project_language(self):
        """Tests that we can add a language to a project, then access
        its page when there are no files."""
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
        self.assertContains(response, '<a href="/fish/">fish</a>')
        self.assertContains(response, '<a href="/fish/pootle/">Pootle</a>')
        self.assertContains(response, "1 project, 0% translated")

    def test_upload_new_file(self):
        """Tests that we can upload a new file into a project."""
        pocontent = wStringIO.StringIO('#: test.c\nmsgid "test"\nmsgstr "rest"\n')
        pocontent.name = "test_new_upload.po"

        post_dict = {
            'file': pocontent,
            'overwrite': 'merge',
            'do_upload': 'upload',
            }
        response = self.client.post("/ar/pootle/", post_dict)

        self.assertContains(response, 'href="/ar/pootle/test_new_upload.po')
        store = Store.objects.get(pootle_path="/ar/pootle/test_new_upload.po")
        self.assertTrue(os.path.isfile(store.file.path))
        self.assertEqual(store.file.read(), pocontent.getvalue())

    def test_upload_overwrite(self):
        """Tests that we can overwrite a file in a project."""
        pocontent = wStringIO.StringIO('#: test.c\nmsgid "fish"\nmsgstr ""\n#: test.c\nmsgid "test"\nmsgstr "barf"\n\n')
        pocontent.name = "pootle.po"

        post_dict = {
            'file': pocontent,
            'overwrite': 'overwrite',
            'do_upload': 'upload',
            }
        response = self.client.post("/af/pootle/", post_dict)

        # Now we only test with 'in' since the header is added
        store = Store.objects.get(pootle_path="/af/pootle/pootle.po")
        self.assertEqual(store.file.read(), pocontent.getvalue())

    def test_upload_new_archive(self):
        """Tests that we can upload a new archive of files into a project."""
        po_content_1 = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        po_content_2 = '#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n'

        archivefile = wStringIO.StringIO()
        archivefile.name = "fish.zip"
        archive = zipfile.ZipFile(archivefile, "w", zipfile.ZIP_DEFLATED)
        archive.writestr("test_archive_1.po", po_content_1)
        archive.writestr("test_archive_2.po", po_content_2)
        archive.close()

        archivefile.seek(0)
        post_dict = {
            'file': archivefile,
            'overwrite': 'merge',
            'do_upload': 'upload',
            }
        response = self.client.post("/ar/pootle/", post_dict)

        self.assertContains(response, 'href="/ar/pootle/test_archive_1.po')
        self.assertContains(response, 'href="/ar/pootle/test_archive_2.po')

        store = Store.objects.get(pootle_path="/ar/pootle/test_archive_1.po")
        self.assertTrue(os.path.isfile(store.file.path))
        self.assertEqual(store.file.read(), po_content_1)

        store = Store.objects.get(pootle_path="/ar/pootle/test_archive_2.po")
        self.assertTrue(os.path.isfile(store.file.path))
        self.assertEqual(store.file.read(), po_content_2)

    def test_upload_over_file(self):
        """Tests that we can upload a new version of a file into a project."""
        pocontent = wStringIO.StringIO('''#: fish.c
msgid "fish"
msgstr ""

#: test.c
msgid "test"
msgstr "resto"

''')
        pocontent.name = "pootle.po"
        post_dict = {
            'file': pocontent,
            'overwrite': 'overwrite',
            'do_upload': 'upload',
            }
        response = self.client.post("/af/pootle/", post_dict)

        pocontent = wStringIO.StringIO('#: test.c\nmsgid "test"\nmsgstr "blo3"\n\n#: fish.c\nmsgid "fish"\nmsgstr "stink"\n')
        pocontent.name = "pootle.po"

        post_dict = {
            'file': pocontent,
            'overwrite': 'merge',
            'do_upload': 'upload',
            }
        response = self.client.post("/af/pootle/", post_dict)

        # NOTE: this is what we do currently: any altered strings become suggestions.
        # It may be a good idea to change this
        mergedcontent = '#: fish.c\nmsgid "fish"\nmsgstr "stink"\n'
        suggestedcontent = '#: test.c\nmsgid ""\n"_: suggested by admin [1963585124]\\n"\n"test"\nmsgstr "blo3"\n'
        store = Store.objects.get(pootle_path="/af/pootle/pootle.po")
        self.assertTrue(store.file.read().find(mergedcontent) >= 0)
        suggestions = [str(sug) for sug in store.findunit('test').get_suggestions()]
        self.assertTrue("blo3" in suggestions)


    def test_upload_new_xliff_file(self):
        """Tests that we can upload a new XLIFF file into a project."""
        xliffcontent = wStringIO.StringIO('''<?xml version='1.0' encoding='utf-8'?>
        <xliff xmlns="urn:oasis:names:tc:xliff:document:1.1" version="1.1">
        <file original="" source-language="en-US" datatype="po">
        <body>
          <trans-unit id="1" xml:space="preserve">
            <source>test</source>
            <target state="needs-review-translation">rest</target>
            <context-group name="po-reference" purpose="location">
              <context context-type="sourcefile">test.c</context>
            </context-group>
          </trans-unit>
        </body>
        </file>
        </xliff>
''')
        xliffcontent.name = 'test_new_xliff_upload.xlf'

        post_dict = {
            'file': xliffcontent,
            'overwrite': 'overwrite',
            'do_upload': 'upload',
            }

        response = self.client.post("/ar/pootle/", post_dict)
        self.assertContains(response,' href="/ar/pootle/test_new_xliff_upload.po')

        #FIXME: test conversion?

    def test_upload_xliff_over_file(self):
        """Tests that we can upload a new version of a XLIFF file into a project."""
        pocontent = wStringIO.StringIO('#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n')
        pocontent.name = "test_upload_xliff.po"
        post_dict = {
            'file': pocontent,
            'overwrite': 'overwrite',
            'do_upload': 'upload',
            }
        response = self.client.post("/ar/pootle/", post_dict)

        xlfcontent = wStringIO.StringIO('''<?xml version="1.0" encoding="utf-8"?>
        <xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1">
        <file datatype="po" original="test_upload_xliff.po" source-language="en-US">
        <body>
            <trans-unit id="test" xml:space="preserve" approved="yes">
                <source>test</source>
                <target state="translated">rested</target>
                <context-group name="po-reference" purpose="location">
                    <context context-type="sourcefile">test.c</context>
                </context-group>
            </trans-unit>
            <trans-unit id="slink" xml:space="preserve" approved="yes">
                <source>slink</source>
                <target state="translated">stink</target>
                <context-group name="po-reference" purpose="location">
                    <context context-type="sourcefile">toad.c</context>
                </context-group>
            </trans-unit>
        </body>
        </file>
        </xliff>''')
        xlfcontent.name = "test_upload_xliff.xlf"

        post_dict = {
            'file': xlfcontent,
            'overwrite': 'merge',
            'do_upload': 'upload',
            }
        response = self.client.post("/ar/pootle/", post_dict)

        # NOTE: this is what we do currently: any altered strings become suggestions.
        # It may be a good idea to change this
        mergedcontent = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n'
        suggestedcontent = '#: test.c\nmsgid ""\n"_: suggested by admin [595179475]\\n"\n"test"\nmsgstr "rested"\n'
        store = Store.objects.get(pootle_path="/ar/pootle/test_upload_xliff.po")
        self.assertTrue(os.path.isfile(store.file.path))
        self.assertTrue(store.file.read().find(mergedcontent) >= 0)

        suggestions = [str(sug) for sug in store.findunit('test').get_suggestions()]
        self.assertTrue('rested' in suggestions)

    def test_submit_translation(self):
        """Tests that we can translate units."""

        submit_dict = {
            'trans0': 'submitted translation',
            'submit0': 'Submit',
            'store': '/af/pootle/pootle.po',
            }
        submit_dict.update(formset_dict([]))
        response = self.client.post("/af/pootle/pootle.po", submit_dict,
                                    QUERY_STRING='view_mode=translate')

        self.assertContains(response, 'submitted translation')
        response = self.client.get("/af/pootle/pootle.po/download")
        store = Store.objects.get(pootle_path="/af/pootle/pootle.po")
        self.assertTrue(store.file.read().find('submitted translation') >= 0)

    def test_submit_plural_translation(self):
        """Tests that we can submit a translation with plurals."""
        pocontent = wStringIO.StringIO('msgid "singular"\nmsgid_plural "plural"\nmsgstr[0] ""\nmsgstr[1] ""\n')
        pocontent.name = 'test_plural_submit.po'

        post_dict = {
            'file': pocontent,
            'overwrite': 'overwrite',
            'do_upload': 'upload',
            }
        response = self.client.post("/ar/pootle/", post_dict)

        submit_dict = {
            'trans0-0': 'a fish',
            'trans0-1': 'some fish',
            'trans0-2': 'lots of fish',
            'submit0': 'Submit',
            'store': '/ar/pootle/test_plural_submit.po',
            }
        submit_dict.update(formset_dict([]))
        response = self.client.post("/ar/pootle/test_plural_submit.po", submit_dict,
                                    QUERY_STRING='view_mode=translate')

        self.assertContains(response, 'a fish')
        self.assertContains(response, 'some fish')
        self.assertContains(response, 'lots of fish')

    def test_submit_plural_to_singular_lang(self):
        """Tests that we can submit a translation with plurals to a language without plurals."""

        pocontent = wStringIO.StringIO('msgid "singular"\nmsgid_plural "plural"\nmsgstr[0] ""\nmsgstr[1] ""\n')
        pocontent.name = 'test_plural_submit.po'

        post_dict = {
            'file': pocontent,
            'overwrite': 'overwrite',
            'do_upload': 'upload',
            }
        response = self.client.post("/ja/pootle/", post_dict)

        submit_dict = {
            'trans0': 'just fish',
            'submit0': 'Submit',
            'store': '/ja/pootle/test_plural_submit.po',
            }
        submit_dict.update(formset_dict([]))
        response = self.client.post("/ja/pootle/test_plural_submit.po", submit_dict,
                                    QUERY_STRING='view_mode=translate')
        self.assertContains(response, 'just fish')

        expectedcontent = 'msgid "singular"\nmsgid_plural "plural"\nmsgstr[0] "just fish"\n'
        response = self.client.get('/ja/pootle/test_plural_submit.po/download')
        store = Store.objects.get(pootle_path="/ja/pootle/test_plural_submit.po")
        self.assertTrue(store.file.read().find(expectedcontent) >= 0)


    def test_submit_fuzzy(self):
        """Tests that we can mark a unit as fuzzy."""

        # Fetch the page and check that the fuzzy checkbox is NOT checked.

        response = self.client.get("/af/pootle/pootle.po", {'view_mode': 'translate'})
        self.assertContains(response, '<input type="checkbox"  name="fuzzy0" accesskey="f" id="fuzzy0" class="fuzzycheck" />')

        submit_dict = {
            'trans0': 'fuzzy translation',
            'fuzzy0': 'on',
            'submit0': 'Submit',
            'store': '/af/pootle/pootle.po',
            }
        submit_dict.update(formset_dict([]))
        response = self.client.post("/af/pootle/pootle.po", submit_dict,
                                    QUERY_STRING='view_mode=translate')
        # Fetch the page again and check that the fuzzy checkbox IS checked.
        response = self.client.get("/af/pootle/pootle.po", {'view_mode': 'translate'})
        self.assertContains(response, '<input type="checkbox" checked="checked" name="fuzzy0" accesskey="f" id="fuzzy0" class="fuzzycheck" />')

        store = Store.objects.get(pootle_path="/af/pootle/pootle.po")
        self.assertTrue(store.getitem(0).isfuzzy())

        # Submit the translation again, without the fuzzy checkbox checked
        submit_dict = {
            'trans0': 'fuzzy translation',
            'fuzzy0': '',
            'submit0': 'Submit',
            'store': '/af/pootle/pootle.po',
            }
        submit_dict.update(formset_dict([]))
        response = self.client.post("/af/pootle/pootle.po", submit_dict,
                                    QUERY_STRING='view_mode=translate')
        # Fetch the page once more and check that the fuzzy checkbox is NOT checked.
        response = self.client.get("/af/pootle/pootle.po", {'view_mode': 'translate'})
        self.assertContains(response, '<input type="checkbox"  name="fuzzy0" accesskey="f" id="fuzzy0" class="fuzzycheck" />')
        self.assertFalse(store.getitem(0).isfuzzy())

    def test_submit_translator_comments(self):
        """Tests that we can edit translator comments."""

        submit_dict = {
            'trans0': 'fish',
            'translator_comments0': 'goodbye\nand thanks for all the fish',
            'submit0': 'Submit',
            'store': '/af/pootle/pootle.po',
            }
        submit_dict.update(formset_dict([]))
        response = self.client.post("/af/pootle/pootle.po", submit_dict,
                                    QUERY_STRING='view_mode=translate')

        store = Store.objects.get(pootle_path='/af/pootle/pootle.po')
        self.assertEqual(store.getitem(0).getnotes(), 'goodbye\nand thanks for all the fish')


class NonprivTests(PootleTestCase):
    def setUp(self):
        super(NonprivTests, self).setUp()
        self.client.login(username='nonpriv', password='nonpriv')

    def test_non_admin_rights(self):
        """checks that non privileged users cannot access admin pages"""
        response = self.client.get('/admin/')
        self.assertContains(response, '', status_code=403)

    def test_upload_suggestions(self):
        """Tests that we can upload when we only have suggest rights."""
        pocontent = wStringIO.StringIO('#: test.c\nmsgid "test"\nmsgstr "samaka"\n')
        pocontent.name = "pootle.po"

        post_dict = {
            'file': pocontent,
            'overwrite': 'merge',
            'do_upload': 'upload',
            }
        response = self.client.post("/af/pootle/", post_dict)

        # Check that the orignal file didn't take the new suggestion.
        # We test with 'in' since the header is added
        store = Store.objects.get(pootle_path="/af/pootle/pootle.po")
        self.assertFalse('msgstr "samaka"' in store.file.read())
        suggestions = [str(sug) for sug in store.findunit('test').get_suggestions()]
        self.assertTrue('samaka' in suggestions)

