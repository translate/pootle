# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.functional import cached_property

from pootle.core.browser import get_table_headings
from pootle.core.helpers import (SIDEBAR_COOKIE_NAME,
                                 get_sidebar_announcements_context)
from pootle.core.url_helpers import split_pootle_path
from pootle.core.utils.stats import (TOP_CONTRIBUTORS_CHUNK_SIZE,
                                     get_top_scorers_data,
                                     get_translation_states)
from pootle_misc.checks import get_qualitycheck_list

from .base import PootleDetailView


class PootleBrowseView(PootleDetailView):
    template_name = 'browser/index.html'
    table_id = None
    table_fields = None
    items = None
    is_store = False

    @property
    def path(self):
        return self.request.path

    @property
    def stats(self):
        return self.object.get_stats()

    @property
    def has_vfolders(self):
        return False

    @cached_property
    def cookie_data(self):
        ctx_, cookie_data = self.sidebar_announcements
        return cookie_data

    @property
    def sidebar_announcements(self):
        return get_sidebar_announcements_context(
            self.request,
            (self.object, ))

    @property
    def disabled_items(self):
        return filter(lambda item: item['is_disabled'], self.items)

    @property
    def table(self):
        if self.table_id and self.table_fields and self.items:
            return {
                'id': self.table_id,
                'fields': self.table_fields,
                'headings': get_table_headings(self.table_fields),
                'items': self.items,
                'disabled_items': self.disabled_items,
            }

    def get(self, *args, **kwargs):
        response = super(PootleBrowseView, self).get(*args, **kwargs)
        if self.cookie_data:
            response.set_cookie(SIDEBAR_COOKIE_NAME, self.cookie_data)
        return response

    def get_context_data(self, *args, **kwargs):
        filters = {}
        can_translate = False
        can_translate_stats = False
        User = get_user_model()
        if self.has_vfolders:
            filters['sort'] = 'priority'

        if self.request.user.is_superuser or self.language:
            can_translate = True
            can_translate_stats = True
            url_action_continue = self.object.get_translate_url(
                state='incomplete',
                **filters)
            url_action_fixcritical = self.object.get_critical_url(
                **filters)
            url_action_review = self.object.get_translate_url(
                state='suggestions',
                **filters)
            url_action_view_all = self.object.get_translate_url(state='all')
        else:
            if self.project:
                can_translate = True
            url_action_continue = None
            url_action_fixcritical = None
            url_action_review = None
            url_action_view_all = None
        ctx, cookie_data_ = self.sidebar_announcements
        ctx.update(super(PootleBrowseView, self).get_context_data(*args, **kwargs))

        lang_code, proj_code = split_pootle_path(self.pootle_path)[:2]
        top_scorers = User.top_scorers(
            project=proj_code,
            language=lang_code,
            limit=TOP_CONTRIBUTORS_CHUNK_SIZE + 1,
        )

        ctx.update(
            {'page': 'browse',
             'stats_refresh_attempts_count':
                 settings.POOTLE_STATS_REFRESH_ATTEMPTS_COUNT,
             'stats': self.stats,
             'translation_states': get_translation_states(self.object),
             'checks': get_qualitycheck_list(self.object),
             'can_translate': can_translate,
             'can_translate_stats': can_translate_stats,
             'url_action_continue': url_action_continue,
             'url_action_fixcritical': url_action_fixcritical,
             'url_action_review': url_action_review,
             'url_action_view_all': url_action_view_all,
             'table': self.table,
             'is_store': self.is_store,
             'top_scorers': top_scorers,
             'top_scorers_data': get_top_scorers_data(
                 top_scorers,
                 TOP_CONTRIBUTORS_CHUNK_SIZE),
             'browser_extends': self.template_extends})

        return ctx
