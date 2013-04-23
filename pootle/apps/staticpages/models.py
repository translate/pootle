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

from django.db import models
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from pootle.core.markup import get_markup_filter_name, MarkupField


class AbstractPage(models.Model):

    active = models.BooleanField(_('Active'),
            help_text=_('Whether this page is active or not.'))

    virtual_path = models.CharField(_("Virtual Path"), max_length=100,
            default='', unique=True,
            help_text=_('The page will be available at /about/<path>/'))

    # TODO: make title and body localizable fields
    title = models.CharField(_("Title"), max_length=100)
    body = MarkupField(_("Content"), blank=True,
            help_text=_('Allowed markup: %s', get_markup_filter_name()))

    url = models.URLField(_("Redirect to URL"), blank=True,
            help_text=_('If set, any references to this page will '
                        'redirect to this URL'))

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.virtual_path

    def clean(self):
        """Fail validation if:

        - URL and body are blank
        - Current virtual path exists in other page models
        """
        if not self.url and not self.body:
            # Translators: 'URL' and 'content' refer to form fields.
            raise ValidationError(_('URL or content must be provided.'))

        pages = [p.objects.filter(virtual_path=self.virtual_path).exists()
                 for p in AbstractPage.__subclasses__()]
        if True in pages:
            raise ValidationError(_(u'Virtual path already in use.'))


class LegalPage(AbstractPage):

    display_on_register = models.BooleanField(_('Display on registration'),
            help_text=_('Whether this page should be displayed on registration.'))

    def localized_title(self):
        return _(self.title)

    def get_absolute_url(self):
        if self.url:
            return self.url

        return reverse('staticpages.views.legalpage',
                       args=[self.virtual_path])

    def get_edit_url(self):
        return reverse('legalpages.edit', args=[self.pk])
