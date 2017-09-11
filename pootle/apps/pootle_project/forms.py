# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.db import connection
from django.forms.models import BaseModelFormSet

from django_rq.queues import get_queue

from pootle.core.utils.db import useable_connection
from pootle.i18n.gettext import ugettext as _
from pootle_config.utils import ObjectConfig
from pootle_language.models import Language
from pootle_misc.forms import LiberalModelChoiceField
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject
from pootle_translationproject.signals import (tp_init_failed_async,
                                               tp_inited_async)


def update_translation_project(tp, response_url):
    """Wraps translation project initializing to allow it to be running
    as RQ job.
    """
    try:
        with useable_connection():
            tp.init_from_templates()
    except Exception as e:
        tp_init_failed_async.send(sender=tp.__class__, instance=tp)
        raise e
    tp_inited_async.send(sender=tp.__class__,
                         instance=tp, response_url=response_url)


class TranslationProjectFormSet(BaseModelFormSet):

    def __init__(self, *args, **kwargs):
        self.response_url = kwargs.pop("response_url")
        super(TranslationProjectFormSet, self).__init__(*args, **kwargs)
        self.queryset = self.queryset.select_related("language", "project")

    def save_new(self, form, commit=True):
        return form.save(
            response_url=self.response_url,
            commit=commit)

    def delete_existing(self, tp, commit=True):
        config = ObjectConfig(tp.project)
        mapping = config.get("pootle.core.lang_mapping", {})
        if tp.language.code in mapping:
            del mapping[tp.language.code]
            config["pootle.core.lang_mapping"] = mapping
        super(TranslationProjectFormSet, self).delete_existing(
            tp, commit=commit)


class TranslationProjectForm(forms.ModelForm):

    language = LiberalModelChoiceField(
        label=_("Language"),
        queryset=Language.objects.all(),
        widget=forms.Select(
            attrs={
                'class': 'js-select2 select2-language'}))
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        widget=forms.HiddenInput())

    fs_code = forms.CharField(
        label="Filesystem code",
        required=False)

    class Meta(object):
        prefix = "existing_language"
        model = TranslationProject
        fields = ('language', 'project')

    def __init__(self, *args, **kwargs):
        """If this form is not bound, it must be called with an initial value
        for Project.
        """
        super(TranslationProjectForm, self).__init__(*args, **kwargs)
        if kwargs.get("instance"):
            project_id = kwargs["instance"].project.pk
            project = kwargs["instance"].project
            language = kwargs["instance"].language
            mappings = project.config.get("pootle.core.lang_mapping", {})
            mapped = mappings.get(language.code)
            self.fields["fs_code"].initial = mapped
        else:
            project_id = kwargs["initial"]["project"]
            self.fields["language"].queryset = (
                self.fields["language"].queryset.exclude(
                    translationproject__project_id=project_id))
        self.fields["project"].queryset = self.fields[
            "project"].queryset.filter(pk=project_id)

    def clean(self):
        project = self.cleaned_data.get("project")
        language = self.cleaned_data.get("language")
        if project and language:
            mapped_code = self.cleaned_data["fs_code"]
            mapping = project.config.get("pootle.core.lang_mapping", {})
            if mapped_code:
                tps = project.translationproject_set.all()
                lang_codes = tps.values_list("language__code", flat=True)
                bad_fs_code = (
                    (mapped_code in mapping.values()
                     and not mapping.get(language.code) == mapped_code)
                    or mapped_code in lang_codes)
                if bad_fs_code:
                    self.errors["fs_code"] = self.error_class(
                        ["Unable to add mapped code '%s' for language '%s'. "
                         "Mapped filesystem codes must be unique and cannot be "
                         "in use with an existing Translation Project"
                         % (mapped_code,
                            language.code)])
            if language.code in mapping.values():
                self.errors["language"] = self.error_class(
                    ["Unable to add language '%s'. "
                     "Another language is already mapped to this code"
                     % language.code])

    def save(self, response_url=None, commit=True):
        tp = self.instance
        initialize_from_templates = False
        if tp.id is None:
            initialize_from_templates = tp.can_be_inited_from_templates()
        tp = super(TranslationProjectForm, self).save(commit)
        if self.cleaned_data["fs_code"]:
            project = tp.project
            config = ObjectConfig(project)
            project_mapping = config.get("pootle.core.lang_mapping", {})
            project_mapping[tp.language.code] = self.cleaned_data["fs_code"]
            config["pootle.core.lang_mapping"] = project_mapping
        if initialize_from_templates:
            def _enqueue_job():
                queue = get_queue('default')
                queue.enqueue(
                    update_translation_project,
                    tp,
                    response_url)
            connection.on_commit(_enqueue_job)
        return tp
