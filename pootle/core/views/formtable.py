# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.template.loader import render_to_string


class Formtable(object):
    row_field = ""
    filters_template = ""
    actions_field = "actions"
    form_method = "POST"
    form_action = ""
    form_css_class = "formtable"

    def __init__(self, form, **kwargs):
        self.form = form
        self.kwargs = kwargs

    @property
    def form_attrs(self):
        return {
            "method": self.form_method,
            "class": self.form_css_class,
            "action": self.form_action}

    @property
    def table_attrs(self):
        return dict({"class": "pootle-table centered"})

    @property
    def actions(self):
        return self.form[self.actions_field]

    @property
    def columns(self):
        return self.kwargs.get("columns", ())

    @property
    def comment(self):
        return (
            self.form[self.form.comment_field]
            if self.form.comment_field
            else "")

    @property
    def sort_columns(self):
        return self.kwargs.get("sort_columns", ())

    @property
    def colspan(self):
        return len(self.columns)

    @property
    def page(self):
        return self.kwargs.get("page", ())

    @property
    def page_no(self):
        return self.form[self.form.page_field]

    @property
    def results_per_page(self):
        return self.form[self.form.per_page_field]

    @property
    def rows(self):
        return (
            self.form[self.row_field]
            if (self.row_field in self.form.fields
                and self.form.fields[self.row_field].choices)
            else [])

    @property
    def filters(self):
        return (
            render_to_string(
                self.filters_template,
                context=dict(formtable=self))
            if self.filters_template
            else "")

    @property
    def form_method(self):
        return self.kwargs.get("method", "POST")

    @property
    def select_all(self):
        return self.form[self.form.select_all_field]

    @property
    def table_css_class(self):
        return 'pootle-table centered'
