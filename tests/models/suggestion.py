# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.template.defaultfilters import escape

from pootle.core.delegate import review
from pootle_store.models import Suggestion


@pytest.mark.django_db
def test_hash(store0):
    """Tests that target hash changes when suggestion is modified"""
    unit = store0.units[0]
    suggestions = review.get(Suggestion)()

    suggestion, created_ = suggestions.add(unit, "gras")
    first_hash = suggestion.target_hash
    suggestion.target = "gras++"
    second_hash = suggestion.target_hash
    assert first_hash != second_hash


@pytest.mark.django_db
def test_accept_suggestion_with_comment_email_escaped(store0, mailoutbox):
    """Tests that email sent on accept suggestions with comment is escaped."""
    unit = store0.units[0]
    suggestion_review_cls = review.get(Suggestion)
    review_instance = suggestion_review_cls()

    suggestion, created_ = review_instance.add(unit, "gras")
    comment = "Very nice"
    suggestion_review_cls([suggestion]).accept(comment=comment)
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert comment in message.body

    suggestion, created_ = review_instance.add(unit, "gras++")
    comment = "Good job not translating <tag> tags"
    suggestion_review_cls([suggestion]).accept(comment=comment)
    assert len(mailoutbox) == 2
    message = mailoutbox[1]
    assert comment not in message.body
    assert escape(comment) in message.body


@pytest.mark.django_db
def test_reject_suggestion_with_comment_email_escaped(store0, mailoutbox):
    """Tests that email sent on reject suggestions with comment is escaped."""
    unit = store0.units[0]
    suggestion_review_cls = review.get(Suggestion)
    review_instance = suggestion_review_cls()

    suggestion, created_ = review_instance.add(unit, "gras")
    comment = "It is wrong"
    suggestion_review_cls([suggestion]).reject(comment=comment)
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert comment in message.body

    suggestion, created_ = review_instance.add(unit, "gras++")
    comment = "The <tag> must not be translated"
    suggestion_review_cls([suggestion]).reject(comment=comment)
    assert len(mailoutbox) == 2
    message = mailoutbox[1]
    assert comment not in message.body
    assert escape(comment) in message.body
