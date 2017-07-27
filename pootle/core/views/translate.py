# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

from django.conf import settings

from pootle.core.url_helpers import get_previous_url
from pootle_app.models.permissions import check_permission
from pootle_checks.constants import CATEGORY_IDS, CHECK_NAMES
from pootle_checks.utils import get_qualitycheck_schema, get_qualitychecks
from pootle_misc.forms import make_search_form

from .base import PootleDetailView


class PootleTranslateView(PootleDetailView):
    template_name = "editor/main.html"
    page_name = "translate"
    view_name = ""

    @property
    def check_data(self):
        return self.object.data_tool.get_checks()

    @property
    def checks(self):
        check_data = self.check_data
        checks = get_qualitychecks()
        schema = {sc["code"]: sc for sc in get_qualitycheck_schema()}
        _checks = {}
        for check, checkid in checks.items():
            if check not in check_data:
                continue
            _checkid = schema[checkid]["name"]
            _checks[_checkid] = _checks.get(
                _checkid, dict(checks=[], title=schema[checkid]["title"]))
            _checks[_checkid]["checks"].append(
                dict(
                    code=check,
                    title=CHECK_NAMES[check],
                    count=check_data[check]))
        return OrderedDict(
            (k, _checks[k])
            for k in CATEGORY_IDS.keys()
            if _checks.get(k))

    @property
    def ctx_path(self):
        return self.pootle_path

    @property
    def vfolder_pk(self):
        return ""

    @property
    def display_vfolder_priority(self):
        return False

    @property
    def chunk_size(self):
        return self.request.user.get_unit_rows()

    def get_context_data(self, *args, **kwargs):
        ctx = super(PootleTranslateView, self).get_context_data(*args, **kwargs)
        ctx.update(
            {'page': self.page_name,
             'chunk_size': self.chunk_size,
             'current_vfolder_pk': self.vfolder_pk,
             'ctx_path': self.ctx_path,
             'display_priority': self.display_vfolder_priority,
             'checks': self.checks,
             'cantranslate': check_permission("translate", self.request),
             'cansuggest': check_permission("suggest", self.request),
             'canreview': check_permission("review", self.request),
             'search_form': make_search_form(request=self.request),
             'previous_url': get_previous_url(self.request),
             'POOTLE_MT_BACKENDS': settings.POOTLE_MT_BACKENDS,
             'AMAGAMA_URL': settings.AMAGAMA_URL,
             'AMAGAMA_SOURCE_LANGUAGES': settings.AMAGAMA_SOURCE_LANGUAGES,
             'editor_extends': self.template_extends})
        return ctx
