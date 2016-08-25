# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


POOTLE_FORMATS = [
    ("po",
     dict(title='Gettext PO',
          extension="po",
          template_extension="pot")),
    ("xliff",
     dict(title='XLIFF',
          extension="xliff",
          template_extension="xliff")),
    ("xlf",
     dict(title='XLIFF',
          extension="xlf",
          template_extension="xlf")),
    ("ts",
     dict(title='TS',
          extension="ts",
          template_extension="ts")),
    ("properties",
     dict(title='Properties',
          extension="properties",
          template_extension="properties")),
    ("lang",
     dict(title='Mozilla Lang',
          extension="lang",
          template_extension="lang")),
    ("l20n",
     dict(title='L20n',
          extension="ftl",
          template_extension="ftl"))]
