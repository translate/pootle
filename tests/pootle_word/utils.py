# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import Levenshtein

from stemming.porter2 import stem

import translate

import pytest

from pootle.core.delegate import stemmer, stopwords, text_comparison
from pootle_word.utils import TextComparison


def test_stemmer():
    assert stemmer.get() is stem


def test_stopwords():
    ttk_path = translate.__path__[0]
    fpath = (
        os.path.join(ttk_path, "share", "stoplist-en")
        if "share" in os.listdir(ttk_path)
        else os.path.join(ttk_path, "..", "share", "stoplist-en"))
    words = set()
    with open(fpath) as f:
        for line in f.read().split("\n"):
            if not line:
                continue
            if line[0] in "<>=@":
                words.add(line[1:].strip().lower())
    stops = stopwords.get()
    assert stops.words == words


@pytest.mark.django_db
def test_text_comparer():
    comparer = text_comparison.get()("Cycling through the examples")
    assert isinstance(comparer, TextComparison)
    assert comparer.context == "Cycling through the examples"
    assert comparer.text == comparer.context
    assert comparer.tokens == [
        word for word
        in comparer.split(comparer.text.lower())
        if word not in comparer.stopwords]
    assert comparer.stems == set(comparer.stemmer(t) for t in comparer.tokens)
    other_text = "cycle home"
    other = text_comparison.get()(other_text)
    assert (
        comparer.jaccard_similarity(other)
        == (len(other.stems.intersection(comparer.stems))
            / float(len(set(other.stems).union(comparer.stems)))))
    assert (
        comparer.levenshtein_distance(other)
        == (Levenshtein.distance(comparer.text, other.text)
            / max(len(comparer.text), len(other.text))))
    assert (
        comparer.tokens_present(other)
        == (len(set(comparer.tokens).intersection(other.tokens))
            / float(len(other.tokens))))
    assert (
        comparer.stems_present(other)
        == (len(set(comparer.stems).intersection(other.stems))
            / float(len(other.stems))))
    assert (
        comparer.similarity(other_text)
        == ((comparer.jaccard_similarity(other)
             + comparer.levenshtein_distance(other)
             + comparer.tokens_present(other)
             + comparer.stems_present(other))
            / 4))
