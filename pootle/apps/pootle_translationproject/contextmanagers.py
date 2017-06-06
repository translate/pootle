# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from contextlib import contextmanager

from django.contrib.auth import get_user_model
from django.dispatch import receiver

from pootle.core.contextmanagers import bulk_operations, keep_data
from pootle.core.signals import (
    update_checks, update_data, update_revisions, update_scores)
from pootle_app.models import Directory
from pootle_data.models import StoreChecksData, StoreData, TPChecksData, TPData
from pootle_score.models import UserStoreScore, UserTPScore
from pootle_store.models import QualityCheck, Store


class Updated(object):
    data = None
    checks = None
    tp_data = False
    revisions = None
    score_stores = None
    score_users = None
    tp_scores = False


def _handle_update_stores(sender, updated):

    @receiver(update_data, sender=sender.__class__)
    def update_tp_data_handler(**kwargs):
        updated.tp_data = True
        update_data.disconnect(
            update_tp_data_handler,
            sender=sender.__class__)

    @receiver(update_scores, sender=sender.__class__)
    def update_tp_scores_handler(**kwargs):
        updated.tp_scores = True
        update_scores.disconnect(
            update_tp_scores_handler,
            sender=sender.__class__)

    if updated.checks:
        with keep_data(suppress=(Store, ), signals=(update_data, )):

            @receiver(update_data, sender=Store)
            def extra_update_data_handler_(**kwargs):
                updated.data = updated.data or {}
                updated.data[kwargs["instance"].id] = kwargs["instance"]

            with bulk_operations(QualityCheck):
                for to_check in updated.checks.values():
                    store = to_check["store"]
                    units = (
                        [unit for unit in to_check["units"]]
                        if to_check["units"]
                        else None)
                    update_checks.send(
                        store.__class__,
                        instance=store,
                        units=units)

    if updated.data:
        stores = updated.data.values()
        for store in stores:
            update_data.send(
                Store,
                instance=store)
    if updated.score_stores:
        for store in updated.score_stores.values():
            update_scores.send(
                store.__class__,
                instance=store,
                users=updated.score_users)


def _update_stores(sender, updated):
    # call signals for stores
    bulk_stores = bulk_operations(
        models=(
            UserStoreScore,
            StoreData,
            StoreChecksData))
    with keep_data(suppress=(sender.__class__, )):
        with bulk_stores:
            _handle_update_stores(sender, updated)


def _callback_handler(sender, updated, **kwargs):

    bulk_tps = bulk_operations(
        models=(
            get_user_model(),
            UserTPScore,
            TPData,
            TPChecksData))
    with keep_data(signals=(update_revisions, )):

        @receiver(update_revisions)
        def update_revisions_handler(**kwargs):
            if updated.revisions is None:
                updated.revisions = set()
            instance = kwargs.get("instance")
            if isinstance(instance, Store):
                updated.revisions.add(kwargs["instance"].parent.pootle_path)
            elif isinstance(instance, Directory):
                updated.revisions.add(kwargs["instance"].pootle_path)

        with bulk_tps:
            _update_stores(sender, updated)

            if updated.tp_data:
                update_data.send(
                    sender.__class__,
                    instance=sender)
            if updated.tp_scores:
                update_scores.send(
                    sender.__class__,
                    instance=sender,
                    users=updated.score_users)
    if updated.revisions:
        update_revisions.send(
            Directory,
            paths=updated.revisions,
            keys=["stats", "checks"])


@contextmanager
def update_tp_after(sender, **kwargs):
    updated = Updated()

    with keep_data():

        @receiver(update_data, sender=Store)
        def update_data_handler(**kwargs):
            if updated.data is None:
                updated.data = {}
            updated.data[kwargs["instance"].id] = kwargs["instance"]

        @receiver(update_checks)
        def update_check_handler(**kwargs):
            if updated.checks is None:
                updated.checks = {}
            units = None
            if isinstance(kwargs.get("instance"), Store):
                store = kwargs["instance"]
                units = set(kwargs.get("units") or [])
            else:
                store = kwargs["instance"].store
                units = set([kwargs["instance"].id])
            updated.checks[store.id] = updated.checks.get(
                store.id,
                dict(store=store, units=set()))
            if units is not None:
                updated.checks[store.id]["units"] |= units

        @receiver(update_scores, sender=Store)
        def update_scores_handler(**kwargs):
            if not updated.score_stores:
                updated.score_stores = {}
            if "instance" in kwargs:
                updated.score_stores[kwargs["instance"].id] = kwargs["instance"]
            if "users" in kwargs:
                updated.score_users = (
                    (updated.score_users or set())
                    | set(kwargs["users"]))
        yield
    kwargs.get("callback", _callback_handler)(
        sender, updated, **kwargs)
