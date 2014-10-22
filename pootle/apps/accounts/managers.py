#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

__all__ = ('UserManager', )

from django.contrib.auth.models import BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """Pootle User manager.

    This manager hides the 'nobody' and 'default' users for normal
    queries, since they are special users. Code that needs access to these
    users should use the methods get_default_user and get_nobody_user.
    """
    def _create_user(self, username, email, password, is_superuser,
                     **extra_fields):
        """Creates and saves a User with the given username, email,
        password and superuser status.

        Adapted from the core ``auth.User`` model's ``UserManager``: we
        have no use for the ``is_staff`` field.
        """
        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email,
                          is_active=True, is_superuser=is_superuser,
                          last_login=now, date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        return self._create_user(username, email, password, False,
                                 **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        return self._create_user(username, email, password, True,
                                 **extra_fields)

    def get_default_user(self):
        return super(UserManager, self).get_queryset().get(username='default')

    def get_nobody_user(self):
        return super(UserManager, self).get_queryset().get(username='nobody')

    def get_system_user(self):
        return super(UserManager, self).get_queryset().get(username='system')

    def hide_defaults(self):
        return super(UserManager, self).get_queryset().exclude(
            username__in=('nobody', 'default', 'system')
        )
