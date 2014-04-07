#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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

from django.db.models import F, Manager, Q


class PageManager(Manager):

    def live(self, user=None, **kwargs):
        """Filters active (live) pages.

        :param user: Current active user. If omitted or the user doesn't
            have administration privileges, only active pages will be
            returned.
        """
        if user and user.is_superuser:
            return self.get_queryset()
        else:
            return self.get_queryset().filter(active=True)

    def pending_user_agreement(self, user, **kwargs):
        """Filters active pages where the given `user` has pending
        agreements.
        """
        # FIXME: This should be a method exclusive to a LegalPage manager
        return self.live().filter(
            Q(agreement__user=user,
              modified_on__gt=F('agreement__agreed_on')) |
            ~Q(agreement__user=user)
        )
