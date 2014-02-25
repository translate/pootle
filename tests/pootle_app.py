import time
import os
import zipfile

from translate.misc import wStringIO

from django.core.urlresolvers import reverse
from django.test import TestCase

from pootle_project.models import Project
from pootle_language.models import Language
from pootle_store.models import Store


def formset_dict(data):
    """convert human readable POST dictionary into brain dead django formset
    dictionary"""
    new_data = {'form-TOTAL_FORMS': len(data), 'form-INITIAL_FORMS': 0}
    for i in range(len(data)):
        for key, value in data[i].iteritems():
            new_data["form-%d-%s" % (i, key)] = value
    return new_data


class AdminTests(TestCase):
    def setUp(self):
        super(AdminTests, self).setUp()
        self.client.login(username='admin', password='admin')

    def test_add_project(self):
        """Checks that we can add a project successfully."""
        response = self.client.get(reverse('pootle-admin-projects'))
        self.assertContains(response, '<a href="%s">tutorial</a>' %
                                       reverse('pootle-project-admin-languages',
                                               args=['tutorial']))
        self.assertContains(response, '<a href="%s">terminology</a>' %
                                      reverse('pootle-project-admin-languages',
                                              args=['terminology']))
        en = Language.objects.get(code='en')
        add_dict = {
            "code": "testproject",
            "localfiletype": "xlf",
            "fullname": "Test Project",
            "checkstyle": "standard",
            "source_language": en.id,
            "treestyle": "gnu",
            }

        response = self.client.post(reverse('pootle-admin-projects'),
                                    formset_dict([add_dict]))
        self.assertContains(response, '<a href="%s">testproject</a>' %
                                      reverse('pootle-project-admin-languages',
                                              args=[add_dict['code']]))

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

        response = self.client.get(reverse('pootle-project-admin-languages',
                                           args=['tutorial']))
        self.assertContains(response, "fish")

        project = Project.objects.get(code='tutorial')
        add_dict = {
            "language": fish.id,
            "project": project.id,
            }
        response = self.client.post(reverse('pootle-project-admin-languages',
                                            args=['tutorial']),
                                    formset_dict([add_dict]))
        self.assertContains(response, '/fish/tutorial/')

        response = self.client.get("/fish/")
        self.assertContains(response, '<a href="/fish/">fish</a>')
        self.assertContains(response, '<a href="/fish/tutorial/">Tutorial</a>')
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
        response = self.client.post("/ar/tutorial/", post_dict)

        self.assertContains(response, 'href="/ar/tutorial/test_new_upload.po')
        store = Store.objects.get(pootle_path="/ar/tutorial/test_new_upload.po")
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
        self.client.post("/af/tutorial/", post_dict)

        # Now we only test with 'in' since the header is added
        store = Store.objects.get(pootle_path="/af/tutorial/pootle.po")
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
        response = self.client.post("/ar/tutorial/", post_dict)

        self.assertContains(response, 'href="/ar/tutorial/test_archive_1.po')
        self.assertContains(response, 'href="/ar/tutorial/test_archive_2.po')

        store = Store.objects.get(pootle_path="/ar/tutorial/test_archive_1.po")
        self.assertTrue(os.path.isfile(store.file.path))
        self.assertEqual(store.file.read(), po_content_1)

        store = Store.objects.get(pootle_path="/ar/tutorial/test_archive_2.po")
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
        self.client.post("/af/tutorial/", post_dict)
        pootle_path = "/af/tutorial/pootle.po"
        self.client.get(pootle_path + "/translate")
        time.sleep(1)
        pocontent = wStringIO.StringIO('#: test.c\nmsgid "test"\nmsgstr "blo3"\n\n#: fish.c\nmsgid "fish"\nmsgstr "stink"\n')
        pocontent.name = "pootle.po"

        post_dict = {
            'file': pocontent,
            'overwrite': 'merge',
            'do_upload': 'upload',
            }
        self.client.post("/af/tutorial/", post_dict)

        # NOTE: this is what we do currently: any altered strings become suggestions.
        # It may be a good idea to change this
        mergedcontent = '#: fish.c\nmsgid "fish"\nmsgstr "stink"\n'
        self.client.get(pootle_path + "/download")
        store = Store.objects.get(pootle_path=pootle_path)
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

        response = self.client.post("/ar/tutorial/", post_dict)
        self.assertContains(response, ' href="/ar/tutorial/test_new_xliff_upload.po')

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
        self.client.post("/ar/tutorial/", post_dict)

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
        self.client.post("/ar/tutorial/", post_dict)

        # NOTE: this is what we do currently: any altered strings become suggestions.
        # It may be a good idea to change this
        mergedcontent = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n'
        store = Store.objects.get(pootle_path="/ar/tutorial/test_upload_xliff.po")
        self.assertTrue(os.path.isfile(store.file.path))
        self.assertTrue(store.file.read().find(mergedcontent) >= 0)

        suggestions = [str(sug) for sug in store.findunit('test').get_suggestions()]
        self.assertTrue('rested' in suggestions)


class NonprivTests(TestCase):

    def test_upload_suggestions(self):
        """Tests that we can upload when we only have suggest rights."""
        pocontent = wStringIO.StringIO('#: test.c\nmsgid "test"\nmsgstr "samaka"\n')
        pocontent.name = "pootle.po"

        post_dict = {
            'file': pocontent,
            'overwrite': 'merge',
            'do_upload': 'upload',
            }
        self.client.post("/af/tutorial/", post_dict)

        # Check that the orignal file didn't take the new suggestion.
        # We test with 'in' since the header is added
        store = Store.objects.get(pootle_path="/af/tutorial/pootle.po")
        self.assertFalse('msgstr "samaka"' in store.file.read())
        suggestions = [str(sug) for sug in store.findunit('test').get_suggestions()]
        self.assertTrue('samaka' in suggestions)
