#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

from django.db                import models

from pootle_app.models import custom_sql_util
from pootle_translationproject.models import TranslationProject
from pootle_app.models.suggestion import Suggestion
from pootle_app.models.profile import PootleProfile

class SubmissionManager(models.Manager):
    def get_top_submitters(self):
        """Return a list of Submissions, where each Submission represents a
        user profile (note that if a user has never made suggestions,
        there will be no entry for that user) where the order is
        descending in the number of suggestion contributions from the
        users.

        One would expect us to return a list of PootleProfiles instead
        of a list of Submissions. This would be ideal, but if we are
        to allow code to further filter the top suggestion results
        using criteria from the Submission model, then we have to
        return a list of Submissions.

        The number of contributions from a profile is stored in the
        attribute 'num_contribs' and the profile is stored in
        'submitter'.

        Please note that the Submission objects returned here are
        useless.  That is, they are valid Submission objects, but for
        a user with 10 suggestions, we'll be given one of these
        objects, without knowing which. But we're not interested in
        the Submission objects anyway.
        """
        fields = {
            'profile_id': custom_sql_util.primary_key_name(PootleProfile),
            'submitter':  custom_sql_util.field_name(Submission, 'submitter'),
        }
        # select_related('submitter__user') will let Django also
        # select the PootleProfile and its related User along with the
        # Submission objects in the query. We do this, since we almost
        # certainly want to get this information after calling
        # get_top_submitters.
        return self.extra(select = {'num_contribs': 'COUNT(%(profile_id)s)' % fields},
                          tables = [custom_sql_util.table_name(PootleProfile)],
                          where  = ["%(profile_id)s = %(submitter)s GROUP BY %(profile_id)s" % fields]
                          ).order_by('-num_contribs').select_related('submitter__user')

class Submission(models.Model):
    class Meta:
        app_label = "pootle_app"
        get_latest_by = "creation_time"

    creation_time       = models.DateTimeField(db_index=True)
    translation_project = models.ForeignKey(TranslationProject, db_index=True)
    submitter           = models.ForeignKey(PootleProfile, null=True, db_index=True)
    from_suggestion     = models.OneToOneField(Suggestion, null=True, db_index=True)

    objects = SubmissionManager()

    def __unicode__(self):
        return u"%s (%s)" % (self.creation_time.strftime("%Y-%m-%d %H:%M"), unicode(self.submitter))
