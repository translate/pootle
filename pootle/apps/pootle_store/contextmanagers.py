# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from contextlib import contextmanager

from django.dispatch import receiver

from pootle.core.contextmanagers import keep_data
from pootle.core.signals import update_data, update_scores


class Updated:
    data = False
    scores = False


@contextmanager
def update_store_after(sender, **kwargs):
    signals = [update_data, update_scores]
    with keep_data(signals=signals):
        updated = Updated()

        @receiver(update_data, sender=sender.__class__)
        def handle_update_data(**kwargs):
            updated.data = True

        @receiver(update_scores, sender=sender.__class__)
        def handle_update_scores(**kwargs):
            updated.scores = True

        yield

    if "kwargs" in kwargs:
        kwargs.update(kwargs.pop("kwargs"))
    if updated.data:
        update_data.send(
            sender.__class__,
            instance=sender,
            **kwargs)
    if updated.scores:
        update_scores.send(
            sender.__class__,
            instance=sender,
            **kwargs)
