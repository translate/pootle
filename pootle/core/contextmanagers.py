# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from contextlib import contextmanager, nested

from django.dispatch.dispatcher import _make_id

from pootle.core.signals import (
    update_checks, update_data, update_revisions, update_scores)


@contextmanager
def suppress_signal(signal, suppress=None):
    handlers = signal.receivers
    receiver_cache = signal.sender_receivers_cache.copy()
    signal.receivers = []
    if suppress:
        refs = [_make_id(sup) for sup in suppress]
        signal.receivers = [h for h in handlers if not h[0][1] in refs]
    else:
        signal.receivers = []
    signal.sender_receivers_cache.clear()
    try:
        yield
    finally:
        signal.sender_receivers_cache = receiver_cache
        signal.receivers = handlers


@contextmanager
def keep_data(keep=True, signals=None, suppress=None):
    signals = (
        signals
        or (update_checks,
            update_data,
            update_revisions,
            update_scores))
    if keep:
        with nested(*[suppress_signal(s, suppress) for s in signals]):
            yield
    else:
        yield
