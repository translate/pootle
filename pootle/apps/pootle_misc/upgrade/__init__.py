#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
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

from __future__ import absolute_import

import logging


def save_version(build, prefix=''):
    """Store a product's build version.

    :param build: the build version number.
    :param prefix: prefix for the 'BUILDVERSION' key.
    """
    if prefix and not prefix.endswith('_'):
        prefix = prefix.upper() + '_'

    key = prefix + 'BUILDVERSION'

    from .. import siteconfig

    config = siteconfig.load_site_config()
    config.set(key, build)
    config.save()


def save_toolkit_version(build=None):
    """Update TT_BUILDVERSION."""
    if not build:
        from translate.__version__ import build

    save_version(build, prefix='tt')

    logging.info("Database now at Toolkit build %d" % int(build))


def save_pootle_version(build=None):
    """Update POOTLE_BUILDVERSION."""
    if not build:
        from pootle.__version__ import build

    save_version(build, prefix='pootle')

    logging.info("Database now at Pootle build %d" % int(build))


def save_legacy_pootle_version(build=None):
    """Update Pootle's BUILDVERSION (legacy version)."""
    if not build:
        from pootle.__version__ import build

    save_version(build)

    logging.info("Database now at Pootle build %d" % build)


def calculate_stats():
    """Calculate full translation statistics.

    First time to visit the front page all stats for projects and
    languages will be calculated which can take forever. Since users don't
    like webpages that take forever let's precalculate the stats here.
    """
    from pootle_language.models import Language
    from pootle_project.models import Project

    logging.info('Calculating translation statistics, this will take '
                 'a few minutes')

    for language in Language.objects.iterator():
        logging.info(u'Language %s is %d%% complete', language.name,
                     language.translated_percentage())

    for project in Project.objects.iterator():
        logging.info(u'Project %s is %d%% complete', project.fullname,
                     project.translated_percentage())

    logging.info(u"Done calculating statistics")


def flush_quality_checks():
    """Revert stores to unchecked state.

    If a store has false positives marked, quality checks will be updated
    keeping false postivies intact.
    """
    from pootle_store.models import Store, QualityCheck, CHECKED, PARSED

    logging.info('Fixing quality checks. This will take a while')

    for store in Store.objects.filter(state=CHECKED).iterator():
        store_checks = QualityCheck.objects.filter(unit__store=store)
        false_positives = store_checks.filter(false_positive=True).count()

        if false_positives:
            logging.debug("%s has false positives, updating quality checks",
                          store.pootle_path)

            for unit in store.units.iterator():
                unit.update_qualitychecks(keep_false_positives=True)
        else:
            logging.debug("%s has no false positives, deleting checks",
                          store.pootle_path)
            store_checks.delete()
            store.state = PARSED
            store.save()


def buildversion_for_fn(fn):
    """Return the build version string for the `fn` function name."""
    return fn.rsplit('_', 1)[-1]


def filter_upgrade_functions(fn, old_buildversion, new_buildversion):
    """Determine if a upgrade function should be run or not.

    :param fn: Function name candidate to be run.
    :param old_buildversion: Old build version to use as a threshold.
    :param new_buildversion: New build version to use as a threshold.
    """
    try:
        function_buildversion = int(buildversion_for_fn(fn))
        return (function_buildversion > int(old_buildversion) and
                function_buildversion <= int(new_buildversion))
    except ValueError:
        return False


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
    # Gather module's functions and their build versions and filter those
    # that need to be executed for the given build version.
    functions = [(f, buildversion_for_fn(f.__name__))
                    for f in mod.__dict__.itervalues()
                    if is_upgrade_function(mod, f)]
    filtered_functions = filter(
        lambda x: filter_upgrade_functions(x[1], old_buildversion,
                                           new_buildversion),
        functions,
    )

    return sorted(filtered_functions, cmp=lambda x,y: cmp(x[1], y[1]))


def run_upgrade(old_ptl_buildversion=None, new_ptl_buildversion=None,
                old_tt_buildversion=None, new_tt_buildversion=None):
    """Perform version-specific actions for Pootle and Translate Toolkit.

    :param old_ptl_buildversion: Pootle's old build version as stored in
        the DB.
    :param new_ptl_buildversion: Pootle's new build version as stored in
        the source code.
    :param old_tt_buildversion: Toolkit's old build version as stored in
        the DB.
    :param new_tt_buildversion: Toolkit's new build version as stored in
        the source code.
    """
    if old_ptl_buildversion and new_ptl_buildversion:
        upgrade('pootle', old_ptl_buildversion, new_ptl_buildversion)

    if old_tt_buildversion and new_tt_buildversion:
        upgrade('ttk', old_ptl_buildversion, new_ptl_buildversion)


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

    save_version_function = {
        'pootle': save_pootle_version,
        'ttk': save_toolkit_version,
    }

    product_module = '.'.join((__name__, product))
    import_module(''.join(('.', product)), __name__)

    upgrade_functions = get_upgrade_functions(sys.modules[product_module],
                                              old_buildversion,
                                              new_buildversion)

    logging.debug('Will run the following upgrade functions: %r',
                  [uf[0].__name__ for uf in upgrade_functions])

    for upgrade_function, upgrade_buildversion in upgrade_functions:
        upgrade_function()
        save_version_function[product](upgrade_buildversion)

    save_version_function[product](new_buildversion)
