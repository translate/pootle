#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.template.base import TemplateDoesNotExist
from django.template.loader import find_template_loader


def get_template_source(name, dirs=None):
    """Retrieves the template's source contents.

    :param name: Template's filename, as passed to the template loader.
    :param dirs: list of directories to optionally override the defaults.
    :return: tuple including file contents and file path.
    """
    for loader_name in settings.TEMPLATE_LOADERS:
        loader = find_template_loader(loader_name)
        if loader is not None:
            try:
                return loader.load_template_source(name, template_dirs=dirs)
            except TemplateDoesNotExist:
                pass

    raise TemplateDoesNotExist(name)
