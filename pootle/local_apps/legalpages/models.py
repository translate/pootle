#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
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
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from pootle_misc.util import apply_markup_filter

class LegalPage(models.Model):

    active = models.BooleanField(_('Active'),
            help_text=_('Whether this page is active or not.'))

    display_on_register = models.BooleanField(_('Display on registration'),
            help_text=_('Whether this page should be displayed on registration.'))

    # TODO: make title and body localizable fields
    title = models.CharField(_("Title"), max_length=100)
    url = models.URLField(_("URL"), blank=True,
            help_text=_('If set, any references to this legal page will redirect ' \
                    'to this URL'))
    slug = models.SlugField(_("slug"),
            help_text=_('The page will be independently available in ' \
                    '/about/<slug>/'))

    try:
        markup_filter = settings.MARKUP_FILTER[0]
    except AttributeError, IndexError:
        markup_filter = u'HTML'
    body = models.TextField(_("Content"), blank=True,
            help_text=_('Allowed markup: %s', markup_filter))

    body_html = models.TextField(editable=False, blank=True)


    def __unicode__(self):
        return self.slug


    def localized_title(self):
        return _(self.title)


    def get_absolute_url(self):

        if self.url:
            return self.url

        return reverse('legalpages.views.legalpage', args=[self.slug])


    def save(self, *args, **kwargs):
        """Applies a markup filter to populate `body_html` upon saving."""

        self.body_html = apply_markup_filter(self.body)
        super(LegalPage, self).save(*args, **kwargs)
