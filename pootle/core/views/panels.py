# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.template import loader
from django.utils.functional import cached_property

from pootle.core.decorators import persistent_property


class Panel(object):
    template_name = None
    panel_name = None

    def __init__(self, view):
        self.view = view

    def get_context_data(self):
        return {}

    def render(self):
        if not self.template_name:
            return ""
        return loader.render_to_string(
            self.template_name, context=self.get_context_data())

    @cached_property
    def cache_key(self):
        return (
            "panel.%s.%s"
            % (self.panel_name, self.view.cache_key))

    @persistent_property
    def content(self):
        return self.render()


class TablePanel(Panel):
    template_name = "browser/includes/table_panel.html"
    table = None

    def get_context_data(self):
        return dict(table=self.table)
