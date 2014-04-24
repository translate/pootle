#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import escape, truncatechars
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from pootle.core.log import log, SCORE_CHANGED
from pootle.core.managers import RelatedManager
from pootle_misc.checks import check_names
from pootle_misc.util import cached_property
from pootle_store.util import FUZZY, TRANSLATED, UNTRANSLATED


EDIT_COEF = 5.0/7
REVIEW_COEF = 2.0/7
SUGG_COEF = 0.2
ANALYZE_COEF = 0.1


#: These are the values for the 'type' field of Submission
class SubmissionTypes(object):
    # None/0 = no information
    NORMAL = 1  # Interactive web editing
    REVERT = 2  # Revert action on the web
    SUGG_ACCEPT = 3  # Accepting a suggestion
    UPLOAD = 4  # Uploading an offline file
    SYSTEM = 5  # Batch actions performed offline
    MUTE_CHECK = 6 # Mute QualityCheck
    UNMUTE_CHECK = 7 # Unmute QualityCheck
    SUGG_ADD = 8 # Add new Suggestion
    SUGG_REJECT = 9 # Reject Suggestion


#: Values for the 'field' field of Submission
class SubmissionFields(object):
    NONE = 0  # non-field submission
    SOURCE = 1  # pootle_store.models.Unit.source
    TARGET = 2  # pootle_store.models.Unit.target
    STATE = 3  # pootle_store.models.Unit.state
    COMMENT = 4  # pootle_store.models.Unit.translator_comment

    NAMES_MAP = {
        NONE: "",
        SOURCE: _("Source"),
        TARGET: _("Target"),
        STATE: _("State"),
        COMMENT: _("Comment"),
    }


class Submission(models.Model):
    class Meta:
        ordering = ["creation_time"]
        get_latest_by = "creation_time"
        db_table = 'pootle_app_submission'

    objects = RelatedManager()
    simple_objects = models.Manager()

    creation_time = models.DateTimeField(db_index=True)
    translation_project = models.ForeignKey(
            'pootle_translationproject.TranslationProject', db_index=True
    )
    submitter = models.ForeignKey('pootle_profile.PootleProfile', null=True,
            db_index=True)
    suggestion = models.ForeignKey('pootle_store.Suggestion', blank=True,
            null=True, db_index=True)
    unit = models.ForeignKey('pootle_store.Unit', blank=True, null=True,
            db_index=True)
    check = models.ForeignKey('pootle_store.QualityCheck', blank=True, null=True,
            db_index=True)
    store = models.ForeignKey('pootle_store.Store', blank=True, null=True,
            db_index=True)

    #: The field in the unit that changed
    field = models.IntegerField(null=True, blank=True, db_index=True)
    # how did this submission come about? (one of the constants above)
    type = models.IntegerField(null=True, blank=True, db_index=True)
    # old_value and new_value can store string representations of multistrings
    # in the case where they store values for a unit's source or target. In
    # such cases, the strings might not be usable as is. Use the two helper
    # functions in pootle_store.fields to convert to and from this format.
    old_value = models.TextField(blank=True, default=u"")
    new_value = models.TextField(blank=True, default=u"")

    # similarity ratio to the best existing suggestion
    similarity = models.FloatField(blank=True, null=True)
    # similarity ratio to the result of machine translation
    mt_similarity = models.FloatField(blank=True, null=True)

    def __unicode__(self):
        return u"%s (%s)" % (self.creation_time.strftime("%Y-%m-%d %H:%M"),
                             unicode(self.submitter))

    @cached_property
    def max_similarity(self):
        """Returns current submission's maximum similarity."""
        if (self.similarity is not None or
            self.mt_similarity is not None):
            return max(self.similarity, self.mt_similarity)

        return 0

    def needs_scorelog(self):
        """Returns ``True`` if the submission needs to log its score."""
        # Changing from untranslated state won't record a score change
        if (self.field == SubmissionFields.STATE and
            int(self.old_value) == UNTRANSLATED):
            return False

        return True


    def as_html(self):
        return self.get_submission_message()

    def get_submission_message(self):
        """Returns a message describing the submission.

        The message includes the user (with link to profile and gravatar), a
        message describing the action performed, and when it was performed.
        """

        unit = None
        if self.unit is not None:
            unit = {
                'source': escape(truncatechars(self.unit, 50)),
                'url': self.unit.get_translate_url(),
            }

            if self.check is not None:
                unit['check_name'] = self.check.name
                unit['check_display_name'] = check_names[self.check.name]
                unit['checks_url'] = reverse('pootle-staticpages-display',
                                             args=['help/quality-checks'])

        if (self.suggestion and
            self.type in (SubmissionTypes.SUGG_ACCEPT, SubmissionTypes.SUGG_REJECT)):
            displayuser = self.suggestion.reviewer
        else:
            # Sadly we may not have submitter information in all the
            # situations yet
            # TODO check if it is true
            if self.submitter:
                displayuser = self.submitter
            else:
                displayuser = User.objects.get_nobody_user().get_profile()

        displayname = displayuser.fullname
        if not displayname:
            displayname = displayuser.user.username

        action_bundle = {
            "profile_url": displayuser.get_absolute_url(),
            "gravatar_url": displayuser.gravatar_url(20),
            "displayname": displayname,
            "username": displayuser.user.username,
            "date": self.creation_time,
            "isoformat_date": self.creation_time.isoformat(),
            "action": "",
        }

        action_bundle["action"] = {
            SubmissionTypes.REVERT: _(
                'reverted translation for '
                '<i><a href="%(url)s">%(source)s</a></i>',
                unit
            ),
            SubmissionTypes.SUGG_ACCEPT: _(
                'accepted suggestion for '
                '<i><a href="%(url)s">%(source)s</a></i>',
                unit
            ),
            SubmissionTypes.SUGG_ADD: _(
                'added suggestion for '
                '<i><a href="%(url)s">%(source)s</a></i>',
                unit
            ),
            SubmissionTypes.SUGG_REJECT: _(
                'rejected suggestion for '
                '<i><a href="%(url)s">%(source)s</a></i>',
                unit
            ),
            SubmissionTypes.UPLOAD: _(
                'uploaded a file'
            ),
            SubmissionTypes.MUTE_CHECK: _(
                'muted '
                '<a href="%(checks_url)s#%(check_name)s">%(check_display_name)s</a>'
                ' check for <i><a href="%(url)s">%(source)s</a></i>',
                unit
            ),
            SubmissionTypes.UNMUTE_CHECK: _(
                'unmuted '
                '<a href="%(checks_url)s#%(check_name)s">%(check_display_name)s</a>'
                ' check for <i><a href="%(url)s">%(source)s</a></i>',
                unit
            ),
        }.get(self.type, '')

        #TODO Look how to detect submissions for "sent suggestion", "rejected
        # suggestion"...

        #TODO Fix bug 3011 and replace the following code with the appropiate
        # one in the dictionary above.

        if not action_bundle["action"]:
            try:
                # If the action is unset, maybe the action is one of the
                # following ones.
                action_bundle["action"] = {
                    TRANSLATED: _(
                        'translated '
                        '<i><a href="%(url)s">%(source)s</a></i>',
                        unit
                    ),
                    FUZZY: _(
                        'pre-translated '
                        '<i><a href="%(url)s">%(source)s</a></i>',
                        unit
                    ),
                    UNTRANSLATED: _(
                        'removed translation for '
                        '<i><a href="%(url)s">%(source)s</a></i>',
                        unit
                    ),
                }.get(self.unit.state, '')
            except AttributeError:
                return ''

        return mark_safe(
            u'<div class="last-action">'
            '  <a href="%(profile_url)s">'
            '    <img src="%(gravatar_url)s" />'
            '    <span title="%(username)s">%(displayname)s</span>'
            '  </a>'
            '  <span class="action-text">%(action)s</span>'
            '  <time class="extra-item-meta js-relative-date"'
            '    title="%(date)s" datetime="%(isoformat_date)s">&nbsp;'
            '  </time>'
            '</div>'
            % action_bundle)

    def save(self, *args, **kwargs):
        super(Submission, self).save(*args, **kwargs)

        if self.needs_scorelog():
            ScoreLog.record_submission(submission=self)


class TranslationActionCodes(object):
    NEW = 0  # 'TA' unit translated
    EDITED = 1  # 'TE' unit edited after someone else
    EDITED_OWN = 2  # 'TX' unit edited after themselves
    DELETED = 3  # 'TD' translation deleted by admin
    REVIEWED = 4  # 'R' translation reviewed
    MARKED_FUZZY = 5  # 'TF' translation’s fuzzy flag is set by admin
    EDIT_PENALTY = 6  # 'XE' translation penalty [when translation deleted]
    REVIEW_PENALTY = 7  # 'XR' translation penalty [when review canceled]
    SUGG_ADDED = 8  # 'S' suggestion added
    SUGG_ACCEPTED = 9  # 'SA' suggestion accepted (counted towards the suggestion author)
    SUGG_REJECTED = 10  # 'SR' suggestion rejected (counted towards the suggestion author)
    SUGG_REVIEWED_ACCEPTED = 11  # 'RA' suggestion accepted (counted towards the reviewer)
    SUGG_REVIEWED_REJECTED = 12  # 'RR' suggestion rejected (counted towards the reviewer)

    NAMES_MAP = {
        NEW: 'TA',
        EDITED: 'TE',
        EDITED_OWN: 'TX',
        DELETED: 'TD',
        REVIEWED: 'R',
        EDIT_PENALTY: 'XE',
        REVIEW_PENALTY: 'XR',
        MARKED_FUZZY: 'TF',
        SUGG_ADDED: 'S',
        SUGG_ACCEPTED: 'SA',
        SUGG_REJECTED: 'SR',
        SUGG_REVIEWED_ACCEPTED: 'RA',
        SUGG_REVIEWED_REJECTED: 'RR',
    }


class ScoreLog(models.Model):
    creation_time = models.DateTimeField(db_index=True, null=False)
    user = models.ForeignKey('pootle_profile.PootleProfile', null=False)
    # current user’s new translation rate
    rate = models.FloatField(null=False, default=0)
    # current user’s review rate
    review_rate = models.FloatField(null=False, default=0)
    # number of words in the original source string
    wordcount = models.PositiveIntegerField(null=False)
    # the reported similarity ratio
    similarity = models.FloatField(null=False)
    # the final calculated score delta for the action
    score_delta = models.FloatField(null=False)
    action_code = models.IntegerField(null=False)
    submission = models.ForeignKey(Submission, null=False)

    @classmethod
    def record_submission(cls, submission):
        """Records a new log entry for ``submission``."""
        score_dict = {
            'creation_time': submission.creation_time,
            'wordcount': submission.unit.source_wordcount,
            'similarity': submission.max_similarity,
            'submission': submission,
        }

        translator = submission.unit.submitted_by
        if submission.unit.reviewed_by:
            reviewer = submission.unit.reviewed_by
        else:
            reviewer = translator

        previous_translator_score = score_dict.copy()
        previous_translator_score['user'] = translator
        previous_reviewer_score = score_dict.copy()
        previous_reviewer_score['user'] = reviewer
        submitter_score = score_dict.copy()
        submitter_score['user'] = submission.submitter
        suggester_score = score_dict.copy()
        if submission.suggestion is not None:
            suggester_score['user'] = submission.suggestion.user

        edit_types = [SubmissionTypes.NORMAL, SubmissionTypes.SYSTEM]
        if (submission.field == SubmissionFields.TARGET and
            submission.type in edit_types):
            if submission.old_value == '' and submission.new_value != '':
                submitter_score['action_code'] = TranslationActionCodes.NEW
            else:
                if submission.new_value == '':
                    submitter_score['action_code'] = \
                        TranslationActionCodes.DELETED

                    previous_translator_score['action_code'] = \
                        TranslationActionCodes.EDIT_PENALTY

                    previous_reviewer_score['action_code'] = \
                        TranslationActionCodes.REVIEW_PENALTY
                else:
                    if (reviewer is not None and
                        submission.submitter.id == reviewer.id):
                        submitter_score['action_code'] = \
                            TranslationActionCodes.EDITED_OWN
                    else:
                        submitter_score['action_code'] = \
                            TranslationActionCodes.EDITED

                        previous_reviewer_score['action_code'] = \
                            TranslationActionCodes.REVIEW_PENALTY

        elif submission.field == SubmissionFields.STATE:
            if (int(submission.old_value) == FUZZY and
                int(submission.new_value) == TRANSLATED and
                not submission.unit._target_updated):
                submitter_score['action_code'] = TranslationActionCodes.REVIEWED

            elif (int(submission.old_value) == TRANSLATED and
                  int(submission.new_value) == FUZZY):
                submitter_score['action_code'] = \
                    TranslationActionCodes.MARKED_FUZZY
                previous_reviewer_score['action_code'] = \
                    TranslationActionCodes.REVIEW_PENALTY

        elif submission.type == SubmissionTypes.SUGG_ADD:
            submitter_score['action_code'] = TranslationActionCodes.SUGG_ADDED

        elif submission.type == SubmissionTypes.SUGG_ACCEPT:
            submitter_score['action_code'] = \
                TranslationActionCodes.SUGG_REVIEWED_ACCEPTED
            suggester_score['action_code'] = \
                TranslationActionCodes.SUGG_ACCEPTED
            previous_reviewer_score['action_code'] = \
                TranslationActionCodes.REVIEW_PENALTY

        elif submission.type == SubmissionTypes.SUGG_REJECT:
            submitter_score['action_code'] = \
                TranslationActionCodes.SUGG_REVIEWED_REJECTED
            suggester_score['action_code'] = TranslationActionCodes.SUGG_REJECTED

        for score in [submitter_score, previous_translator_score,
                      previous_reviewer_score, suggester_score]:
            if 'action_code' in score and score['user'] is not None:
               ScoreLog.objects.create(**score)

    def save(self, *args, **kwargs):
        # copy current user rate
        self.rate = self.user.rate
        self.review_rate = self.user.review_rate
        self.score_delta = self.get_score_delta()

        super(ScoreLog, self).save(*args, **kwargs)

        self.user.score += self.score_delta
        self.user.save()
        self.log()

    def log(self):
        d = {
            'user': self.user,
            'action': SCORE_CHANGED,
            'score_delta': self.score_delta,
            'code': TranslationActionCodes.NAMES_MAP[self.action_code],
            'unit': self.submission.unit.id,
            'wordcount': self.wordcount,
            'similarity': self.similarity,
            'total': self.user.score,
        }

        params = ['%(user)s', '%(action)s', '%(score_delta)s',
                  '%(code)s', '#%(unit)s']

        zero_types = [
            TranslationActionCodes.MARKED_FUZZY,
            TranslationActionCodes.DELETED,
        ]
        no_similarity_types = [
            TranslationActionCodes.SUGG_REVIEWED_REJECTED,
            TranslationActionCodes.SUGG_REVIEWED_ACCEPTED,
            TranslationActionCodes.REVIEW_PENALTY,
            TranslationActionCodes.REVIEWED,
        ]

        if self.action_code not in zero_types:
            params.append('NS=%(wordcount)s')

            if self.action_code not in no_similarity_types:
                  params.append('S=%(similarity)s')

        params.append('(total: %(total)s)')

        log("\t".join(params) % d)

    def get_score_delta(self):
        """Returns the score change performed by the current action."""
        ns = self.wordcount
        s = self.similarity
        rawTranslationCost = ns * EDIT_COEF * (1 - s)
        reviewCost = ns * REVIEW_COEF
        analyzeCost = ns * ANALYZE_COEF

        def get_sugg_rejected():
            try:
                s = self.submission.suggestion.submission_set \
                        .get(type=SubmissionTypes.SUGG_ADD) \
                        .similarity
                self.similarity = 0 if s is None else s
                rawTranslationCost = ns * EDIT_COEF * (1 - s)
            except:
                rawTranslationCost = 0

            return (-1) * (rawTranslationCost * SUGG_COEF + analyzeCost)

        def get_edit_penalty():
            try:
                s = Submission.objects.get(
                    unit__id=self.submission.unit_id,
                    submitter__id=self.submission.unit.submitted_by_id,
                    creation_time=self.submission.unit.submitted_on,
                    field=SubmissionFields.TARGET,
                    type=SubmissionTypes.NORMAL
                ).similarity
                self.similarity = 0 if s is None else s
                rawTranslationCost = ns * EDIT_COEF * (1 - s)
            except:
                rawTranslationCost = 0

            return (-1) * rawTranslationCost

        def get_sugg_accepted():
            try:
                s = self.submission.suggestion.submission_set \
                        .get(type=SubmissionTypes.SUGG_ADD) \
                        .similarity
                self.similarity = 0 if s is None else s
                rawTranslationCost = ns * EDIT_COEF * (1 - s)
            except:
                rawTranslationCost = 0

            return rawTranslationCost * (1 - SUGG_COEF)

        return {
            TranslationActionCodes.NEW: lambda: rawTranslationCost + reviewCost,
            TranslationActionCodes.EDITED: lambda: rawTranslationCost + reviewCost,
            TranslationActionCodes.EDITED_OWN: lambda: rawTranslationCost,
            TranslationActionCodes.REVIEWED: lambda: reviewCost,
            TranslationActionCodes.EDIT_PENALTY: get_edit_penalty,
            TranslationActionCodes.MARKED_FUZZY: lambda: 0,
            TranslationActionCodes.DELETED: lambda: 0,
            TranslationActionCodes.REVIEW_PENALTY: lambda: (-1) * reviewCost,
            TranslationActionCodes.SUGG_ADDED: lambda: rawTranslationCost * SUGG_COEF,
            TranslationActionCodes.SUGG_ACCEPTED: get_sugg_accepted,
            TranslationActionCodes.SUGG_REVIEWED_ACCEPTED: lambda: reviewCost,
            TranslationActionCodes.SUGG_REJECTED: get_sugg_rejected,
            TranslationActionCodes.SUGG_REVIEWED_REJECTED: lambda: analyzeCost,
        }.get(self.action_code, 0)()

    def get_paid_words(self):
        """Returns the translated and reviewed words in the current action."""
        ns = self.wordcount
        s = self.similarity
        translated_words = ns * (1 - s)
        reviewed_words = ns

        def get_sugg_reviewed_accepted():
            suggester = self.submission.suggestion.user.pk
            reviewer = self.submission.submitter.pk
            if suggester == reviewer:
                if self.submission.old_value == '':
                    return translated_words, 0
            else:
                return 0, reviewed_words

            return 0, 0

        def get_sugg_accepted():
            suggester = self.submission.suggestion.user.pk
            reviewer = self.submission.submitter.pk
            if suggester != reviewer:
                if self.submission.old_value == '':
                    return translated_words, 0

            return 0, 0

        return {
            TranslationActionCodes.NEW: lambda: (translated_words, 0),
            TranslationActionCodes.EDITED: lambda: (0, reviewed_words),
            TranslationActionCodes.REVIEWED: lambda: (0, reviewed_words),
            TranslationActionCodes.SUGG_ACCEPTED: get_sugg_accepted,
            TranslationActionCodes.SUGG_REVIEWED_ACCEPTED: get_sugg_reviewed_accepted,
        }.get(self.action_code, lambda:(0, 0))()
