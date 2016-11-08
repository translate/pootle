# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings

from pootle.core.url_helpers import get_previous_url
from pootle_app.models.permissions import check_permission
from pootle_misc.checks import get_qualitycheck_schema
from pootle_misc.forms import make_search_form

from .base import PootleDetailView


class PootleTranslateView(PootleDetailView):
    template_name = "editor/main.html"

    @property
    def ctx_path(self):
        return self.pootle_path

    @property
    def vfolder_pk(self):
        return ""

    @property
    def display_vfolder_priority(self):
        return False

    def get_context_data(self, *args, **kwargs):
        from pootle_misc.checks import get_qualitychecks

        ctx = super(PootleTranslateView, self).get_context_data(*args, **kwargs)
        checks = get_qualitychecks()
        schema = {sc["code"]: sc for sc in get_qualitycheck_schema()}
        check_data = self.object.data_tool.get_checks()
        _checks = {}
        for check, cat in checks.items():
            if check not in check_data:
                continue
            _checks[cat] = _checks.get(
                cat, dict(checks=[], title=schema[cat]["title"]))
            _checks[cat]["checks"].append(
                dict(code=check, count=check_data[check]))
        ctx.update(
            {'page': 'translate',
             'current_vfolder_pk': self.vfolder_pk,
             'ctx_path': self.ctx_path,
             'display_priority': self.display_vfolder_priority,
             'checks': _checks,
             'cantranslate': check_permission("translate", self.request),
             'cansuggest': check_permission("suggest", self.request),
             'canreview': check_permission("review", self.request),
             'search_form': make_search_form(request=self.request),
             'previous_url': get_previous_url(self.request),
             'POOTLE_MT_BACKENDS': settings.POOTLE_MT_BACKENDS,
             'AMAGAMA_URL': settings.AMAGAMA_URL,
             'editor_extends': self.template_extends})
        return ctx
