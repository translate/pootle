#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

import os

from translate.storage.xliff import xlifffile

from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from pootle_store.models import Store

def export_as_xliff(request, pootle_path):
    if pootle_path[0] != '/':
        pootle_path = '/' + pootle_path
    store = get_object_or_404(Store, pootle_path=pootle_path)
    outputstore = store.convert(xlifffile)
    outputstore.switchfile(store.name, createifmissing=True)
    encoding = getattr(store.file.store, "encoding", "UTF-8")
    content_type = "application/x-xliff; charset=UTF-8"
    response = HttpResponse(str(outputstore), content_type=content_type)
    filename, ext = os.path.splitext(store.name)
    filename += os.path.extsep + 'xlf'
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response
