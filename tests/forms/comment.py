# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.plugin import getter
from pootle_comment.delegate import comment_should_not_be_saved
from pootle_comment.models import Comment
from pootle_comment.forms import CommentForm, UnsecuredCommentForm

from pootle_store.models import Unit


@pytest.mark.django_db
def test_comment_form():
    # must be bound to an object
    with pytest.raises(TypeError):
        CommentForm()
    with pytest.raises(AttributeError):
        CommentForm("some string")
    unit = Unit.objects.first()
    form = CommentForm(unit)
    secdata = form.generate_security_data()
    assert secdata["object_pk"] == str(unit.pk)
    assert secdata["content_type"] == str(unit._meta)
    assert "timestamp" in secdata
    assert "security_hash" in secdata


@pytest.mark.django_db
def test_comment_form_post(admin):
    unit = Unit.objects.first()
    form = CommentForm(unit)
    kwargs = dict(
        comment="Foo!",
        object_pk=str(unit.pk),
        content_type=str(unit._meta),
        name=admin.display_name,
        email=admin.email,
        timestamp=form.initial.get("timestamp"),
        security_hash=form.initial.get("security_hash"))
    post_form = CommentForm(unit, kwargs)
    if post_form.is_valid():
        post_form.save()
    comment = Comment.objects.first()
    assert comment.comment == "Foo!"
    assert ".".join(comment.content_type.natural_key()) == str(unit._meta)
    assert comment.object_pk == str(unit.pk)
    assert comment.user is None
    assert comment.name == admin.display_name
    assert comment.email == admin.email


@pytest.mark.django_db
def test_unsecured_comment_form_post(admin):
    unit = Unit.objects.first()
    kwargs = dict(
        data=dict(comment="Foo!"),
        target_object=unit,
        request_user=admin)
    post_form = UnsecuredCommentForm(**kwargs)
    if post_form.is_valid():
        post_form.save()
    comment = Comment.objects.first()
    assert comment.comment == "Foo!"
    assert ".".join(comment.content_type.natural_key()) == str(unit._meta)
    assert comment.object_pk == str(unit.pk)
    assert comment.user == admin
    assert comment.name == admin.display_name
    assert comment.email == admin.email


@pytest.mark.django_db
def test_unsecured_comment_form_should_save(admin):
    unit = Unit.objects.first()
    BAD_WORDS = ["google", "oracle", "apple", "microsoft"]

    @getter(comment_should_not_be_saved, sender=Unit)
    def comment_handler(sender, **kwargs):
        for bad_word in BAD_WORDS:
            if bad_word in kwargs["comment"].comment:
                return "You cant say '%s' round here" % bad_word

    kwargs = dict(
        data=dict(comment="google is foo!"),
        target_object=unit,
        request_user=admin)
    post_form = UnsecuredCommentForm(**kwargs)
    assert not post_form.is_valid()
    assert post_form.errors["comment"] == ["You cant say 'google' round here"]
    kwargs = dict(
        data=dict(
            comment="You can say linux though, or gnu/linux if you prefer"),
        target_object=unit,
        request_user=admin)
    post_form = UnsecuredCommentForm(**kwargs)
    assert post_form.is_valid()
