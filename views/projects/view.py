from django.http import Http404

from Pootle import pan_app, indexpage, adminpages

from Pootle.views.util import render_to_kid
from Pootle.views.util import render_jtoolkit

def check_project_code(project_code):
    if not pan_app.get_po_tree().hasproject(None, project_code):
        raise Http404
    else:
        return project_code

def project_language_index(request, project_code, _path_var):
    print "project_language_index"
    return render_jtoolkit(indexpage.ProjectLanguageIndex(check_project_code(project_code), request))

def project_admin(request, project_code):
    print "project_admin"
    return render_jtoolkit(adminpages.ProjectAdminPage(check_project_code(project_code), request, request.POST.copy()))

def projects_index(request, path):
    print "projects_index"
    return render_jtoolkit(indexpage.ProjectsIndex(request))
