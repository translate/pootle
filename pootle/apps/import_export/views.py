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
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from translate.storage import po
from pootle_store.models import Store
from .forms import UploadForm


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


def _import_file(file):
    pofile = po.pofile(file.read())
    header = pofile.parseheader()
    pootle_path = header.get("X-Pootle-Path")
    if not pootle_path:
        raise ValueError("File %r missing X-Pootle-Path header\n" % (file.name))

    rev = header.get("X-Pootle-Revision")
    if not rev or not rev.isdigit():
        raise ValueError("File %r missing or invalid X-Pootle-Revision header\n" % (file.name))
    rev = int(rev)

    try:
        store, created = Store.objects.get_or_create(pootle_path=pootle_path)
        if rev < store.get_max_unit_revision():
            # TODO we could potentially check at the unit level and only reject
            # units older than most recent. But that's in store.update().
            raise ValueError("File %r was rejected because its X-Pootle-Revision is too old." % (file.name))
    except Exception as e:
        raise ValueError("Could not create %r. Missing Project/Language? (%s)" % (file.name, e))

    store.update(overwrite=True, store=pofile)


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
                            with zf.open(path, "r") as f:
                                _import_file(f)
                else:
                    # It is necessary to seek to the beginning because
                    # is_zipfile fucks the file, and thus cannot be read.
                    django_file.seek(0)
                    _import_file(django_file)
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
