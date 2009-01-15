from django.http import Http404

from Pootle import pan_app, indexpage, adminpages

from pootle_app.views.auth import redirect
from pootle_app.views.util import render_to_kid, render_jtoolkit
from pootle_app.models import TranslationProject

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

@user_can_admin_project
def project_admin(request, project_code):
    return render_jtoolkit(adminpages.ProjectAdminPage(check_project_code(project_code), request, request.POST.copy()))

def projects_index(request, path):
    return render_jtoolkit(indexpage.ProjectsIndex(request))
