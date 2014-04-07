#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _

from pootle.core.markup import get_markup_filter_name, MarkupField


def get_site_title():
    try:
        pootle_site = PootleSite.objects.get_current()
        return pootle_site.title
    except Exception:
        return PootleSite._meta.get_field('title').default


def get_site_description():
    try:
        pootle_site = PootleSite.objects.get_current()
        return pootle_site.description
    except Exception:
        return PootleSite._meta.get_field('description').default


def get_legacy_site_title():
    """Retrieve the site title from the database as stored by djblets."""
    from pootle_misc.siteconfig import load_site_config

    siteconfig = load_site_config()
    return siteconfig.get('TITLE')


def get_legacy_site_description():
    """Retrieve the site description from the database as stored by djblets."""
    from pootle_misc.siteconfig import load_site_config

    siteconfig = load_site_config()
    return siteconfig.get('DESCRIPTION')


class PootleSiteManager(models.Manager):

    def get_current(self):
        """Return the site configuration for the current Pootle site."""
        return PootleSite.objects.get(site=Site.objects.get_current())


class PootleSite(models.Model):
    """Model to store each specific Pootle site configuration.

    The configuration includes some data for install/upgrade mechanisms.
    """
    site = models.OneToOneField(Site, editable=False)
    title = models.CharField(
        max_length=50,
        blank=False,
        default="Pootle Demo",
        verbose_name=_("Title"),
        help_text=_("The name for this Pootle server"),
    )
    description = MarkupField(
        blank=True,
        default='',
        verbose_name=_("Description"),
        help_text=_("The description and instructions shown on the about "
                    "page. Allowed markup: %s", get_markup_filter_name()),
    )

    objects = PootleSiteManager()

    class Meta:
        app_label = "pootle_app"
