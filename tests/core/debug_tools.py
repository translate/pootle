# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re
import time

from pootle.core.debug import (
    debug_sql, log_new_queries, log_timing, timings)

import pytest


def test_debug_timing_logger(caplog):
    start = time.time()

    log_timing(start)
    message = caplog.records[0].message
    assert message.startswith("Timing: ")
    assert message.endswith(" seconds")

    log_timing(start, timed="Foo")
    message = caplog.records[1].message
    assert message.startswith("Timing for Foo: ")
    assert message.endswith(" seconds")


def test_debug_timing_contextmanager(caplog):
    with timings():
        pass
    message = caplog.records[0].message
    assert message.startswith("Timing: ")
    assert message.endswith(" seconds")

    with timings(timed="Foo"):
        pass
    message = caplog.records[1].message
    assert message.startswith("Timing for Foo: ")
    assert message.endswith(" seconds")


@pytest.mark.django_db
def test_debug_sql_logger(caplog, settings):
    from pootle_project.models import Project

    from django.db import connection

    settings.DEBUG = True

    queries = len(connection.queries)

    log_new_queries(queries)
    assert caplog.records == []

    # trigger some sql and log
    Project.objects.count()
    log_new_queries(queries)

    timing = caplog.records[0].message
    sql = caplog.records[1].message

    # match the timing, sql
    assert re.match("^\d+?\.\d+?$", timing)
    assert "SELECT COUNT" in sql
    assert "pootle_app_project" in sql


@pytest.mark.django_db
def test_debug_sql_contextmanager(caplog, settings):
    from pootle_project.models import Project

    with debug_sql():
        pass
    assert caplog.records == []

    # should work even when debug is False
    settings.DEBUG = False

    # trigger some sql and log
    with debug_sql():
        Project.objects.count()

    timing = caplog.records[0].message
    sql = caplog.records[1].message

    # match the timing, sql
    assert re.match("^\d+?\.\d+?$", timing)
    assert "SELECT COUNT" in sql
    assert "pootle_app_project" in sql

    # settings shold be correct
    assert settings.DEBUG is False
