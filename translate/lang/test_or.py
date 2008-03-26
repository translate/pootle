#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory

def test_punctranslate():
    """Tests that we can translate punctuation."""
    language = factory.getlanguage('or')
    assert language.punctranslate(u"Document loaded") == u"Document loaded"
    assert language.punctranslate(u"Document loaded.") == u"Document loaded।"

def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('or')
    sentences = language.sentences(u"ଗୋଟିଏ ଚାବିକୁ ଆଲୋକପାତ କରିବା ପାଇଁ ମାଉସ ସୂଚକକୁ ତାହା ଉପରକୁ ଘୁଞ୍ଚାନ୍ତୁ। ଚୟନ କରିବା ପାଇଁ ଗୋଟିଏ ସୁଇଚକୁ ଦବାନ୍ତୁ।")
    assert sentences == [u"ଗୋଟିଏ ଚାବିକୁ ଆଲୋକପାତ କରିବା ପାଇଁ ମାଉସ ସୂଚକକୁ ତାହା ଉପରକୁ ଘୁଞ୍ଚାନ୍ତୁ।", u"ଚୟନ କରିବା ପାଇଁ ଗୋଟିଏ ସୁଇଚକୁ ଦବାନ୍ତୁ।"]

