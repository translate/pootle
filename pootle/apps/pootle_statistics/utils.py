# -*- coding: utf-8 -*-
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.functional import cached_property

from pootle.core.decorators import persistent_property
from pootle.core.url_helpers import split_pootle_path
from pootle.core.utils.stats import TOP_CONTRIBUTORS_CHUNK_SIZE



class Contributors(object):

    def __init__(self, include_anon=False,
                 project_codes=None, language_codes=None,
                 since=None, until=None, sort_by="username"):
        self.include_anon = include_anon
        self.project_codes = project_codes
        self.language_codes = language_codes
        self.since = since
        self.until = until
        self.sort_by = sort_by

    @property
    def user_qs(self):
        User = get_user_model()
        if self.include_anon:
            return User.objects.exclude(username__in=["system", "default"])
        return User.objects.hide_meta()

    @property
    def user_filters(self):
        return Q(submission__gt=0)

    @property
    def site_filters(self):
        q = Q()
        tp_related = "submission__translation_project__"
        if self.project_codes:
            q = q & Q(
                **{"%sproject__code__in" % tp_related: self.project_codes})
        if self.language_codes:
            q = q & Q(
                **{"%slanguage__code__in" % tp_related: self.language_codes})
        return q

    @property
    def time_filters(self):
        q = Q()
        if self.since is not None:
            q = q & Q(submission__creation_time__gte=self.since)
        if self.until is not None:
            q = q & Q(submission__creation_time__lte=self.until)
        return q

    @property
    def filters(self):
        return self.user_filters & self.site_filters & self.time_filters

    def __iter__(self):
        for k in self.contributors:
            yield k

    def __getitem__(self, k):
        return self.contributors[k]

    def items(self):
        return self.contributors.items()

    @cached_property
    def contributors(self):
        qs = self.user_qs.filter(self.filters).annotate(
            contributions=Count("submission"))
        if self.sort_by == "contributions":
            qs = qs.order_by("-contributions", "username")
        else:
            qs = qs.order_by("username")
        return OrderedDict(
            [(user["username"], user)
             for user
             in qs.values("username", "full_name", "contributions", "email")])


class TopScorersDataTool(object):
    ns = 'pootle.top_scores'

    def __init__(self, context, pootle_path):
        self.context = context
        self.pootle_path = pootle_path

    @property
    def cache_key(self):
        return (
            "%s.%s"
            % (self.context.data_tool.cache_key,
               timezone.now().date()))

    @persistent_property
    def data(self):
        User = get_user_model()
        lang_code, proj_code = split_pootle_path(self.pootle_path)[:2]
        return User.top_scorers(
            project=proj_code,
            language=lang_code,
            limit=TOP_CONTRIBUTORS_CHUNK_SIZE + 1)
