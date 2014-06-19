#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.contrib.auth.models import User, UserManager, AnonymousUser
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.utils.html import simple_email_re as email_re
from django.utils.translation import ugettext_lazy as _


class PootleProfile(models.Model):

    # This is the only required field.
    user = models.OneToOneField(settings.AUTH_USER_MODEL, unique=True, db_index=True)

    class Meta:
        db_table = 'pootle_app_pootleprofile'

    ############################ Properties ###################################

    ############################ Methods ######################################

    def __unicode__(self):
        username = self.user.username

        if email_re.match(username):
            username = username.strip().rsplit('@', 1)[0]

        return username

    def get_absolute_url(self):
        return reverse('profiles_profile_detail', args=[self.user.username])

    def gravatar_url(self, size=80):
        return self.user.gravatar_url(size)


################################ Signal handlers ##############################

def create_pootle_profile(sender, instance, **kwargs):
    """A post-save hook for the User model which ensures that it gets an
    associated PootleProfile.
    """
    try:
        profile = instance.get_profile()
    except PootleProfile.DoesNotExist:
        profile = PootleProfile(user=instance)
        profile.save()

post_save.connect(create_pootle_profile, sender=User)
