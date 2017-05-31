# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.functional import cached_property

from pootle.core.decorators import persistent_property
from pootle.core.delegate import revision, text_comparison
from pootle_store.constants import TRANSLATED
from pootle_store.models import Unit
from pootle_translationproject.models import TranslationProject
from pootle_word.utils import TextStemmer

from .apps import PootleTerminologyConfig


class UnitTerminology(TextStemmer):

    def __init__(self, context):
        super(UnitTerminology, self).__init__(context)
        if not self.is_terminology:
            raise ValueError("Unit must be a terminology unit")

    @property
    def is_terminology(self):
        return (
            self.context.store.name.startswith("pootle-terminology")
            or (self.context.store.translation_project.project.code
                == "terminology"))

    @property
    def existing_stems(self):
        return set(
            self.stem_set.values_list(
                "root", flat=True))

    @property
    def missing_stems(self):
        return (
            self.stems
            - set(self.stem_model.objects.filter(
                root__in=self.stems).values_list("root", flat=True)))

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
                               .values_list("id", flat=True)))

    def clear_stems(self, stems):
        # not sure if this delecetes the m2m or the stem
        self.stem_set.filter(root__in=stems).delete()

    def create_stems(self, stems):
        self.stem_model.objects.bulk_create(
            self.stem_model(root=root)
            for root
            in stems)

    def stem(self):
        stems = self.stems
        existing_stems = self.existing_stems
        missing_stems = self.missing_stems
        if existing_stems:
            self.clear_stems(existing_stems - stems)
        if missing_stems:
            self.create_stems(missing_stems)
        if stems - existing_stems:
            self.associate_stems(stems - existing_stems)


class UnitTerminologyMatcher(TextStemmer):

    ns = "pootle.terminology.matcher"
    sw_version = PootleTerminologyConfig.version
    similarity_threshold = .2
    max_matches = 10

    @property
    def revision_context(self):
        term_tp = TranslationProject.objects.select_related("directory").filter(
            language_id=self.language_id,
            project__code="terminology").first()
        if term_tp:
            return term_tp.directory

    @property
    def rev_cache_key(self):
        rev_context = self.revision_context
        return (
            revision.get(rev_context.__class__)(rev_context).get(key="stats")
            if rev_context
            else "")

    @property
    def cache_key(self):
        return (
            "%s.%s.%s"
            % (self.language_id,
               self.rev_cache_key,
               hash(self.text)))

    @property
    def language_id(self):
        return self.context.store.translation_project.language.id

    @property
    def terminology_units(self):
        return Unit.objects.filter(
            state=TRANSLATED,
            store__translation_project__project__code="terminology",
            store__translation_project__language_id=self.language_id)

    @cached_property
    def comparison(self):
        return text_comparison.get()(self.text)

    def similar(self, results):
        matches = []
        matched = []
        for result in results:
            target_pair = (
                result.source_f.lower().strip(),
                result.target_f.lower().strip())
            if target_pair in matched:
                continue
            similarity = self.comparison.similarity(result.source_f)
            if similarity > self.similarity_threshold:
                matches.append((similarity, result))
                matched.append(target_pair)
        return sorted(matches, key=lambda x: -x[0])[:self.max_matches]

    @persistent_property
    def matches(self):
        return self.similar(
            self.terminology_units.filter(
                stems__root__in=self.stems).distinct())
