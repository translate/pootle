#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import pytest

from translate.misc import wStringIO

from pootle_store.models import Store


@pytest.mark.xfail
def test_upload_new_file(admin_client):
    """Tests that we can upload a new file into a translation project."""
    pocontent = wStringIO.StringIO('#: test.c\nmsgid "test"\nmsgstr "rest"\n')
    pocontent.name = "test_new_upload.po"

    post_dict = {
        'file': pocontent,
        'overwrite': 'merge',
        'do_upload': 'upload',
    }
    response = admin_client.post("/ar/tutorial/", post_dict)

    assert 'href="/ar/tutorial/test_new_upload.po' in response
    store = Store.objects.get(pootle_path="/ar/tutorial/test_new_upload.po")
    assert os.path.isfile(store.file.path)
    assert store.file.read() == pocontent.getvalue()


@pytest.mark.xfail
def test_upload_overwrite(admin_client):
    """Tests that we can overwrite a file in a project."""
    pocontent = wStringIO.StringIO('#: test.c\nmsgid "fish"\nmsgstr ""\n#: test.c\nmsgid "test"\nmsgstr "barf"\n\n')
    pocontent.name = "pootle.po"

    post_dict = {
        'file': pocontent,
        'overwrite': 'overwrite',
        'do_upload': 'upload',
    }
    admin_client.post("/af/tutorial/", post_dict)

    # Now we only test with 'in' since the header is added
    store = Store.objects.get(pootle_path="/af/tutorial/pootle.po")
    assert store.file.read() == pocontent.getvalue()


@pytest.mark.xfail
def test_upload_new_archive(admin_client):
    """Tests that we can upload a new archive of files into a project."""
    import zipfile
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
    response = admin_client.post("/ar/tutorial/", post_dict)

    assert 'href="/ar/tutorial/test_archive_1.po' in response
    assert 'href="/ar/tutorial/test_archive_2.po' in response

    store = Store.objects.get(pootle_path="/ar/tutorial/test_archive_1.po")
    assert os.path.isfile(store.file.path)
    assert store.file.read() == po_content_1

    store = Store.objects.get(pootle_path="/ar/tutorial/test_archive_2.po")
    assert os.path.isfile(store.file.path)
    assert store.file.read() == po_content_2


@pytest.mark.xfail
def test_upload_over_file(admin_client):
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
    admin_client.post("/af/tutorial/", post_dict)
    pootle_path = "/af/tutorial/pootle.po"
    admin_client.get(pootle_path + "/translate")
    pocontent = wStringIO.StringIO('#: test.c\nmsgid "test"\nmsgstr "blo3"\n\n#: fish.c\nmsgid "fish"\nmsgstr "stink"\n')
    pocontent.name = "pootle.po"

    post_dict = {
        'file': pocontent,
        'overwrite': 'merge',
        'do_upload': 'upload',
    }
    admin_client.post("/af/tutorial/", post_dict)

    # NOTE: this is what we do currently: any altered strings become suggestions.
    # It may be a good idea to change this
    mergedcontent = '#: fish.c\nmsgid "fish"\nmsgstr "stink"\n'
    admin_client.get(pootle_path + "/download")
    store = Store.objects.get(pootle_path=pootle_path)
    assert store.file.read().find(mergedcontent) >= 0
    suggestions = [str(sug) for sug in store.findunit('test').get_suggestions()]
    assert "blo3" in suggestions


@pytest.mark.xfail
def test_upload_new_xliff_file(admin_client):
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

    response = admin_client.post("/ar/tutorial/", post_dict)
    assert ' href="/ar/tutorial/test_new_xliff_upload.po' in response


@pytest.mark.xfail
def test_upload_xliff_over_file(admin_client):
    """Tests that we can upload a new version of a XLIFF file into a project."""
    pocontent = wStringIO.StringIO('#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n')
    pocontent.name = "test_upload_xliff.po"
    post_dict = {
        'file': pocontent,
        'overwrite': 'overwrite',
        'do_upload': 'upload',
    }
    admin_client.post("/ar/tutorial/", post_dict)

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
    admin_client.post("/ar/tutorial/", post_dict)

    # NOTE: this is what we do currently: any altered strings become suggestions.
    # It may be a good idea to change this
    mergedcontent = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n'
    store = Store.objects.get(pootle_path="/ar/tutorial/test_upload_xliff.po")
    assert os.path.isfile(store.file.path)
    assert store.file.read().find(mergedcontent) >= 0

    suggestions = [str(sug) for sug in store.findunit('test').get_suggestions()]
    assert "rested" in suggestions


@pytest.mark.xfail
def test_upload_suggestions(admin_client):
    """Tests that we can upload when we only have suggest rights."""
    pocontent = wStringIO.StringIO('#: test.c\nmsgid "test"\nmsgstr "samaka"\n')
    pocontent.name = "pootle.po"

    post_dict = {
        'file': pocontent,
        'overwrite': 'merge',
        'do_upload': 'upload',
    }
    admin_client.post("/af/tutorial/", post_dict)

    # Check that the orignal file didn't take the new suggestion.
    # We test with 'in' since the header is added
    store = Store.objects.get(pootle_path="/af/tutorial/pootle.po")
    assert 'msgstr "samaka"' not in store.file.read()

    suggestions = [str(sug) for sug in store.findunit('test').get_suggestions()]
    assert 'samaka' in suggestions
