from django.http import Http404
from django.forms.models import modelformset_factory, BaseModelFormSet
from django import forms
from django.forms.formsets import ManagementForm
from django.utils.translation import ugettext as _

from Pootle import pan_app, indexpage, adminpages

from pootle_app.views.auth import redirect
from pootle_app.views.util import render_to_kid, render_jtoolkit, KidRequestContext, \
    init_formset_from_data, choices_from_models, selected_model
from pootle_app.models import TranslationProject, Language, Project

def user_can_admin_project(f):
    def decorated_f(request, project_code, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('/projects/%s' % project_code, message=_("Only administrators may modify the project options."))
        else:
            return f(request, project_code, *args, **kwargs)
    return decorated_f

def check_project_code(project_code):
    if not pan_app.get_po_tree().hasproject(None, project_code):
        raise Http404
    else:
        return project_code

def project_language_index(request, project_code, _path_var):
    return render_jtoolkit(indexpage.ProjectLanguageIndex(check_project_code(project_code), request))

class LanguageForm(forms.ModelForm):
    update = forms.BooleanField(required=False)

    class Meta:
        prefix="existing_language"        

LanguageFormset = modelformset_factory(Language, LanguageForm, fields=['update'], extra=0)

def make_new_language_form(existing_languages, post_vars=None):
    new_languages = [language for language in Language.objects.all() if not language in set(existing_languages)]

    class NewLanguageForm(forms.Form):
        add_language = forms.ChoiceField(choices=choices_from_models(new_languages), label=_("Add language"))

    return NewLanguageForm(post_vars)

def process_post(request, project):
    def process_existing_languages(request, project):
        formset = init_formset_from_data(LanguageFormset, request.POST)
        if formset.is_valid():
            for form in formset.forms:
                if form['update'].data:
                    language = form.instance
                    translation_project = pan_app.get_po_tree().getproject(language.code, project.code)
                    translation_project.converttemplates(request)
        return formset

    def process_new_language(request, project, languages):
        new_language_form = make_new_language_form(languages, request.POST)

        if new_language_form.is_valid():
            new_language = selected_model(Language, new_language_form['add_language'])
            if new_language is not None:
                pan_app.get_po_tree().addtranslationproject(new_language.code, project.code)

    if request.method == 'POST':
        formset = process_existing_languages(request, project)
        process_new_language(request, project, [form.instance for form in formset.forms])

def process_get(request, project):
    if request.method == 'GET':
        try:
            language_code = request.GET['updatelanguage']
            translation_project = pan_app.get_po_tree().getproject(language_code, project.code)
            if 'initialize' in request.GET:
                translation_project.initialize(request, language_code)
            elif 'doupdatelanguage' in request.GET:
                translation_project.converttemplates(request)
        except KeyError:
            pass

@user_can_admin_project
def project_admin(request, project_code):
    project = Project.objects.get(code=project_code)

    process_get(request, project)
    process_post(request, project)

    existing_languages = pan_app.get_po_tree().get_valid_languages(project.code)
    formset = LanguageFormset(queryset=existing_languages)
    new_language_form = make_new_language_form(existing_languages)

    template_vars = {
        "pagetitle":          _("Pootle Admin: %s") % project.fullname,
        "norights_text":      _("You do not have the rights to administer this project."),
        "project":            project,
        "iso_code":           _("ISO Code"),
        "full_name":          _("Full Name"),
        "existing_title":     _("Existing languages"),
        "formset":            formset,
        "new_language_form":  new_language_form,
        "update_button":      _("Update Languages"),
        "add_button":         _("Add Language"),
        "main_link":          _("Back to main page"),
        "update_link":        _("Update from templates"), 
        "initialize_link":    _("Initialize"),
        "instancetitle":      getattr(pan_app.prefs, "title", _("Pootle Demo"))}

    return render_to_kid("projectadmin.html", KidRequestContext(request, template_vars))

def projects_index(request, path):
    return render_jtoolkit(indexpage.ProjectsIndex(request))
