# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_statistics.models import SubmissionTypes
from pootle_store.models import SuggestionStates
from pootle_store.util import FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED


class FilterNotFound(Exception):
    pass


class BaseUnitFilter(object):

    def __init__(self, qs, *args, **kwargs):
        self.qs = qs

    def filter(self, unit_filter):
        try:
            return getattr(
                self, "filter_%s" % unit_filter.replace("-", "_"))()
        except AttributeError:
            raise FilterNotFound()


class UnitChecksFilter(BaseUnitFilter):

    def __init__(self, qs, *args, **kwargs):
        self.qs = qs
        self.checks = kwargs.get("checks")
        self.category = kwargs.get("category")

    def filter_checks(self):
        if self.checks:
            return self.qs.filter(
                qualitycheck__false_positive=False,
                qualitycheck__name__in=self.checks).distinct()
        elif self.category:
            return self.qs.filter(
                qualitycheck__false_positive=False,
                qualitycheck__category=self.category).distinct()
        return self.qs.none()


class UnitStateFilter(BaseUnitFilter):
    """Filter a Unit qs based on unit state"""

    def filter_all(self):
        return self.qs

    def filter_translated(self):
        return self.qs.filter(state__gt=FUZZY)

    def filter_untranslated(self):
        return self.qs.filter(state__gt=OBSOLETE, state__lt=FUZZY)

    def filter_fuzzy(self):
        return self.qs.filter(state__gt=UNTRANSLATED, state__lt=TRANSLATED)

    def filter_incomplete(self):
        return self.qs.filter(state__gt=OBSOLETE, state__lt=TRANSLATED)


class UnitContributionFilter(BaseUnitFilter):
    """Filter a Unit qs based on user contributions"""

    def __init__(self, qs, *args, **kwargs):
        self.qs = qs
        self.user = kwargs.get("user")

    def filter_suggestions(self):
        return self.qs.filter(
            suggestion__state=SuggestionStates.PENDING).distinct()

    def filter_user_suggestions(self):
        if not self.user:
            return self.qs.none()
        return self.qs.filter(
            suggestion__user=self.user,
            suggestion__state=SuggestionStates.PENDING).distinct()

    def filter_my_suggestions(self):
        return self.filter_user_suggestions()

    def filter_user_suggestions_accepted(self):
        if not self.user:
            return self.qs.none()
        return self.qs.filter(
            suggestion__user=self.user,
            suggestion__state=SuggestionStates.ACCEPTED).distinct()

    def filter_user_suggestions_rejected(self):
        if not self.user:
            return self.qs.none()
        return self.qs.filter(
            suggestion__user=self.user,
            suggestion__state=SuggestionStates.REJECTED).distinct()

    def filter_user_submissions(self):
        if not self.user:
            return self.qs.none()
        return self.qs.filter(
            submitted_by=self.user,
            submission__type__in=SubmissionTypes.EDIT_TYPES).distinct()

    def filter_my_submissions(self):
        return self.filter_user_submissions()

    def filter_user_submissions_overwritten(self):
        if not self.user:
            return self.qs.none()
        qs = self.qs.filter(
            submitted_by=self.user,
            submission__type__in=SubmissionTypes.EDIT_TYPES)
        return qs.exclude(submitted_by=self.user).distinct()

    def filter_my_submissions_overwritten(self):
        return self.filter_user_submissions_overwritten()


class UnitSearchFilter(object):

    filters = (
        UnitChecksFilter, UnitStateFilter, UnitContributionFilter)

    def filter(self, qs, unit_filter, *args, **kwargs):
        for search_filter in self.filters:
            # try each of the filter classes to find one with a method to handle
            # `unit_filter`
            try:
                return search_filter(qs, *args, **kwargs).filter(unit_filter)
            except FilterNotFound:
                pass
        # if none match then return the empty qs
        return qs.none()


class UnitTextSearch(object):
    """Search Unit's fields for text strings
    """

    search_fields = (
        "source_f", "target_f", "locations",
        "translator_comment", "developer_comment")
    search_mappings = {
        "notes": ["translator_comment", "developer_comment"],
        "source": ["source_f"],
        "target": ["target_f"]}

    def __init__(self, qs):
        self.qs = qs

    def get_search_fields(self, sfields):
        search_fields = set()
        for field in sfields:
            if field in self.search_mappings:
                search_fields.update(self.search_mappings[field])
            elif field in self.search_fields:
                search_fields.add(field)
        return search_fields

    def get_words(self, text, exact):
        if exact:
            return [text]
        return [t.strip() for t in text.split(" ") if t.strip()]

    def search(self, text, sfields, exact=False):
        result = self.qs.none()
        words = self.get_words(text, exact)

        for k in self.get_search_fields(sfields):
            result = result | self.search_field(k, words)
        return result

    def search_field(self, k, words):
        subresult = self.qs
        for word in words:
            subresult = subresult.filter(
                **{("%s__icontains" % k): word})
        return subresult
