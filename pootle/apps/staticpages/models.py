#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.aggregates import Max
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from pootle.core.markup import get_markup_filter_name, MarkupField
from pootle.core.mixins import DirtyFieldsMixin

from .managers import PageManager


class AbstractPage(DirtyFieldsMixin, models.Model):

    active = models.BooleanField(
        _('Active'),
        default=False,
        help_text=_('Whether this page is active or not.'),
    )
    virtual_path = models.CharField(
        _("Virtual Path"),
        max_length=100,
        default='',
        unique=True,
        help_text='/pages/',
    )
    # TODO: make title and body localizable fields
    title = models.CharField(_("Title"), max_length=100)
    body = MarkupField(
        # Translators: Content that will be used to display this static page
        _("Display Content"),
        blank=True,
        help_text=_('Allowed markup: %s', get_markup_filter_name()),
    )
    url = models.URLField(
        _("Redirect to URL"),
        blank=True,
        help_text=_('If set, any references to this page will redirect to this'
                    ' URL'),
    )
    # This will go away with bug 2830, but works fine for now.
    modified_on = models.DateTimeField(
        default=now,
        editable=False,
    )

    objects = PageManager()

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.virtual_path

    def save(self):
        # Update the `modified_on` timestamp only when specific fields change.
        dirty_fields = self.get_dirty_fields()
        if any(field in dirty_fields for field in ('title', 'body', 'url')):
            self.modified_on = now()

        super(AbstractPage, self).save()

    def get_absolute_url(self):
        if self.url:
            return self.url

        return reverse('pootle-staticpages-display', args=[self.virtual_path])

    @staticmethod
    def max_pk():
        """Returns the sum of all the highest PKs for each submodel."""
        return reduce(
            lambda x, y: x + y,
            [int(p.objects.aggregate(Max('pk')).values()[0] or 0)
             for p in AbstractPage.__subclasses__()],
        )

    def clean(self):
        """Fail validation if:

        - URL and body are blank
        - Current virtual path exists in other page models
        """
        if not self.url and not self.body:
            # Translators: 'URL' and 'content' refer to form fields.
            raise ValidationError(_('URL or content must be provided.'))

        pages = [p.objects.filter(
                     Q(virtual_path=self.virtual_path),
                     ~Q(pk=self.pk),
                 ).exists()
                 for p in AbstractPage.__subclasses__()]
        if True in pages:
            raise ValidationError(_(u'Virtual path already in use.'))


class LegalPage(AbstractPage):

    display_name = _('Legal Page')

    def localized_title(self):
        return _(self.title)

    def get_edit_url(self):
        return reverse('pootle-staticpages-edit', args=['legal', self.pk])


class StaticPage(AbstractPage):

    display_name = _('Regular Page')

    def get_edit_url(self):
        page_type = 'static'
        if self.virtual_path.startswith('announcements/'):
            page_type = 'announcements'
        return reverse('pootle-staticpages-edit', args=[page_type, self.pk])


class Agreement(models.Model):
    """Tracks who agreed a specific legal document and when."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    document = models.ForeignKey(LegalPage)
    agreed_on = models.DateTimeField(
        default=now,
        editable=False,
    )

    class Meta:
        unique_together = ('user', 'document',)

    def save(self, **kwargs):
        # When updating always explicitly renew agreement date
        if self.pk:
            self.agreed_on = now()

        super(Agreement, self).save(**kwargs)
