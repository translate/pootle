# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

from django import forms
from django.db import connection
from django.forms.models import BaseModelFormSet

from django_rq.queues import get_queue

from pootle.core.utils.db import useable_connection
from pootle.i18n.gettext import ugettext as _
from pootle_language.models import Language
from pootle_misc.forms import LiberalModelChoiceField
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject
from pootle_translationproject.signals import (tp_init_failed_async,
                                               tp_inited_async)


def update_translation_project(tp, initialize_from_templates, response_url):
    """Wraps translation project initializing to allow it to be running
    as RQ job.
    """
    try:
        with useable_connection():
            if initialize_from_templates:
                tp.init_from_templates()
            else:
                tp.update_from_disk()
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
        else:
            project_id = kwargs["initial"]["project"]
            self.fields["language"].queryset = (
                self.fields["language"].queryset.exclude(
                    translationproject__project_id=project_id))
        self.fields["project"].queryset = self.fields[
            "project"].queryset.filter(pk=project_id)

    def clean(self):
        if not self.cleaned_data.get("id"):
            exists_on_disk = (
                self.cleaned_data["language"].code
                in os.listdir(self.cleaned_data["project"].get_real_path()))
            if exists_on_disk:
                errordict = dict(
                    lang=self.cleaned_data["language"].code,
                    path=os.path.join(
                        self.cleaned_data["project"].get_real_path(),
                        self.cleaned_data["language"].code))
                raise forms.ValidationError(
                    _("Cannot create translation project for language "
                      "'%(lang)s', path '%(path)s' already exists",
                      errordict))

    def save(self, response_url, commit=True):
        tp = self.instance
        initialize_from_templates = False
        if tp.id is None:
            initialize_from_templates = tp.can_be_inited_from_templates()
        tp = super(TranslationProjectForm, self).save(commit)

        def _enqueue_job():
            queue = get_queue('default')
            queue.enqueue(update_translation_project,
                          tp, initialize_from_templates,
                          response_url)
        connection.on_commit(_enqueue_job)
        return tp
