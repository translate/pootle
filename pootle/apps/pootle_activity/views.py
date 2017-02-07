# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model
from django.views.generic import FormView

from pootle.core.delegate import timeline
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject

from .forms import PootleActivityForm


User = get_user_model()


class PootleActivityView(FormView):

    template_name = "activity/index.html"
    form_class = PootleActivityForm

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        ctx = super(PootleActivityView, self).get_context_data(**kwargs)

        form = ctx["form"]
        if form.is_valid():
            object_type = form.cleaned_data["object_type"]
            object_name = form.cleaned_data["object_name"]
            if object_type == "user":
                target = User.objects.get(username=object_name)
            elif object_type == "project":
                target = Project.objects.get(code=object_name)
            elif object_type == "store":
                target = Store.objects.get(pootle_path=object_name)
            elif object_type == "tp":
                target = TranslationProject.objects.get(pootle_path=object_name)
            elif object_type == "language":
                target = Language.objects.get(code=object_name)
            ctx["target"] = target
            ctx["timeline"] = timeline.get(target.__class__)(target)
        return ctx
