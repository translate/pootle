#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models import F, Manager


class PageManager(Manager):

    def live(self, user=None, **kwargs):
        """Filters active (live) pages.

        :param user: Current active user. If omitted or the user doesn't
            have administration privileges, only active pages will be
            returned.
        """
        if user is not None and user.is_superuser:
            return self.get_queryset()

        return self.get_queryset().filter(active=True)

    def pending_user_agreement(self, user, **kwargs):
        """Filters active pages where the given `user` has pending
        agreements.
        """
        # FIXME: This should be a method exclusive to a LegalPage manager
        return self.live().exclude(
            agreement__user=user,
            modified_on__lt=F('agreement__agreed_on'),
        ).distinct()
