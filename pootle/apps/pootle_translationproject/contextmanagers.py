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
from pootle.core.signals import (
    update_checks, update_data, update_revisions)
from pootle_app.models import Directory
from pootle_store.models import Store


class Updated:
    data = set()
    checks = set()
    tp_data = False
    dirs = set()
    revisions = set()


@contextmanager
def update_tp_after(sender, **kwargs):
    updated = Updated()

    with keep_data():

        @receiver(update_data, sender=Store)
        def update_data_handler(**kwargs):
            updated.data.add(kwargs["instance"])

        @receiver(update_checks, sender=Store)
        def update_check_handler(**kwargs):
            # this could be optimized by only checking units
            updated.checks.add(kwargs["instance"])
        yield

    with keep_data(signals=(update_revisions, )):

        @receiver(update_revisions)
        def update_revisions_handler(**kwargs):
            instance = kwargs.get("instance")
            if isinstance(instance, Store):
                updated.revisions.add(kwargs["instance"].parent.pootle_path)
            elif isinstance(instance, Directory):
                updated.revisions.add(kwargs["instance"].pootle_path)

        if updated.checks:
            update_checks.send(
                sender.__class__,
                instance=sender,
                stores=updated.checks)

        with keep_data(suppress=(sender.__class__, )):

            @receiver(update_data, sender=sender.__class__)
            def update_tp_data_handler(**kwargs):
                updated.tp_data = True
                update_data.disconnect(
                    update_tp_data_handler,
                    sender=sender.__class__)

            if updated.data:
                stores = sender.stores.select_related(
                    "data", "parent").filter(
                        id__in=(st.id for st in updated.data))
                for store in stores:
                    update_data.send(
                        Store,
                        instance=store)
        if updated.tp_data:
            update_data.send(
                sender.__class__,
                instance=sender)

    if updated.revisions:
        update_revisions.send(
            Directory,
            paths=updated.revisions,
            keys=["stats", "checks"])
