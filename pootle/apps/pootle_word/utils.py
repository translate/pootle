# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import re

import Levenshtein
import translate

from django.utils.functional import cached_property

from pootle.core.delegate import stemmer, stopwords


class Stopwords(object):

    @cached_property
    def words(self):
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
        return words


class TextStemmer(object):

    def __init__(self, context):
        self.context = context

    def split(self, words):
        return re.split(u"[^\w'-]+", words)

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


class TextComparison(TextStemmer):

    @property
    def text(self):
        return self.context

    def jaccard_similarity(self, other):
        return (
            len(other.stems.intersection(self.stems))
            / float(len(set(other.stems).union(self.stems))))

    def levenshtein_distance(self, other):
        return (
            Levenshtein.distance(self.text, other.text)
            / max(len(self.text), len(other.text)))

    def tokens_present(self, other):
        return (
            len(set(self.tokens).intersection(other.tokens))
            / float(len(other.tokens)))

    def stems_present(self, other):
        return (
            len(set(self.stems).intersection(other.stems))
            / float(len(other.stems)))

    def similarity(self, other):
        other = self.__class__(other)
        return (
            (self.jaccard_similarity(other)
             + self.levenshtein_distance(other)
             + self.tokens_present(other)
             + self.stems_present(other))
            / 4)
