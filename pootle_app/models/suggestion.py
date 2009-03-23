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
from profile import PootleProfile
from translation_project import TranslationProject
from store import Unit

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
        
    creation_time       = models.DateTimeField()
    translation_project = models.ForeignKey(TranslationProject)
    suggester           = models.ForeignKey(PootleProfile, related_name='suggestions_suggester_set')
    reviewer            = models.ForeignKey(PootleProfile, related_name='suggestions_reviewer_set', null=True)
    review_time         = models.DateTimeField(null=True)
    unit                = models.OneToOneField(Unit)

    objects = SuggestionManager()

def _get_suggestions(profile, status):
    return Suggestion.objects.filter(suggester=profile).filter(unit__state=status)

def suggestions_accepted(profile):
    return _get_suggestions(profile, "accepted").all()

def suggestions_rejected(profile):
    return _get_suggestions(profile, "rejected").all()

def suggestions_pending(profile):
    return _get_suggestions(profile, "pending").all()

def suggestions_reviewed(profile):
    return _get_suggestions(profile, "reviewed").all()

def suggestions_accepted_count(profile):
    return _get_suggestions(profile, "accepted").count()

def suggestions_rejected_count(profile):
    return _get_suggestions(profile, "rejected").count()

def suggestions_pending_count(profile):
    return _get_suggestions(profile, "pending").count()

def suggestions_reviewed_count(profile):
    return _get_suggestions(profile, "reviewed").count()
