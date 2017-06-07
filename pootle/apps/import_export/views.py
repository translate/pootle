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

from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponse
from django.shortcuts import redirect

from pootle.core.delegate import language_team
from pootle.core.views.base import PootleDetailView
from pootle_app.models.permissions import check_permission
from pootle_store.models import Store
from pootle_translationproject.views import TPDirectoryMixin

from .forms import UploadForm
from .utils import TPTMXExporter, import_file


def download(contents, name, content_type):
    response = HttpResponse(contents, content_type=content_type)
    response["Content-Disposition"] = "attachment; filename=%s" % (name)
    return response


def export(request):
    path = request.GET.get("path")
    if not path:
        raise Http404
    stores = Store.objects.live().select_related(
        "data",
        "filetype__extension",
        "translation_project",
        "translation_project__project",
        "translation_project__language").filter(pootle_path__startswith=path)
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


def handle_upload_form(request, tp):
    """Process the upload form."""
    valid_extensions = tp.project.filetype_tool.valid_extensions
    if "po" not in valid_extensions:
        return {}
    language = tp.language
    team = language_team.get(tp.language.__class__)(language)

    uploader_list = [(request.user.id, request.user.display_name), ]
    if check_permission('administrate', request):
        User = get_user_model()
        uploader_list = [
            (user.id, user.display_name)
            for user
            in (team.submitters | team.reviewers | team.admins | team.superusers)]

    if request.method == "POST" and "file" in request.FILES:
        upload_form = UploadForm(
            request.POST,
            request.FILES,
            uploader_list=uploader_list
        )

        if upload_form.is_valid():
            uploader_id = upload_form.cleaned_data["user_id"]
            django_file = request.FILES["file"]
            uploader = request.user
            if uploader_id and uploader_id != uploader.id:
                User = get_user_model()
                uploader = User.objects.get(
                    id=upload_form.cleaned_data["user_id"]
                )

            try:
                if is_zipfile(django_file):
                    with ZipFile(django_file, "r") as zf:
                        for path in zf.namelist():
                            if path.endswith("/"):
                                # is a directory
                                continue
                            ext = os.path.splitext(path)[1].strip(".")
                            if ext not in valid_extensions:
                                continue
                            with zf.open(path, "r") as f:
                                import_file(f, user=uploader)
                else:
                    # is_zipfile consumes the file buffer
                    django_file.seek(0)
                    import_file(django_file, user=uploader)
            except Exception as e:
                upload_form.add_error("file", e)
                return {
                    "upload_form": upload_form,
                }
        else:
            return {
                "upload_form": upload_form,
            }

    # Always return a blank upload form unless the upload form is not valid.
    return {
        "upload_form": UploadForm(
            uploader_list=uploader_list,
            initial=dict(user_id=request.user.id)
        ),
    }


class TPOfflineTMView(TPDirectoryMixin, PootleDetailView):

    @property
    def path(self):
        return "/%s/%s/" % (self.kwargs['language_code'],
                            self.kwargs['project_code'])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        exporter = TPTMXExporter(self.tp)
        url = exporter.get_url()
        if url is not None:
            return redirect(url)
        raise Http404
