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



        
