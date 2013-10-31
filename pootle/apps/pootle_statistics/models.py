#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
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

from django.db import models
from django.template.defaultfilters import escape, truncatechars
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from pootle.core.managers import RelatedManager
from pootle_store.util import FUZZY, TRANSLATED, UNTRANSLATED


#: These are the values for the 'type' field of Submission
class SubmissionTypes(object):
    # None/0 = no information
    NORMAL = 1  # Interactive web editing
    REVERT = 2  # Revert action on the web
    SUGG_ACCEPT = 3  # Accepting a suggestion
    UPLOAD = 4  # Uploading an offline file


#: Values for the 'field' field of Submission
class SubmissionFields(object):
    SOURCE = 1  # pootle_store.models.Unit.source
    TARGET = 2  # pootle_store.models.Unit.target
    STATE = 3  # pootle_store.models.Unit.state
    COMMENT = 4  # pootle_store.models.Unit.translator_comment

    NAMES_MAP = {
        SOURCE: _("Source"),
        TARGET: _("Target"),
        STATE: _("State"),
        COMMENT: _("Comment"),
    }


class Submission(models.Model):

    creation_time = models.DateTimeField(db_index=True)
    translation_project = models.ForeignKey(
            'pootle_translationproject.TranslationProject', db_index=True
    )
    submitter = models.ForeignKey('pootle_profile.PootleProfile', null=True,
                                  db_index=True)
    from_suggestion = models.OneToOneField('pootle_app.Suggestion', null=True,
                                           db_index=True)
    unit = models.ForeignKey('pootle_store.Unit', blank=True, null=True,
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

    objects = RelatedManager()

    class Meta:
        ordering = ["creation_time"]
        get_latest_by = "creation_time"
        db_table = 'pootle_app_submission'

    def __unicode__(self):
        return u"%s (%s)" % (self.creation_time.strftime("%Y-%m-%d %H:%M"),
                             unicode(self.submitter))

    @classmethod
    def get_latest_for_dir(cls, directory):
        """Returns the latest submission, if any, for the given directory.

        The submission is returned as an action bundle. An empty string is
        returned if no submission exists for the given directory.
        """
        try:
            criteria = {
                'unit__store__pootle_path__startswith': directory.pootle_path,
            }
            sub = Submission.objects.filter(**criteria).latest()
        except Submission.DoesNotExist:
            return ''
        return sub.get_submission_message()

    def as_html(self):
        # Sadly we may not have submitter information in all the situations yet
        if self.submitter:
            submitter_info = u'<a href="%(profile_url)s">%(submitter)s</a>' % {
                    'profile_url': self.submitter.get_absolute_url(),
                    'submitter': unicode(self.submitter),
                }
        else:
            submitter_info = _("anonymous user")

        snippet = u'%(time)s (%(submitter_info)s)' % {
                    'time': self.creation_time.strftime("%Y-%m-%d %H:%M"),
                    'submitter_info': submitter_info,
                }

        return mark_safe(snippet)

    def get_submission_message(self):
        """Returns a message describing the submission.

        The message includes the user (with link to profile and gravatar), a
        message describing the action performed, and when it was performed.
        """

        action_bundle = {
            "profile_url": self.submitter.get_absolute_url(),
            "gravatar_url": self.submitter.gravatar_url(20),
            "username": self.submitter.user.username,
        }

        unit = {
            'user': ('  <a href="%(profile_url)s">'
                     '    <span>%(username)s</span>'
                     '  </a>') % action_bundle,
        }

        if self.unit is not None:
            unit.update({
                'source': escape(truncatechars(self.unit, 50)),
                'url': self.unit.get_absolute_url(),
            })

        action_bundle.update({
            "date": self.creation_time,
            "isoformat_date": self.creation_time.isoformat(),
            "action": {
                SubmissionTypes.REVERT: _('%(user)s reverted translation for '
                                          'string <i><a href="%(url)s">'
                                          '%(source)s</a></i>', unit),
                SubmissionTypes.SUGG_ACCEPT: _('%(user)s accepted suggestion '
                                               'for string <i><a href="%(url)s">'
                                               '%(source)s</a></i>', unit),
                SubmissionTypes.UPLOAD: _('%(user)s uploaded a file', unit),
            }.get(self.type, ''),
        })

        #TODO Look how to detect submissions for "sent suggestion", "rejected
        # suggestion"...

        #TODO Fix bug 3011 and replace the following code with the appropiate
        # one in the dictionary above.

        if not action_bundle["action"]:
            try:
                # If the action is unset, maybe the action is one of the
                # following ones.
                action_bundle["action"] = {
                    TRANSLATED: _('%(user)s submitted translation for string '
                                  '<i><a href="%(url)s">%(source)s</a></i>',
                                  unit),
                    FUZZY: _('%(user)s submitted "needs work" translation for '
                             'string <i><a href="%(url)s">%(source)s</a></i>',
                             unit),
                    UNTRANSLATED: _('%(user)s removed translation for string '
                                    '<i><a href="%(url)s">%(source)s</a></i>',
                                    unit),
                }.get(self.unit.state, '')
            except AttributeError:
                return ''

        # If it is not possible to provide the action performed, then it is
        # better to not return anything at all.
        if not action_bundle["action"]:
            return ''

        return (u'<div class="last-action">'
            '  <a href="%(profile_url)s">'
            '    <img src="%(gravatar_url)s" />'
            '  </a>'
            '  %(action)s'
            '  <time class="extra-item-meta js-relative-date"'
            '    title="%(date)s" datetime="%(isoformat_date)s">&nbsp;'
            '  </time>'
            '</div>' % action_bundle)
