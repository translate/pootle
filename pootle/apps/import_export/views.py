#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2015 Zuza Software Foundation
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

import os
from io import BytesIO
from zipfile import ZipFile, is_zipfile
from django.http import Http404, HttpResponse
from pootle_store.models import Store
from .forms import UploadForm
from .utils import import_file


def download(contents, name, content_type):
    response = HttpResponse(contents, content_type=content_type)
    response["Content-Disposition"] = "attachment; filename=%s" % (name)
    return response


def export(request):
    path = request.GET.get("path")
    if not path:
        raise Http404

    stores = Store.objects.filter(pootle_path__startswith=path)
    num_items = stores.count()

    if not num_items:
        raise Http404

    if num_items == 1:
        store = stores.get()
        contents = BytesIO(store.serialize())
        name = os.path.basename(store.pootle_path)
        contents.seek(0)
        return download(contents.read(), name, "application/octet-stream")

    # zip all the stores together
    f = BytesIO()
    prefix = path.strip("/").replace("/", "-")
    if not prefix:
        prefix = "export"
    with BytesIO() as f:
        with ZipFile(f, "w") as zf:
            for store in stores:
                zf.writestr(prefix + store.pootle_path, store.serialize())

        return download(f.getvalue(), "%s.zip" % (prefix), "application/zip")


def handle_upload_form(request):
    """Process the upload form."""
    if request.method == "POST" and "file" in request.FILES:
        upload_form = UploadForm(request.POST, request.FILES)

        if upload_form.is_valid():
            django_file = request.FILES["file"]
            try:
                if is_zipfile(django_file):
                    with ZipFile(django_file, "r") as zf:
                        for path in zf.namelist():
                            if path.endswith("/"):
                                # is a directory
                                continue
                            with zf.open(path, "r") as f:
                                import_file(f)
                else:
                    # It is necessary to seek to the beginning because
                    # is_zipfile fucks the file, and thus cannot be read.
                    django_file.seek(0)
                    import_file(django_file)
            except Exception as e:
                upload_form.add_error("file", e.message)
                return {
                    "upload_form": upload_form,
                    "display_sidebar": True,
                }

    # Always return a blank upload form unless the upload form is not valid.
    return {
        "upload_form": UploadForm(),
        "display_sidebar": True,
    }
