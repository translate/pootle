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

from django.db import models, DatabaseError


def get_pootle_build(default=0):
    """Get the Pootle build version for the current deployment, if any."""
    try:
        build = PootleConfig.objects.get_current().ptl_build
    except Exception:
        build = 0

    if not build:
        build = get_legacy_ptl_build()

    # We have some code that depends on the build version being not less than a
    # specific value.
    if build < default:
        build = default

    return build


def get_toolkit_build(default=0):
    """Get the Toolkit build version for the current deployment, if any."""
    try:
        build = PootleConfig.objects.get_current().ttk_build
    except Exception:
        build = 0

    if not build:
        build = get_legacy_ttk_build()

    # We have some code that depends on the build version being not less than a
    # specific value.
    if build < default:
        build = default

    return build


def get_legacy_ptl_build():
    """Retrieve a Pootle build version stored using djblets.

    This allows to retrieve build versions stored using the old
    POOTLE_BUILDVERSION or the even older BUILDVERSION.
    """
    from pootle_misc.siteconfig import load_site_config

    try:
        config = load_site_config()
        build = config.get('POOTLE_BUILDVERSION', 0)

        if not build:
            # Ancient Pootle versions used BUILDVERSION instead.
            build = config.get('BUILDVERSION', 0)
    except DatabaseError:
        build = 0

    return int(build)


def get_legacy_ttk_build():
    """Retrieve a Toolkit build version stored using djblets."""
    from pootle_misc.siteconfig import load_site_config

    try:
        config = load_site_config()
        build = int(config.get('TT_BUILDVERSION', 0))
    except DatabaseError:
        build = 0

    return build


class PootleConfigManager(models.Manager):

    def get_current(self):
        """Return the object holding the Pootle configuration."""
        return PootleConfig.objects.all()[0]


class PootleConfig(models.Model):
    """Model to store Pootle configuration on the database.

    The configuration includes some data for install/upgrade mechanisms.
    """
    ptl_build = models.PositiveIntegerField(default=0)
    ttk_build = models.PositiveIntegerField(default=0)

    objects = PootleConfigManager()

    class Meta:
        app_label = "pootle_app"
