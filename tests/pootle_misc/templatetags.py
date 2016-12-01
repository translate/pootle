# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.template import Context, Template


def _render_str(string, context=None):
    context = context or {}
    context = Context(context)
    return Template(string).render(context)


def test_templatetag_progress_bar():
    rendered = _render_str("{% load common_tags %}{% progress_bar 0 0 0 %}")
    assert "<span class=\'value translated\'>0%</span>" in rendered
    assert '<span class=\'value fuzzy\'>0%</span>' in rendered
    assert '<span class=\'value untranslated\'>0%</span>' in rendered
    rendered = _render_str(
        "{% load common_tags %}{% progress_bar 123 23 73 %}")
    assert "<span class=\'value translated\'>59.3%</span>" in rendered
    assert "<span class=\'value fuzzy\'>18.7%</span>" in rendered
    assert "<span class=\'value untranslated\'>22.0%</span>" in rendered
    assert '<td class="translated" style="width: 59.3%">' in rendered
    assert '<td class="fuzzy" style="width: 18.7%">' in rendered
    assert '<td class="untranslated" style="width: 22.0%">' in rendered
