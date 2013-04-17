#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
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
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from pootle.core.markup import get_markup_filter_name, MarkupField


class AbstractPage(models.Model):

    active = models.BooleanField(_('Active'),
            help_text=_('Whether this page is active or not.'))

    # Translators: See http://en.wikipedia.org/wiki/Slug_%28web_publishing%29#Slug
    slug = models.SlugField(_("Slug"), default='',
            help_text=_('The page will be available at /about/<slug>/'))

    # TODO: make title and body localizable fields
    title = models.CharField(_("Title"), max_length=100)
    body = MarkupField(_("Content"), blank=True,
            help_text=_('Allowed markup: %s', get_markup_filter_name()))

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.slug


class LegalPage(AbstractPage):

    display_on_register = models.BooleanField(_('Display on registration'),
            help_text=_('Whether this page should be displayed on registration.'))

    url = models.URLField(_("URL"), blank=True,
            help_text=_('If set, any references to this legal page will '
                        'redirect to this URL'))

    def localized_title(self):
        return _(self.title)

    def get_absolute_url(self):
        if self.url:
            return self.url

        return reverse('staticpages.views.legalpage', args=[self.slug])
