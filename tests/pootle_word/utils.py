# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

from stemming.porter2 import stem

import translate

from pootle.core.delegate import stemmer, stopwords


def test_stemmer():
    assert stemmer.get() is stem


def test_stopwords():
    fpath = os.path.join(translate.__path__[0], "share", "stoplist-en")
    words = set()
    with open(fpath) as f:
        for line in f.read().split("\n"):
            if not line:
                continue
            if line[0] in "<>=@":
                words.add(line[1:].strip().lower())
    stops = stopwords.get()
    assert stops.words == words
