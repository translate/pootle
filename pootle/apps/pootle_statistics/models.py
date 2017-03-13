# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F
from django.template.defaultfilters import truncatechars
from django.urls import reverse

from pootle.core.log import SCORE_CHANGED, log
from pootle.core.utils import dateformat
from pootle.core.user import get_system_user
from pootle.i18n.gettext import ugettext_lazy as _
from pootle_misc.checks import check_names
from pootle_store.constants import FUZZY, TRANSLATED, UNTRANSLATED
from pootle_store.fields import to_python


MUTED = "0"
SIMILARITY_THRESHOLD = 0.5
UNMUTED = "1"


#: These are the values for the 'type' field of Submission
class SubmissionTypes(object):
    # None/0 = no information
    WEB = 1  # Interactive web editing
    UPLOAD = 4  # Uploading an offline file
    SYSTEM = 5  # Batch actions performed offline

    # Combined types that rely on other types (useful for querying)
    # Please use the `_TYPES` suffix to make it clear they're not core
    # types that are stored in the DB

    EDIT_TYPES = [WEB, SYSTEM, UPLOAD]
    CONTRIBUTION_TYPES = [WEB, SYSTEM]


#: Values for the 'field' field of Submission
class SubmissionFields(object):
    NONE = 0  # non-field submission
    SOURCE = 1  # pootle_store.models.Unit.source
    TARGET = 2  # pootle_store.models.Unit.target
    STATE = 3  # pootle_store.models.Unit.state
    COMMENT = 4  # pootle_store.models.Unit.translator_comment
    CHECK = 5

    TRANSLATION_FIELDS = [TARGET]

    NAMES_MAP = {
        NONE: "",
        SOURCE: _("Source"),
        TARGET: _("Target"),
        STATE: _("State"),
        COMMENT: _("Comment"),
    }


class TranslationActionTypes(object):
    TRANSLATED = 0
    EDITED = 1
    PRE_TRANSLATED = 2
    REMOVED = 3
    REVIEWED = 4
    NEEDS_WORK = 5


class SubmissionQuerySet(models.QuerySet):

    def _earliest_or_latest(self, field_name=None, direction="-"):
        """
        Overrides QuerySet._earliest_or_latest to add pk for secondary ordering
        """
        order_by = field_name or getattr(self.model._meta, 'get_latest_by')
        assert bool(order_by), "earliest() and latest() require either a "\
            "field_name parameter or 'get_latest_by' in the model"
        assert self.query.can_filter(), \
            "Cannot change a query once a slice has been taken."
        obj = self._clone()
        obj.query.set_limits(high=1)
        obj.query.clear_ordering(force_empty=True)
        # add pk as secondary ordering for Submissions
        obj.query.add_ordering('%s%s' % (direction, order_by),
                               '%s%s' % (direction, "pk"))
        return obj.get()

    def earliest(self, field_name=None):
        return self._earliest_or_latest(field_name=field_name, direction="")

    def latest(self, field_name=None):
        return self._earliest_or_latest(field_name=field_name, direction="-")


class SubmissionManager(models.Manager):

    def get_queryset(self):
        return SubmissionQuerySet(self.model, using=self._db)

    def get_unit_comments(self):
        """Submissions that change a `Unit`'s comment.

        :return: Queryset of `Submissions`s that change a `Unit`'s comment.
        """
        return self.get_queryset().filter(field=SubmissionFields.COMMENT)

    def get_unit_edits(self):
        """`Submission`s that change a `Unit`'s `target`.

        :return: Queryset of `Submissions`s that change a `Unit`'s target.
        """
        return (
            self.get_queryset().exclude(new_value__isnull=True).filter(
                field__in=SubmissionFields.TRANSLATION_FIELDS,
                type__in=SubmissionTypes.EDIT_TYPES,
            )
        )

    def get_unit_state_changes(self):
        """Submissions that change a unit's STATE.

        :return: Queryset of `Submissions`s change a `Unit`'s `STATE`
            - ie FUZZY/TRANSLATED/UNTRANSLATED.
        """
        return self.get_queryset().filter(field=SubmissionFields.STATE)

    def get_unit_suggestion_reviews(self):
        """Submissions that review (reject/accept) `Unit` suggestions.

        :return: Queryset of `Submissions`s that `REJECT`/`ACCEPT`
            `Suggestion`s.
        """
        # reject_suggestion does not set field so we must exclude STATE reviews
        # and it seems there are submissions that use STATE and are in
        # REVIEW_TYPES
        return (self.get_queryset().exclude(
            field=SubmissionFields.STATE).filter(
                suggestion__isnull=False))


class Submission(models.Model):
    class Meta(object):
        ordering = ["creation_time", "pk"]
        index_together = ["submitter", "creation_time", "id"]
        get_latest_by = "creation_time"
        db_table = 'pootle_app_submission'
        base_manager_name = 'objects'

    objects = SubmissionManager()

    creation_time = models.DateTimeField(db_index=True)
    translation_project = models.ForeignKey(
        'pootle_translationproject.TranslationProject',
        db_index=True, on_delete=models.CASCADE)
    submitter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        db_index=True,
        on_delete=models.SET(get_system_user))
    suggestion = models.ForeignKey('pootle_store.Suggestion', blank=True,
                                   null=True, db_index=True,
                                   on_delete=models.CASCADE)
    unit = models.ForeignKey('pootle_store.Unit', blank=True, null=True,
                             db_index=True, on_delete=models.CASCADE)
    quality_check = models.ForeignKey('pootle_store.QualityCheck', blank=True,
                                      null=True, db_index=True,
                                      on_delete=models.CASCADE)

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

    # Unit revision when submission was created if applicable
    revision = models.IntegerField(
        null=True,
        db_index=True,
        blank=True)

    def __unicode__(self):
        return u"%s (%s)" % (self.creation_time.strftime("%Y-%m-%d %H:%M"),
                             unicode(self.submitter))

    def needs_scorelog(self):
        """Returns ``True`` if the submission needs to log its score."""
        # Changing from untranslated state won't record a score change
        not_needed = (
            (self.field == SubmissionFields.STATE
             and int(self.old_value) == UNTRANSLATED)
            or (self.submitter
                and (self.submitter.username
                     in get_user_model().objects.META_USERS)))
        if not_needed:
            return False
        return True

    def get_submission_info(self):
        """Returns a dictionary describing the submission.

        The dict includes the user (with link to profile and gravatar),
        a type and translation_action_type describing the action performed,
        and when it was performed.
        """
        result = {}

        if self.unit is not None:
            result.update({
                'unit_source': truncatechars(self.unit, 50),
                'unit_url': self.unit.get_translate_url(),
            })

            if self.quality_check is not None:
                check_name = self.quality_check.name
                result.update({
                    'check_name': check_name,
                    'check_display_name': check_names.get(check_name,
                                                          check_name),
                    'checks_url': reverse('pootle-checks-descriptions'),
                })
        # Sadly we may not have submitter information in all the
        # situations yet
        # TODO check if it is true
        if self.submitter:
            displayuser = self.submitter
        else:
            User = get_user_model()
            displayuser = User.objects.get_nobody_user()

        result.update({
            "profile_url": displayuser.get_absolute_url(),
            "email": displayuser.email_hash,
            "displayname": displayuser.display_name,
            "username": displayuser.username,
            "display_datetime": dateformat.format(self.creation_time),
            "type": self.type,
            "mtime": int(dateformat.format(self.creation_time, 'U')),
        })

        # TODO Fix bug 3011 and remove the following code related to
        # TranslationActionTypes.

        if self.type in SubmissionTypes.EDIT_TYPES:
            translation_action_type = None
            try:
                if self.field == SubmissionFields.TARGET:
                    if self.new_value != '':
                        # Note that we analyze current unit state:
                        # if this submission is not last unit state
                        # can be changed
                        if self.unit.state == TRANSLATED:

                            if self.old_value == '':
                                translation_action_type = \
                                    TranslationActionTypes.TRANSLATED
                            else:
                                translation_action_type = \
                                    TranslationActionTypes.EDITED
                        elif self.unit.state == FUZZY:
                            if self.old_value == '':
                                translation_action_type = \
                                    TranslationActionTypes.PRE_TRANSLATED
                            else:
                                translation_action_type = \
                                    TranslationActionTypes.EDITED
                    else:
                        translation_action_type = \
                            TranslationActionTypes.REMOVED
                elif self.field == SubmissionFields.STATE:
                    # Note that a submission where field is STATE
                    # should be created before a submission where
                    # field is TARGET

                    translation_action_type = {
                        TRANSLATED: TranslationActionTypes.REVIEWED,
                        FUZZY: TranslationActionTypes.NEEDS_WORK
                    }.get(int(to_python(self.new_value)), None)

            except AttributeError:
                return result

            if translation_action_type is not None:
                result['translation_action_type'] = translation_action_type

        return result

    def save(self, *args, **kwargs):
        if self.unit:
            self.revision = self.unit.revision
        super(Submission, self).save(*args, **kwargs)

        if not self.needs_scorelog():
            return

        meta_users = get_user_model().objects.META_USERS
        system_users = get_user_model().objects.filter(
            username__in=meta_users).values_list("id", flat=True)

        scorelogs_created = []
        for score in ScoreLog.get_scorelogs(submission=self):
            if score.get("user") and score["user"].id in system_users:
                continue
            if 'action_code' in score and score['user'] is not None:
                scorelogs_created.append(ScoreLog(**score))
        if scorelogs_created:
            self.scorelog_set.add(*scorelogs_created, bulk=False)


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
    # 'SA' suggestion accepted (counted towards the suggestion author)
    SUGG_ACCEPTED = 9
    # 'SR' suggestion rejected (counted towards the suggestion author)
    SUGG_REJECTED = 10
    # 'RA' suggestion accepted (counted towards the reviewer)
    SUGG_REVIEWED_ACCEPTED = 11
    # 'RR' suggestion rejected (counted towards the reviewer)
    SUGG_REVIEWED_REJECTED = 12

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False,
                             on_delete=models.CASCADE)
    # number of words in the original source string
    wordcount = models.PositiveIntegerField(null=False)
    # the final calculated score delta for the action
    score_delta = models.FloatField(null=False)
    action_code = models.IntegerField(null=False)
    submission = models.ForeignKey(Submission, null=False,
                                   on_delete=models.CASCADE)
    translated_wordcount = models.PositiveIntegerField(null=True)

    class Meta(object):
        unique_together = ('submission', 'action_code')

    @classmethod
    def get_scorelogs(cls, submission):
        """Records a new log entry for ``submission``."""
        score_dict = {
            'creation_time': submission.creation_time,
            'wordcount': submission.unit.source_wordcount,
            'submission': submission,
        }

        translator_id = (
            submission.unit.changed
            and submission.unit.change.submitted_by_id)
        if submission.unit.changed and submission.unit.change.reviewed_by_id:
            reviewer_id = submission.unit.change.reviewed_by_id
        else:
            reviewer_id = translator_id

        previous_translator_score = score_dict.copy()
        previous_reviewer_score = score_dict.copy()
        submitter_score = score_dict.copy()
        submitter_score['user'] = submission.submitter
        suggester_score = score_dict.copy()
        if submission.suggestion is not None:
            suggester_score['user'] = submission.suggestion.user

        if (submission.field == SubmissionFields.TARGET and
            submission.type in SubmissionTypes.EDIT_TYPES):
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
                    if (reviewer_id is not None and
                        submission.submitter_id == reviewer_id):
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
                not submission.unit.target_updated):
                submitter_score['action_code'] = \
                    TranslationActionCodes.REVIEWED

            elif (int(submission.old_value) == TRANSLATED and
                  int(submission.new_value) == FUZZY):
                submitter_score['action_code'] = \
                    TranslationActionCodes.MARKED_FUZZY
                previous_reviewer_score['action_code'] = \
                    TranslationActionCodes.REVIEW_PENALTY

        if 'action_code' in previous_translator_score:
            previous_translator_score['user'] = submission.unit.change.submitted_by
        if 'action_code' in previous_reviewer_score:
            previous_reviewer_score['user'] = (
                submission.unit.change.reviewed_by
                if submission.unit.change.reviewed_by_id
                else submission.unit.change.submitted_by)
        return [submitter_score, previous_translator_score,
                previous_reviewer_score, suggester_score]

    def save(self, *args, **kwargs):
        self.score_delta = self.get_score_delta()
        translated = self.get_paid_wordcounts()[0]
        self.translated_wordcount = translated

        super(ScoreLog, self).save(*args, **kwargs)

        User = get_user_model()
        User.objects.filter(id=self.user.id).update(
            score=F('score') + self.score_delta
        )
        self.log()

    def log(self):
        d = {
            'user': self.user,
            'action': SCORE_CHANGED,
            'score_delta': self.score_delta,
            'code': TranslationActionCodes.NAMES_MAP[self.action_code],
            'unit': self.submission.unit.id,
            'wordcount': self.wordcount,
            'total': self.user.score,
        }

        params = ['%(user)s', '%(action)s', '%(score_delta)s',
                  '%(code)s', '#%(unit)s']

        zero_types = [
            TranslationActionCodes.MARKED_FUZZY,
            TranslationActionCodes.DELETED,
        ]

        if self.action_code not in zero_types:
            params.append('NS=%(wordcount)s')

        params.append('(total: %(total)s)')

        log("\t".join(params) % d)

    def get_score_delta(self):
        """Returns the score change performed by the current action."""
        EDIT_COEF = settings.POOTLE_SCORE_COEFFICIENTS['EDIT']
        REVIEW_COEF = settings.POOTLE_SCORE_COEFFICIENTS['REVIEW']

        ns = self.wordcount
        rawTranslationCost = ns * EDIT_COEF
        reviewCost = ns * REVIEW_COEF

        return {
            TranslationActionCodes.NEW:
                lambda: rawTranslationCost + reviewCost,
            TranslationActionCodes.EDITED:
                lambda: rawTranslationCost + reviewCost,
            TranslationActionCodes.EDITED_OWN: lambda: rawTranslationCost,
            TranslationActionCodes.REVIEWED: lambda: reviewCost,
            TranslationActionCodes.MARKED_FUZZY: lambda: 0,
            TranslationActionCodes.DELETED: lambda: 0,
            TranslationActionCodes.REVIEW_PENALTY: lambda: (-1) * reviewCost,
        }.get(self.action_code, lambda: 0)()

    def get_paid_wordcounts(self):
        """Returns the translated and reviewed wordcount in the current
        action.
        """

        EDIT_COEF = settings.POOTLE_SCORE_COEFFICIENTS['EDIT']
        REVIEW_COEF = settings.POOTLE_SCORE_COEFFICIENTS['REVIEW']

        ns = self.wordcount

        rate = EDIT_COEF + REVIEW_COEF
        review_rate = REVIEW_COEF
        raw_rate = rate - review_rate

        # if similarity is zero then translated_words would be
        # ns * (1 - s), that equals sum of raw_translation and
        # review costs divided by translation_rate
        translated_words = (ns * raw_rate + ns * review_rate) / rate
        translated_words = round(translated_words, 4)
        reviewed_words = ns

        def get_edited():
            return None, reviewed_words

        return {
            TranslationActionCodes.NEW: lambda: (translated_words, None),
            TranslationActionCodes.EDITED: get_edited,
            TranslationActionCodes.REVIEWED: lambda: (None, reviewed_words),
        }.get(self.action_code, lambda: (None, None))()
