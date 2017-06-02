# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.aggregates import Max
from django.urls import reverse
from django.utils.timezone import now

from pootle.core.markup import MarkupField, get_markup_filter_display_name
from pootle.i18n.gettext import ugettext_lazy as _

from .managers import PageManager


ANN_TYPE = u'announcements'
ANN_VPATH = ANN_TYPE + u'/'


class AbstractPage(models.Model):

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
        help_text=_('Allowed markup: %s', get_markup_filter_display_name()),
    )
    url = models.URLField(
        _("Redirect to URL"),
        blank=True,
        help_text=_('If set, this page will redirect to this URL'),
    )
    modified_on = models.DateTimeField(
        default=now,
        editable=False,
    )

    objects = PageManager()

    class Meta(object):
        abstract = True

    def __unicode__(self):
        return self.virtual_path

    def save(self, **kwargs):
        # Update the `modified_on` timestamp only when specific fields change.
        if self.pk is None or self.has_changes():
            self.modified_on = now()

        super(AbstractPage, self).save(**kwargs)

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

        pages = [p.objects.filter(Q(virtual_path=self.virtual_path),
                                  ~Q(pk=self.pk),).exists() for p in
                 AbstractPage.__subclasses__()]
        if True in pages:
            raise ValidationError(_(u'Virtual path already in use.'))

    def has_changes(self):
        old_page = self.__class__.objects.get(pk=self.pk)
        return any((getattr(old_page, field) != getattr(self, field))
                   for field in ('title', 'body', 'url'))


class LegalPage(AbstractPage):

    display_name = _('Legal Page')

    def localized_title(self):
        return _(self.title)

    def get_edit_url(self):
        return reverse('pootle-staticpages-edit', args=['legal', self.pk])


class StaticPage(AbstractPage):

    display_name = _('Regular Page')

    @classmethod
    def get_announcement_for(cls, pootle_path, user=None):
        """Return the announcement for the specified pootle path and user."""
        virtual_path = ANN_VPATH + pootle_path.strip('/')
        try:
            return cls.objects.live(user).get(virtual_path=virtual_path)
        except StaticPage.DoesNotExist:
            return None

    def get_edit_url(self):
        page_type = 'static'
        if self.virtual_path.startswith(ANN_VPATH):
            page_type = ANN_TYPE
        return reverse('pootle-staticpages-edit', args=[page_type, self.pk])


class Agreement(models.Model):
    """Tracks who agreed a specific legal document and when."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_index=False,
        on_delete=models.CASCADE)
    document = models.ForeignKey(LegalPage, on_delete=models.CASCADE)
    agreed_on = models.DateTimeField(
        default=now,
        editable=False,
    )

    class Meta(object):
        unique_together = ('user', 'document',)

    def __unicode__(self):
        return u'%s (%s@%s)' % (self.document, self.user, self.agreed_on)

    def save(self, **kwargs):
        # When updating always explicitly renew agreement date
        if self.pk:
            self.agreed_on = now()

        super(Agreement, self).save(**kwargs)
