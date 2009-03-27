# -*- coding: utf-8 -*-
from Pootle import pootle
from pootle_app.models import store_filen

def setup_module(module):
    """initialize global variables in the module"""
    parser = pootle.PootleOptionParser()
    options, args = parser.parse_args(["--servertype=dummy"])
    module.server = parser.getserver(options)
    # shortcuts to make tests easier
    module.potree = module.server.potree

def test_init():
    """tests that the index can be initialized"""
    for languagecode, languagename in potree.getlanguages("pootle"):
        translationproject = potree.getproject(languagecode, "pootle")
        assert translationproject.make_indexer()

def test_search():
    """tests that the index can be initialized"""
    pass_search = store_file.Search(searchtext="login")
    fail_search = store_file.Search(searchtext="Zrogny")
    for languagecode, languagename in potree.getlanguages("pootle"):
        translationproject = potree.getproject(languagecode, "pootle")
        print translationproject.make_indexer().location
        pass_search_results = translationproject.searchpoitems("pootle.po", -1, pass_search)
        pass_search_results = [(pofilename, item) for pofilename, item in pass_search_results]
        assert pass_search_results
        fail_search_results = translationproject.searchpoitems("pootle.po", -1, fail_search)
        fail_search_results = [(pofilename, item) for pofilename, item in fail_search_results]
        assert not fail_search_results

