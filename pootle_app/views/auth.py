import urllib

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect
from django.conf import settings
from django.http import HttpResponseRedirect

from pootle_app.views.util import render_to_kid, KidRequestContext
from pootle_app import project_tree

from Pootle import pan_app
from Pootle.pagelayout import completetemplatevars
from Pootle.i18n.jtoolkit_i18n import localize, tr_lang

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
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
                return response
        else:
            form = AuthenticationForm(request)
        request.session.set_test_cookie()
        languages = project_tree.get_languages()
        context = {
            'languages': [{'name': tr_lang(language.fullname), 'code': language.code} for language in languages],
            'form': form,
            }

        # kid template compatibility
        context.update({
            'pagetitle': localize("Login to Pootle"),
            'introtext': None,
            'language_title': localize('Language:'),
            'password_title': localize("Password:"),
            })

        return render_to_kid("login.html", KidRequestContext(request, context))
        #return render_to_response("login.html", RequestContext(request, context))

def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect('/')

def redirect(url, **kwargs):
    if len(kwargs) > 0:
        return HttpResponseRedirect('%s?%s' % (url, urllib.urlencode(kwargs)))
    else:
        return HttpResponseRedirect(url)
