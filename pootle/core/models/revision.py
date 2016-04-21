# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from ..cache import get_cache


cache = get_cache('redis')


class NoRevision(Exception):
    pass


class Revision(object):
    """Wrapper around the revision counter stored in Redis."""

    CACHE_KEY = 'pootle:revision'
    INITIAL = 0

    @classmethod
    def initialize(cls, force=False):
        """Initializes the revision with `cls.INITIAL`.

        :param force: whether to overwrite the number if there's a
            revision already set or not.
        :return: `True` if the initial value was set, `False` otherwise.
        """
        if force:
            return cls.set(cls.INITIAL)

        return cls.add(cls.INITIAL)

    @classmethod
    def get(cls):
        """Gets the current revision number.

        :return: The current revision number, or `None` if
            there's no revision set.
        """
        return cache.get(cls.CACHE_KEY)

    @classmethod
    def set(cls, value):
        """Sets the revision number to `value`, regardless of whether
        there's a value previously set or not.

        :return: `True` if the value was set, `False` otherwise.
        """
        return cache.set(cls.CACHE_KEY, value)

    @classmethod
    def add(cls, value):
        """Sets the revision number to `value`, only if there's no
        revision already set.

        :return: `True` if the value was set, `False` otherwise.
        """
        return cache.add(cls.CACHE_KEY, value)

    @classmethod
    def incr(cls):
        """Increments the revision number.

        :return: the new revision number after incrementing it, or the
            initial number if there's no revision stored yet.
        """
        try:
            return cache.incr(cls.CACHE_KEY)
        except ValueError:
            raise NoRevision()
