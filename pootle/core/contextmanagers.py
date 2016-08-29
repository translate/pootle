# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from contextlib import contextmanager

from pootle.core.signals import clear_cache


@contextmanager
def expires_cache(expire=False):
    if not expire:
        handlers = clear_cache.receivers
        clear_cache.receivers = []
    yield
    if not expire:
        clear_cache.receivers = handlers
