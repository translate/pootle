# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
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

    stores = Store.objects.live().filter(pootle_path__startswith=path)
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
                try:
                    data = store.serialize()
                except Exception as e:
                    logging.error("Could not serialize %r: %s",
                                  store.pootle_path, e)
                    continue
                zf.writestr(prefix + store.pootle_path, data)

        return download(f.getvalue(), "%s.zip" % (prefix), "application/zip")


def handle_upload_form(request, project):
    """Process the upload form."""
    if request.method == "POST" and "file" in request.FILES:
        upload_form = UploadForm(request.POST, request.FILES)
        project_filetypes = [project.localfiletype,
                             project.get_template_filetype()]

        if upload_form.is_valid():
            django_file = request.FILES["file"]
            try:
                if is_zipfile(django_file):
                    with ZipFile(django_file, "r") as zf:
                        for path in zf.namelist():
                            if path.endswith("/"):
                                # is a directory
                                continue
                            ext = os.path.splitext(path)[1].strip(".")
                            if ext not in project_filetypes:
                                continue
                            with zf.open(path, "r") as f:
                                import_file(f, user=request.user)
                else:
                    # It is necessary to seek to the beginning because
                    # is_zipfile fucks the file, and thus cannot be read.
                    django_file.seek(0)
                    import_file(django_file, user=request.user)
            except Exception as e:
                upload_form.add_error("file", e)
                return {
                    "upload_form": upload_form,
                }

    # Always return a blank upload form unless the upload form is not valid.
    return {
        "upload_form": UploadForm(),
    }
