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
from zipfile import ZipFile

from translate.storage.factory import getclass
from translate.storage import tmx

from django.conf import settings
from django.utils.functional import cached_property

from pootle.core.delegate import revision
from pootle.i18n.gettext import ugettext_lazy as _
from pootle_app.models.permissions import check_user_permission
from pootle_statistics.models import SubmissionTypes
from pootle_store.constants import TRANSLATED
from pootle_store.models import Store

from .exceptions import (FileImportError, MissingPootlePathError,
                         MissingPootleRevError, UnsupportedFiletypeError)


logger = logging.getLogger(__name__)


def import_file(f, user=None):
    ttk = getclass(f)(f.read())
    if not hasattr(ttk, "parseheader"):
        raise UnsupportedFiletypeError(_("Unsupported filetype '%s', only PO "
                                         "files are supported at this time\n",
                                         f.name))
    header = ttk.parseheader()
    pootle_path = header.get("X-Pootle-Path")
    if not pootle_path:
        raise MissingPootlePathError(_("File '%s' missing X-Pootle-Path "
                                       "header\n", f.name))

    rev = header.get("X-Pootle-Revision")
    if not rev or not rev.isdigit():
        raise MissingPootleRevError(_("File '%s' missing or invalid "
                                      "X-Pootle-Revision header\n",
                                      f.name))
    rev = int(rev)

    try:
        store = Store.objects.get(pootle_path=pootle_path)
    except Store.DoesNotExist as e:
        raise FileImportError(_("Could not create '%s'. Missing "
                                "Project/Language? (%s)", (f.name, e)))

    tp = store.translation_project
    allow_add_and_obsolete = ((tp.project.checkstyle == 'terminology'
                               or tp.is_template_project)
                              and check_user_permission(user,
                                                        'administrate',
                                                        tp.directory))
    try:
        store.update(store=ttk, user=user,
                     submission_type=SubmissionTypes.UPLOAD,
                     store_revision=rev,
                     allow_add_and_obsolete=allow_add_and_obsolete)
    except Exception as e:
        # This should not happen!
        logger.error("Error importing file: %s", str(e))
        raise FileImportError(_("There was an error uploading your file"))


class TPTMXExporter(object):

    def __init__(self, context):
        self.context = context

    @property
    def exported_revision(self):
        return revision.get(self.context.__class__)(
            self.context).get(key="pootle.offline.tm")

    @cached_property
    def revision(self):
        return revision.get(self.context.__class__)(
            self.context.directory).get(key="stats")

    def update_exported_revision(self):
        if self.has_changes():
            revision.get(self.context.__class__)(
                self.context).set(keys=["pootle.offline.tm"],
                                  value=self.revision)

    def has_changes(self):
        return self.revision != self.exported_revision

    @property
    def directory(self):
        return os.path.join(settings.MEDIA_ROOT,
                            'offline_tm',
                            self.context.language.code)

    @property
    def filename(self):
        return ".".join([self.context.project.fullname.replace(' ', '_'),
                         self.context.language.code, self.revision, 'tmx',
                         'zip'])

    @property
    def abs_filepath(self):
        return os.path.join(self.directory, self.filename)

    def export(self):
        source_language = self.context.project.source_language.code
        target_language = self.context.language.code

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        tmxfile = tmx.tmxfile()
        for store in self.context.stores.live().iterator():
            for unit in store.units.filter(state=TRANSLATED):
                tmxfile.addtranslation(unit.source, source_language,
                                       unit.target, target_language,
                                       unit.developer_comment)

        bs = BytesIO()
        tmxfile.serialize(bs)
        with open(self.abs_filepath, "wb") as f:
            with ZipFile(f, "w") as zf:
                zf.writestr(self.filename, bs.getvalue())

        self.update_exported_revision()

        return self.abs_filepath
