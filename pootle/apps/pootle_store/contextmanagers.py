# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from contextlib import contextmanager

from pootle.core.contextmanagers import keep_data
from pootle.core.signals import update_data, update_scores


@contextmanager
def update_data_after(sender, **kwargs):
    signals = kwargs.get("signals", [update_data, update_scores])
    with keep_data(signals=signals, suppress=kwargs.get("suppress")):
        yield
    if "kwargs" in kwargs:
        kwargs.update(kwargs.pop("kwargs"))
    for signal in signals:
        signal.send(
            sender.__class__,
            instance=sender,
            **kwargs)
