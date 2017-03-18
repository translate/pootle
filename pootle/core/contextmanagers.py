# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from contextlib import contextmanager, nested

from pootle.core.signals import update_data, update_scores


@contextmanager
def suppress_signal(signal):
    handlers = signal.receivers
    receiver_cache = signal.sender_receivers_cache.copy()
    signal.receivers = []
    try:
        yield
    finally:
        signal.sender_receivers_cache = receiver_cache
        signal.receivers = handlers


@contextmanager
def keep_data(keep=True, signals=(update_data, update_scores)):
    if keep:
        with nested(*[suppress_signal(s) for s in signals]):
            yield
    else:
        yield


@contextmanager
def update_data_after(sender, **kwargs):
    signals = kwargs.get("signals", [update_data, update_scores])
    with keep_data(signals=signals):
        yield
    if "kwargs" in kwargs:
        kwargs.update(kwargs.pop("kwargs"))
    for signal in signals:
        signal.send(
            sender.__class__,
            instance=sender,
            **kwargs)
