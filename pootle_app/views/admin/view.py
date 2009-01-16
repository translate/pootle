from django.http import HttpResponseRedirect

from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.forms import ModelForm
from django.forms.models import modelformset_factory, BaseModelFormSet

from django.utils.translation import ugettext as _

from jToolkit import prefs

from Pootle import pan_app, adminpages
from pootle_app.views.auth import redirect
from pootle_app.views.util import render_jtoolkit, render_to_kid, KidRequestContext
from pootle_app.models import Language, Project, User

def user_is_admin(f):
    def decorated_f(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login', message=_("You must log in to administer Pootle."))
        elif not request.user.is_superuser:
            return redirect('/home', message=_("You do not have the rights to administer Pootle.")) 
        else:
            return f(request, *args, **kwargs)
    return decorated_f

@user_is_admin
def index(request, path):
    if request.method == 'POST':
        prefs.change_preferences(pan_app.prefs, arg_dict)
    return render_jtoolkit(adminpages.AdminPage(request))

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
        formset = formset_class(request.POST, queryset=model_class.objects.all())
        # Validate all the forms in the formset
        if formset.is_valid():
            # If all is well, Django can save all our data for us
            formset.save()
        else:
            # Otherwise, complain to the user that something went wrong
            return formset, _("There are errors in the form. Please review the problems below.")
    return formset_class(queryset=model_class.objects.all()), None

@user_is_admin
def edit(request, template, model_class, **kwargs):
    formset, msg = process_modelformset(request, model_class, **kwargs)

    template_vars = {"pagetitle": _("Pootle Languages Admin Page"),
                     "formset":   formset,
                     "text":      {"home":        _("Home"),
                                   "admin":       _("Main admin page"),
                                   "projects":    _("Projects"), 
                                   "savechanges": _("Save changes"),
                                   "error_msg":  msg}}

    return render_to_kid(template, KidRequestContext(request, template_vars))
