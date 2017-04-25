# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from contextlib import contextmanager, nested

from django.dispatch import receiver
from django.dispatch.dispatcher import _make_id

from pootle.core.signals import (
    create, delete, update,
    update_checks, update_data, update_revisions, update_scores)


class BulkUpdated(object):
    create = None
    delete_qs = None
    delete = None
    delete_ids = set()
    update_qs = None
    update = None
    updates = None
    update_fields = set()
    update_objects = None


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


def _create_handler(updated, **kwargs):
    to_create = kwargs.get("objects") or []
    to_create += (
        [kwargs.get("instance")]
        if kwargs.get("instance")
        else [])
    if to_create:
        updated.create = (updated.create or []) + to_create


def _delete_handler(updated, **kwargs):
    if "objects" in kwargs:
        if updated.delete_qs is None:
            updated.delete_qs = kwargs["objects"]
        else:
            updated.delete_qs = (
                updated.delete_qs
                | kwargs["objects"])
    if "instance" in kwargs:
        updated.delete_ids.add(kwargs["instance"].pk)


def _update_handler(updated, **kwargs):
    if "update_fields" in kwargs:
        # update these fields (~only)
        updated.update_fields = (
            updated.update_fields
            | kwargs["update_fields"])
    if "updates" in kwargs:
        # dict of pk: dict(up=date)
        updated.updates = (
            kwargs["updates"]
            if updated.updates is None
            else (updated.updates.update(kwargs["updates"])
                  or updated.updates))
    if "objects" in kwargs:
        updated.update_objects = (
            kwargs["objects"]
            if updated.update_objects is None
            else (updated.update_objects
                  + kwargs["objects"]))
    if "instance" in kwargs:
        updated.update_objects = (
            [kwargs["instance"]]
            if updated.update_objects is None
            else (updated.update_objects
                  + [kwargs["instance"]]))


def _callback_handler(model, updated):

    # delete
    to_delete = None
    if updated.delete_ids is not None:
        to_delete = model.objects.filter(
            pk__in=updated.delete_ids)
    if updated.delete_qs is not None:
        to_delete = (
            updated.delete_qs
            if to_delete is None
            else to_delete | updated.delete_qs)
    if to_delete is not None:
        delete.send(
            model,
            objects=to_delete)

    # create
    if updated.create is not None:
        create.send(
            model,
            objects=updated.create)

    # update
    should_update = (
        updated.update_objects is not None
        or updated.updates is not None)
    if should_update:
        update.send(
            model,
            objects=updated.update_objects,
            updates=updated.updates,
            update_fields=updated.update_fields)


@contextmanager
def bulk_context(model=None, **kwargs):
    updated = BulkUpdated()
    signals = [create, delete, update]
    create_handler = kwargs.pop("create", _create_handler)
    delete_handler = kwargs.pop("delete", _delete_handler)
    update_handler = kwargs.pop("update", _update_handler)
    callback_handler = kwargs.pop("callback", _callback_handler)

    with keep_data(signals=signals, suppress=(model, )):

        @receiver(create, sender=model)
        def handle_create(**kwargs):
            create_handler(updated, **kwargs)

        @receiver(delete, sender=model)
        def handle_delete(**kwargs):
            delete_handler(updated, **kwargs)

        @receiver(update, sender=model)
        def handle_update(**kwargs):
            update_handler(updated, **kwargs)
        yield
    callback_handler(model, updated)


@contextmanager
def bulk_operations(model=None, models=None, **kwargs):
    if models is None and model is not None:
        models = [model]
    with nested(*(bulk_context(m, **kwargs) for m in models)):
        yield
