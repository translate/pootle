#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2014 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import escape, truncatechars
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from pootle.core.managers import RelatedManager
from pootle_misc.checks import check_names
from pootle_store.util import FUZZY, TRANSLATED, UNTRANSLATED


class SubmissionTypes(object):
    """Values for the 'type' field of Submission."""
    # None/0 = no information
    NORMAL = 1  # Interactive web editing
    REVERT = 2  # Revert action on the web
    SUGG_ACCEPT = 3  # Accepting a suggestion
    UPLOAD = 4  # Uploading an offline file
    SYSTEM = 5  # Batch actions performed offline
    MUTE_CHECK = 6  # Mute QualityCheck
    UNMUTE_CHECK = 7  # Unmute QualityCheck


class SubmissionFields(object):
    """Values for the 'field' field of Submission."""
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

    creation_time = models.DateTimeField(db_index=True)
    translation_project = models.ForeignKey(
        'pootle_translationproject.TranslationProject',
        db_index=True,
    )
    submitter = models.ForeignKey(
        'pootle_profile.PootleProfile',
        null=True,
        db_index=True,
    )
    from_suggestion = models.OneToOneField(
        'pootle_app.Suggestion',
        null=True,
        db_index=True,
    )
    unit = models.ForeignKey(
        'pootle_store.Unit',
        blank=True,
        null=True,
        db_index=True,
    )
    check = models.ForeignKey(
        'pootle_store.QualityCheck',
        blank=True,
        null=True,
        db_index=True,
    )
    # The field that was changed in the unit.
    field = models.IntegerField(null=True, blank=True, db_index=True)

    # How did this submission come about? (one of the constants above).
    type = models.IntegerField(null=True, blank=True, db_index=True)

    # old_value and new_value can store string representations of multistrings
    # in the case where they store values for a unit's source or target. In
    # such cases, the strings might not be usable as is. Use the two helper
    # functions in pootle_store.fields to convert to and from this format.
    old_value = models.TextField(blank=True, default=u"")
    new_value = models.TextField(blank=True, default=u"")

    objects = RelatedManager()
    simple_objects = models.Manager()

    class Meta:
        ordering = ["creation_time"]
        get_latest_by = "creation_time"
        db_table = 'pootle_app_submission'

    def __unicode__(self):
        return u"%s (%s)" % (self.creation_time.strftime("%Y-%m-%d %H:%M"),
                             unicode(self.submitter))

    def as_html(self):
        return self.get_submission_message()

    def get_submission_message(self):
        """Return a message describing the submission.

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
                unit['checks_url'] = ('http://docs.translatehouse.org/'
                                      'projects/translate-toolkit/en/latest/'
                                      'commands/pofilter_tests.html')

        if self.from_suggestion:
            displayuser = self.from_suggestion.reviewer
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
