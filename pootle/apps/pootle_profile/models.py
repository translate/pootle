#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.contrib.auth.models import User, UserManager, AnonymousUser
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.utils.html import simple_email_re as email_re
from django.utils.translation import ugettext_lazy as _

from pootle_language.models import Language
from pootle_statistics.models import Submission, SubmissionTypes
from pootle_store.models import SuggestionStates
from pootle_translationproject.models import TranslationProject


class PootleProfile(models.Model):

    # This is the only required field.
    user = models.OneToOneField(settings.AUTH_USER_MODEL, unique=True, db_index=True)

    class Meta:
        db_table = 'pootle_app_pootleprofile'

    ############################ Properties ###################################

    @property
    def contributions(self):
        """Get user contributions grouped by language and project.

        :return: List of tuples containing the following information::

            [
              ('Language 1', [
                  ('Project 1', [
                      {
                        'id': 'foo-bar',
                        'count': 0,
                        'url': 'foo/bar',
                      },
                      {
                        'id': 'bar-foo',
                        'count': 3,
                        'url': 'baz/blah',
                      },
                      {
                        'id': 'baz-blah',
                        'count': 5,
                        'url': 'bar/baz',
                      },
                  ]),
                  ('Project 2', [
                      ...
                  ]),
              ]),
              ('LanguageN', [
                  ('Project N', [
                      ...
                  ]),
                  ('Project N+1', [
                      ...
                  ]),
              ]),
            ]
        """

        def suggestion_count(tp, state):
            "Return a filtered count of the user's suggestions (internal)"
            return self.user.suggestions.filter(translation_project=tp, state=state).count()

        # TODO: optimize — we need a schema that helps reduce the number
        # of needed queries for these kind of data retrievals.
        contributions = []
        username = self.user.username

        languages = Language.objects.filter(
                translationproject__submission__submitter=self.user,
                translationproject__submission__type=SubmissionTypes.NORMAL,
            ).distinct()

        for language in languages:
            translation_projects = TranslationProject.objects.filter(
                    language=language,
                    submission__submitter=self.user,
                    submission__type=SubmissionTypes.NORMAL,
                ).distinct().order_by('project__fullname')

            tp_user_stats = []
            # Retrieve tp-specific stats for this user.
            for tp in translation_projects:
                # Submissions from the user done from the editor
                total_subs = Submission.objects.filter(
                    submitter=self.user,
                    translation_project=tp,
                    type=SubmissionTypes.NORMAL,
                )
                # Submissions from the user done from the editor that have been
                # overwritten by other users
                overwritten_subs = total_subs.exclude(unit__submitted_by=self)

                tp_stats = [
                    {
                        'id': 'suggestions-pending',
                        'count': suggestion_count(tp, SuggestionStates.PENDING),
                        'url': tp.get_translate_url(state='user-suggestions',
                                                    user=username),
                    },
                    {
                        'id': 'suggestions-accepted',
                        'count': suggestion_count(tp, SuggestionStates.ACCEPTED),
                        'url': tp.get_translate_url(
                            state='user-suggestions-accepted',
                            user=username,
                        ),
                    },
                    {
                        'id': 'suggestions-rejected',
                        'count': suggestion_count(tp, SuggestionStates.REJECTED),
                        'url': tp.get_translate_url(
                            state='user-suggestions-rejected',
                            user=username,
                        ),
                    },
                    {
                        'id': 'submissions-total',
                        'count': total_subs.count(),
                        'url': tp.get_translate_url(state='user-submissions',
                                                    user=username),
                    },
                    {
                        'id': 'submissions-overwritten',
                        'count': overwritten_subs.count(),
                        'url': tp.get_translate_url(
                            state='user-submissions-overwritten',
                            user=username,
                        ),
                    },
                ]

                tp_user_stats.append((tp, tp_stats))

            contributions.append((language, tp_user_stats))

        return contributions

    ############################ Methods ######################################

    def __unicode__(self):
        username = self.user.username

        if email_re.match(username):
            username = username.strip().rsplit('@', 1)[0]

        return username

    def get_absolute_url(self):
        return reverse('profiles_profile_detail', args=[self.user.username])

    def gravatar_url(self, size=80):
        return self.user.gravatar_url(size)


################################ Signal handlers ##############################

def create_pootle_profile(sender, instance, **kwargs):
    """A post-save hook for the User model which ensures that it gets an
    associated PootleProfile.
    """
    try:
        profile = instance.get_profile()
    except PootleProfile.DoesNotExist:
        profile = PootleProfile(user=instance)
        profile.save()

post_save.connect(create_pootle_profile, sender=User)
