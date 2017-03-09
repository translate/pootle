# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import datetime

from django import forms
from django.contrib.auth import get_user_model
from django.utils.functional import cached_property

from django_comments.forms import CommentForm as DjCommentForm

from pootle.core.utils.timezone import make_aware

from .delegate import comment_should_not_be_saved
from .exceptions import CommentNotSaved
from .signals import comment_was_saved


User = get_user_model()


class RequestUserFormMixin(object):
    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("request_user")
        super(RequestUserFormMixin, self).__init__(*args, **kwargs)
        for k in ["user", "name", "email"]:
            if k in self.fields:
                self.fields[k].required = False

    def clean_user(self):
        return self.request_user


class CommentForm(RequestUserFormMixin, DjCommentForm):
    user = forms.ModelChoiceField(queryset=User.objects.all())

    def __init__(self, target_object, data=None, *args, **kwargs):
        d = data
        if data and not getattr(data, '_mutable', True):
            d = data.copy()
            d["object_pk"] = str(target_object.pk)
            d["content_type"] = str(target_object._meta)

        super(CommentForm, self).__init__(target_object, d, *args, **kwargs)

    @cached_property
    def comment(self):
        return self.get_comment_object()

    def clean(self):
        super(CommentForm, self).clean()
        should_not_save = comment_should_not_be_saved.get(
            self.target_object.__class__,
            instance=self.target_object,
            comment=self.comment)
        if should_not_save:
            raise CommentNotSaved(dict(comment=should_not_save))

    def save(self):
        comment = self.comment
        comment.user = self.cleaned_data["user"]
        comment.submit_date = make_aware(datetime.now())
        comment.save()
        comment_was_saved.send(
            sender=comment.__class__,
            comment=comment)


class UnsecuredCommentForm(CommentForm):

    def __init__(self, target_object, data=None, *args, **kwargs):
        super(UnsecuredCommentForm, self).__init__(
            target_object, data, *args, **kwargs)
        self.data.update(self.generate_security_data())
