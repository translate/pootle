#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.storage.factory import getclass

from django.utils.translation import ugettext as _

from pootle_store.models import Store


def import_file(file):
    f = getclass(file)(file.read())
    header = f.parseheader()
    pootle_path = header.get("X-Pootle-Path")
    if not pootle_path:
        raise ValueError(_("File %r missing X-Pootle-Path header\n") % (file.name))

    rev = header.get("X-Pootle-Revision")
    if not rev or not rev.isdigit():
        raise ValueError(
            _("File %r missing or invalid X-Pootle-Revision header\n") % (file.name)
        )
    rev = int(rev)

    try:
        store, created = Store.objects.get_or_create(pootle_path=pootle_path)
        if rev < store.get_max_unit_revision():
            # TODO we could potentially check at the unit level and only reject
            # units older than most recent. But that's in store.update().
            raise ValueError(
                _("File %r was rejected because its X-Pootle-Revision is too old.")
                % (file.name)
            )
    except Exception as e:
        raise ValueError(
            _("Could not create %r. Missing Project/Language? (%s)")
            % (file.name, e)
        )

    store.update(overwrite=True, store=f)
