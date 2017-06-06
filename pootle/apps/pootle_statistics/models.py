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
from django.template.defaultfilters import truncatechars
from django.urls import reverse

from pootle.core.user import get_system_user
from pootle.core.utils import dateformat
from pootle.i18n.gettext import ugettext_lazy as _
from pootle_checks.constants import CHECK_NAMES
from pootle_store.constants import FUZZY, TRANSLATED
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
        CHECK: (_("Check")),
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
        index_together = ["submitter", "creation_time"]
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
        db_index=False,
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
                    'check_display_name': CHECK_NAMES.get(check_name,
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
