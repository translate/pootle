# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.functional import cached_property
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

from pootle.i18n.gettext import ugettext as _
from pootle_misc.checks import get_qualitycheck_list


class ChecksDisplay(object):

    def __init__(self, context):
        self.context = context

    @property
    def check_schema(self):
        return get_qualitycheck_list(self.context)

    @cached_property
    def check_data(self):
        return self.context.data_tool.get_checks()

    @property
    def checks_by_category(self):
        _checks = []
        for check in self.check_schema:
            if check["code"] not in self.check_data:
                continue
            check["count"] = self.check_data[check["code"]]
            _checks.append(check)
        return _checks


class StatsDisplay(object):

    def __init__(self, context, stats=None):
        self.context = context
        self._stats = stats

    @cached_property
    def stat_data(self):
        if self._stats:
            return self._stats
        return self.context.data_tool.get_stats()

    @cached_property
    def stats(self):
        stats = self.stat_data
        self.add_children_info(stats)
        if stats.get("last_submission"):
            stats["last_submission"]["msg"] = (
                self.get_action_message(stats["last_submission"]))
        return stats

    def add_children_info(self, stats):
        for k, child in stats["children"].items():
            child["incomplete"] = child["total"] - child["translated"]
            child["untranslated"] = child["total"] - child["translated"]

    def get_action_message(self, action):
        msg = ""
        params = dict(
            user=format_html(
                u"<a href='{}' class='user-name'>{}</a>",
                action["profile_url"],
                escape(action["displayname"])),
            source=format_html(
                u"<a href='{}'>{}</a>",
                action["unit_url"],
                escape(action["unit_source"])))
        if action.get("check_name"):
            params["check"] = format_html(
                u"<a href='{}'>{}</a>",
                action["checks_url"],
                escape(action["check_display_name"]))
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
