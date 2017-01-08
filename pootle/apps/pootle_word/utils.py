# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import re

import translate

from django.utils.functional import cached_property

from pootle.core.delegate import stemmer, stopwords


class Stopwords(object):

    @cached_property
    def words(self):
        fpath = os.path.join(translate.__path__[0], "share", "stoplist-en")
        words = set()
        with open(fpath) as f:
            for line in f.read().split("\n"):
                if not line:
                    continue
                if line[0] in "<>=@":
                    words.add(line[1:].strip().lower())
        return words


class TextStemmer(object):

    def __init__(self, context):
        self.context = context

    def split(self, words):
        return re.split(u"[\W]+", words)

    @property
    def stopwords(self):
        return stopwords.get().words

    @property
    def tokens(self):
        return [
            t.lower()
            for t
            in self.split(self.text)
            if (len(t) > 2
                and t.lower() not in self.stopwords)]

    @property
    def text(self):
        return self.context.source_f

    @property
    def stemmer(self):
        return stemmer.get()

    @property
    def stems(self):
        return self.get_stems(self.tokens)

    def get_stems(self, tokens):
        return set(self.stemmer(t) for t in tokens)
