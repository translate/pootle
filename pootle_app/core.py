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

from django.db import models, connection
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Permission
from django.conf import settings

from translate.filters import checks
from translate.storage import statsdb

from pootle_app.profile import PootleProfile
from pootle_app.util import table_name, field_name, primary_key_name, unzip

stats_cache = statsdb.StatsCache(settings.STATS_DB_PATH)

def get_latest_changes(manager, query):
    cursor = connection.cursor()
    cursor.execute(query)
    return dict(cursor.fetchall())

class LanguageManager(models.Manager):
    # Note that we specifically exclude the templates project
    get_latest_changes_query = """
        SELECT   %(language_id)s, MIN(%(creation_time)s)
        FROM     %(language_table)s
                 LEFT OUTER JOIN %(translation_project_table)s
                     ON %(language_id)s = %(translation_project_language)s
                 LEFT OUTER JOIN %(submission_table)s
                     ON %(translation_project_id)s = %(submission_translation_project)s
        WHERE    %(language_code)s <> 'templates'
        GROUP BY %(language_name)s
        ORDER BY %(language_code)s
    """
    
    def get_latest_changes(self):
        from pootle_app.translation_project import TranslationProject

        fields = {
            'language_code':                   field_name(Language, 'code'),
            'language_name':                   field_name(Language, 'fullname'),
            'creation_time':                   field_name(Submission, 'creation_time'),
            'language_table':                  table_name(Language), 
            'submission_table':                table_name(Submission),
            'language_id':                     primary_key_name(Language),
            'submission_translation_project':  field_name(Submission, 'translation_project'),
            'translation_project_table':       table_name(TranslationProject),
            'translation_project_id':          primary_key_name(TranslationProject),
            'translation_project_language':    field_name(TranslationProject, 'language'),
            }

        return get_latest_changes(self, self.get_latest_changes_query % fields)

    # The following method prevents the templates project from being
    # returned by normal queries on the Language table.
    def hide_special(self):
        return super(LanguageManager, self).get_query_set().exclude(code='templates')

    def include_hidden(self):
        return super(LanguageManager, self).get_query_set()

class Language(models.Model):
    class Meta:
        ordering = ['code']

    code_help_text = u'ISO 639 language code for the language, possibly followed by an underscore (_) and an ISO 3166 country code. <a href="http://www.w3.org/International/articles/language-tags/">More information</a>'
    nplurals_help_text = u'For more information, visit <a href="http://translate.sourceforge.net/wiki/l10n/pluralforms">our wiki page</a> on plural forms'
    pluralequation_help_text = u'For more information, visit <a href="http://translate.sourceforge.net/wiki/l10n/pluralforms">our wiki page</a> on plural forms'
    specialchars_help_text = u'Enter any special characters that users might find difficult to type'

    nplural_choices = ((0, u'unknown'), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6))

    code           = models.CharField(max_length=50, null=False, unique=True, db_index=True, help_text=code_help_text)
    fullname       = models.CharField(max_length=255, null=False, verbose_name=_("Full Name"))
    specialchars   = models.CharField(max_length=255, blank=True, verbose_name=_("Special Chars"), help_text=specialchars_help_text)
    nplurals       = models.SmallIntegerField(default=0, choices=nplural_choices, verbose_name=_("Number of Plurals"), help_text=nplurals_help_text)
    pluralequation = models.CharField(max_length=255, blank=True, verbose_name=_("Plural Equation"), help_text=pluralequation_help_text)

    objects = LanguageManager()

    def __unicode__(self):
        return self.fullname

class ProjectManager(models.Manager):
    get_latest_changes_query = """
        SELECT   %(project_id)s, MIN(%(creation_time)s)
        FROM     %(project_table)s
                 LEFT OUTER JOIN %(translation_project_table)s
                      ON %(project_id)s = %(translation_project_project)s
                 LEFT OUTER JOIN %(submission_table)s
                      ON %(translation_project_id)s = %(submission_translation_project)s
        GROUP BY %(project_name)s
        ORDER BY %(project_code)s
    """

    def get_latest_changes(self):
        from pootle_app.translation_project import TranslationProject

        fields =  {
            'project_code':                   field_name(Project, 'code'),
            'creation_time':                  field_name(Submission, 'creation_time'),
            'project_table':                  table_name(Project),
            'submission_table':               table_name(Submission),
            'project_id':                     primary_key_name(Project),
            'submission_translation_project': field_name(Submission, 'translation_project'),
            'project_name':                   field_name(Project, 'fullname'),
            'translation_project_table':      table_name(TranslationProject),
            'translation_project_id':         primary_key_name(TranslationProject),
            'translation_project_project':    field_name(TranslationProject, 'project'),
            }

        return get_latest_changes(self, self.get_latest_changes_query % fields)

class Project(models.Model):
    class Meta:
        ordering = ['code']

    code_help_text = u'A short code for the project. This should only contain ASCII characters, numbers, and the underscore (_) character.'
    description_help_text = u'A description of this project. This is useful to give more information or instructions. This field should be valid HTML.'

    checker_choices = [('standard', 'standard')]
    checkers = list(checks.projectcheckers.keys())
    checkers.sort()
    checker_choices.extend([(checker, checker) for checker in checkers])
    local_choices = (
            ('po', 'Gettext PO'),
            ('xlf', 'XLIFF')
    )
    treestyle_choices = (
            # TODO: check that the None is stored and handled correctly
            ('auto', _(u'Automatic detection (slower)')),
            ('gnu', _(u'GNU style: all languages in one directory; files named by language code')),
            ('nongnu', _(u'Non-GNU: Each language in its own directory')),
    )

    code           = models.CharField(max_length=255, null=False, unique=True, db_index=True, help_text=code_help_text)
    fullname       = models.CharField(max_length=255, null=False, verbose_name=_("Full name"))
    description    = models.TextField(blank=True, help_text=description_help_text)
    checkstyle     = models.CharField(max_length=50, default='standard', null=False, choices=checker_choices)
    localfiletype  = models.CharField(max_length=50, default="po", choices=local_choices)
    treestyle      = models.CharField(max_length=20, default='auto', choices=treestyle_choices)
    ignoredfiles   = models.CharField(max_length=255, blank=True, null=False, default="")
    createmofiles  = models.BooleanField(default=False)

    objects = ProjectManager()

    def __unicode__(self):
        return self.fullname

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
            'profile_id': primary_key_name(PootleProfile),
            'submitter':  field_name(Submission, 'submitter'),
        }
        # select_related('submitter__user') will let Django also
        # select the PootleProfile and its related User along with the
        # Submission objects in the query. We do this, since we almost
        # certainly want to get this information after calling
        # get_top_submitters.
        return self.extra(select = {'num_contribs': 'COUNT(%(profile_id)s)' % fields},
                          tables = [table_name(PootleProfile)],
                          where  = ["%(profile_id)s = %(submitter)s GROUP BY %(profile_id)s" % fields]
                          ).order_by('-num_contribs').select_related('submitter__user')

class Submission(models.Model):
    creation_time       = models.DateTimeField()
    translation_project = models.ForeignKey('TranslationProject')
    submitter           = models.ForeignKey(PootleProfile, null=True)
    unit                = models.OneToOneField('Unit')
    from_suggestion     = models.OneToOneField('Suggestion', null=True)

    objects = SubmissionManager()

class SuggestionManager(models.Manager):
    def _get_top_results(self, profile_field):
        fields = {
            'profile_id':    primary_key_name(PootleProfile),
            'profile_field': field_name(Suggestion, profile_field)
        }
        # select_related('suggester__user') will let Django also
        # select the PootleProfile and its related User along with the
        # Suggestion objects in the query. We do this, since we almost
        # certainly want to get this information after calling
        # get_top_suggesters.
        return self.extra(select = {'num_contribs': 'COUNT(%(profile_id)s)' % fields},
                          tables = [table_name(PootleProfile)],
                          where  = ["%(profile_id)s = %(profile_field)s GROUP BY %(profile_id)s" % fields]
                          ).order_by('-num_contribs')

    def get_top_suggesters(self):
        return self._get_top_results('suggester').select_related('suggester__user')

    def get_top_reviewers(self):
        return self._get_top_results('reviewer').select_related('reviewer__user')

class Suggestion(models.Model):
    creation_time       = models.DateTimeField()
    translation_project = models.ForeignKey('TranslationProject')
    suggester           = models.ForeignKey(PootleProfile, related_name='suggestions_suggester_set')
    reviewer            = models.ForeignKey(PootleProfile, related_name='suggestions_reviewer_set', null=True)
    review_time         = models.DateTimeField(null=True)
    unit                = models.OneToOneField('Unit')

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

def submissions_count(profile):
    return profile.submission_set.count()
