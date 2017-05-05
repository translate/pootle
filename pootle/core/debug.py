# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import gc
import logging
import resource
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
    debug_logger.debug("total db calls: %s", len(new_queries))


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


def _get_mem_usage(proc=None):
    return resource.getrusage(
        proc or resource.RUSAGE_SELF).ru_maxrss


@contextmanager
def memusage(proc=None):
    usage = {}
    gc.collect()
    usage["initial"] = _get_mem_usage(proc)
    yield usage
    gc.collect()
    usage["after"] = _get_mem_usage(proc)
    usage["used"] = usage["after"] - usage["initial"]
