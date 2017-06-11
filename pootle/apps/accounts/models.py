# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re
from hashlib import md5

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import ProtectedError, Q
from django.forms.models import model_to_dict
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.functional import cached_property

from allauth.account.models import EmailAddress
from allauth.account.utils import sync_user_email_addresses

from pootle.core.views.display import ActionDisplay
from pootle.i18n import formatter
from pootle.i18n.gettext import ugettext_lazy as _
from pootle_statistics.models import Submission
from pootle_store.models import Unit

from .managers import UserManager
from .utils import UserMerger, UserPurger


__all__ = ('User', )


CURRENCIES = (('USD', 'USD'), ('EUR', 'EUR'), ('CNY', 'CNY'), ('JPY', 'JPY'))


class User(AbstractBaseUser):
    """The Pootle User.

    ``username``, ``password`` and ``email`` are required. Other fields
    are optional.

    Note that the ``password`` and ``last_login`` fields are inherited
    from ``AbstractBaseUser``.
    """

    username = models.CharField(
        _('Username'), max_length=30, unique=True,
        help_text=_('Required. 30 characters or fewer. Letters, numbers and '
                    '@/./+/-/_ characters'),
        validators=[
            RegexValidator(re.compile('^[\w.@+-]+$', re.UNICODE),
                           _('Enter a valid username.'),
                           'invalid')
        ],
        error_messages={
            'unique': _('A user with that username already exists.'),
        },
    )
    email = models.EmailField(_('Email Address'), max_length=255)
    full_name = models.CharField(_('Full Name'), max_length=255, blank=True)

    is_active = models.BooleanField(
        _('Active'),
        default=True,
        db_index=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    is_superuser = models.BooleanField(
        _('Superuser Status'),
        default=False,
        db_index=True,
        help_text=_('Designates that this user has all permissions without '
                    'explicitly assigning them.'))

    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    # Translation setting fields
    unit_rows = models.SmallIntegerField(default=9,
                                         verbose_name=_("Number of Rows"))
    alt_src_langs = models.ManyToManyField(
        'pootle_language.Language', blank=True, db_index=True,
        limit_choices_to=~Q(code='templates'),
        verbose_name=_("Alternative Source Languages"))

    # Score-related fields
    score = models.FloatField(_('Score'), null=False, default=0)
    is_employee = models.BooleanField(_('Is employee?'), default=False)
    twitter = models.CharField(_('Twitter'), max_length=15, null=True,
                               blank=True)
    website = models.URLField(_('Website'), null=True, blank=True)
    linkedin = models.URLField(_('LinkedIn'), null=True, blank=True)
    bio = models.TextField(_('Short Bio'), null=True, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    @property
    def display_name(self):
        """Human-readable display name."""
        return (self.get_full_name()
                if self.get_full_name()
                else self.get_short_name())

    @property
    def public_score(self):
        return formatter.number(round(self.score))

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
        return self.username in \
            UserManager.META_USERS + settings.POOTLE_META_USERS

    @cached_property
    def email_hash(self):
        try:
            return md5(force_bytes(self.email)).hexdigest()
        except UnicodeEncodeError:
            return None

    def __unicode__(self):
        return self.username

    def save(self, *args, **kwargs):
        old_email = (None
                     if self.pk is None
                     else User.objects.get(pk=self.pk).email)

        super(User, self).save(*args, **kwargs)

        self.sync_email(old_email)

    def delete(self, *args, **kwargs):
        """Deletes a user instance.

        Trying to delete a meta user raises the `ProtectedError` exception.
        """
        if self.is_meta:
            raise ProtectedError('Cannot remove meta user instances', None)

        purge = kwargs.pop("purge", False)

        if purge:
            UserPurger(self).purge()
        else:
            UserMerger(self, User.objects.get_nobody_user()).merge()

        super(User, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('pootle-user-profile', args=[self.username])

    def field_values(self):
        """Returns the user's field-values (can be encoded as e.g. JSON)."""
        values = model_to_dict(self, exclude=['password'])
        values["alt_src_langs"] = list(
            values["alt_src_langs"].values_list("pk", flat=True))
        return values

    @property
    def is_anonymous(self):
        """Returns `True` if this is an anonymous user."""
        return self.username == 'nobody'

    @property
    def is_authenticated(self):
        """Returns `True` if this is an authenticated user."""
        return self.username != 'nobody'

    def is_system(self):
        """Returns `True` if this is the special `system` user."""
        return self.username == 'system'

    def has_manager_permissions(self):
        """Tells if the user is a manager for any language, project or TP."""
        if self.is_anonymous:
            return False
        if self.is_superuser:
            return True
        criteria = {
            'positive_permissions__codename': 'administrate',
            'directory__pootle_path__regex': r'^/[^/]*/([^/]*/)?$',
        }
        return self.permissionset_set.filter(**criteria).exists()

    def get_full_name(self):
        """Returns the user's full name."""
        return self.full_name.strip()

    def get_short_name(self):
        """Returns the short name for the user."""
        return self.username

    def email_user(self, subject, message, from_email=None):
        """Sends an email to this user."""
        send_mail(subject, message, from_email, [self.email])

    def clean_fields(self, exclude=None):
        super(User, self).clean_fields(exclude=exclude)

        self.validate_email()

    def validate_email(self):
        """Ensure emails are unique across the models tracking emails.

        Since it's essential to keep email addresses unique to support our
        workflows, a `ValidationError` will be raised if the email trying
        to be saved is already assigned to some other user.
        """
        lookup = Q(email__iexact=self.email)
        if self.pk is not None:
            # When there's an update, ensure no one else has this address
            lookup &= ~Q(user=self)

        try:
            EmailAddress.objects.get(lookup)
        except EmailAddress.DoesNotExist:
            pass
        else:
            raise ValidationError({
                'email': [_('This email address already exists.')]
            })

    def sync_email(self, old_email):
        """Syncs up `self.email` with allauth's own `EmailAddress` model.

        :param old_email: Address this user previously had
        """
        if old_email != self.email:  # Update
            EmailAddress.objects.filter(
                user=self,
                email__iexact=old_email,
            ).update(email=self.email)
        else:
            sync_user_email_addresses(self)

    def gravatar_url(self, size=80):
        if not self.email_hash:
            return ''

        return 'https://secure.gravatar.com/avatar/%s?s=%d&d=mm' % \
            (self.email_hash, size)

    def get_suggestion_reviews(self):
        return self.submission_set.get_unit_suggestion_reviews()

    def get_unit_rows(self):
        return min(max(self.unit_rows, 5), 49)

    def get_unit_states_changed(self):
        return self.submission_set.get_unit_state_changes()

    def get_units_created(self):
        """Units that were created by this user.

        :return: Queryset of `Unit`s that were created by this user.
        """
        return Unit.objects.filter(unit_source__created_by=self)

    def last_event(self, locale=None):
        """Returns the latest submission linked with this user. If there's
        no activity, `None` is returned instead.
        """
        last_event = Submission.objects.select_related(
            "unit",
            "unit__store",
            "unit__store__parent").filter(submitter=self).last()
        if last_event:
            return ActionDisplay(
                last_event.get_submission_info(),
                locale=locale)
