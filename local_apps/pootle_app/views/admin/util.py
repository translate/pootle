#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.forms.models import modelformset_factory
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.shortcuts import render_to_response
from django.template import RequestContext

from pootle_misc.baseurl import redirect
from pootle_app.views.util import form_set_as_table

def user_is_admin(f):
    def decorated_f(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('/accounts/login/', message=_("You must log in to administer Pootle."))
        elif not request.user.is_superuser:
            return redirect('/accounts/'+request.user.username +'/', message=_("You do not have the rights to administer Pootle.")) 
        else:
            return f(request, *args, **kwargs)
    return decorated_f

def process_modelformset(request, model_class, **kwargs):
    """With the Django model class 'model_class' and the Django form class 'form_class',
    construct a Django formset which can manipulate """

    # Create a formset class for the model 'model_class' (i.e. it will contain forms whose
    # contents are based on the fields of 'model_class'); parameters for the construction
    # of the forms used in the formset should be in kwargs. In Django 1.0, the interface
    # to modelformset_factory is
    # def modelformset_factory(model, form=ModelForm, formfield_callback=lambda f: f.formfield(),
    #                          formset=BaseModelFormSet,
    #                          extra=1, can_delete=False, can_order=False,
    #                          max_num=0, fields=None, exclude=None)
    formset_class = modelformset_factory(model_class, **kwargs)

    # If the request is a POST, we want to possibly update our data
    if request.method == 'POST':
        # Create a formset from all the 'model_class' instances whose values will
        # be updated using the contents of request.POST
        formset = formset_class(request.POST)
        # Validate all the forms in the formset
        if formset.is_valid():
            # If all is well, Django can save all our data for us
            formset.save()
        else:
            # Otherwise, complain to the user that something went wrong
            return formset, _("There are errors in the form. Please review the problems below.")
        
    queryset = model_class.objects.all()
    return formset_class(queryset=queryset), None


@user_is_admin
def edit(request, template, model_class,
         model_args={'title':'','formid':'','submitname':''},
         link=None, linkfield='code', **kwargs):
    formset, msg = process_modelformset(request, model_class, **kwargs)
    #FIXME: title should differ depending on model_class
    template_vars = {"pagetitle": _("Pootle Languages Admin Page"),
            "formset_text":  mark_safe(form_set_as_table(formset, link, linkfield)),
            "formset":  formset,
            "text":      {"home":        _("Home"),
                "admin":       _("Main admin page"),
                "title":    model_args['title'], 
                "savechanges": _("Save changes"),
                "submitname": model_args['submitname'],
                "formid": model_args['formid'],
                "error_msg":  msg}}
    return render_to_response(template, template_vars, context_instance=RequestContext(request))
