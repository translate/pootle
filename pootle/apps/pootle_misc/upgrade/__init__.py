#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013, 2014 Zuza Software Foundation
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

"""Pootle upgrade code."""

import logging


def ensure_pootle_config():
    """Ensure that the PootleConfig object exists, so the code can use it."""
    from pootle_app.models import PootleConfig

    try:
        PootleConfig.objects.get_current()
        logging.info("No need to migrate old build versions.")
    except Exception:
        from pootle_app.models.pootle_config import (get_legacy_ptl_build,
                                                     get_legacy_ttk_build)

        # Copy the Pootle and Translate Toolkit build versions.
        pootle_config = PootleConfig(
            ptl_build=get_legacy_ptl_build(),
            ttk_build=get_legacy_ttk_build(),
        )
        pootle_config.save()
        logging.info("Succesfully migrated old build versions to new "
                     "PootleConfig.")


def save_build_version(product, build_version):
    """Update build version number for specified product."""
    from pootle_app.models import PootleConfig

    pootle_config = PootleConfig.objects.get_current()

    if product == 'pootle':
        pootle_config.ptl_build = build_version
    elif product == 'ttk':
        pootle_config.ttk_build = build_version

    pootle_config.save()

    if product == 'pootle':
        logging.info("Database now at Pootle build %d" % build_version)
    elif product == 'ttk':
        logging.info("Database now at Toolkit build %d" % build_version)


def buildversion_for(func):
    """Return the build version for the given upgrade function."""
    fn = func.__name__
    build_string = fn.rsplit('_', 1)[-1]
    return int(build_string)


def is_upgrade_function(mod, func):
    """Return True if `func` is a upgrade function in `mod`."""
    import inspect
    return (inspect.isfunction(func) and
            inspect.getmodule(func) == mod and
            func.__name__.startswith('upgrade_to_'))


def get_upgrade_functions(mod, old_buildversion, new_buildversion):
    """Return a list of tuples of the upgrade functions to be executed
    and their respective build numbers.

    :param mod: Module which contains the upgrade functions. You'll
        probably want to use `sys.modules[__name__]` when calling.
    :param old_buildversion: Old build version to use as a threshold.
    :param new_buildversion: New build version to use as a threshold.
    """
    # Gather module's upgrade functions and their build versions.
    functions = [(func, buildversion_for(func))
                 for func in mod.__dict__.itervalues()
                 if is_upgrade_function(mod, func)]

    # Filter the ones that need to be executed for the given build versions.
    funcs_to_run = [x for x in functions
                    if x[1] > old_buildversion and x[1] <= new_buildversion]

    return sorted(funcs_to_run, cmp=lambda x, y: cmp(x[1], y[1]))


def upgrade(product, old_buildversion, new_buildversion):
    """Upgrade to the latest build version and executes any needed actions.

    :param product: Product that needs to be upgraded. It must be a valid
        module name in this package.
    :param old_buildversion: Old build version that was stored in the DB
        at the time of running the upgrade command.
    :param new_buildversion: New build version as stored in the source code.
    """
    import sys
    from django.utils.importlib import import_module

    # Before upgrading anything try to migrate the buildversions to the new
    # PootleConfig model, so all the code uses the same way to retrieve and
    # save the build versions.
    ensure_pootle_config()

    product_module = '.'.join((__name__, product))
    import_module(''.join(('.', product)), __name__)

    upgrade_functions = get_upgrade_functions(sys.modules[product_module],
                                              old_buildversion,
                                              new_buildversion)

    logging.debug('Will run the following upgrade functions: %r',
                  [uf[0].__name__ for uf in upgrade_functions])

    for upgrade_function, upgrade_buildversion in upgrade_functions:
        upgrade_function()
        save_build_version(product, upgrade_buildversion)

    if len(upgrade_functions) == 0:
        save_build_version(product, new_buildversion)
