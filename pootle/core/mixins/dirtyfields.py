#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models.signals import post_save


__all__ = ('DirtyFieldsMixin',)


class DirtyFieldsMixin(object):
    """Tracks dirty fields in a model.

    Initial code borrowed from django-dirtyfields, which is
    Copyright (c) Praekelt Foundation and individual contributors
    """

    def __init__(self, *args, **kwargs):
        super(DirtyFieldsMixin, self).__init__(*args, **kwargs)
        post_save.connect(
            reset_state, sender=self.__class__,
            dispatch_uid='%s-DirtyFieldsMixin-sweeper' %
                         self.__class__.__name__,
        )
        reset_state(sender=self.__class__, instance=self)

    def _as_dict(self):
        return {f.name: self.__dict__[f.name]
                for f in self._meta.local_fields
                if not f.rel}

    def get_dirty_fields(self):
        new_state = self._as_dict()
        return {key: value
                for key, value in self._original_state.iteritems()
                if value != new_state[key]}

    def is_dirty(self):
        # In order to be dirty we need to have been saved at least once,
        # so we check for a primary key and we need our dirty fields to
        # not be empty
        if not self.pk:
            return True

        return {} != self.get_dirty_fields()


def reset_state(sender, instance, **kwargs):
    instance._original_state = instance._as_dict()
