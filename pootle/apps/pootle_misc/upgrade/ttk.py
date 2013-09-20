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

"""Translate Toolkit version-specific upgrade actions."""

import logging


def upgrade_to_12008():
    from pootle_store.models import Store, PARSED

    logging.info('Reparsing Qt ts')

    criteria = {
        'state__gt': PARSED,
        'translation_project__project__localfiletype': 'ts',
        'file__iendswith': '.ts',
    }
    for store in Store.objects.filter(**criteria).iterator():
        store.sync(update_translation=True)
        store.update(update_structure=True, update_translation=True)
