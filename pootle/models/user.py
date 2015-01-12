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


__all__ = ('User', )

import datetime
import re
from hashlib import md5

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import ProtectedError, Sum, Q
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from pootle.core.cache import make_method_key
from pootle.managers import UserManager
from pootle_language.models import Language
from pootle_misc.util import jsonify
from pootle_statistics.models import Submission, SubmissionTypes
from pootle_store.models import SuggestionStates
from pootle_translationproject.models import TranslationProject


CURRENCIES = (('USD', 'USD'), ('EUR', 'EUR'))


def _humanize_score(score):
    """Returns a human-readable score for public display."""
    return int(round(score))


class User(AbstractBaseUser, PermissionsMixin):
    """The Pootle User.

    ``username``, ``password`` and ``email`` are required. Other fields
    are optional.

    Note that the ``password`` and ``last_login`` fields are inherited
    from ``AbstractBaseUser``.
    """
    username = models.CharField(_('Username'), max_length=30, unique=True,
        help_text=_('Required. 30 characters or fewer. Letters, numbers and '
                    '@/./+/-/_ characters'),
        validators=[
            RegexValidator(re.compile('^[\w.@+-]+$'),
                           _('Enter a valid username.'),
                           'invalid')
        ],
    )
    email = models.EmailField(_('Email Address'), max_length=255)
    full_name = models.CharField(_('Full Name'), max_length=255, blank=True)

    is_active = models.BooleanField(_('Active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))

    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    # Translation setting fields
    unit_rows = models.SmallIntegerField(default=9,
            verbose_name=_("Number of Rows"))
    alt_src_langs = models.ManyToManyField('pootle_language.Language',
            blank=True, db_index=True, limit_choices_to=~Q(code='templates'),
            verbose_name=_("Alternative Source Languages"))

    # Score-related fields
    rate = models.FloatField(_('Rate'), null=False, default=0)
    review_rate = models.FloatField(_('Review Rate'), null=False, default=0)
    hourly_rate = models.FloatField(_('Hourly Rate'), null=False, default=0)
    score = models.FloatField(_('Score'), null=False, default=0)
    currency = models.CharField(_('Currency'), max_length=3, null=True,
                                blank=True, choices=CURRENCIES)
    is_employee = models.BooleanField(_('Is employee?'), default=False)
    twitter = models.CharField(_('Twitter'), max_length=15, null=True,
                               blank=True)
    website = models.URLField(_('Website'), null=True, blank=True)
    linkedin = models.URLField(_('LinkedIn'), null=True, blank=True)
    bio = models.TextField(_('Short Bio'), null=True, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    class Meta:
        app_label = 'pootle'

    @property
    def display_name(self):
        """Human-readable display name."""
        return (self.get_full_name() if self.get_full_name()
                                     else self.get_short_name())

    @property
    def formatted_name(self):
        """Full name (username)"""
        if self.get_full_name():
            return "%s (%s)" % (self.get_full_name(), self.get_short_name())

        return self.get_short_name()

    @property
    def public_score(self):
        return _humanize_score(self.score)

    @property
    def public_total_score(self):
        """Total score for a specific period.

        Since `total_score` is not an attribute of the `User` model, this
        should be used with user objects retrieved via `User.top_scorers()`.
        """
        return _humanize_score(getattr(self, 'total_score', self.score))

    @property
    def has_contact_details(self):
        """Returns ``True`` if any contact details have been set."""
        return bool(self.website or self.twitter or self.linkedin)

    @property
    def twitter_url(self):
        return 'https://twitter.com/{0}'.format(self.twitter)

    @cached_property
    def is_meta(self):
        """Returns `True` if this is a special fake user."""
        meta_users = UserManager.META_USERS
        if settings.POOTLE_META_USERS:
            meta_users += settings.POOTLE_META_USERS

        return self.username in meta_users

    @cached_property
    def email_hash(self):
        try:
            return md5(self.email).hexdigest()
        except UnicodeEncodeError:
            return None

    @classmethod
    def get(cls, user):
        """Return the expected user instance.

        This function is only necessary if `user` could be anonymous,
        because we want to work with the instance of the special `nobody`
        user instead of Django's own `AnonymousUser`.

        If you know for certain that a user is logged in, then use it
        straight away.
        """
        if user.is_authenticated():
            return user

        return cls.objects.get_nobody_user()

    @classmethod
    def top_scorers(cls, days=30, language=None, project=None, limit=5):
        """Returns users with the top scores.

        :param days: period of days to account for scores.
        :param language: limit results to the given language code.
        :param project: limit results to the given project code.
        :param limit: limit results to this number of users. Values other
            than positive numbers will return the entire result set.
        """
        cache_kwargs = {
            'days': days,
            'language': language,
            'project': project,
            'limit': limit,
        }
        cache_key = make_method_key(cls, 'top_scorers', cache_kwargs)

        top_scorers = cache.get(cache_key, None)
        if top_scorers is not None:
            return top_scorers

        now = timezone.now()
        past = now + datetime.timedelta(-days)

        lookup_kwargs = {
            'scorelog__creation_time__range': [past, now],
        }

        if language is not None:
            lookup_kwargs.update({
                'scorelog__submission__translation_project__language__code':
                    language,
            })

        if project is not None:
            lookup_kwargs.update({
                'scorelog__submission__translation_project__project__code':
                    project,
            })

        top_scorers = cls.objects.hide_meta().filter(
            **lookup_kwargs
        ).annotate(
            total_score=Sum('scorelog__score_delta'),
        ).order_by('-total_score')

        if isinstance(limit, (int, long)) and limit > 0:
            top_scorers = top_scorers[:limit]

        cache.set(cache_key, list(top_scorers), 60)
        return top_scorers

    def __unicode__(self):
        return self.username

    def delete(self, *args, **kwargs):
        """Deletes a user instance.

        Trying to delete a meta user raises the `ProtectedError` exception.
        """
        if self.is_meta:
            raise ProtectedError('Cannot remove meta user instances', None)

        super(User, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('pootle-user-profile', args=[self.username])

    def as_json(self):
        """Returns the user's field-values as a JSON-encoded string."""
        return jsonify(model_to_dict(self, exclude=['password']))

    def is_anonymous(self):
        """Returns `True` if this is an anonymous user.

        Since we treat the `nobody` user as special anonymous-like user,
        we can't rely on `auth.User` model's `is_authenticated()` method.
        """
        return self.username == 'nobody'

    def is_system(self):
        """Returns `True` if this is the special `system` user."""
        return self.username == 'system'

    def get_full_name(self):
        """Returns the user's full name."""
        return self.full_name.strip()

    def get_short_name(self):
        """Returns the short name for the user."""
        return self.username

    def email_user(self, subject, message, from_email=None):
        """Sends an email to this user."""
        send_mail(subject, message, from_email, [self.email])

    def gravatar_url(self, size=80):
        if not self.email_hash:
            return ''

        return 'https://secure.gravatar.com/avatar/%s?s=%d&d=mm' % \
            (self.email_hash, size)

    def get_unit_rows(self):
        return min(max(self.unit_rows, 5), 49)

    def pending_suggestion_count(self, tp):
        """Returns the number of pending suggestions for the user in the given
        translation project.

        :param tp: a :cls:`TranslationProject` object.
        """
        return self.suggestions.filter(unit__store__translation_project=tp,
                                       state=SuggestionStates.PENDING).count()

    def accepted_suggestion_count(self, tp):
        """Returns the number of accepted suggestions for the user in the given
        translation project.

        :param tp: a :cls:`TranslationProject` object.
        """
        return self.suggestions.filter(unit__store__translation_project=tp,
                                       state=SuggestionStates.ACCEPTED).count()

    def rejected_suggestion_count(self, tp):
        """Returns the number of rejected suggestions for the user in the given
        translation project.

        :param tp: a :cls:`TranslationProject` object.
        """
        return self.suggestions.filter(unit__store__translation_project=tp,
                                       state=SuggestionStates.REJECTED).count()

    def total_submission_count(self, tp):
        """Returns the number of submissions the current user has done from the
        editor in the given translation project.

        :param tp: a :cls:`TranslationProject` object.
        """
        return Submission.objects.filter(
            submitter=self,
            translation_project=tp,
            type__in=SubmissionTypes.CONTRIBUTION_TYPES,
        ).count()

    def overwritten_submission_count(self, tp):
        """Returns the number of submissions the current user has done from the
        editor and have been overwritten by other users in the given
        translation project.

        :param tp: a :cls:`TranslationProject` object.
        """
        return Submission.objects.filter(
            submitter=self,
            translation_project=tp,
            type__in=SubmissionTypes.CONTRIBUTION_TYPES,
        ).exclude(
            unit__submitted_by=self,
        ).count()

    def top_language(self, days=30):
        """Returns the top language the user has contributed to and its
        position.

        "Top language" is defined as the language with the highest
        aggregate score delta within the last `days` days.

        :param days: period of days to account for scores.
        :return: Tuple of `(position, Language)`. If there's no delta in
            the score for the given period for any of the languages,
            `(-1, None)` is returned.
        """
        position = -1

        now = timezone.now()
        past = now + datetime.timedelta(-days)

        sum_field = 'translationproject__submission__scorelog__score_delta'
        lookup_kwargs = {
            'translationproject__submission__scorelog__user': self,
            'translationproject__submission__scorelog__creation_time__range':
                [past, now]
        }

        try:
            language = Language.objects.filter(**lookup_kwargs) \
                                       .annotate(score=Sum(sum_field)) \
                                       .order_by('-score')[0]
        except IndexError:
            language = None

        if language is not None:
            language_scorers = self.top_scorers(language=language.code,
                                                days=days, limit=None)
            for index, user in enumerate(language_scorers, start=1):
                if user == self:
                    position = index
                    break

        return (position, language)

    def last_event(self):
        """Returns the latest submission linked with this user. If there's
        no activity, `None` is returned instead.
        """
        return Submission.objects.filter(submitter=self).latest()
