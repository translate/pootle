# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings

from .constants import STATES_NAMES, TRANSLATED
from .unit.altsrc import AltSrcUnits


def find_altsrcs(unit, alt_src_langs, store=None, project=None):
    from pootle_store.models import Unit

    if not alt_src_langs:
        return []

    store = store or unit.store
    project = project or store.translation_project.project

    altsrcs_qs = Unit.objects.filter(
        unitid_hash=unit.unitid_hash,
        store__translation_project__project=project,
        store__translation_project__language__in=alt_src_langs,
        state=TRANSLATED)
    return AltSrcUnits(altsrcs_qs).units


def get_change_str(changes):
    """Returns a formatted string for the non-zero items of a `changes`
    dictionary.

    If all elements are zero, `nothing changed` is returned.
    """
    res = [u'%s %d' % (key, changes[key])
           for key in changes if changes[key] > 0]

    if res:
        return ", ".join(res)

    return "no changed"


def parse_pootle_revision(store):
    if hasattr(store, "parseheader"):
        pootle_revision = store.parseheader().get("X-Pootle-Revision",
                                                  None)
        if pootle_revision is not None:
            return int(pootle_revision)
    return None


def get_state_name(code, default="untranslated"):
    return STATES_NAMES.get(code, default)


def vfolders_installed():
    return "virtualfolder" in settings.INSTALLED_APPS
