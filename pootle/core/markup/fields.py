#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
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

import logging

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils.safestring import mark_safe
from south.modelsinspector import add_introspection_rules

from .filters import apply_markup_filter
from .widgets import MarkupTextarea


__all__ = ('Markup', 'MarkupField',)


logger = logging.getLogger('pootle.markup')


_rendered_cache_key = lambda obj, pk, field: '_%s_%s_%s_rendered' % \
        (obj, pk, field)


class Markup(object):

    def __init__(self, instance, field_name, rendered_cache_key):
        self.instance = instance
        self.field_name = field_name
        self.cache_key = rendered_cache_key

    @property
    def raw(self):
        return self.instance.__dict__[self.field_name]

    @raw.setter
    def raw(self, value):
        setattr(self.instance, self.field_name, value)

    @property
    def rendered(self):
        rendered = cache.get(self.cache_key)

        if not rendered:
            logger.debug(u'Caching rendered output of %r', self.cache_key)
            rendered = apply_markup_filter(self.raw)
            cache.set(self.cache_key, rendered,
                      settings.OBJECT_CACHE_TIMEOUT)

        return rendered

    def __unicode__(self):
        return mark_safe(self.rendered)

    def __nonzero__(self):
        return self.raw.strip() != '' and self.raw is not None


class MarkupDescriptor(object):

    def __init__(self, field):
        self.field = field

    def __get__(self, obj, owner):
        if obj is None:
            raise AttributeError('Can only be accessed via an instance.')

        markup = obj.__dict__[self.field.name]
        if markup is None:
            return None

        cache_key = _rendered_cache_key(obj.__class__.__name__,
                                        obj.pk,
                                        self.field.name)
        return Markup(obj, self.field.name, cache_key)

    def __set__(self, obj, value):
        if isinstance(value, Markup):
            obj.__dict__[self.field.name] = value.raw
        else:
            obj.__dict__[self.field.name] = value


class MarkupField(models.TextField):

    description = 'Text field supporting different markup formats.'

    def contribute_to_class(self, cls, name):
        super(MarkupField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, MarkupDescriptor(self))

    def pre_save(self, model_instance, add):
        value = super(MarkupField, self).pre_save(model_instance, add)

        if not add:
            # Invalidate cache to force rendering upon next retrieval.
            cache_key = _rendered_cache_key(model_instance.__class__.__name__,
                                            model_instance.pk,
                                            self.name)
            logger.debug('Invalidating cache for %r', cache_key)
            cache.delete(cache_key)

        return value.raw

    def get_prep_value(self, value):
        if isinstance(value, Markup):
            return value.raw

        return value

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)

    def formfield(self, **kwargs):
        defaults = {'widget': MarkupTextarea}
        defaults.update(kwargs)
        return super(MarkupField, self).formfield(**defaults)


add_introspection_rules(
        [],
        ["^pootle\.core\.markup\.fields\.MarkupField"],
    )
