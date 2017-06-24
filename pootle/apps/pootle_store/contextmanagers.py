# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from contextlib import contextmanager

from django.dispatch import receiver

from pootle.core.contextmanagers import bulk_operations, keep_data
from pootle.core.signals import (
    update_checks, update_data, update_revisions, update_scores)
from pootle_data.models import StoreChecksData, StoreData, TPChecksData, TPData
from pootle_score.models import UserStoreScore

from .models import Unit


class Updated(object):
    data = False
    scores = None
    checks = None
    revisions = False


def _callback_handler(sender, updated, **kwargs):

    bulk_pootle = bulk_operations(
        models=(
            UserStoreScore,
            TPData,
            TPChecksData,
            StoreData,
            StoreChecksData))

    with keep_data(signals=(update_revisions, )):
        with bulk_pootle:

            @receiver(update_revisions)
            def handle_update_revisions(**kwargs):
                updated.revisions = True

            if updated.checks:
                update_checks.send(
                    sender.__class__,
                    instance=sender,
                    units=updated.checks,
                    **kwargs)
            if updated.data:
                update_data.send(
                    sender.__class__,
                    instance=sender,
                    **kwargs)
            if updated.scores:
                update_scores.send(
                    sender.__class__,
                    instance=sender,
                    users=updated.scores,
                    **kwargs)
    if updated.revisions:
        update_revisions.send(
            sender.__class__,
            instance=sender,
            keys=["stats", "checks"])


@contextmanager
def update_store_after(sender, **kwargs):
    signals = [
        update_checks,
        update_data,
        update_revisions,
        update_scores]

    with keep_data(signals=signals):
        updated = Updated()

        @receiver(update_checks, sender=Unit)
        def handle_update_checks(**kwargs):
            if updated.checks is None:
                updated.checks = set()
            updated.checks.add(kwargs["instance"].id)

        @receiver(update_data, sender=sender.__class__)
        def handle_update_data(**kwargs):
            updated.data = True
            update_data.disconnect(
                handle_update_data,
                sender=sender.__class__)

        @receiver(update_scores, sender=sender.__class__)
        def handle_update_scores(**kwargs):
            if updated.scores is None:
                updated.scores = set()
            updated.scores = (
                updated.scores
                | set(kwargs.get("users") or []))
        yield

    if "kwargs" in kwargs:
        kwargs.update(kwargs.pop("kwargs"))
    kwargs.get("callback", _callback_handler)(
        sender, updated, **kwargs)
