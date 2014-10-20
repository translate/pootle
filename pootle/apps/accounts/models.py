#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import re
from hashlib import md5

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from pootle_app.models import Directory
from pootle_autonotices.signals import new_object
from pootle_language.models import Language
from pootle_statistics.models import Submission, SubmissionTypes
from pootle_store.models import SuggestionStates
from pootle_translationproject.models import TranslationProject
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """The Pootle User.

    ``username``, ``password`` and ``email`` are required. Other fields
    are optional.

    Note that the ``password`` and ``last_login`` fields are inherited
    from ``AbstractBaseUser``.
    """
    username = models.CharField(_("username"), max_length=30, unique=True,
        help_text=_("Required. 30 characters or fewer. Letters, numbers and "
                    "@/./+/-/_ characters"),
        validators=[
            RegexValidator(re.compile("^[\w.@+-]+$"),
                           _("Enter a valid username."),
                           "invalid")
        ],
    )
    email = models.EmailField(_("email address"), max_length=255)
    full_name = models.CharField(_("Full name"), max_length=255, blank=True)

    is_active = models.BooleanField(_("active"), default=True,
        help_text=_("Designates whether this user should be treated as "
                    "active. Unselect this instead of deleting accounts."))

    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    # Profile fields
    _unit_rows = models.SmallIntegerField(_("Number of Rows"), default=9,
        db_column="unit_rows")

    alt_src_langs = models.ManyToManyField(
        "pootle_language.Language",
        blank=True,
        db_index=True,
        limit_choices_to=~Q(code="templates"),
        related_name="user_alt_src_langs",
        verbose_name=_("Alternative Source Languages"),
    )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    @property
    def display_name(self):
        """Human-readable display name."""
        return (self.get_full_name() if self.get_full_name()
                                     else self.get_short_name())

    @property
    def is_staff(self):
        # For compatibility with django admin.
        return self.is_superuser

    def __unicode__(self):
        return self.username

    def get_absolute_url(self):
        # FIXME: adapt once we get rid of the profiles app
        return reverse("profiles_profile_detail", args=[self.username])

    @cached_property
    def email_hash(self):
        try:
            return md5(self.email).hexdigest()
        except UnicodeEncodeError:
            return None

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
            return self.suggestions.filter(translation_project=tp, state=state).count()

        contributions = []
        username = self.username

        languages = Language.objects.filter(
            translationproject__submission__submitter=self,
            translationproject__submission__type=SubmissionTypes.NORMAL,
        ).distinct()

        for language in languages:
            translation_projects = TranslationProject.objects.filter(
                    language=language,
                    submission__submitter=self,
                    submission__type=SubmissionTypes.NORMAL,
                ).distinct().order_by('project__fullname')

            tp_user_stats = []
            # Retrieve tp-specific stats for this user.
            for tp in translation_projects:
                # Submissions from the user done from the editor
                total_subs = Submission.objects.filter(
                    submitter=self,
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

    @property
    def unit_rows(self):
        # NOTE: This could be done using MinValueValidator and MaxValueValidator
        # But that is more complicated than really necessary
        return min(max(self._unit_rows, 5), 49)

    def gravatar_url(self, size=80):
        if not self.email_hash:
            return ""

        api_url = "https://secure.gravatar.com/avatar/%(hash)s?s=%(size)d&d=mm"
        return api_url % {"hash": self.email_hash, "size": size}

    def get_full_name(self):
        """Returns the user's full name."""
        return self.full_name

    def get_short_name(self):
        """Returns the short name for the user."""
        return self.username

    def email_user(self, subject, message, from_email=None):
        """Sends an email to this user."""
        send_mail(subject, message, from_email, [self.email])


@receiver(post_save, sender=User)
def new_user(sender, instance, created=False, raw=False, **kwargs):
    if raw:
        return

    args = {
        "url": instance.get_absolute_url(),
        "user": instance,
    }
    message = 'New user <a href="%(url)s">%(user)s</a> registered.' % args
    new_object(created, message, parent=Directory.objects.root)
