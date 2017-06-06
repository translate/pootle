# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import functools
import logging
import time

import pytest
from pytest_pootle import utils


logger = logging.getLogger("POOTLE_DEBUG")


@pytest.fixture(scope="session")
def log_timings(request, timings):
    return functools.partial(
        utils.log_test_timing,
        logger,
        timings)


@pytest.fixture(scope="session")
def timings(request):
    debug_tests = request.config.getoption("--debug-tests")

    if not debug_tests:
        return
    if debug_tests != "-":
        logger.addHandler(logging.FileHandler(debug_tests))
    utils.log_test_start(logger)
    timings = dict(start=time.time(), tests={})
    request.addfinalizer(
        functools.partial(
            utils.log_test_report,
            logger,
            timings))
    return timings
