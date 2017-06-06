# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import time
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.functional import cached_property

from django_comments.forms import CommentForm as DjCommentForm

from pootle.core.utils.timezone import make_aware

from .delegate import comment_should_not_be_saved
from .exceptions import CommentNotSaved
from .signals import comment_was_saved


User = get_user_model()


class CommentForm(DjCommentForm):

    @cached_property
    def comment(self):
        try:
            return self.get_comment_object()
        except ValueError as e:
            raise ValidationError(e)

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
        comment.submit_date = make_aware(datetime.now())
        comment.save()
        comment_was_saved.send(
            sender=comment.__class__,
            comment=comment)


class UnsecuredCommentForm(CommentForm):
    """This form does not check for security hash, and uses the view's
    request.user
    """

    def __init__(self, target_object, request_user, data=None, *args, **kwargs):
        self.request_user = request_user
        self.timestamp = str(int(time.time()))
        mangled_fields = [
            "name", "timestamp", "object_pk", "security_hash",
            "content_type", "email"]
        super(UnsecuredCommentForm, self).__init__(
            target_object, data, *args, **kwargs)
        for field in mangled_fields:
            self.fields[field].required = False

    def clean_email(self):
        return self.request_user.email

    def clean_name(self):
        return self.request_user.display_name

    def clean_content_type(self):
        return str(self.target_object._meta)

    def clean_object_pk(self):
        return str(self.target_object._get_pk_val())

    def clean_timestamp(self):
        return self.timestamp

    def clean_security_hash(self):
        return self.initial_security_hash(self.timestamp)

    def save(self):
        comment = self.comment
        comment.user = self.request_user
        comment.submit_date = make_aware(datetime.now())
        comment.save()
        comment_was_saved.send(
            sender=comment.__class__,
            comment=comment)
