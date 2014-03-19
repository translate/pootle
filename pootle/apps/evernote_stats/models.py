#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.


from django.db import models

from pootle_statistics.models import Submission, SubmissionFields
from pootle_store.signals import translation_submitted

from .util import diff_stat, wordcount


class SubmissionStats(models.Model):
    submission = models.OneToOneField('pootle_statistics.Submission',
            null=True)

    initial_translation = models.BooleanField()
    source_wordcount = models.IntegerField(default=0, null=True)
    words_added = models.IntegerField(default=0, null=True)
    words_removed = models.IntegerField(default=0, null=True)
    chars_added = models.IntegerField(default=0, null=True)
    chars_removed = models.IntegerField(default=0, null=True)

    def __unicode__(self):
        return "[insert: %d, delete: %d, update: %d -> %d] in submission %s" % \
            (
                self.w_insert, self.w_delete, self.w_delete_update,
                self.w_insert_update, self.submission
            )


def save_submission_stats(sender, **kwargs):
    """A post-save hook for the `TranslationProject` model which saves
    word statistics of current submission.
    """
    unit = kwargs.get('unit')
    profile = kwargs.get('profile')

    try:
        sub = Submission.objects.get(unit=unit, submitter=profile,
                                     creation_time=unit.submitted_on,
                                     field=SubmissionFields.TARGET)

        ss = SubmissionStats(submission=sub)

        if sub.old_value == '':
            if sub.new_value != '':
                ss.words_added, ss.words_removed = \
                    diff_stat(unit.source_f.split(), unit.target_f.split())
                ss.chars_added, ss.chars_removed = \
                    diff_stat(unit.source_f, unit.target_f)

                ss.initial_translation = True
                ss.source_wordcount = wordcount(unit.source_f)
        else:
            ss.words_added, ss.words_removed = \
                diff_stat(sub.old_value.split(), sub.new_value.split())
            ss.chars_added, ss.chars_removed = \
                diff_stat(sub.old_value, sub.new_value)
            ss.source_wordcount = wordcount(unit.source_f)

        ss.save()
    except:
        pass

# evernote_stats is disabled
# TODO remove evernote_stats
# translation_submitted.connect(save_submission_stats, sender=None)
