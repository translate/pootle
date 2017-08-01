# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter


register = template.Library()
select2_langs = []


@register.filter
@stringfilter
def is_select2_lang(language_code):
    """Return the script tag snippet if the language has l10n for Select2."""
    if not language_code:
        return ''
    global select2_langs
    if not select2_langs:
        select2_l10n_dir = os.path.join(
            settings.WORKING_DIR, 'static', 'js', 'select2_l10n')
        select2_langs = [f.split(".")[0]
                         for f in os.listdir(select2_l10n_dir)
                         if (os.path.isfile(os.path.join(select2_l10n_dir, f))
                             and f.endswith('.js'))]
    return language_code if language_code in select2_langs else ''
