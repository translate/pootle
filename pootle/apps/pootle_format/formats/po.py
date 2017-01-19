# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.storage import poheader

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max
from django.utils import timezone

from pootle.core.utils import dateformat
from pootle.core.utils.timezone import datetime_min
from pootle.core.utils.version import get_major_minor_version
from pootle_statistics.models import Submission
from pootle_store.syncer import StoreSyncer


class PoStoreSyncer(StoreSyncer):

    def get_latest_submission(self, mtime):
        user_displayname = None
        user_email = None
        fields = (
            "submitter__username",
            "submitter__full_name",
            "submitter__email")
        submissions = self.translation_project.submission_set.exclude(
            submitter__username="nobody")
        try:
            username, fullname, user_email = (
                submissions.filter(creation_time=mtime)
                           .values_list(*fields).latest())
        except Submission.DoesNotExist:
            try:
                _mtime, username, fullname, user_email = (
                    submissions.values_list("creation_time", *fields)
                               .latest())
                mtime = min(_mtime, mtime)
            except ObjectDoesNotExist:
                pass
        if user_email:
            user_displayname = (
                fullname.strip()
                if fullname.strip()
                else username)
        return mtime, user_displayname, user_email

    def get_po_revision_date(self, mtime):
        return (
            "%s%s"
            % (mtime.strftime('%Y-%m-%d %H:%M'),
               poheader.tzstring()))

    def get_po_mtime(self, mtime):
        return (
            '%s.%06d'
            % (int(dateformat.format(mtime, 'U')),
               mtime.microsecond))

    def get_po_headers(self, mtime, user_displayname, user_email):
        headerupdates = {
            'PO_Revision_Date': self.get_po_revision_date(mtime),
            'X_Generator': "Pootle %s" % get_major_minor_version(),
            'X_POOTLE_MTIME': self.get_po_mtime(mtime)}
        headerupdates['Last_Translator'] = (
            user_displayname and user_email
            and ('%s <%s>'
                 % (user_displayname,
                    user_email))
            or 'Anonymous Pootle User')
        return headerupdates

    def update_po_headers(self, disk_store, mtime, user_displayname, user_email):
        disk_store.updateheader(
            add=True,
            **self.get_po_headers(mtime, user_displayname, user_email))
        if self.language.nplurals and self.language.pluralequation:
            disk_store.updateheaderplural(
                self.language.nplurals,
                self.language.pluralequation)

    def update_store_header(self, disk_store, **kwargs):
        super(PoStoreSyncer, self).update_store_header(disk_store, **kwargs)
        user = kwargs.get("user")
        mtime = self.store.units.aggregate(mtime=Max("mtime"))["mtime"]
        if mtime is None or mtime == datetime_min:
            mtime = timezone.now()
        user_displayname = None
        user_email = None
        if user is None:
            (mtime,
             user_displayname,
             user_email) = self.get_latest_submission(mtime)
        elif user.is_authenticated:
            user_displayname = user.display_name
            user_email = user.email
        self.update_po_headers(disk_store, mtime, user_displayname, user_email)
