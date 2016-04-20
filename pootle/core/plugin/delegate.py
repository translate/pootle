# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.dispatch import Signal
from django.dispatch.dispatcher import NO_RECEIVERS

from .exceptions import StopProviding
from .results import GatheredDict


class Provider(Signal):

    result_class = GatheredDict

    def __init__(self, *args, **kwargs):
        self.result_class = kwargs.pop("result_class", self.result_class)
        super(Provider, self).__init__(*args, **kwargs)

    def gather(self, sender=None, **named):
        gathered = self.result_class(self)
        named["gathered"] = gathered
        no_receivers = (
            not self.receivers
            or self.sender_receivers_cache.get(sender) is NO_RECEIVERS)
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

    def get(self, sender=None, **named):
        no_receivers = (
            not self.receivers
            or self.sender_receivers_cache.get(sender) is NO_RECEIVERS)
        if no_receivers:
            return None
        for receiver in self._live_receivers(sender):
            response = receiver(signal=self, sender=sender, **named)
            if response is not None:
                return response


def getter(signal, **kwargs):
    def _decorator(func):
        if isinstance(signal, (list, tuple)):
            for s in signal:
                s.connect(func, **kwargs)
        else:
            signal.connect(func, **kwargs)
        return func
    return _decorator
