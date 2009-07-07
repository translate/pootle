# Create your views here.

from django.db import models
from django.forms import ModelForm
from django import forms
from pootle_notifications.models import Notice
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext

from django import forms
from pootle_app.models import Language, Project, TranslationProject

def index(request):
    links = {}
    link = {'add language notice':'notice/lang/'}
    links.add(link)
    link = {'add project notice':'notice/proj/'}
    links.append(link)
    return render_to_response('pootle_notifications/index.html', {'links': links,},
            context_instance=RequestContext(request)  )

class NoticeForm(ModelForm):
    LANG_CHOICES = Language.objects.values_list('id', 'fullname')
    content = ContentType.objects.get(model='language')
    content_type = forms.ModelChoiceField(initial=content.id, queryset=ContentType.objects.all(),
                         widget=forms.HiddenInput())
    object_id = forms.CharField(label=_("Language"), widget=forms.Select(choices=LANG_CHOICES))
    class Meta:
        model = Notice

class ProjectNoticeForm(ModelForm):
    PROJ_CHOICES = Project.objects.values_list('id', 'fullname')
    content = ContentType.objects.get(model='project')
    content_type = forms.ModelChoiceField(initial=content.id, queryset=ContentType.objects.all(),
                         widget=forms.HiddenInput())
    object_id = forms.CharField(label=_("Project"), widget=forms.Select(choices=PROJ_CHOICES))
    class Meta:
        model = Notice

class TransProjectNoticeForm(ModelForm):
    TRANSPROJ_CHOICES = TranslationProject.objects.values_list('id', 'real_path')
    content = ContentType.objects.get(model='translationproject')
    content_type = forms.ModelChoiceField(initial=content.id, queryset=ContentType.objects.all(),
                         widget=forms.HiddenInput())
    object_id = forms.CharField(label=_("Translation Project"), widget=forms.Select(choices=TRANSPROJ_CHOICES))
    class Meta:
        model = Notice

def lang_notice(request):
    if request.method == 'POST': # If the form has been submitted...
        form = NoticeForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            form.save()
            return HttpResponseRedirect('') # Redirect after POST
    else:
        form = NoticeForm() # An unbound form

    return render_to_response('pootle_notifications/notice.html', {'form': form,},
            context_instance=RequestContext(request)  )

def proj_notice(request):
    if request.method == 'POST': # If the form has been submitted...
        form = ProjectNoticeForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            form.save()
            return HttpResponseRedirect('') # Redirect after POST
    else:
        form = ProjectNoticeForm() # An unbound form

    return render_to_response('pootle_notifications/notice.html', {'form': form,},
            context_instance=RequestContext(request)  )

def transproj_notices(request):
    if request.method == 'POST': # If the form has been submitted...
        form = TransProjectNoticeForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            form.save()
            return HttpResponseRedirect('') # Redirect after POST
    else:
        form = TransProjectNoticeForm() # An unbound form

    return render_to_response('pootle_notifications/notice.html', {'form': form,},
            context_instance=RequestContext(request)  )

