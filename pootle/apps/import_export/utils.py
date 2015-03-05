#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2015 Zuza Software Foundation
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

from django.utils.translation import ugettext as _
from translate.storage import po
from pootle_store.models import Store


def import_file(file):
    pofile = po.pofile(file.read())
    header = pofile.parseheader()
    pootle_path = header.get("X-Pootle-Path")
    if not pootle_path:
        raise ValueError(_("File %r missing X-Pootle-Path header\n") % (file.name))

    rev = header.get("X-Pootle-Revision")
    if not rev or not rev.isdigit():
        raise ValueError(_("File %r missing or invalid X-Pootle-Revision header\n") % (file.name))
    rev = int(rev)

    try:
        store, created = Store.objects.get_or_create(pootle_path=pootle_path)
        if rev < store.get_max_unit_revision():
            # TODO we could potentially check at the unit level and only reject
            # units older than most recent. But that's in store.update().
            raise ValueError(_("File %r was rejected because its X-Pootle-Revision is too old.") % (file.name))
    except Exception as e:
        raise ValueError(_("Could not create %r. Missing Project/Language? (%s)") % (file.name, e))

    store.update(overwrite=True, store=pofile)
