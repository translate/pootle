
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect
from django.conf import settings

from Pootle import pan_app

from Pootle.views.util import render_to_kid, KidRequestContext
from Pootle.pagelayout import completetemplatevars

def login(request):
    message = None
    redirect_to = request.REQUEST.get(REDIRECT_FIELD_NAME, '')
    if not redirect_to or '://' in redirect_to or ' ' in redirect_to:
        redirect_to = '/home/'

    if request.user.is_authenticated():
        return HttpResponseRedirect(redirect_to)
    else:
        if request.POST:
            form = AuthenticationForm(request, data=request.POST)
            # do login here
            if form.is_valid():
                from django.contrib.auth import login
                login(request, form.get_user())
                if request.session.test_cookie_worked():
                    request.session.delete_test_cookie()

                language = request.POST.get('language') # FIXME: validation missing
                response = HttpResponseRedirect(redirect_to)
                response.set_cookie(settings.LANGUAGE_NAME_COOKIE, language)
                return response
        else:
            form = AuthenticationForm(request)
        request.session.set_test_cookie()
        languages = pan_app.get_po_tree().getlanguages()
        context = {
            'languages': [{'name': i[1], 'code':i[0]} for i in languages],
            'form': form,
            }

        # kid template compatibility
        context.update({
            'pagetitle': request.localize("Login to Pootle"),
            'introtext': None,
            'language_title': request.localize('Language:'),
            'password_title': request.localize("Password:"),
            })

        return render_to_kid("login.html", KidRequestContext(request, context))
        #return render_to_response("login.html", RequestContext(request, context))

def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect('/')

