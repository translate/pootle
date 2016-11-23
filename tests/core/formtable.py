# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.template import Context, Template

from pootle.core.views.formtable import Formtable

from .forms import DummyFormtableForm


def test_formtable():

    form = DummyFormtableForm()
    formtable = Formtable(form)

    assert formtable.actions_field == "actions"
    assert formtable.actions == form[formtable.actions_field]
    assert formtable.columns == ()
    assert formtable.colspan == 0
    assert formtable.filters == ""
    assert formtable.filters_template == ""
    assert formtable.form == form
    assert formtable.form_action == ""
    assert formtable.form_method == "POST"
    assert formtable.form_css_class == "formtable"
    assert formtable.form_attrs == {
        "action": formtable.form_action,
        "method": formtable.form_method,
        "class": formtable.form_css_class}
    assert formtable.kwargs == {}
    assert formtable.page == ()
    assert formtable.row_field == ""
    assert formtable.table_css_class == 'pootle-table centered'
    assert formtable.table_attrs == {'class': formtable.table_css_class}
    assert formtable.rows == []
    assert formtable.sort_columns == ()


def _render_template(string, context=None):
    context = context or {}
    context = Context(context)
    return Template(string).render(context=context)


def test_formtable_inclusion_tag():

    form = DummyFormtableForm()
    formtable = Formtable(form)
    rendered = _render_template(
        "{% load core %}{% formtable formtable %}",
        context=dict(formtable=formtable))
    assert rendered.strip("\n").startswith('<form')
    assert 'class="formtable"' in rendered
    assert rendered.strip("\n").endswith('</form>')
