# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Random utilities for tests."""

import io
import json
from uuid import uuid4

from translate.storage.factory import getclass


STRING_STORE = """
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"Report-Msgid-Bugs-To: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"X-Generator: Pootle Tests\\n"
%(x_pootle_headers)s

%(units)s
"""

STRING_POOTLE_HEADERS = """
"X-Pootle-Path: %(pootle_path)s\\n"
"X-Pootle-Revision: %(revision)s\\n"
"""

STRING_UNIT = """
#: %(src)s
msgid "%(src)s"
msgstr "%(target)s"
"""


def setup_store(pootle_path):
    from pootle.core.url_helpers import split_pootle_path
    from pootle_translationproject.models import TranslationProject

    from .factories import StoreDBFactory

    (lang_code, proj_code,
     dir_path, filename) = split_pootle_path(pootle_path)
    tp = TranslationProject.objects.get(
        language__code=lang_code, project__code=proj_code)
    directory = tp.directory.get_relative(dir_path)

    return StoreDBFactory(
        translation_project=tp, parent=directory, name=filename)


def create_store(pootle_path=None, store_revision=None, units=None):
    _units = []
    for src, target in units or []:
        _units.append(STRING_UNIT % {"src": src, "target": target})
    units = "\n\n".join(_units)
    x_pootle_headers = ""
    if pootle_path and store_revision:
        x_pootle_headers = (STRING_POOTLE_HEADERS.strip()
                            % {"pootle_path": pootle_path,
                               "revision": store_revision})
    string_store = STRING_STORE % {"x_pootle_headers": x_pootle_headers,
                                   "units": units}
    io_store = io.BytesIO(string_store.encode())
    return getclass(io_store)(io_store.read())


def get_test_uids(offset=0, count=1, pootle_path="^/language0/"):
    """Returns a list translated unit uids from ~middle of
    translated units dataset
    """
    from pootle_store.models import TRANSLATED, Unit

    units = Unit.objects.filter(
        store__pootle_path__regex=pootle_path).filter(state=TRANSLATED)
    begin = (units.count() / 2) + offset
    return list(units[begin: begin + count].values_list("pk", flat=True))


def items_equal(left, right):
    """Returns `True` if items in `left` list are equal to items in
    `right` list.
    """
    try:
        return sorted(left) == sorted(right)
    except TypeError:  # non-iterable
        return False


def create_api_request(rf, method='get', url='/', data='', user=None):
    """Convenience function to create and setup fake requests."""
    if data:
        data = json.dumps(data)

    request_method = getattr(rf, method)
    request = request_method(url, data=data, content_type='application/json')
    request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

    if user is not None:
        request.user = user

    return request


def update_store(store, units=None, store_revision=None, add_headers=False,
                 user=None, submission_type=None, resolve_conflict=None):
    from pootle_store.models import POOTLE_WINS
    if resolve_conflict is None:
        resolve_conflict = POOTLE_WINS
    store_headers = {}
    if add_headers and store_revision:
        store_headers = {"store_revision": store_revision,
                         "pootle_path": store.pootle_path}
    store.update(store=create_store(units=units, **store_headers),
                 store_revision=store_revision,
                 user=user, submission_type=submission_type,
                 resolve_conflict=resolve_conflict)


def get_translated_storefile(store, pootle_path=None):
    """Returns file store with added translations for untranslated units."""
    storeclass = store.get_file_class()
    filestore = store.convert(storeclass)
    for i, unit in enumerate(filestore.units):
        if not unit.istranslated():
            unit.target = "Translation of %s" % unit.source

    path = pootle_path if pootle_path is not None else store.pootle_path
    filestore.updateheader(add=True, X_Pootle_Path=path)
    filestore.updateheader(add=True,
                           X_Pootle_Revision=store.get_max_unit_revision())

    return filestore


def add_store_fs(store, fs_path, synced=False):
    from pootle_fs.models import StoreFS

    if synced:
        return StoreFS.objects.create(
            store=store,
            path=fs_path,
            last_sync_hash=uuid4().hex,
            last_sync_revision=store.get_max_unit_revision())
    return StoreFS.objects.create(
        store=store,
        path=fs_path)
