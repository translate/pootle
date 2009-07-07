
from django.db import models
from django.forms import ModelForm
from django import forms
from django.contrib.contenttypes.models import ContentType

from pootle_notifications.models import Notice
from pootle_app.models import Language, Project, TranslationProject
from pootle_app.models.permissions import get_matching_permissions


class LanguageNoticeForm(ModelForm):
    LANG_CHOICES = Language.objects.all()
    content = ContentType.objects.get(model='language')
    content_type = forms.ModelChoiceField(initial=content.id, queryset=ContentType.objects.all(),
                         widget=forms.HiddenInput())
    object_id = forms.CharField(label=_("Language"), widget=forms.Select(choices=LANG_CHOICES))
    class Meta:
        model = Notice

    def filter_by_permission(self, user):
        result = []
        profile = user.get_profile()
        for choice in self.fields['object_id'].widget.choices:
            if 'administrate' in get_matching_permissions(profile, choice.directory):
                value = (choice.id, choice.fullname)
                result.append(value)
        
        self.fields['object_id'].widget.choices = result

class ProjectNoticeForm(ModelForm):
    PROJ_CHOICES = Project.objects.values_list('id', 'fullname')
    content = ContentType.objects.get(model='project')
    content_type = forms.ModelChoiceField(initial=content.id, queryset=ContentType.objects.all(),
                         widget=forms.HiddenInput())
    object_id = forms.CharField(label=_("Project"), widget=forms.Select(choices=PROJ_CHOICES))
    class Meta:
        model = Notice

class TransProjectNoticeForm(ModelForm):
    TRANSPROJ_CHOICES = TranslationProject.objects.all()
    content = ContentType.objects.get(model='translationproject')
    content_type = forms.ModelChoiceField(initial=content.id, queryset=ContentType.objects.all(),
                         widget=forms.HiddenInput())
    object_id = forms.CharField(label=_("Translation Project"), widget=forms.Select(choices=TRANSPROJ_CHOICES))
    class Meta:
        model = Notice
    def filter_by_permission(self, user):
        result = []
        profile = user.get_profile()
        for choice in self.fields['object_id'].widget.choices:
            if 'administrate' in get_matching_permissions(profile, choice.directory):
                value = (choice.id, choice.real_path)
                result.append(value)
        
        self.fields['object_id'].widget.choices = result

