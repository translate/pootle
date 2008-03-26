#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests decoration handling functions that are used by checks"""

from translate.filters import prefilters

def test_filterwordswithpunctuation():
    string = "Nothing in here."
    filtered = prefilters.filterwordswithpunctuation(string)
    assert filtered == string
    # test listed words (start / end with apostrophe)
    string = "'n Boom het 'n tak."
    filtered = prefilters.filterwordswithpunctuation(string)
    assert filtered == "n Boom het n tak."
    # test words containing apostrophe
    string = "It's in it's own place."
    filtered = prefilters.filterwordswithpunctuation(string)
    assert filtered == "Its in its own place."
    # test strings in unicode
    string = u"Iṱ'š"
    filtered = prefilters.filterwordswithpunctuation(string)
    assert filtered == u"Iṱš"
