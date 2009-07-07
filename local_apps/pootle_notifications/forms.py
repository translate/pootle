
from django.db import models
from django.forms import ModelForm
from django import forms
from django.contrib.contenttypes.models import ContentType

from pootle_notifications.models import Notice
from pootle_app.models import Language, Project, TranslationProject
from pootle_app.models.permissions import get_matching_permissions


class LanguageNoticeForm(ModelForm):
    content = ContentType.objects.get(model='language')
    content_type = forms.ModelChoiceField(initial=content.id, queryset=ContentType.objects.all(),
                         widget=forms.HiddenInput())
    object_id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = Notice

    def set_initial_value(self, code):
        language = Language.objects.get(code = code);
        self.fields['object_id'].initial = language.id

class ProjectNoticeForm(ModelForm):
    PROJ_CHOICES = Project.objects.values_list('id', 'fullname')
    content = ContentType.objects.get(model='project')
    content_type = forms.ModelChoiceField(initial=content.id, queryset=ContentType.objects.all(),
                         widget=forms.HiddenInput())
    object_id = forms.CharField(label=_("Project"), widget=forms.Select(choices=PROJ_CHOICES))
    class Meta:
        model = Notice

class TransProjectNoticeForm(ModelForm):
    content = ContentType.objects.get(model='translationproject')
    content_type = forms.ModelChoiceField(initial=content.id, queryset=ContentType.objects.all(),
                         widget=forms.HiddenInput())

    object_id = forms.IntegerField(widget=forms.HiddenInput())
    class Meta:
        model = Notice
    def set_initial_value(self, language_code, project_code):
        real_path = project_code + "/" + language_code;
        transproj = TranslationProject.objects.get(real_path = real_path)
        self.fields['object_id'].initial = transproj.id
        
