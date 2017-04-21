# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils.functional import cached_property

from accounts.proxy import DisplayUser
from pootle.core.primitives import PrefixedDict
from pootle.core.url_helpers import get_editor_filter, split_pootle_path
from pootle.core.utils import dateformat
from pootle_checks.constants import CHECK_NAMES
from pootle_store.constants import FUZZY, TRANSLATED
from pootle_store.fields import to_python

from .models import SubmissionFields, SubmissionTypes, TranslationActionTypes


class SubmissionProxy(object):
    """Wraps a dictionary of submission values, which is useful for wrapping
    results from qs.values calls
    """

    fields = (
        "type",
        "old_value",
        "new_value",
        "creation_time",
        "field")
    qc_fields = (
        "quality_check_id",
        "quality_check__name")
    submitter_fields = (
        "submitter_id",
        "submitter__username",
        "submitter__email",
        "submitter__full_name")
    suggestion_fields = (
        "suggestion_id",
        "suggestion__target_f", )
    suggestion_reviewer_fields = (
        "suggestion__reviewer__full_name",
        "suggestion__reviewer__email",
        "suggestion__reviewer__username")
    suggestion_user_fields = (
        "suggestion__user__full_name",
        "suggestion__user__email",
        "suggestion__user__username")
    unit_fields = (
        "unit_id",
        "unit__state",
        "unit__source_f",
        "unit__store__pootle_path")
    timeline_fields = (
        fields
        + qc_fields
        + submitter_fields
        + suggestion_fields
        + suggestion_user_fields)
    info_fields = (
        fields
        + qc_fields
        + submitter_fields
        + suggestion_fields
        + suggestion_reviewer_fields
        + unit_fields)

    def __init__(self, values, prefix=""):
        if prefix:
            self.values = PrefixedDict(values, prefix)
        else:
            self.values = values

    def __getattr__(self, k):
        try:
            return self.__dict__["values"][k] or ""
        except KeyError:
            return self.__getattribute__(k)

    @property
    def field(self):
        return self.values["field"]

    @property
    def field_name(self):
        return SubmissionFields.NAMES_MAP.get(self.field, None)

    @property
    def qc_name(self):
        return self.values['quality_check__name']

    @property
    def suggestion(self):
        return self.values['suggestion_id']

    @property
    def suggestion_full_name(self):
        return self.values.get('suggestion__user__full_name')

    @property
    def suggestion_username(self):
        return self.values.get('suggestion__user__username')

    @property
    def suggestion_target(self):
        return self.values.get('suggestion__target_f')

    @property
    def unit(self):
        return self.values.get('unit_id')

    @property
    def unit_state(self):
        return self.values.get('unit__state')

    @property
    def unit_source(self):
        return self.values.get('unit__source_f')

    @property
    def submitter_display(self):
        return DisplayUser(
            self.values["submitter__username"],
            self.values["submitter__full_name"],
            self.values["submitter__email"])

    @property
    def suggestion_reviewer_display(self):
        return DisplayUser(
            self.values["suggestion__reviewer__username"],
            self.values["suggestion__reviewer__full_name"],
            self.values["suggestion__reviewer__email"])

    @cached_property
    def display_user(self):
        return self.submitter_display

    @property
    def unit_pootle_path(self):
        return self.values.get("unit__store__pootle_path")

    @property
    def unit_translate_url(self):
        if not self.unit:
            return
        store_url = u''.join(
            [reverse("pootle-tp-store-translate",
                     args=split_pootle_path(self.unit_pootle_path)),
             get_editor_filter()])
        return (
            "%s%s"
            % (store_url,
               '#unit=%s' % unicode(self.unit)))

    @property
    def unit_info(self):
        info = {}
        if self.unit is None:
            return info
        info.update(
            dict(unit_source=truncatechars(self.unit_source, 50),
                 unit_url=self.unit_translate_url))
        if self.qc_name is None:
            return info
        info.update(
            dict(check_name=self.qc_name,
                 check_display_name=CHECK_NAMES.get(self.qc_name, self.qc_name),
                 checks_url=reverse('pootle-checks-descriptions')))
        return info

    @property
    def submission_info(self):
        return {
            "profile_url": self.display_user.get_absolute_url(),
            "email": self.display_user.email_hash,
            "displayname": self.display_user.display_name,
            "username": self.display_user.username,
            "display_datetime": dateformat.format(self.creation_time),
            "type": self.type,
            "mtime": int(dateformat.format(self.creation_time, 'U'))}

    @property
    def translation_action_type(self):
        if not self.unit:
            return
        if self.type not in SubmissionTypes.EDIT_TYPES:
            return
        if self.field == SubmissionFields.STATE:
            # Note that a submission where field is STATE
            # should be created before a submission where
            # field is TARGET
            state = int(to_python(self.new_value))
            if state == TRANSLATED:
                return TranslationActionTypes.REVIEWED
            elif state == FUZZY:
                return TranslationActionTypes.NEEDS_WORK
        if self.field != SubmissionFields.TARGET:
            return
        if self.new_value == '':
            return TranslationActionTypes.REMOVED
        # Note that we analyze current unit state:
        # if this submission is not last unit state
        # can be changed
        if self.unit_state not in [TRANSLATED, FUZZY]:
            return

        if self.old_value != '':
            return TranslationActionTypes.EDITED

        return (
            TranslationActionTypes.PRE_TRANSLATED
            if self.unit_state == FUZZY
            else TranslationActionTypes.TRANSLATED)

    def get_submission_info(self):
        result = self.unit_info
        result.update(self.submission_info)
        if self.translation_action_type is not None:
            result["translation_action_type"] = self.translation_action_type
        return result
