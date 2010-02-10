#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

# NOTE: Import this file in your urls.py or some place before
#       any code relying on settings is imported.

from django.contrib.sites.models import Site

from djblets.siteconfig.models import SiteConfiguration
from djblets.siteconfig.django_settings import apply_django_settings, generate_defaults

settings_map = {
    # siteconfig key    settings.py key
    'DESCRIPTION':        'DESCRIPTION',
    'TITLE'      :        'TITLE',
}

defaults = generate_defaults(settings_map)

def load_site_config():
    """Sets up the SiteConfiguration, provides defaults and syncs settings."""
    try:
        siteconfig = SiteConfiguration.objects.get_current()
    except SiteConfiguration.DoesNotExist:
        # Either warn or just create the thing. Depends on your app
        siteconfig = SiteConfiguration(site=Site.objects.get_current(),
                                       version="1.0")
        siteconfig.save()

    if not siteconfig.get_defaults():
        siteconfig.add_defaults(defaults)
    apply_django_settings(siteconfig, settings_map)
    return siteconfig
