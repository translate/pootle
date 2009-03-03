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
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save

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
    input_width     = models.SmallIntegerField(default=40)
    input_height    = models.SmallIntegerField(default=5)
    languages       = models.ManyToManyField('Language', blank=True, related_name="user_languages")
    projects        = models.ManyToManyField('Project', blank=True)
    login_type      = models.CharField(max_length=50, default="hash")
    activation_code = models.CharField(max_length=255, default="")
    ui_lang         = models.ForeignKey('Language', blank=True, null=True,
                                        verbose_name=_("Interface language"))
    alt_src_langs   = models.ManyToManyField('Language', blank=True, related_name="user_alt_src_langs",
                                             verbose_name=_("Alternative source languages"))

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

def create_pootle_profile(sender, instance, **kwargs):
    """A post-save hook for the User model which ensures that it gets an
    associated PootleProfile."""
    try:
        profile = instance.get_profile()
    except PootleProfile.DoesNotExist:
        profile = PootleProfile(user=instance)
        profile.save()

post_save.connect(create_pootle_profile, sender=User)

def get_profile(user):
    """Return the PootleProfile associated with a user.

    This function is only necessary if 'user' could be an anonymous
    user.  If you know for certain that a user is logged in, then use
    the .get_profile() method on a user instead."""
    if user.is_authenticated():
        # Return the PootleProfile associated with authenticated users
        return user.get_profile()
    else:
        # Anonymous users get the PootleProfile associated with the 'nobody' user
        return User.objects.include_hidden().get(username='nobody').get_profile()

