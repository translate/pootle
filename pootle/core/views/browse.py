# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from pootle.core.browser import get_table_headings
from pootle.core.helpers import (SIDEBAR_COOKIE_NAME,
                                 get_sidebar_announcements_context)
from pootle.core.url_helpers import split_pootle_path
from pootle.core.utils.stats import (TOP_CONTRIBUTORS_CHUNK_SIZE,
                                     get_top_scorers_data,
                                     get_translation_states)
from pootle.i18n.gettext import ugettext as _
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
        return self.object.data_tool.get_stats(user=self.request.user)

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
        return filter(lambda item: item.get('is_disabled'), self.items)

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

    def get_action_message(self, action):
        params = dict(
            user=action["displayname"],
            source=(
                "<a href='%s'>%s</a>"
                % (action["unit_url"], action["unit_source"])),
            check=action.get("check_name"))
        if (action["type"] == 2):
            msg = _('%(user)s removed translation for %(source)s', params)
        if (action["type"] == 3):
            msg = _('%(user)s accepted suggestion for %(source)s', params)
        if (action["type"] == 4):
            msg = _('%(user)s uploaded file', params)
        if (action["type"] == 6):
            msg = _('%(user)s muted %(check)s for %(source)s', params)
        if (action["type"] == 7):
            msg = _('%(user)s unmuted %(check)s for %(source)s', params)
        if (action["type"] == 8):
            msg = _('%(user)s added suggestion for %(source)s', params)
        if (action["type"] == 9):
            msg = _('%(user)s rejected suggestion for %(source)s', params)
        if (action["type"] in [1, 5]):
            if action.get("translation_action_type") == 0:
                msg = _('%(user)s translated %(source)s', params)
            if action.get("translation_action_type") == 1:
                msg = _('%(user)s edited %(source)s', params)
            if action.get("translation_action_type") == 2:
                msg = _('%(user)s pre-translated %(source)s', params)
            if action.get("translation_action_type") == 3:
                msg = _('%(user)s removed translation for %(source)s', params)
            if action.get("translation_action_type") == 4:
                msg = _('%(user)s reviewed %(source)s', params)
            if action.get("translation_action_type") == 5:
                msg = _('%(user)s marked as needs work %(source)s', params)
        return mark_safe(msg)

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
        top_scorer_data = get_top_scorers_data(
            top_scorers,
            TOP_CONTRIBUTORS_CHUNK_SIZE)

        stats = self.stats
        table = self.table
        table_items = table["items"]

        from natural.date import duration
        for item in table_items:
            if item["code"] in stats["children"]:
                item["stats"] = stats["children"][item["code"]]
            elif item["title"] in stats["children"]:
                item["stats"] = stats["children"][item["title"]]
            if item["stats"].get("lastaction"):
                item["stats"]["lastaction"] = duration(
                    item["stats"]["lastaction"]["mtime"])
                item["stats"]["incomplete"] = (
                    item["stats"]["total"] - item["stats"]["translated"])
                dt = duration(item["stats"]["last_submission"]["mtime"])
                grav = (
                    'https://secure.gravatar.com/avatar/%s?s=%d&d=mm'
                    % (item["stats"]["last_submission"]["email"], 20))
                item["stats"]["lastupdated"] = dict(
                    name=item["stats"]["last_submission"]["displayname"],
                    at=dt,
                    grav=grav,
                    profile_url=item["stats"]["last_submission"]["profile_url"])
        del stats["children"]
        # table["items"] = table["items"][:5]
        states = get_translation_states(self.object)
        _stats = {}
        for state in states:
            if state["state"] == "untranslated":
                _stats[state["state"]] = state["count"] = (
                    stats["total"] - stats["fuzzy"] - stats["translated"])
            else:
                _stats[state["state"]] = state["count"] = stats[state["state"]]
            state["percent"] = round(
                (float(state["count"]) / stats["total"]) * 100, 1)
        _stats["suggestions"] = stats["suggestions"]
        _stats["critical"] = stats["critical"]
        _stats["incomplete"] = stats["total"] - stats["translated"]
        _stats["lastaction"] = dict(
            msg=self.get_action_message(stats["lastaction"]),
            name=stats["lastaction"]["displayname"],
            at=duration(stats["lastaction"]["mtime"]),
            grav=grav,
            profile_url=stats["lastaction"]["profile_url"])
        if stats["lastupdated"]:
            _stats["lastupdated"] = dict(
                url=stats["lastupdated"]["unit_url"],
                source=stats["lastupdated"]["unit_source"],
                at=duration(stats["lastupdated"]["creation_time"]))
        checks = get_qualitycheck_list(self.object)
        check_data = self.object.data_tool.get_checks()
        _checks = []
        for check in checks:
            if check["code"] not in check_data:
                continue
            check["count"] = check_data[check["code"]]
            _checks.append(check)
        ctx.update(
            {'page': 'browse',
             'translation_states': states,
             'stats': _stats,
             'checks': _checks,
             'can_translate': can_translate,
             'can_translate_stats': can_translate_stats,
             'url_action_continue': url_action_continue,
             'url_action_fixcritical': url_action_fixcritical,
             'url_action_review': url_action_review,
             'url_action_view_all': url_action_view_all,
             'top_scorers': top_scorers,
             'top_scorers_data': top_scorer_data,
             'table': table,
             'is_store': self.is_store,
             'browser_extends': self.template_extends})

        return ctx
