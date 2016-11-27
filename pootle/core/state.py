# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import time


logger = logging.getLogger(__name__)


class ItemState(object):

    def __init__(self, state, state_type, **kwargs):
        self.state = state
        self.state_type = state_type
        self.kwargs = kwargs

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and other.state_type == self.state_type
            and other.state == self.state
            and (sorted(self.kwargs.items())
                 == sorted(other.kwargs.items())))

    def __getattr__(self, k):
        if self.__dict__.get("kwargs") and k in self.__dict__["kwargs"]:
            return self.kwargs[k]
        return self.__getattribute__(k)

    def __str__(self):
        return (
            "<%s(%s): %s %s>"
            % (self.__class__.__name__,
               self.state.context,
               self.state_type,
               self.kwargs))


class State(object):

    item_state_class = ItemState
    prefix = "state"

    def __init__(self, context, load=True, **kwargs):
        self.context = context
        self.__state__ = {}
        self.kwargs = kwargs
        if load:
            self.reload()

    def __contains__(self, k):
        return k in self.__state__ and self.__state__[k]

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.context == other.context
            and sorted(self.kwargs.items()) == sorted(other.kwargs.items())
            and self.prefix == other.prefix)

    def __getitem__(self, k):
        return self.__state__[k]

    def __setitem__(self, k, v):
        self.__state__[k] = v

    def __iter__(self):
        for k in self.__state__:
            if self.__state__[k]:
                yield k

    def __str__(self):
        if not self.has_changed:
            return (
                "<%s(%s): Nothing to report>"
                % (self.__class__.__name__,
                   self.context))
        return (
            "<%s(%s): %s>"
            % (self.__class__.__name__,
               self.context,
               ', '.join(["%s: %s" % (k, len(self.__state__[k]))
                          for k in self.states
                          if self.__state__[k]])))

    @property
    def changed(self):
        return {k: len(v) for k, v in self.__state__.items() if v}

    @property
    def has_changed(self):
        return any(self.__state__.values())

    @property
    def states(self):
        return [x[6:] for x in dir(self) if x.startswith("state_")]

    def add(self, k, v):
        if k in self.__state__:
            self.__state__[k].append(v)

    def clear_cache(self):
        self.__state__ = {k: [] for k in self.states}

    def reload(self):
        self.clear_cache()
        logger.debug("Checking state")
        reload_start = time.time()
        for k in self.states:
            start = time.time()
            state_attr = getattr(
                self, "%s_%s" % (self.prefix, k), None)
            count = 0
            if callable(state_attr):
                for v in state_attr(**self.kwargs):
                    count += 1
                    self.add(
                        k, self.item_state_class(self, k, **v))
            else:
                for v in state_attr:
                    count += 1
                    self.add(
                        k, self.item_state_class(self, k, **v))
            logger.debug(
                "Checked '%s' (%s) in %s seconds",
                k, count, time.time() - start)
        logger.debug(
            "Reloaded state in %s seconds",
            time.time() - reload_start)
        return self
