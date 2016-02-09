# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import functools

from django.db.models import Q

from pootle_misc.checks import get_category_id
from pootle_statistics.models import SubmissionTypes

import pootle_store
from ..models import SuggestionStates


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

    def search(self, text, sfields, exact=False):
        if exact:
            words = [text]
        else:
            words = text.split()
        result = self.qs.none()
        for k, v in self.search_mappings.items():
            if k in sfields:
                sfields += v
        for k in filter(lambda x: x in self.search_fields, sfields):
            result = result | self.search_field(k, words)
        return result

    def search_field(self, k, words):
        subresult = self.qs
        for word in words:
            subresult = subresult.filter(
                **{("%s__icontains" % k): word})
        return subresult


def call_with(*keys):
    """Only call the wrapped method if all of the keys are present in the **kwa
    that the method is called with.

    If all of the keys are present these are removed from the kwa and used in
    order as list arguments

    If any are not present then self.qs is returned.
    """

    def class_wrapper(f):

        @functools.wraps(f)
        def method_wrapper(self, **kwa):
            if not all(kwa.get(k, None) for k in keys):
                return self.qs
            return f(
                self,
                *[kwa[k] for k
                  in keys],
                **{k: v for k, v
                   in kwa.items()
                   if k not in keys})
        return method_wrapper
    return class_wrapper


class SearchFilter(object):

    # these filter methods are run in order if the required kwa key(s) are
    # present
    filters = [
        "vfolder", "unit_filter", "checks", "mtime",
        "month", "text_search"]

    # filter functions for retrieving unit_filter queries
    translated_q = lambda self, user: Q(
        state=pootle_store.util.TRANSLATED)
    untranslated_q = lambda self, user: Q(
        state=pootle_store.util.UNTRANSLATED)
    fuzzy_q = lambda self, user: Q(
        state=pootle_store.util.FUZZY)
    incomplete_q = lambda self, user: Q(
        Q(state=pootle_store.util.UNTRANSLATED)
        | Q(state=pootle_store.util.FUZZY))
    suggestions_q = lambda self, user: Q(
        suggestion__state=SuggestionStates.PENDING)
    user_suggestions_q = lambda self, user: Q(
        suggestion__state=SuggestionStates.PENDING,
        suggestion__user=user)
    user_suggestions_accepted_q = lambda self, user: Q(
        suggestion__state=SuggestionStates.ACCEPTED,
        suggestion__user=user)
    user_suggestions_rejected_q = lambda self, user: Q(
        suggestion__state=SuggestionStates.REJECTED,
        suggestion__user=user)
    user_submissions_q = lambda self, user: Q(
        suggestion__state=SubmissionTypes.EDIT_TYPES,
        suggestion__user=user)
    user_submissions_overwritten_q = lambda self, user: Q(
        Q(submission__submitter=user,
          submission__type__in=SubmissionTypes.EDIT_TYPES),
        ~Q(submitted_by=user))

    def __init__(self, qs):
        self.qs = qs

    def filter_checks(self, **kwa):
        checks = kwa.get("checks", None)
        category = kwa.get("category", None)
        if checks is not None:
            return self.qs.filter(
                qualitycheck__false_positive=False,
                qualitycheck__name__in=checks)
        elif category:
            return self.qs.filter(
                qualitycheck__false_positive=False,
                qualitycheck__category=get_category_id(category))
        return self.qs

    def filter_qs(self, **kwa):
        """Filter a qs with given kwa

        Calls self.filter methods in the order set in self.filters

        :return: (count, filtered_qs) where count is the total number
            of results before the filter_from_uid filter is applied and
            filtered_qs is the queryset after all filters have been applied.
        """
        for _filter in self.filters:
            self.qs = getattr(self, "filter_%s" % _filter)(**kwa)
        return self.qs

    @call_with("vfolder")
    def filter_vfolder(self, vfolder, **kwa):
        return self.qs.filter(vfolders=vfolder)

    @call_with("filter", "user")
    def filter_unit_filter(self, unit_filter, user, **kwa):
        query_attr = "%s_q" % unit_filter.replace("-", "_")
        query_method = getattr(self, query_attr, None)
        if query_method is not None:
            return self.qs.filter(query_method(user))
        return self.qs

    @call_with("modified_since")
    def filter_mtime(self, modified_since, **kwa):
        return self.qs.filter(
            submitted_on__gt=modified_since)

    @call_with("month")
    def filter_month(self, month, **kwa):
        [start, end] = month
        return self.qs.filter(
            submitted_on__gte=start,
            submitted_on__lte=end)

    @call_with("search", "sfields")
    def filter_text_search(self, search, sfields, **kwa):
        return UnitTextSearch(self.qs).search(
            search,
            sfields,
            "exact" in kwa.get("soptions", []))
