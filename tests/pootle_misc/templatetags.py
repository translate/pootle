# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.template import Context, Template

from pootle.core.delegate import scores


def _render_str(string, context=None):
    context = context or {}
    context = Context(context)
    return Template(string).render(context)


def test_templatetag_progress_bar():
    rendered = _render_str("{% load common_tags %}{% progress_bar 0 0 0 %}")
    assert "<span class='legend translated'></span>0%" in rendered
    assert "<span class='legend fuzzy'></span>0%" in rendered
    assert "<span class='legend untranslated'></span>0%" in rendered
    rendered = _render_str(
        "{% load common_tags %}{% progress_bar 123 23 73 %}")
    assert "<span class='legend translated'></span>59.3%" in rendered
    assert "<span class='legend fuzzy'></span>18.7%" in rendered
    assert "<span class='legend untranslated'></span>22.0%" in rendered
    assert '<td class="translated" style="width: 59.3%">' in rendered
    assert '<td class="fuzzy" style="width: 18.7%">' in rendered
    assert '<td class="untranslated" style="width: 22.0%">' in rendered


@pytest.mark.django_db
def test_inclusion_tag_top_scorers(project_set, member):
    score_data = scores.get(project_set.__class__)(project_set)
    rendered = _render_str(
        "{% load common_tags %}{% top_scorers user score_data %}",
        context=dict(
            user=member,
            score_data=score_data.display()))
    top_scorer = list(score_data.display())[0]
    assert top_scorer["public_total_score"] in rendered
    assert top_scorer["user"].email_hash in rendered
