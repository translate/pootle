#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2013 Zuza Software Foundation
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

"""
NOTE: Import this file in your urls.py or some place before any code relying on
      settings is imported.
"""

from django.contrib.sites.models import Site

from djblets.siteconfig.models import SiteConfiguration


def load_site_config():
    """Set up the SiteConfiguration, provide defaults and sync settings."""
    try:
        siteconfig = SiteConfiguration.objects.get_current()
    except SiteConfiguration.DoesNotExist:
        siteconfig = SiteConfiguration(site=Site.objects.get_current(),
                                       version="1.0")
        siteconfig.save()

    # If TITLE and DESCRIPTION are not on the database then pick the defaults
    # from the settings and save them in the database.
    if not siteconfig.get_defaults():
        from django.conf import settings

        defaults = {}

        for setting_name in ('DESCRIPTION', 'TITLE'):
            if hasattr(settings, setting_name):
                defaults[setting_name] = getattr(settings, setting_name)

        siteconfig.add_defaults(defaults)

    return siteconfig
