# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import threading
import types
from contextlib import contextmanager, nested

from django.dispatch import Signal, receiver

from pootle.core.signals import (
    create, delete, update, update_checks, update_data, update_revisions,
    update_scores)


class BulkUpdated(object):
    create = None
    delete_qs = None
    delete = None
    delete_ids = None
    update_qs = None
    update = None
    updates = None
    update_fields = None
    update_objects = None


@contextmanager
def suppress_signal(signal, suppress=None):
    lock = threading.Lock()
    suppressed_thread = threading.current_thread().ident

    _orig_send = signal.send
    _orig_connect = signal.connect
    temp_signal = Signal()

    def _should_suppress(*args, **kwargs):
        sender = args[0] if args else kwargs.get("sender")
        return (
            threading.current_thread().ident == suppressed_thread
            and (not suppress
                 or not sender
                 or sender in suppress))

    def suppressed_send(self, *args, **kwargs):
        return (
            _orig_send(*args, **kwargs)
            if not _should_suppress(*args, **kwargs)
            else temp_signal.send(*args, **kwargs))

    def suppressed_connect(self, func, *args, **kwargs):
        return (
            _orig_connect(func, *args, **kwargs)
            if not _should_suppress(*args, **kwargs)
            else temp_signal.connect(func, *args, **kwargs))
    with lock:
        signal.send = types.MethodType(suppressed_send, signal)
        signal.connect = types.MethodType(suppressed_connect, signal)
    try:
        yield
    finally:
        with lock:
            signal.send = _orig_send
            signal.connect = _orig_connect


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
        if updated.delete_ids is None:
            updated.delete_ids = set()
        updated.delete_ids.add(kwargs["instance"].pk)


def _update_handler(updated, **kwargs):
    if kwargs.get("update_fields"):
        if updated.update_fields is None:
            updated.update_fields = set()
        # update these fields (~only)
        updated.update_fields = (
            updated.update_fields
            | set(kwargs["update_fields"]))
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
