#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
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

"""Translate Toolkit version-specific upgrade actions."""

from __future__ import absolute_import

import logging

from . import save_toolkit_version


def upgrade_to_12008():
    from pootle_store.models import Store, PARSED

    logging.info('Reparsing Qt ts')

    for store in Store.objects \
                      .filter(state__gt=PARSED,
                              translation_project__project__localfiletype='ts',
                              file__iendswith='.ts').iterator():
        store.sync(update_translation=True)
        store.update(update_structure=True, update_translation=True,
                     conservative=False)

    save_toolkit_version(12008)


def upgrade(old_buildversion, new_buildversion):
    """Upgrades to the latest build version and executes any needed actions.

    :param old_buildversion: Old build version that was stored in the DB
        at the time of running the upgrade command.
    :param new_buildversion: New build version as stored in the source code.
    """
    import sys
    from . import get_upgrade_functions

    filtered_fns = get_upgrade_functions(sys.modules[__name__],
                                         old_buildversion, new_buildversion)

    logging.debug('Will run the following upgrade functions: %r',
                  filtered_fns)

    for upgrade_fn in filtered_fns:
        globals()[upgrade_fn]()
        # TODO: Call `save_xxx_version` here, removing this task from
        # `upgrade_to_yyy` functions

    save_toolkit_version(new_buildversion)
