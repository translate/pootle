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

from django.db import models
from django.utils.translation import ugettext_lazy as _

import custom_sql_util
from profile import PootleProfile
from translation_project import TranslationProject

class SuggestionManager(models.Manager):
    def _get_top_results(self, profile_field):
        from profile import PootleProfile

        fields = {
            'profile_id':    custom_sql_util.primary_key_name(PootleProfile),
            'profile_field': custom_sql_util.field_name(Suggestion, profile_field)
        }
        # select_related('suggester__user') will let Django also
        # select the PootleProfile and its related User along with the
        # Suggestion objects in the query. We do this, since we almost
        # certainly want to get this information after calling
        # get_top_suggesters.
        return self.extra(select = {'num_contribs': 'COUNT(%(profile_id)s)' % fields},
                          tables = [custom_sql_util.table_name(PootleProfile)],
                          where  = ["%(profile_id)s = %(profile_field)s GROUP BY %(profile_id)s" % fields]
                          ).order_by('-num_contribs')

    def get_top_suggesters(self):
        return self._get_top_results('suggester').select_related('suggester__user')

    def get_top_reviewers(self):
        return self._get_top_results('reviewer').select_related('reviewer__user')

class Suggestion(models.Model):
    class Meta:
        app_label = "pootle_app"

    state_choices = [('pending', _('Pending')),
                     ('accepted', _('accepted')),
                     ]
        
    creation_time       = models.DateTimeField(db_index=True)
    translation_project = models.ForeignKey(TranslationProject, db_index=True)
    suggester           = models.ForeignKey(PootleProfile, db_index=True, related_name='suggestions_suggester_set')
    reviewer            = models.ForeignKey(PootleProfile, db_index=True, related_name='suggestions_reviewer_set', null=True)
    review_time         = models.DateTimeField(null=True, db_index=True)
    unit                = models.IntegerField(null=False, db_index=True)
    state               = models.CharField(max_length=16, default='pending', null=False, choices=state_choices, db_index=True)

    objects = SuggestionManager()

def _get_suggestions(profile, status):
    return Suggestion.objects.filter(suggester=profile, state=status)

