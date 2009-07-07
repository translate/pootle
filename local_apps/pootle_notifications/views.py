# Create your views here.

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType

from pootle_notifications.forms import LanguageNoticeForm, ProjectNoticeForm, TransProjectNoticeForm
from pootle_notifications.models import Notice
from pootle_app.models import Language, Project, TranslationProject

@login_required
def lang_notice(request, language_code):
    if request.method == 'POST': # If the form has been submitted...
        form = LanguageNoticeForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            form.save()
            return HttpResponseRedirect('') # Redirect after POST
    else:
        form = LanguageNoticeForm() # An unbound form
        form.set_initial_value(language_code)

    template_vars = {
            "title" : _("Add language notice"),
            "form"  : form,
            }
    return render_to_response('pootle_notifications/notice.html', template_vars,
            context_instance=RequestContext(request)  )

    
@login_required
def view_lang_notices(request, language_code):
    lang = Language.objects.get(code=language_code)
    content = Notice(content_object = lang)
    lang_notices =  Notice.objects.get_notices(content)
    template_vars = {
            "title" : _("%s notices", lang.fullname),
            "notices"  : lang_notices,
            }
    return render_to_response('pootle_notifications/index.html', template_vars,
            context_instance=RequestContext(request)  )

@login_required
def view_transproj_notices(request, language_code, project_code):
    transproj = TranslationProject.objects.get(real_path = project_code + "/" + language_code)
    content = Notice(content_object = transproj)
    transproj_notices =  Notice.objects.get_notices(content)
    template_vars = {
            "title" : _("translation project notices"),
            "notices"  : transproj_notices,
            }
    return render_to_response('pootle_notifications/index.html', template_vars,
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
def transproj_notice(request, language_code, project_code):
    if request.method == 'POST': # If the form has been submitted...
        form = TransProjectNoticeForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            form.save()
            return HttpResponseRedirect('') # Redirect after POST
    else:
        form = TransProjectNoticeForm() # An unbound form
        form.set_initial_value(language_code, project_code)

    template_vars = {
            "title" : _("Add translation project notice"),
            "form"  : form,
            }
    
    return render_to_response('pootle_notifications/notice.html', template_vars,
            context_instance=RequestContext(request)  )

def view_notice_item(request, notice_id):
    notice_type = ContentType.objects.get_for_model(Notice)
    notice = notice_type.get_object_for_this_type(id=notice_id)
    template_vars = {
            "title" : _("View Notice"),
            "notice_message"  : notice.message,
            }
    
    return render_to_response('pootle_notifications/viewnotice.html', template_vars,
            context_instance=RequestContext(request)  )

