# Create your views here.

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required

from pootle_notifications.forms import LanguageNoticeForm, ProjectNoticeForm, TransProjectNoticeForm

@login_required
def lang_notice(request):
    if request.method == 'POST': # If the form has been submitted...
        form = LanguageNoticeForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            form.save()
            return HttpResponseRedirect('') # Redirect after POST
    else:
        form = LanguageNoticeForm() # An unbound form
        form.filter_by_permission(request.user)

    template_vars = {
            "title" : _("Add language notice"),
            "form"  : form,
            }
    return render_to_response('pootle_notifications/notice.html', template_vars,
            context_instance=RequestContext(request)  )

@login_required
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

    template_vars = {
            "title" : _("Add project notice"),
            "form"  : form,
            }
    return render_to_response('pootle_notifications/notice.html', template_vars,
            context_instance=RequestContext(request)  )

@login_required
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
        form.filter_by_permission(request.user)

    template_vars = {
            "title" : _("Add translation project notice"),
            "form"  : form,
            }
    
    return render_to_response('pootle_notifications/notice.html', template_vars,
            context_instance=RequestContext(request)  )

