#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms

from .models import Language


class LanguageSpecialCharsForm(forms.ModelForm):

    class Meta(object):
        model = Language
        fields = ('specialchars',)
