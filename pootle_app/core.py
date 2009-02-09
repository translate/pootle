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

from django.db import models, connection, backend
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User, Permission
from pootle_app.profile import *
from translate.filters import checks

def table_name(table):
    return table._meta.db_table

def field_name(table, field_name):
    return '%s.%s' % (table_name(table), table._meta.get_field(field_name).column)

def primary_key_name(table):
    return field_name(table, table._meta.pk.name)

def unzip(lst):
    left_lst = []
    right_lst = []
    for left, right in lst:
        left_lst.append(left)
        right_lst.append(right)
    return left_lst, right_lst

def get_latest_changes(manager, query):
    """manager is a Django model manager and query is a raw SQL query
    which returns a 2-tuple of object ids and modification times.

    This function returns a list of the Django objects corresponding
    to the ids and assings the modification times for each object to
    the attribute 'latest_change'.
    """
    cursor = connection.cursor()
    cursor.execute(query)
    # cursor.fetchall() gives a (object id, creation time) 2-tuple
    # which we unzip to two lists. 
    ids, latest_changes = unzip(cursor.fetchall())
    # Use the supplied manager's in_bulk operation to get an
    # id->object map where the objects are the Django models
    # corresponding the to the ids.
    id_obj_map = manager.in_bulk(ids)
    # Build a list of objects using by extracting values from
    # from id_obj_map in the order of the ids in 'ids'
    objs = [id_obj_map[id] for id in ids]
    # For each object in 'objs', assign its creation time
    # to the attribute 'latest_change'
    for obj, latest_change in zip(objs, latest_changes):
        obj.latest_change = latest_change
    return objs

class LanguageManager(models.Manager):
    # Note that we specifically exclude the templates project
    get_latest_changes_query = """
        SELECT   %(language_id)s, MIN(%(creation_time)s)
        FROM     %(language_table)s LEFT OUTER JOIN %(submission_table)s
                 ON %(language_id)s = %(submission_language)s
        WHERE    %(language_code)s <> 'templates'
        GROUP BY %(language_name)s
        ORDER BY %(language_code)s
    """
    
    def get_latest_changes(self):
        fields = {'language_code':       field_name(Language, 'code'),
                  'language_name':       field_name(Language, 'fullname'),
                  'creation_time':       field_name(Submission, 'creation_time'),
                  'language_table':      table_name(Language), 
                  'submission_table':    table_name(Submission),
                  'language_id':         primary_key_name(Language),
                  'submission_language': field_name(Submission, 'language')}

        return get_latest_changes(self, self.get_latest_changes_query % fields)

    # The following method prevents the templates project from being
    # returned by normal queries on the Language table.
    def get_query_set(self):
        return super(LanguageManager, self).get_query_set().exclude(code='templates')

    def include_hidden(self):
        return super(LanguageManager, self).get_query_set()

    # Special method to get hold of the templates language object
    def templates_project(self):
        return super(LanguageManager, self).get_query_set().get(code='templates')

    def has_templates_project(self):
        return super(LanguageManager, self).get_query_set().filter(code='templates').count() > 0

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
        FROM     %(project_table)s LEFT OUTER JOIN %(submission_table)s
                 ON %(project_id)s = %(submission_project)s
        GROUP BY %(project_name)s
        ORDER BY %(project_code)s
    """

    def get_latest_changes(self):
        fields =  {'project_code':        field_name(Project, 'code'),
                   'creation_time':       field_name(Submission, 'creation_time'),
                   'project_table':       table_name(Project),
                   'submission_table':    table_name(Submission),
                   'project_id':          primary_key_name(Project),
                   'submission_project':  field_name(Submission, 'project'),
                   'project_name':        field_name(Project, 'fullname')}

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
            ('xl', 'XLIFF')
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

class TranslationProject(models.Model):
    class Meta:
        unique_together = ('language', 'project')

    language         = models.ForeignKey(Language, db_index=True)
    project          = models.ForeignKey(Project, db_index=True)
    project_dir      = models.FilePathField()
    file_style       = models.CharField(max_length=255, blank=True, null=False, default="")

class Right(models.Model):
    class Meta:
        unique_together = ('profile', 'translation_project')

    profile             = models.ForeignKey(PootleProfile, db_index=True)
    translation_project = models.ForeignKey(TranslationProject, db_index=True)
    permissions         = models.ManyToManyField(Permission)

class Goal(models.Model):
    """A goal is a named collection of files. Goals partition the files of
    translation project. In other words, every file is either in no
    goals or exactly in one goal.
    """
    name                = models.CharField(max_length=255, null=False, verbose_name=_("Name"))
    # A pointer to the TranslationProject of which this Goal is a part.
    translation_project = models.ForeignKey(TranslationProject)
    # Every goal can contain a number of users and every user can be
    # involved with a number of goals.
    profiles            = models.ManyToManyField(PootleProfile, related_name='goals')

class Store(models.Model):
    """A model representing a translation store (i.e. a PO or XLIFF file)."""
    # The filesystem path of the store.
    path = models.FilePathField(db_index=True)
    # A store can be part of many goals and a goal can contain many files
    goals = models.ManyToManyField(Goal, related_name='stores')

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
    creation_time  = models.DateTimeField()
    language       = models.ForeignKey('Language')
    project        = models.ForeignKey('Project')
    filename       = models.FilePathField()
    source         = models.CharField(max_length=255)
    trans          = models.CharField(max_length=255)
    submitter      = models.ForeignKey(PootleProfile, null=True)

    objects = SubmissionManager()

class SuggestionManager(models.Manager):
    def get_top_suggesters(self):
        """See the comment for SubmissionManager.get_top_submitters."""

        fields = {
            'profile_id':    primary_key_name(PootleProfile),
            'suggester':     field_name(Suggestion, 'suggester'),
            'review_status': field_name(Suggestion, 'review_status')
        }
        # select_related('suggester__user') will let Django also
        # select the PootleProfile and its related User along with the
        # Suggestion objects in the query. We do this, since we almost
        # certainly want to get this information after calling
        # get_top_suggesters.
        return self.extra(select = {'num_contribs': 'COUNT(%(profile_id)s)' % fields},
                          tables = [table_name(PootleProfile)],
                          where  = ["%(profile_id)s = %(suggester)s GROUP BY %(profile_id)s" % fields]
                          ).order_by('-num_contribs').select_related('suggester__user')

    def get_top_reviewers(self):
        return self.get_top_suggesters().filter(review_status='review')

class Suggestion(models.Model):
    creation_time  = models.DateTimeField()
    language       = models.ForeignKey('Language')
    project        = models.ForeignKey('Project')
    filename       = models.FilePathField()
    source         = models.CharField(max_length=255)
    trans          = models.CharField(max_length=255)
    suggester      = models.ForeignKey(PootleProfile, related_name='suggestions_suggester_set')
    reviewer       = models.ForeignKey(PootleProfile, related_name='suggestions_reviewer_set', null=True)
    review_status  = models.CharField(max_length=255)
    review_time    = models.DateTimeField(null=True)
    review_submission = models.OneToOneField('Submission', null=True)

    objects = SuggestionManager()

def _get_suggestions(profile, status):
    return Suggestion.objects.filter(suggester=profile).filter(review_status=status)

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
