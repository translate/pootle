# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.template.loader import render_to_string


class FormTable(object):
    row_field = ""
    header_template = ""

    def __init__(self, form, **kwargs):
        self.form = form
        self.kwargs = kwargs

    @property
    def columns(self):
        return self.kwargs.get("columns", ())

    @property
    def page(self):
        return self.kwargs.get("page", ())

    @property
    def rows(self):
        return self.form[self.row_field]

    @property
    def header_rows(self):
        if self.header_template:
            return render_to_string(
                self.header_template,
                dict(form=self.form, page=self.page))
