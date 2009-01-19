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
try:
    from pootle_app.profile import PootleProfile
except ImportError:
    from profile import PootleProfile
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

def _do_query(query, replacements, fields, params=()):
    all_fields = fields.copy()
    all_fields.update((key, var % fields) for key, var in replacements.iteritems())
    final_query = query % all_fields
    # print "going to execute %s \n\nwith params = %s" % (final_query, params)
    cursor = connection.cursor()
    cursor.execute(final_query, params)
    # cursor.fetchall() returns a list of (profile_id, count) 
    # two tuples which we unzip into a list of profile_ids and
    # a list of counts
    profile_ids, counts = unzip(cursor.fetchall())
    # Get a dictionary of profile_id -> PootleProfile models
    profiles = PootleProfile.objects.select_related('user').in_bulk(profile_ids)
    # profile_ids gives us the profile ids in the order we want (descending in
    # the number of contributions), so we use these indices to pull the profile
    # objects from the profiles dictionary.
    return zip((profiles[id] for id in profile_ids), counts)

class SubmissionManager(models.Manager):
    # Select all PootleProfile ids, along with the count of the
    # Submission objects which point to the respective PootleProfile
    # objects. To do this, we join the PootleProfile table with the
    # Submission on the ids of PootleProfile objects.
    # 
    # We choose the PootleProfile ids as our grouping.
    #
    # Since we're interested only in the top five contributions,
    # we choose a descending order in terms of the submission count,
    # and limit our results using the LIMIT directive.
    #
    # %(constraint)s allows the specification of arbitrary WHERE
    # clauses.
    QUERY = """
        SELECT   %(profile_id)s, COUNT(%(submission_id)s)
        FROM     %(profile_table)s INNER JOIN %(submission_table)s
                 ON %(profile_id)s = %(submitter)s
        %(constraint)s
        GROUP    BY %(profile_id)s
        ORDER    BY COUNT(%(submission_id)s) DESC
        LIMIT    5"""

    def get_top_submitters(self):
        # Note the %%s below. After string substitution, this will become %s,
        # which cursor.execute will fill with the project code.
        return _do_query(self.QUERY,
                         {'constraint': ''},
                         self.get_fields())

    def get_top_submitters_by_project(self, project):
        # Note the %%s below. After string substitution, this will become %s,
        # which cursor.execute will fill with the project code.
        return _do_query(self.QUERY,
                         {'constraint': 'WHERE %(project)s = %%s'},
                         self.get_fields(), (project,))

    def get_top_submitters_by_language(self, language):
        # Note the %%s below. After string substitution, this will become %s,
        # which cursor.execute will fill with the project code.
        return _do_query(self.QUERY,
                         {'constraint': 'WHERE %(language)s = %%s'},
                         self.get_fields(), (language,))

    def get_top_submitters_by_project_and_language(self, project, language):
        # Note the %%s below. After string substitution, this will become %s,
        # which cursor.execute will fill with the project code.
        return _do_query(self.QUERY,
                         {'constraint': 'WHERE %(project)s = %%s AND %(language)s = %%s'},
                         self.get_fields(), (project, language))

    @classmethod
    def get_fields(cls):
        return {'profile_id':       primary_key_name(PootleProfile),
                'submission_id':    primary_key_name(Submission),
                'profile_table':    table_name(PootleProfile),
                'submission_table': table_name(Submission),
                'submitter':        field_name(Submission, 'submitter'),
                'language':         field_name(Submission, 'language'),
                'project':          field_name(Submission, 'project') }

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
    # Select all PootleProfile ids, along with the count of the
    # Suggestion objects which point to the respective PootleProfile
    # objects. To do this, we join the PootleProfile table with the
    # Suggestion on the ids of PootleProfile objects.
    # 
    # We choose the PootleProfile ids as our grouping.
    #
    # Since we're interested only in the top five contributions,
    # we choose a descending order in terms of the suggestion count,
    # and limit our results using the LIMIT directive.
    #
    # %(constraint)s allows the specification of arbitrary WHERE
    # clauses.
    QUERY = """
        SELECT %(profile_id)s, COUNT(%(suggestion_id)s)
        FROM   %(profile_table)s INNER JOIN %(suggestion_table)s
               ON %(profile_id)s = %(suggester)s
        %(constraint)s
        GROUP  BY %(profile_id)s
        ORDER  BY COUNT(%(suggestion_id)s) DESC
        LIMIT  5"""

    def get_top_suggesters(self):
        return _do_query(self.QUERY,
                         {'constraint': ''}, 
                         self.get_fields())

    def get_top_suggesters_by_project(self, project_code):
        # Note the %%s below. After string substitution, this will become %s, 
        # which cursor.execute will fill with the project code.
        return _do_query(self.QUERY,
                         {'constraint': 'WHERE %(project)s = %%s'},
                         self.get_fields(), (project_code,))

    def get_top_suggesters_by_language(self, language_code):
        # Note the %%s below. After string substitution, this will become %s,
        # which cursor.execute will fill with the project code.
        return _do_query(self.QUERY,
                         {'constraint': 'WHERE %(language)s = %%s'},
                         self.get_fields(), (language_code,))

    def get_top_suggesters_by_project_and_language(self, project_code, language_code):
        # Note the %%s below. After string substitution, this will become %s,
        # which cursor.execute will fill with the project code.
        return _do_query(self.QUERY,
                         {'constraint': 'WHERE %(project)s = %%s AND %(language)s = %%s'},
                         self.get_fields(), (project_code, language_code))

    def get_top_reviewers(self):
        return _do_query(self.QUERY,
                         {'constraint': 'WHERE %(review_status)s = "accepted"'},
                         self.get_fields())

    def get_top_reviewers_by_project(self, project_code):
        # Note the %%s below. After string substitution, this will become %s,
        # which cursor.execute will fill with the project code.
        return _do_query(self.QUERY,
                         {'constraint': 'WHERE %(review_status)s = "accepted" AND %(language)s = %%s'},
                         self.get_fields(), (project_code,))

    def get_top_reviewers_by_language(self, language_code):
        # Note the %%s below. After string substitution, this will become %s,
        # which cursor.execute will fill with the project code.
        return _do_query(self.QUERY,
                         {'constraint': 'WHERE %(review_status)s = "accepted" AND %(language)s = %%s'},
                        self.get_fields(), (language_code,))

    def get_top_reviewers_by_project_and_language(self, project_code, language_code):
        # Note the %%s below. After string substitution, this will become %s,
        # which cursor.execute will fill with the project code.
        return _do_query(self.QUERY,
                         {'constraint': 'WHERE %(review_status)s = "accepted" AND %(project)s = %%s AND %(language)s = %%s'},
                         self.get_fields(), (project_code, language_code))

    @classmethod
    def get_fields(cls):
        return {
            'profile_table':    table_name(PootleProfile),
            'profile_id':       primary_key_name(PootleProfile),

            'suggestion_table': table_name(Suggestion),
            'suggestion_id':    primary_key_name(Suggestion),
            'suggester':        field_name(Suggestion, 'suggester'),
            'reviewer':         field_name(Suggestion, 'reviewer'),
            'language':         field_name(Suggestion, 'language'),
            'project':          field_name(Suggestion, 'project'),
            'review_status':    field_name(Suggestion, 'review_status')
        }

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

