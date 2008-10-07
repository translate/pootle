#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory

def test_punctranslate():
    """Tests that we can translate punctuation."""
    language = factory.getlanguage('vi')
    assert language.punctranslate(u"abc efg") == u"abc efg"
    assert language.punctranslate(u"abc efg.") == u"abc efg."
    assert language.punctranslate(u"abc efg!") == u"abc efg !"
    assert language.punctranslate(u"abc efg? hij!") == u"abc efg? hij !"
    assert language.punctranslate(u"Delete file: %s?") == u"Delete file : %s?"
    assert language.punctranslate(u'The user "root"') == u"The user « root »"
    # More exhaustive testing of the quoting is in test_fr.py
    assert language.punctranslate(u'Lưu "Tập tin"') == u"Lưu « Tập tin »"
    assert language.punctranslate(u"Lưu 'Tập tin'") == u"Lưu « Tập tin »"
    assert language.punctranslate(u"Lưu `Tập tin'") == u"Lưu « Tập tin »"

def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('vi')
    sentences = language.sentences(u"Normal case. Nothing interesting.")
    assert sentences == [u"Normal case.", u"Nothing interesting."]
    sentences = language.sentences(u"Is that the case ? Sounds interesting !")
    assert sentences == [u"Is that the case ?", u"Sounds interesting !"]
