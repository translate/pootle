#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
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

from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from pootle_app.lib.util import RelatedManager
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
    class Meta:
        get_latest_by = "creation_time"
        db_table = 'pootle_app_submission'

    objects = RelatedManager()

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
        return sub.get_as_action_bundle()

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

    def get_as_action_bundle(self):
        """Returns the submission as an action bundle.

        The bundle contains only the data that is necessary for showing the
        GitHub-like latest action message.
        """

        unit = None
        if self.unit:
            unit = {
                'id': self.unit.pk,
                'url': self.unit.get_absolute_url(),
            }

        action_bundle = {
            "action": {
                SubmissionTypes.REVERT: _('reverted translation for '
                                          '<a href="%(url)s">string %(id)d</a>',
                                          unit),
                SubmissionTypes.REVERT: _('reverted translation for '
                                          '<a href="%(url)s">string %(id)d</a>',
                                          unit),
                SubmissionTypes.SUGG_ACCEPT: _('accepted suggestion for '
                                               '<a href="%(url)s">string %(id)d'
                                               '</a>', unit),
                SubmissionTypes.UPLOAD: _('uploaded file'),
            }.get(self.type, ''),
            "by_profile": self.submitter,
            "date": self.creation_time,
            "unit": self.unit,
        }

        #TODO Look how to detect submissions for "sent suggestion", "rejected
        # suggestion"...

        #TODO Fix bug 3011 and replace the following code with the appropiate
        # one in the dictionary above.

        if not action_bundle["action"]:
            # If the action is unset, maybe the action is one of the following.
            action_bundle["action"] = {
                TRANSLATED: _('sent translation for <a href="%(url)s">string '
                              '%(id)d</a>', unit),
                FUZZY: _('sent "needs work" translation for <a href="%(url)s">'
                         'string %(id)d</a>', unit),
                UNTRANSLATED: _('removed translation for <a href="%(url)s">'
                                'string %(id)d</a>', unit),
            }.get(self.unit.state, "")

        return action_bundle
