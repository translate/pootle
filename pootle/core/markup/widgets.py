# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms


__all__ = ('MarkupTextarea',)


class MarkupTextarea(forms.widgets.Textarea):

    def render(self, name, value, attrs=None):
        if value is not None and not isinstance(value, unicode):
            value = value.raw

        return super(MarkupTextarea, self).render(name, value, attrs)
