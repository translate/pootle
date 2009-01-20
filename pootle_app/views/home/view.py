import locale

from django import forms
from django.forms import ModelForm
from django.forms.models import inlineformset_factory
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.contrib.auth import decorators

from Pootle import pagelayout, pan_app, indexpage
from pootle_app.models import get_profile, PootleProfile
from pootle_app.views.util import render_to_kid, KidRequestContext
from pootle_app.views.util import render_jtoolkit
from Pootle.i18n import gettext
from pootle_app.views.auth import redirect

def user_is_authenticated(f):
    def decorated_f(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('/login.html', message=_("You need to log in to access your home page"))
        else:
            return f(request, *args, **kwargs)
    return decorated_f

class UserForm(ModelForm):
    password = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class PootleProfileForm(ModelForm):
    class Meta:
        model = PootleProfile
        exclude = ('user', 'activation_code', 'login_type')

@user_is_authenticated
def options(request):
    if request.method == 'POST':
        post = request.POST.copy()
        if 'password' in post and post['password'].strip() != u'':
            request.user.set_password('password')
        del post['password']
        
        user_form = UserForm(post, instance=request.user)
        profile_form = PootleProfileForm(post, instance=get_profile(request.user))

        user_form.save()
        profile_form.save()
        # Activate the newly selected interface language so that the user will
        # immediately see a translated interface. But only do this if the user
        # selected an interface language.
        if profile_form['ui_lang'].data != '':
            gettext.activate_for_profile(get_profile(request.user))
    elif request.method == 'GET':
        user_form = UserForm(instance=request.user)
        profile_form = PootleProfileForm(instance=get_profile(request.user))
      
    template_vars = {"pagetitle":      _("Options for: %s") % request.user.username,
                     "introtext":      "TBD",
                     "detailstitle":   _("Personal Details"),
                     "fullname_title": _("Name"),
                     "user_form":      user_form,
                     "profile_form":   profile_form }

    return render_to_kid("options.html", KidRequestContext(request, template_vars))

@user_is_authenticated
def index(request, path):
    return render_jtoolkit(indexpage.UserIndex(request))
