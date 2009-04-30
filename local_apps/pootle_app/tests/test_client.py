import urlparse
import StringIO
import os

import zipfile
from translate.misc import wStringIO
from translate.storage import factory

from django.test.client import Client
from django.http import QueryDict
from django.conf import settings

from pootle_store.models import Store

ADMIN_USER = {'username': 'admin', 'password': 'admin'}
NONPRIV_USER = {'username': 'nonpriv', 'password': 'nonpriv'}

def follow_redirect(client, response):
    new_response = response
    while new_response.status_code in (301, 302, 303, 307):  
        scheme, netloc, path, query, fragment = urlparse.urlsplit(new_response['Location'])
        new_response = client.get(path, QueryDict(query))
    return new_response

def formset_dict(data):
    """convert human readable POST dictionary into brain dead django formset dictionary"""
    new_data = {'form-TOTAL_FORMS': len(data), 'form-INITIAL_FORMS': 0}
    for i in range(len(data)):
        for key, value in data[i].iteritems():
            new_data["form-%d-%s" % (i,key)] = value
    return new_data
        
def get_store(pootle_path):
    store = Store.objects.get(pootle_path=pootle_path)
    store_path = os.path.join(settings.PODIRECTORY, store.real_path)
    return factory.getobject(store_path)

def test_login():
    """Checks that login works and sets cookies."""
    client = Client()
    response = client.get('/')
    assert "Log in" in response.content
    
    # check login leads us to a normal page
    response = follow_redirect(client, client.post('/login.html', ADMIN_USER))
    assert client.cookies.has_key('sessionid')
    
    # check login is retained on next fetch
    response = client.get('/')
    assert "Log in" not in response.content
    
def test_logout():
    """Checks that logout works after logging in."""
    client = Client()
    # make sure we start logged in
    client.login(**ADMIN_USER)
    response = client.get('/')
    assert "Log out" in response.content
    
    # check login leads us to a normal page
    response = follow_redirect(client, client.get("/logout.html"))
    assert "Log in" in response.content
        

def test_non_admin_rights():
    """Checks that, without admin rights, we can't access the admin screen."""
    client = Client()
    response = follow_redirect(client, client.get("/admin/"))
    assert "You must log in to administer Pootle" in response.content
    
    client.login(**NONPRIV_USER)
    
    response = follow_redirect(client, client.get("/admin/"))
    assert "You do not have the rights to administer Pootle." in response.content


def test_admin_rights():
    """Checks that admin rights work properly."""
    client = Client()
    client.login(**ADMIN_USER)
    
    response = client.get('/')
    assert '<a href="/admin/">Admin</a>' in response.content
    
    response = client.get("/admin/")
    assert "<title>Pootle Admin Page</title>" in response.content



def test_add_project():
    """Checks that we can add a project successfully."""
    client = Client()
    client.login(**ADMIN_USER)

    response = client.get("/admin/projects.html")
    assert '<a href="/projects/pootle/admin.html">pootle</a>' in response.content
    assert '<a href="/projects/terminology/admin.html">terminology</a>' in response.content

    add_dict = {
        "code": "testproject",                                       
        "localfiletype": "xlf",                                     
        "fullname": "Test Project",                                
        "checkstyle": "standard",
        "treestyle": "gnu",
    }
    
    response = client.post("/admin/projects.html", formset_dict([add_dict]))
    assert '<a href="/projects/testproject/admin.html">testproject</a>' in response.content
    
    # check for the actual model
    from pootle_app.models import Project
    testproject = Project.objects.get(code="testproject")
    assert testproject
    assert testproject.fullname == add_dict['fullname']
    assert testproject.checkstyle == add_dict['checkstyle']
    assert testproject.localfiletype == add_dict['localfiletype']
    assert testproject.treestyle == add_dict['treestyle']


def test_add_project_language():
    """Tests that we can add a language to a project, then access its page when there are no files."""
    client = Client()
    client.login(**ADMIN_USER)

    from pootle_app.models import Language
    fish = Language(code="fish", fullname="fish")
    fish.save()
    
    response = client.get("/projects/pootle/admin.html")
    assert "fish"  in response.content
    
    
    add_dict = {
        "add_language": fish.id,
    }
    add_dict.update(formset_dict([]))
    response = client.post("/projects/pootle/admin.html", add_dict)
    assert "fish" in response.content
    
    response = client.get("/fish/")
    assert "fish" in response.content
    assert '<a href="pootle/">Pootle</a>' in response.content
    assert "2 projects, average 0% translated" in response.content

def test_upload_new_file():
    """Tests that we can upload a new file into a project."""
    client = Client()
    client.login(**ADMIN_USER)

    pocontent = StringIO.StringIO('#: test.c\nmsgid "test"\nmsgstr "rest"\n')
    pocontent.name = "test_new_upload.po"
    
    post_dict = {
        'file': pocontent,
        'overwrite': '',
        'do_upload': 'upload',
    }
    
    response = client.post("/ar/pootle/", post_dict)
    assert ' href="/ar/pootle/test_new_upload.po?' in response.content

    store = Store.objects.get(pootle_path="/ar/pootle/test_new_upload.po")
    pofile_storename = os.path.join(settings.PODIRECTORY, store.real_path)
    assert os.path.isfile(pofile_storename)
    assert open(pofile_storename).read() == pocontent.getvalue()
    
    download = client.get("/ar/pootle/test_new_upload.po/export/po")
    assert download.content == pocontent.getvalue()

def test_upload_new_xliff_file():
    """Tests that we can upload a new XLIFF file into a project."""
    client = Client()
    client.login(**ADMIN_USER)
    
    xliffcontent = StringIO.StringIO('''<?xml version='1.0' encoding='utf-8'?>
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
        'overwrite': '',
        'do_upload': 'upload',
    }
        
    response = client.post("/ar/pootle/", post_dict)
    assert ' href="/ar/pootle/test_new_xliff_upload.po?' in response.content

    #FIXME: test conversion?
    #store = Store.objects.get(pootle_path="/ar/pootle/test_new_xliff_upload.po")
    #xliff_storename = os.path.join(settings.PODIRECTORY, store.real_path)
    #assert os.path.isfile(pofile_storename)
    #assert open(pofile_storename).read() == xliffcontent.getvalue()
    #download = client.get("/ar/pootle/test_new_xliff_upload.po/export/xlf")
    #assert download.content == xliffcontent.getvalue()
    

def test_upload_suggestions():
    """Tests that we can upload when we only have suggest rights."""
    client = Client()
    client.login(**NONPRIV_USER)

    pocontent = StringIO.StringIO('#: test.c\nmsgid "fish"\nmsgstr "samaka"\n')
    pocontent.name = "pootle.po"
    
    post_dict = {
        'file': pocontent,
        'overwrite': '',
        'do_upload': 'upload',
    }
    
    response = client.post("/af/pootle/", post_dict)

    # Check that the orignal file didn't take the new suggestion.
    # We test with 'in' since the header is added
    download = client.get("/af/pootle/pootle.po/export/po")
    assert 'msgstr "samaka"' not in download.content
    store = Store.objects.get(pootle_path="/af/pootle/pootle.po")
    pofile_storename = store.file.path
    pending_filename = store.pending.path
    suggestions_content = open(pending_filename, 'r').read()
    assert 'msgstr "samaka"' in suggestions_content


def test_upload_overwrite():
    """Tests that we can overwrite a file in a project."""
    client = Client()
    client.login(**ADMIN_USER)
    
    pocontent = StringIO.StringIO('#: test.c\nmsgid "fish"\nmsgstr ""\n#: test.c\nmsgid "test"\nmsgstr "barf"\n\n')
    pocontent.name = "pootle.po"
    
    post_dict = {
        'file': pocontent,
        'overwrite': 'checked',
        'do_upload': 'upload',
    }
    
    response = client.post("/af/pootle/", post_dict)

    # Now we only test with 'in' since the header is added
    store = Store.objects.get(pootle_path="/af/pootle/pootle.po")
    pofile_storename = os.path.join(settings.PODIRECTORY, store.real_path)
    assert open(pofile_storename).read() == pocontent.getvalue()
    

def test_upload_new_archive():
    """Tests that we can upload a new archive of files into a project."""
    client = Client()
    client.login(**ADMIN_USER)

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
        'overwrite': '',
        'do_upload': 'upload',
    }
    
    response = client.post("/ar/pootle/", post_dict)

    assert ' href="/ar/pootle/test_archive_1.po?' in response.content
    assert ' href="/ar/pootle/test_archive_2.po?' in response.content

    store = Store.objects.get(pootle_path="/ar/pootle/test_archive_1.po")
    pofile_storename = os.path.join(settings.PODIRECTORY, store.real_path)
    assert os.path.isfile(pofile_storename)
    assert open(pofile_storename).read() == po_content_1

    download = client.get("/ar/pootle/test_archive_2.po/export/po")
    assert po_content_2 == download.content
    
def test_upload_over_file():
    """Tests that we can upload a new version of a file into a project."""
    client = Client()
    client.login(**ADMIN_USER)
    pocontent = StringIO.StringIO('''#: fish.c
msgid "fish"
msgstr ""

#: test.c
msgid "test"
msgstr "resto"

''')
    pocontent.name = "pootle.po"
    post_dict = {
        'file': pocontent,
        'overwrite': 'checked',
        'do_upload': 'upload',
    }
    response = client.post("/af/pootle/", post_dict)
    
    pocontent = StringIO.StringIO('#: test.c\nmsgid "test"\nmsgstr "blo3"\n\n#: fish.c\nmsgid "fish"\nmsgstr "stink"\n')
    pocontent.name = "pootle.po"

    post_dict = {
        'file': pocontent,
        'overwrite': '',
        'do_upload': 'upload',
    }
    response = client.post("/af/pootle/", post_dict)

    # NOTE: this is what we do currently: any altered strings become suggestions.
    # It may be a good idea to change this
    mergedcontent = '#: fish.c\nmsgid "fish"\nmsgstr "stink"\n'
    suggestedcontent = '#: test.c\nmsgid ""\n"_: suggested by admin\\n"\n"test"\nmsgstr "blo3"\n'
    store = Store.objects.get(pootle_path="/af/pootle/pootle.po")
    pofile_storename = store.file.path
    assert open(pofile_storename).read().find(mergedcontent) >= 0
    
    pendingfile_storename = store.pending.path
    assert os.path.isfile(pendingfile_storename)
    assert open(pendingfile_storename).read().find(suggestedcontent) >= 0


def test_upload_xliff_over_file():
    """Tests that we can upload a new version of a XLIFF file into a project."""
    client = Client()
    client.login(**ADMIN_USER)
    
    pocontent = StringIO.StringIO('#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#: frog.c\nmsgid "tadpole"\nmsgstr "fish"\n')
    pocontent.name = "test_upload_xliff.po"
    post_dict = {
        'file': pocontent,
        'overwrite': 'checked',
        'do_upload': 'upload',
    }
    response = client.post("/ar/pootle/", post_dict)

    xlfcontent = StringIO.StringIO('''<?xml version="1.0" encoding="utf-8"?>
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
</xliff>''')
    xlfcontent.name = "test_upload_xliff.xlf"
    
    post_dict = {
        'file': xlfcontent,
        'overwrite': '',
        'do_upload': 'upload',
    }
    response = client.post("/ar/pootle/", post_dict)

    # NOTE: this is what we do currently: any altered strings become suggestions.
    # It may be a good idea to change this
    mergedcontent = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n#~ msgid "tadpole"\n#~ msgstr "fish"\n\n#: toad.c\nmsgid "slink"\nmsgstr "stink"\n'
    suggestedcontent = '#: test.c\nmsgid ""\n"_: suggested by admin\\n"\n"test"\nmsgstr "rested"\n'
    store = Store.objects.get(pootle_path="/ar/pootle/test_upload_xliff.po")
    pofile_storename = store.file.path
    assert os.path.isfile(pofile_storename)
    assert open(pofile_storename).read().find(mergedcontent) >= 0

    pendingfile_storename = store.pending.path
    assert os.path.isfile(pendingfile_storename)
    assert open(pendingfile_storename).read().find(suggestedcontent) >= 0


def test_submit_translation():
    """Tests that we can upload a new file into a project."""
    client = Client()
    client.login(**ADMIN_USER)

    submit_dict = {
        'trans0': 'submitted translation',
        'submit0': 'Submit',
        'store': '/af/pootle/pootle.po',
    }
    submit_dict.update(formset_dict([]))
    response = client.post("/af/pootle/pootle.po",
                           submit_dict,
                           QUERY_STRING='view_mode=translate')
    
    assert 'submitted translation' in response.content

    store = Store.objects.get(pootle_path="/af/pootle/pootle.po")
    pofile_storename = os.path.join(settings.PODIRECTORY, store.real_path)    
    assert open(pofile_storename).read().find('submitted translation') >= 0

def test_submit_plural_translation():
    """Tests that we can submit a translation with plurals."""
    client = Client()
    client.login(**ADMIN_USER)

    pocontent = StringIO.StringIO('msgid "singular"\nmsgid_plural "plural"\nmsgstr[0] ""\nmsgstr[1] ""\n')
    pocontent.name = 'test_plural_submit.po'

    post_dict = {
        'file': pocontent,
        'overwrite': 'checked',
        'do_upload': 'upload',
    }
    response = client.post("/ar/pootle/", post_dict)

    submit_dict = {
        'trans0-0': 'a fish',
        'trans0-1': 'some fish',
        'trans0-2': 'lots of fish',
        'submit0': 'Submit',
        'store': '/ar/pootle/test_plural_submit.po',
    }
    submit_dict.update(formset_dict([]))
    response = client.post("/ar/pootle/test_plural_submit.po",
                          submit_dict, QUERY_STRING='view_mode=translate')

    assert 'a fish' in response.content
    assert 'some fish' in response.content
    assert 'lots of fish' in response.content
        
def test_submit_plural_to_singular_lang():
    """Tests that we can submit a translation with plurals to a language without plurals."""
    client = Client()
    client.login(**ADMIN_USER)
        
    pocontent = StringIO.StringIO('msgid "singular"\nmsgid_plural "plural"\nmsgstr[0] ""\nmsgstr[1] ""\n')
    pocontent.name = 'test_plural_submit.po'

    post_dict = {
        'file': pocontent,
        'overwrite': 'checked',
        'do_upload': 'upload',
    }
    response = client.post("/ja/pootle/", post_dict)

    submit_dict = {
        'trans0': 'just fish',
        'submit0': 'Submit',
        'store': '/ja/pootle/test_plural_submit.po',
    }
    submit_dict.update(formset_dict([]))
    response = client.post("/ja/pootle/test_plural_submit.po",
                          submit_dict, QUERY_STRING='view_mode=translate')

    assert 'just fish' in response.content

    expectedcontent = 'msgid "singular"\nmsgid_plural "plural"\nmsgstr[0] "just fish"\n'

    store = Store.objects.get(pootle_path="/ja/pootle/test_plural_submit.po")
    pofile_storename = os.path.join(settings.PODIRECTORY, store.real_path)
    assert open(pofile_storename).read().find(expectedcontent) >= 0


def test_submit_fuzzy():
    """Tests that we can mark a unit as fuzzy."""
    client = Client()
    client.login(**ADMIN_USER)

    # Fetch the page and check that the fuzzy checkbox is NOT checked.
    
    response = client.get("/af/pootle/pootle.po", {'view_mode': 'translate'})
    assert '<input class="fuzzycheck" accesskey="f" type="checkbox" name="fuzzy0" id="fuzzy0" />' in response.content
    
    submit_dict = {
        'trans0': 'fuzzy translation',
        'fuzzy0': 'on',
        'submit0': 'Submit',
        'store': '/af/pootle/pootle.po',
    }
    submit_dict.update(formset_dict([]))
    response = client.post("/af/pootle/pootle.po",
                           submit_dict, QUERY_STRING='view_mode=translate')
    # Fetch the page again and check that the fuzzy checkbox IS checked.
    response = client.get("/af/pootle/pootle.po", {'view_mode': 'translate'})
    assert '<input checked="checked" name="fuzzy0" accesskey="f" type="checkbox" id="fuzzy0" class="fuzzycheck" />' in response.content

    pofile = get_store("/af/pootle/pootle.po")
    assert pofile.units[0].isfuzzy()

    # Submit the translation again, without the fuzzy checkbox checked
    submit_dict = {
        'trans0': 'fuzzy translation',
        'fuzzy0': '',
        'submit0': 'Submit',
        'store': '/af/pootle/pootle.po',
    }
    submit_dict.update(formset_dict([]))
    response = client.post("/af/pootle/pootle.po",
                           submit_dict, QUERY_STRING='view_mode=translate')
    # Fetch the page once more and check that the fuzzy checkbox is NOT checked.
    response = client.get("/af/pootle/pootle.po", {'view_mode': 'translate'})
    assert '<input class="fuzzycheck" accesskey="f" type="checkbox" name="fuzzy0" id="fuzzy0" />' in response.content
    pofile = get_store("/af/pootle/pootle.po")
    assert not pofile.units[0].isfuzzy()
        
def test_submit_translator_comments():
    """Tests that we can edit translator comments."""
    client = Client()
    client.login(**ADMIN_USER)

    submit_dict = {
        'trans0': 'fish',
        'translator_comments0': 'goodbye\nand thanks for all the fish',
        'submit0': 'Submit',
        'store': '/af/pootle/pootle.po',
    }
    submit_dict.update(formset_dict([]))
    response = client.post("/af/pootle/pootle.po",
                           submit_dict,
                           QUERY_STRING='view_mode=translate')

    pofile = get_store("/af/pootle/pootle.po")
    
    assert pofile.units[0].getnotes() == 'goodbye\nand thanks for all the fish'



        
