#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

__all__ = ('DirtyFieldsMixin',)

from django.db.models.signals import post_save


class DirtyFieldsMixin(object):
    """Track dirty fields in a model.

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
        return dict([(f.name, self.__dict__[f.name])
                     for f in self._meta.local_fields if not f.rel])

    def get_dirty_fields(self):
        new_state = self._as_dict()
        return dict([(key, value)
                     for key, value in self._original_state.iteritems()
                     if value != new_state[key]])

    def is_dirty(self):
        # In order to be dirty we need to have been saved at least once,
        # so we check for a primary key and we need our dirty fields to
        # not be empty.
        if not self.pk:
            return True

        return {} != self.get_dirty_fields()


def reset_state(sender, instance, **kwargs):
    instance._original_state = instance._as_dict()
