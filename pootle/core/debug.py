# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import time
from contextlib import contextmanager


logger = logging.getLogger("POOTLE_DEBUG")


def log_timing(start, timed=None, debug_logger=None):
    debug_logger = debug_logger or logger
    timing = time.time() - start
    if timed:
        msg = (
            "Timing for %s: %s seconds"
            % (timed, timing))
    else:
        msg = (
            "Timing: %s seconds"
            % timing)
    debug_logger.debug(msg)


def log_new_queries(queries, debug_logger=None):
    from django.db import connection

    debug_logger = debug_logger or logger
    new_queries = list(connection.queries[queries:])
    for query in new_queries:
        debug_logger.debug(query["time"])
        debug_logger.debug("\t%s", query["sql"])


@contextmanager
def timings(timed=None, debug_logger=None):
    start = time.time()
    yield
    log_timing(
        start,
        timed,
        debug_logger or logger)


@contextmanager
def debug_sql(debug_logger=None):
    from django.conf import settings
    from django.db import connection

    debug = settings.DEBUG
    settings.DEBUG = True
    queries = len(connection.queries)
    try:
        yield
    finally:
        log_new_queries(
            queries,
            debug_logger)
        settings.DEBUG = debug
