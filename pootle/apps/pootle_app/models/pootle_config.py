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
        try:
            from pootle_misc.siteconfig import get_build

            build = get_build('POOTLE_BUILDVERSION')

            if not build:
                # Old Pootle versions used BUILDVERSION instead.
                build = get_build('BUILDVERSION')
        except DatabaseError:
            # Assume that the DatabaseError is because we have a blank
            # database from a new install.
            # TODO: is there a better way to do this?
            build = 0

    # We have some code that depends on the build version being not less than a
    # specific value.
    if default and build < default:
        build = default

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
