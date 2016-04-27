# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models import Manager


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

    def has_pending_agreement(self, user):
        agreements = self.pending_user_agreement(user)
        return len(list(agreements)) > 0

    def pending_user_agreement(self, user, **kwargs):
        """Filters active pages where the given `user` has pending
        agreements.
        """
        # FIXME: This should be a method exclusive to a LegalPage manager
        return self.raw('''
            SELECT DISTINCT staticpages_legalpage.id
            FROM staticpages_legalpage
            WHERE (staticpages_legalpage.active = %s
                   AND NOT (staticpages_legalpage.id IN
                            (SELECT A.document_id
                             FROM staticpages_legalpage AS LP
                             INNER JOIN staticpages_agreement AS A
                                        ON LP.id = A.document_id
                             WHERE A.user_id = %s AND
                             A.agreed_on > LP.modified_on)))
        ''', [True, user.id])
