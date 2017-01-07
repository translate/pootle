# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re

from pootle.core.delegate import stemmer


STOPWORDS = []


class TextStemmer(object):

    def __init__(self, context):
        self.context = context

    def split(self, words):
        return re.split(u"[\W]+", words)

    @property
    def stop_words(self):
        return STOPWORDS

    @property
    def tokens(self):
        return [
            t.lower()
            for t
            in self.split(self.text)
            if (len(t) > 2
                and t not in self.stop_words)]

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
