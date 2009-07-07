# Create your views here.

from django.db import models
from django.forms import ModelForm
from pootle_notifications.models import LanguageNotice
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from pootle_notifications.models import LanguageNotice

from django import forms
from pootle_app.models import Language

class LanguageNoticeForm(ModelForm):
   #object_id = forms.ForeignKey(Language, verbose_name=_('language'))
   class Meta:
       model = LanguageNotice

def language_notice(request):
    if request.method == 'POST': # If the form has been submitted...
        form = LanguageNoticeForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            form.save()
            return HttpResponseRedirect('') # Redirect after POST
    else:
        form = LanguageNoticeForm() # An unbound form

    return render_to_response('pootle_notifications/custom.html', {'form': form,},
            context_instance=RequestContext(request)  )


