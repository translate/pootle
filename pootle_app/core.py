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

from django.contrib.auth.models import User
from Pootle.pootle_app.profile import PootleProfile

def table_name(table):
    return table._meta.db_table

def field_name(table, field_name):
    return '%s.%s' % (table_name(table), table._meta.get_field(field_name).column)

def primary_key_name(table):
    return field_name(table, table._meta.pk.name)

class LanguageManager(models.Manager):
    def get_latest_changes(self):
        fields = {'language_code':       field_name(Language, 'code'),
                  'language_name':       field_name(Language, 'fullname'),
                  'creation_time':       field_name(Submission, 'creation_time'),
                  'language_table':      table_name(Language), 
                  'submission_table':    table_name(Submission),
                  'language_id':         primary_key_name(Language),
                  'submission_language': field_name(Submission, 'language')}

        query = """SELECT   %(language_code)s, %(language_name)s, MIN(%(creation_time)s)
                   FROM     %(language_table)s LEFT OUTER JOIN %(submission_table)s
                            ON %(language_id)s = %(submission_language)s
                   GROUP BY %(language_name)s
                   ORDER BY %(language_code)s""" % fields

        cursor = connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()

class Language(models.Model):
    code           = models.CharField(max_length=50, null=False, unique=True)
    fullname       = models.CharField(max_length=255, null=False)
    nplurals       = models.SmallIntegerField(default=1)
    pluralequation = models.CharField(max_length=255)
    specialchars   = models.CharField(max_length=255)

    objects = LanguageManager()

class ProjectManager(models.Manager):
    def get_latest_changes(self):
        fields = {'project_code':        field_name(Project, 'code'),
                  'creation_time':       field_name(Submission, 'creation_time'),
                  'project_table':       table_name(Project),
                  'submission_table':    table_name(Submission),
                  'project_id':          primary_key_name(Project),
                  'submission_project':  field_name(Submission, 'project'),
                  'project_name':        field_name(Project, 'fullname')}

        query = """SELECT   %(project_code)s, MIN(%(creation_time)s)
                   FROM     %(project_table)s LEFT OUTER JOIN %(submission_table)s
                            ON %(project_id)s = %(submission_project)s
                   GROUP BY %(project_name)s
                   ORDER BY %(project_code)s""" % fields

        cursor = connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()

class Project(models.Model):
    code           = models.CharField(max_length=255, null=False, unique=True)
    fullname       = models.CharField(max_length=255, null=False)
    description    = models.TextField()
    checkstyle     = models.CharField(max_length=50, null=False)
    localfiletype  = models.CharField(max_length=50, default="")
    createmofiles  = models.BooleanField(default=False)
    treestyle      = models.CharField(max_length=20, default="")
    ignoredfiles   = models.CharField(max_length=255, null=False, default="")

    objects = ProjectManager()

def _do_query(query, replacements, fields, params=()):
    all_fields = fields.copy()
    all_fields.update((key, var % fields) for key, var in replacements.iteritems())
    final_query = query % all_fields
    # print "going to execute %s \n\nwith params = %s" % (final_query, params)

    cursor = connection.cursor()
    cursor.execute(final_query, params)
    return [(User.objects.filter(id=user_id)[0], count) for user_id, count in cursor.fetchall()[:5]]

class SubmissionManager(models.Manager):
    QUERY = """
        SELECT   %(user_id)s, COUNT(%(submission_id)s)
        FROM     %(profile_table)s INNER JOIN %(submission_table)s
                 ON %(user_id)s = %(submitter)s
        %(constraint)s
        GROUP BY %(user_id)s
        ORDER BY COUNT(%(submission_id)s)"""

    def get_top_submitters(self):
        return _do_query(self.QUERY, {'constraint': ''}, self.get_fields())

    def get_top_submitters_by_project(self, project):
        return _do_query(self.QUERY, {'constraint': 'WHERE %(project)s = %%s'}, self.get_fields(), (project,))

    def get_top_submitters_by_language(self, language):
        return _do_query(self.QUERY, {'constraint': 'WHERE %(language)s = %%s'}, self.get_fields(), (language,))

    def get_top_submitters_by_project_and_language(self, project, language):
        return _do_query(self.QUERY, {'constraint': 'WHERE %(project)s = %%s AND %(language)s = %%s'}, self.get_fields(),
                         (project, language))

    @classmethod
    def get_fields(cls):
        return {'user_id':          field_name(PootleProfile, 'user'),
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
    QUERY = """
        SELECT %(user_id)s, COUNT(%(suggestion_id)s)
        FROM   %(profile_table)s INNER JOIN %(suggestion_table)s
               ON %(user_id)s = %(suggester)s
        %(constraint)s
        GROUP  BY %(user_id)s
        ORDER  BY COUNT(%(suggestion_id)s)"""

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
            'user_id':          field_name(PootleProfile, 'user'),

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

