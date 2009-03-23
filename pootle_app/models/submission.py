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

from django.utils.translation import ugettext_lazy as _
from django.db                import models

import custom_sql_util
from language import Language
from project import Project
from translation_project import TranslationProject
from suggestion import Suggestion
from store import Unit
from profile import PootleProfile

class SubmissionManager(models.Manager):
    get_latest_changes_query = """
        SELECT   %(object_id)s, MIN(%(creation_time)s)
        FROM     %(object_table)s
                 LEFT OUTER JOIN %(translation_project_table)s
                      ON %(object_id)s = %(translation_project_object)s
                 LEFT OUTER JOIN %(submission_table)s
                      ON %(translation_project_id)s = %(submission_translation_project)s
        %(constraint)s
        GROUP BY %(object_name)s
        ORDER BY %(object_code)s
    """

    def get_common_fields(self):
        return {
            'creation_time':                   custom_sql_util.field_name(Submission, 'creation_time'),
            'submission_table':                custom_sql_util.table_name(Submission),
            'submission_translation_project':  custom_sql_util.field_name(Submission, 'translation_project'),
            'translation_project_table':       custom_sql_util.table_name(TranslationProject),
            'translation_project_id':          custom_sql_util.primary_key_name(TranslationProject),
            }
    
    def get_latest_language_changes(self):
        fields = self.get_common_fields()
        fields.update({
            'object_code':                     custom_sql_util.field_name(Language, 'code'),
            'object_name':                     custom_sql_util.field_name(Language, 'fullname'),
            'object_table':                    custom_sql_util.table_name(Language), 
            'object_id':                       custom_sql_util.primary_key_name(Language),
            'translation_project_object':      custom_sql_util.field_name(TranslationProject, 'language'),
            'constraint':                      "WHERE %s <> 'templates'" % custom_sql_util.field_name(Language, 'code')
            })

        return custom_sql_util.get_latest_changes(self, self.get_latest_changes_query % fields)

    def get_latest_project_changes(self):
        fields = self.get_common_fields()
        fields.update({
            'object_code':                    custom_sql_util.field_name(Project, 'code'),
            'object_name':                    custom_sql_util.field_name(Project, 'fullname'),
            'object_table':                   custom_sql_util.table_name(Project),
            'object_id':                      custom_sql_util.primary_key_name(Project),
            'translation_project_object':     custom_sql_util.field_name(TranslationProject, 'project'),
            'constraint':                     ''
            })

        return custom_sql_util.get_latest_changes(self, self.get_latest_changes_query % fields)

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
        from profile import PootleProfile

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

    creation_time       = models.DateTimeField()
    translation_project = models.ForeignKey(TranslationProject)
    submitter           = models.ForeignKey(PootleProfile, null=True)
    unit                = models.OneToOneField(Unit)
    from_suggestion     = models.OneToOneField(Suggestion, null=True)

    objects = SubmissionManager()

def submissions_count(profile):
    return profile.submission_set.count()
