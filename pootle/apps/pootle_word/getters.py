# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from stemming.porter2 import stem

from pootle.core.delegate import stemmer, stopwords, text_comparison
from pootle.core.plugin import getter

from .utils import Stopwords, TextComparison


site_stopwords = Stopwords()


@getter(stemmer)
def get_stemmer(**kwargs_):
    return stem


@getter(stopwords)
def get_stopwords(**kwargs_):
    return site_stopwords


@getter(text_comparison)
def get_text_comparison(**kwargs_):
    return TextComparison
