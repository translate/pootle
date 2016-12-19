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

from pootle.i18n import formatter
from pootle.i18n.gettext import ugettext as _
from pootle.local.dates import timesince
from pootle_misc.checks import get_qualitycheck_list


class ActionDisplay(object):

    def __init__(self, action):
        self.action = action

    @property
    def since(self):
        return timesince(self.action["mtime"])

    @property
    def check_name(self):
        return self.action.get("check_name")

    @property
    def checks_url(self):
        return self.action.get("checks_url")

    @property
    def check_display_name(self):
        return escape(self.action["check_display_name"])

    @property
    def display_name(self):
        return escape(self.action["displayname"])

    @property
    def profile_url(self):
        return self.action["profile_url"]

    @property
    def unit_url(self):
        return self.action.get("unit_url")

    @property
    def unit_source(self):
        return self.action.get("unit_source")

    @property
    def params(self):
        params = dict(
            user=self.formatted_user,
            source=self.formatted_source)
        if self.check_name:
            params["check"] = format_html(
                u"<a href='{}'>{}</a>",
                self.checks_url,
                self.check_display_name)
        return params

    @property
    def formatted_user(self):
        return format_html(
            u"<a href='{}' class='user-name'>{}</a>",
            self.profile_url,
            self.display_name)

    @property
    def formatted_source(self):
        return format_html(
            u"<a href='{}'>{}</a>",
            self.unit_url,
            self.unit_source)

    @property
    def action_type(self):
        return self.action["type"]

    @property
    def translation_action_type(self):
        return self.action.get("translation_action_type")

    @property
    def message(self):
        msg = ""
        params = self.params
        if (self.action_type == 2):
            msg = _('%(user)s removed translation for %(source)s', params)
        if (self.action_type == 3):
            msg = _('%(user)s accepted suggestion for %(source)s', params)
        if (self.action_type == 4):
            msg = _('%(user)s uploaded file', params)
        if (self.action_type == 6):
            msg = _('%(user)s muted %(check)s for %(source)s', params)
        if (self.action_type == 7):
            msg = _('%(user)s unmuted %(check)s for %(source)s', params)
        if (self.action_type == 8):
            msg = _('%(user)s added suggestion for %(source)s', params)
        if (self.action_type == 9):
            msg = _('%(user)s rejected suggestion for %(source)s', params)
        if (self.action_type in [1, 5]):
            if self.translation_action_type == 0:
                msg = _('%(user)s translated %(source)s', params)
            if self.translation_action_type == 1:
                msg = _('%(user)s edited %(source)s', params)
            if self.translation_action_type == 2:
                msg = _('%(user)s pre-translated %(source)s', params)
            if self.translation_action_type == 3:
                msg = _('%(user)s removed translation for %(source)s', params)
            if self.translation_action_type == 4:
                msg = _('%(user)s reviewed %(source)s', params)
            if self.translation_action_type == 5:
                msg = _('%(user)s marked as needs work %(source)s', params)
        return mark_safe(msg)


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
            check["count_display"] = formatter.number(check["count"])
            _checks.append(check)
        return _checks


class StatsDisplay(object):

    def __init__(self, context, stats=None):
        self.context = context
        self._stats = stats

    @staticmethod
    def make_display_stat(d, keys=["total", "critical", "incomplete",
                                   "suggestions", "fuzzy", "untranslated"]):
        assert isinstance(d, dict)
        for k in keys:
            if k in d:
                d[k + '_display'] = formatter.number(d[k])

    @cached_property
    def stat_data(self):
        if self._stats is not None:
            return self._stats
        return self.context.data_tool.get_stats()

    @cached_property
    def stats(self):
        stats = self.stat_data
        self.add_children_info(stats)
        self.make_display_stat(stats)
        if stats.get("last_submission"):
            stats["last_submission"]["msg"] = (
                self.get_action_message(stats["last_submission"]))
        return stats

    def add_children_info(self, stats):
        for k, child in stats["children"].items():
            child["incomplete"] = child["total"] - child["translated"]
            child["untranslated"] = child["total"] - child["translated"]
            self.make_display_stat(child)

    def get_action_message(self, action):
        return ActionDisplay(action).message
