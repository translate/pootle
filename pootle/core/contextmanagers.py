# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from contextlib import contextmanager

from pootle.core.signals import update_data


@contextmanager
def keep_data(keep=True):
    if keep:
        handlers = update_data.receivers
        update_data.receivers = []
    yield
    if keep:
        update_data.receivers = handlers
