# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.dispatch import Signal
from django.dispatch.dispatcher import NO_RECEIVERS, NONE_ID, _make_id, weakref

from .exceptions import StopProviding
from .results import GatheredDict


class Provider(Signal):

    result_class = GatheredDict

    def __init__(self, *args, **kwargs):
        self.result_class = kwargs.pop("result_class", self.result_class)
        self._sender_map = {}
        super(Provider, self).__init__(*args, **kwargs)

    def gather(self, sender=None, **named):
        gathered = self.result_class(self)
        named["gathered"] = gathered
        no_receivers = (
            not self.receivers
            or (sender and self.use_caching
                and not self._dead_receivers
                and self.sender_receivers_cache.get(sender) is NO_RECEIVERS))
        if no_receivers:
            return gathered
        for provider in self._live_receivers(sender):
            try:
                gathered.add_result(
                    provider,
                    provider(signal=self, sender=sender, **named))
            except StopProviding as e:
                # allow a provider to prevent further gathering
                gathered.add_result(
                    provider,
                    e.result)
                break
        return gathered

    def connect(self, receiver, sender=None, weak=True, dispatch_uid=None):
        super(Provider, self).connect(receiver, sender, weak, dispatch_uid)
        self._sender_map[_make_id(sender)] = sender

    def _live_receivers(self, sender):
        """
        Filter sequence of receivers to get resolved, live receivers.
        This checks for weak references and resolves them, then returning only
        live receivers.
        """
        with self.lock:
            self._clear_dead_receivers()
            senderkey = _make_id(sender)
            receivers = []
            for (receiverkey, r_senderkey), receiver in self.receivers:
                r_sender = self._sender_map[r_senderkey]
                if r_senderkey == NONE_ID or r_senderkey == senderkey:
                    receivers.append(receiver)
                elif sender and issubclass(sender, r_sender):
                    receivers.append(receiver)
            if self.use_caching and sender:
                if not receivers:
                    self.sender_receivers_cache[sender] = NO_RECEIVERS
                else:
                    # Note, we must cache the weakref versions.
                    self.sender_receivers_cache[sender] = receivers
        non_weak_receivers = []
        for receiver in receivers:
            if isinstance(receiver, weakref.ReferenceType):
                # Dereference the weak reference.
                receiver = receiver()
                if receiver is not None:
                    non_weak_receivers.append(receiver)
            else:
                non_weak_receivers.append(receiver)
        return non_weak_receivers


def provider(signal, **kwargs):
    def _decorator(func):
        if isinstance(signal, (list, tuple)):
            for s in signal:
                s.connect(func, **kwargs)
        else:
            signal.connect(func, **kwargs)
        return func
    return _decorator


class Getter(Signal):

    def __init__(self, *args, **kwargs):
        super(Getter, self).__init__(*args, **kwargs)
        self.use_caching = True

    def get(self, sender=None, **named):
        receivers_cache = self.sender_receivers_cache.get(sender)
        no_receivers = (
            not self.receivers
            or receivers_cache is NO_RECEIVERS)
        if no_receivers:
            return None
        elif receivers_cache:
            for receiver in receivers_cache:
                if isinstance(receiver, weakref.ReferenceType):
                    # Dereference the weak reference.
                    receiver = receiver()
                if receiver is not None:
                    response = receiver(signal=self, sender=sender, **named)
                    if response is not None:
                        return response
        for receiver in self._live_receivers(sender):
            response = receiver(signal=self, sender=sender, **named)
            if response is not None:
                return response


def getter(signal, **kwargs):
    def _connect(s, func, **kwargs):
        senders = kwargs.pop('sender', None)
        if isinstance(senders, (list, tuple)):
            for sender in senders:
                s.connect(func, sender=sender, **kwargs)
        else:
            s.connect(func, sender=senders, **kwargs)

    def _decorator(func):
        if isinstance(signal, (list, tuple)):
            for s in signal:
                _connect(s, func, **kwargs)
        else:
            _connect(signal, func, **kwargs)
        return func
    return _decorator
