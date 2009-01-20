#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.db import models
from django.contrib.auth.models import User, UserManager, AnonymousUser
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

class PootleUserManager(UserManager):
    """A manager class which is meant to replace the manager class for the User model. This manager
    hides the 'nobody' and 'default' users for normal queries, since they are special users. Code
    that needs access to these users should use the methods get_default_user and get_nobody_user."""
    def get_query_set(self):
        return super(PootleUserManager, self).get_query_set().exclude(username__in=('nobody', 'default'))

    def get_default_user(self):
        return super(PootleUserManager, self).get_query_set().select_related(depth=1).get(username='default')

    def get_nobody_user(self):
        return super(PootleUserManager, self).get_query_set().select_related(depth=1).get(username='nobody')

    def include_hidden(self):
        return super(PootleUserManager, self).get_query_set()

# Since PootleUserManager has no state, we can just replace the User manager's class with PootleUserManager
# to get the desired functionality.
User.objects.__class__ = PootleUserManager

class PootleProfile(models.Model):
    # This is the only required field
    user = models.ForeignKey(User, unique=True)

    translate_rows  = models.SmallIntegerField(default=7)
    view_rows       = models.SmallIntegerField(default=10)
    input_width     = models.SmallIntegerField(default=10)
    input_height    = models.SmallIntegerField(default=1)
    languages       = models.ManyToManyField('Language', blank=True, related_name="user_languages")
    projects        = models.ManyToManyField('Project', blank=True)
    login_type      = models.CharField(max_length=50, default="hash")
    activation_code = models.CharField(max_length=255, default="")
    ui_lang         = models.ForeignKey('Language', blank=True, null=True,
                                        verbose_name=_("Interface language"))
    alt_src_langs   = models.ManyToManyField('Language', blank=True, related_name="user_alt_src_langs",
                                             verbose_name=_("Alternative source languages"))

    def _get_suggestions(self, status):
        from Pootle.pootle_app.models import Suggestion
        return Suggestion.objects.filter(suggester=self).filter(review_status=status)

    suggestions_accepted = property(lambda self: self._get_suggestions("accepted").all())
    suggestions_rejected = property(lambda self: self._get_suggestions("rejected").all())
    suggestions_pending  = property(lambda self: self._get_suggestions("pending").all())
    suggestions_reviewed = property(lambda self: self._get_suggestions("reviewed").all())

    suggestions_accepted_count = property(lambda self: self._get_suggestions("accepted").count())
    suggestions_rejected_count = property(lambda self: self._get_suggestions("rejected").count())
    suggestions_pending_count  = property(lambda self: self._get_suggestions("pending").count())
    suggestions_reviewed_count = property(lambda self: self._get_suggestions("reviewed").count())

    submissions_count = property(lambda self: self.submission_set.count())

    def _get_status(self):
        return "Foo"

    status = property(_get_status)

    isopen = property(lambda self: True)

    def _get_pootle_user(self):
        if self.user_id is not None:
            return self.user
        else:
            return AnonymousUser()

    pootle_user = property(_get_pootle_user)

    def get_messages(self):
        # TODO: This should be a DB column
        return []


def make_default_profile(user_model):
    from Pootle.pootle_app.models import Language
    profile = PootleProfile()
    if not user_model.is_anonymous():
        profile.user_id = user_model.id
        # We have to associate the newly created profile
        # with the User model (if User is a logged in user
        # and not an anonymous user). We must also save the 
        # profile, since otherwise a future call to 'get_profile'
        # below will return a new profile (and not the one
        # we just created).
        profile.save()
    return profile

def get_profile(user_model):
    if user_model.is_authenticated():
        try:
            return user_model.get_profile()
        except PootleProfile.DoesNotExist, _e:
            # A registered user which current has no profile info
            return make_default_profile(user_model)
    else:
        # An anonymous user which has no profile
        return make_default_profile(user_model)

def make_pootle_user(**kwargs):
    user = User(**kwargs)
    user.save()
    make_default_profile(user)
    return user

def save_user(user):
    user.save()
    get_profile(user).save()
