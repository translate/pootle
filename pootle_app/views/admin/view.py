from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect
from django import forms
from django.forms.models import modelformset_factory, BaseModelFormSet
from django.utils.translation import ugettext as _

from jToolkit import prefs

from Pootle import pan_app, adminpages
from pootle_app.views.util import render_jtoolkit, render_to_kid, KidRequestContext
from pootle_app.models import Language
from pootle_app.views.auth import redirect

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

@user_is_admin
def users(request):
    if request.method == 'POST':
        pan_app.pootle_server.changeusers(request, request.POST.copy())
    return render_jtoolkit(adminpages.UsersAdminPage(pan_app.pootle_server, request))

LanguageFormSet = modelformset_factory(Language, can_delete=True)

@user_is_admin
def languages(request):
    if request.method == 'POST':
        language_formset = LanguageFormSet(request.POST, queryset=Language.objects.all())
        if language_formset.is_valid():
            # Set of all the forms in the formset
            all_forms = set(language_formset.forms)
            # Set of the forms which were deleted
            deleted_forms = set(language_formset.deleted_forms)
            # Set of new entries
            new_forms = set(language_formset.extra_forms)
            # Remove the deleted forms and new entries from all_forms
            all_forms = all_forms - (deleted_forms | new_forms)
            # Delete the database models referenced by the deleted forms
            for form in deleted_forms:
                form.instance.delete()
            # Save all the forms that have not been deleted
            for form in all_forms:
                form.save()
            # Save all new entries. Only save a new entry if its
            # language code is not empty.
            for form in new_forms:
                if form['code'].data != '':
                    form.save()
            # Reload the list of languages to show the user.
            language_formset = LanguageFormSet(queryset=Language.objects.all())
    else:
        language_formset = LanguageFormSet(queryset=Language.objects.all())

    template_vars = {"pagetitle":        _("Pootle Languages Admin Page"),
                     "language_formset": language_formset,
                     "text":             {"home":        _("Home"),
                                          "admin":       _("Main admin page"),
                                          "projects":    _("Projects"), 
                                          "savechanges": _("Save changes"),
                                          "errors_msg":  _("There are errors in the form. Please review the problems below.")}}

    return render_to_kid("adminlanguages.html", KidRequestContext(request, template_vars))

@user_is_admin
def projects(request):
    if request.method == 'POST':
        pan_app.get_po_tree().changeprojects(request)
    return render_jtoolkit(adminpages.ProjectsAdminPage(request))
