# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re

from django.utils.functional import cached_property

from pootle.core.delegate import stemmer


STOPWORDS = []


class Terminology(object):

    def __init__(self, context):
        self.context = context

    @property
    def is_terminology(self):
        return (
            self.context.store.translation_project.project.code
            == "terminology")

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
        return set(self.stemmer(t) for t in self.tokens)


class UnitTerminology(Terminology):

    def __init__(self, context):
        super(UnitTerminology, self).__init__(context)
        if not self.is_terminology:
            raise ValueError("Unit must be a terminology unit")

    @cached_property
    def existing_stems(self):
        return list(
            self.stem_set.values_list(
                "root", flat=True))

    @property
    def stem_model(self):
        return self.stem_set.model

    @property
    def stem_set(self):
        return self.context.stems

    @property
    def stem_m2m(self):
        return self.stem_set.through

    def associate_stems(self, stems):
        self.stem_m2m.objects.bulk_create(
            self.stem_m2m(stem_id=stem_id, unit_id=self.context.id)
            for stem_id
            in list(
                self.stem_model.objects.filter(root__in=stems)
                               .exclude(root__in=self.existing_stems)
                               .values_list("id", flat=True)))

    def remove_stems(self, stems):
        if self.existing_stems:
            # not sure if this delecetes the m2m or the stem
            self.stem_set.exclude(root__in=stems).delete()

    def create_stems(self, stems):
        self.stem_model.objects.bulk_create(
            self.stem_model(root=root)
            for root
            in stems
            if root not in self.existing_stems)

    def stem(self):
        stems = self.stems
        self.remove_stems(stems)
        self.create_stems(stems)
        self.associate_stems(stems)
        if "existing_stems" in self.__dict__:
            del self.__dict__["existing_stems"]
