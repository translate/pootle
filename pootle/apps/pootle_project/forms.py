# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.conf import settings
from django.db import connection
from django.forms.models import BaseModelFormSet
from django.urls import set_script_prefix
from django.utils.encoding import force_unicode

from django_rq.queues import get_queue

from pootle.core.utils.db import useable_connection
from pootle.i18n.gettext import ugettext as _
from pootle_language.models import Language
from pootle_misc.forms import LiberalModelChoiceField
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject
from pootle_translationproject.signals import (tp_deleted_async,
                                               tp_deletion_failed_async,
                                               tp_init_failed_async,
                                               tp_inited_async)


def update_translation_project(tp, initialize_from_templates, response_url):
    """Wraps translation project initializing to allow it to be running
    as RQ job.
    """
    script_name = (u'/'
                   if settings.FORCE_SCRIPT_NAME is None
                   else force_unicode(settings.FORCE_SCRIPT_NAME))
    set_script_prefix(script_name)

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


def delete_translation_project(tp):
    """Wraps translation project initializing to allow it to be running
    as RQ job.
    """
    script_name = (u'/'
                   if settings.FORCE_SCRIPT_NAME is None
                   else force_unicode(settings.FORCE_SCRIPT_NAME))
    set_script_prefix(script_name)

    try:
        with useable_connection():
            tp.delete()
    except Exception as e:
        tp_deletion_failed_async.send(sender=tp.__class__, instance=tp)
        raise e
    tp_deleted_async.send(sender=tp.__class__, instance=tp)


class TranslationProjectFormSet(BaseModelFormSet):

    def __init__(self, *args, **kwargs):
        self.response_url = kwargs.pop("response_url")
        super(TranslationProjectFormSet, self).__init__(*args, **kwargs)

    def save_new(self, form, commit=True):
        return form.save(
            response_url=self.response_url,
            commit=commit)

    def delete_existing(self, obj, commit=True):
        if commit:
            obj.awaiting_deletion = True
            obj.save()

            def _delete_translation_project():
                queue = get_queue('default')
                queue.enqueue(delete_translation_project, obj)

            connection.on_commit(_delete_translation_project)


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
