# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Random utilities for tests."""

import io
import sys
import time
import types
from contextlib import contextmanager
from datetime import datetime
from uuid import uuid4

from translate.storage.factory import getclass

from pootle.core.plugin.delegate import Getter, Provider


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

FUZZY_STRING_UNIT = """
#: %(src)s
#, fuzzy
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
    return StoreDBFactory(
        translation_project=tp, parent=tp.directory, name=filename)


def create_store(pootle_path=None, store_revision=None, units=None):
    _units = []
    for src, target, is_fuzzy in units or []:
        if is_fuzzy:
            _units.append(FUZZY_STRING_UNIT % {"src": src, "target": target})
        else:
            _units.append(STRING_UNIT % {"src": src, "target": target})

    units = "\n\n".join(_units)
    x_pootle_headers = ""
    if pootle_path and store_revision:
        x_pootle_headers = (STRING_POOTLE_HEADERS.strip()
                            % {"pootle_path": pootle_path,
                               "revision": store_revision})
    string_store = STRING_STORE % {"x_pootle_headers": x_pootle_headers,
                                   "units": units}
    io_store = io.BytesIO(string_store.encode('utf-8'))
    return getclass(io_store)(io_store.read())


def get_test_uids(offset=0, count=1, pootle_path="^/language0/"):
    """Returns a list translated unit uids from ~middle of
    translated units dataset
    """
    from pootle_store.constants import TRANSLATED
    from pootle_store.models import Unit

    units = Unit.objects.filter(
        store__pootle_path__regex=pootle_path).filter(state=TRANSLATED)
    begin = (units.count() / 2) + offset
    return list(units[begin: begin + count].values_list("pk", flat=True))


def items_equal(left, right):
    """Returns `True` if items in `left` list are equal to items in
    `right` list.
    """
    return sorted(left) == sorted(right)


def create_api_request(rf, method='get', url='/', data='', user=None,
                       encode_as_json=True):
    """Convenience function to create and setup fake requests."""
    content_type = 'application/x-www-form-urlencoded'
    if data and encode_as_json:
        from pootle.core.utils.json import jsonify
        content_type = 'application/json'
        data = jsonify(data)

    request_method = getattr(rf, method.lower())
    request = request_method(url, data=data, content_type=content_type)
    request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

    if user is not None:
        request.user = user

    return request


def update_store(store, units=None, store_revision=None,
                 user=None, submission_type=None, resolve_conflict=None):
    from pootle_store.models import POOTLE_WINS

    if resolve_conflict is None:
        resolve_conflict = POOTLE_WINS
    store.update(
        store=create_store(units=units),
        store_revision=store_revision,
        user=user, submission_type=submission_type,
        resolve_conflict=resolve_conflict)


def get_translated_storefile(store, pootle_path=None):
    """Returns file store with added translations for untranslated units."""
    storeclass = store.syncer.file_class
    filestore = store.syncer.convert(storeclass)
    for unit in filestore.units:
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


def log_test_start(debug_logger):
    debug_logger.debug(
        "\n%s\nTESTS START: %s\nTESTS: py.test %s\n%s",
        "=" * 80,
        datetime.now(),
        " ".join(sys.argv[1:]),
        "=" * 80)


def log_test_timing(debug_logger, timings, name, start):
    from django.db import connection

    time_taken = time.time() - start
    timings["tests"][name] = dict(
        slow_queries=[
            q for q
            in connection.queries
            if float(q["time"]) > 0],
        query_count=len(connection.queries),
        timing=time_taken)
    debug_logger.debug(
        "{: <70} {: <10} {: <10}".format(
            *(name,
              round(time_taken, 4),
              len(connection.queries))))


def log_test_report(debug_logger, timings):
    debug_logger.debug(
        "%s\nTESTS END: %s",
        "=" * 80,
        datetime.now())
    total_time = time.time() - timings["start"]
    total_queries = sum(
        t["query_count"]
        for t
        in timings["tests"].values())
    if total_queries:
        avg_query_time = total_time / total_queries
        debug_logger.debug(
            "TESTS AVERAGE query time: %s",
            avg_query_time)
    debug_logger.debug(
        "TESTS TOTAL test time: %s",
        total_time)
    debug_logger.debug(
        "TESTS TOTAL queries: %s",
        total_queries)
    debug_logger.debug("%s\n" % ("=" * 80))


@contextmanager
def suppress_getter(getter):
    _orig_get = getter.get
    _orig_connect = getter.connect
    temp_getter = Getter()

    def suppressed_get(self, *args, **kwargs):
        return temp_getter.get(*args, **kwargs)

    def suppressed_connect(self, func, *args, **kwargs):
        return temp_getter.connect(func, *args, **kwargs)

    getter.get = types.MethodType(suppressed_get, getter)
    getter.connect = types.MethodType(suppressed_connect, getter)
    try:
        yield
    finally:
        getter.get = _orig_get
        getter.connect = _orig_connect


@contextmanager
def suppress_provider(provider):
    _orig_gather = provider.gather
    _orig_connect = provider.connect
    temp_provider = Provider()

    def suppressed_gather(self, *args, **kwargs):
        return temp_provider.gather(*args, **kwargs)

    def suppressed_connect(self, func, *args, **kwargs):
        return temp_provider.connect(func, *args, **kwargs)

    provider.gather = types.MethodType(suppressed_gather, provider)
    provider.connect = types.MethodType(suppressed_connect, provider)
    try:
        yield
    finally:
        provider.gather = _orig_gather
        provider.connect = _orig_connect
