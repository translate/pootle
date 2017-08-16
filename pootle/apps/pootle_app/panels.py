# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re

from django.utils.safestring import mark_safe

from pootle.core.browser import get_table_headings
from pootle.core.decorators import persistent_property
from pootle.core.views.panels import TablePanel
from pootle.i18n.dates import timesince

from .apps import PootleConfig


class ChildrenPanel(TablePanel):
    ns = "pootle.app"
    sw_version = PootleConfig.version
    panel_name = "children"
    _table_fields = (
        'name', 'progress', 'activity',
        'total', 'need-translation',
        'suggestions', 'critical')

    @property
    def table_fields(self):
        fields = (
            ("name", "total")
            if self.view.is_templates_context
            else self._table_fields)
        if self.view.has_admin_access:
            fields += ('last-updated', )
        return fields

    @property
    def children(self):
        return self.view.object_children

    @property
    def table(self):
        if self.view.object_children:
            return {
                'id': self.view.view_name,
                'fields': self.table_fields,
                'headings': get_table_headings(self.table_fields),
                'rows': self.view.object_children}

    @persistent_property
    def _content(self):
        return self.render()

    @property
    def child_update_times(self):
        _times = {}
        for child in self.children:
            if not child.get("stats"):
                continue
            last_created_unit = (
                timesince(
                    child["stats"]["last_created_unit"]["creation_time"],
                    locale=self.view.request_lang)
                if child["stats"].get("last_created_unit")
                else None)
            last_submission = (
                timesince(
                    child["stats"]["last_submission"]["mtime"],
                    locale=self.view.request_lang)
                if child["stats"].get("last_submission")
                else None)
            _times[child["code"]] = (last_submission, last_created_unit)
        return _times

    @property
    def content(self):
        return self.update_times(self._content)

    def get_context_data(self):
        return dict(
            table=self.table,
            can_translate=self.view.can_translate)

    def update_times(self, content):
        times = {}
        update_times = self.child_update_times.items()
        for name, (last_submission, last_created_unit) in update_times:
            if last_submission:
                times[
                    "_XXX_LAST_SUBMISSION_%s_LAST_SUBMISSION_XXX_"
                    % name] = last_submission
            if last_created_unit:
                times[
                    "_XXX_LAST_CREATED_%s_LAST_CREATED_XXX_"
                    % name] = last_created_unit
        if times:
            regex = re.compile("(%s)" % "|".join(map(re.escape, times.keys())))
            return mark_safe(
                regex.sub(
                    lambda match: times[match.string[match.start():match.end()]],
                    content))
        return content
