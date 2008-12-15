import os
from os import path
import kid
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from jToolkit.web import server
from jToolkit.widgets import widgets
import mimetypes

from Pootle.pagelayout import completetemplatevars

# settings.py is in the root of our Django application's
# directory structure, so we can use path.dirname to
# find the root directory.
from Pootle import settings
root_dir = path.dirname(settings.__file__)

kid.enable_import()

def find_template(relative_template_path):
    """Find the full path of the template whose relative path is
    'relative_template_path'."""

    for template_dir in settings.TEMPLATE_DIRS:
        full_template_path = path.join(root_dir, template_dir, relative_template_path)
        if path.exists(full_template_path):
            return full_template_path
    raise Exception('No template named %s found' % relative_template_path)

def render(relative_template_path, **template_vars):
    # Find the template at relative_template_path, get the
    # constructed kid template and pass template_vars
    # through...
    template = kid.Template(file = find_template(relative_template_path), **template_vars)
    
    # Render the template to a string and send the string
    # to HttpResponse
    return HttpResponse(template.serialize(output="xhtml"))

class AttrDict(dict):
    # THIS IS TAKEN FROM JTOOLKIT
    """Dictionary that also allows access to keys using attributes"""
    def __getattr__(self, attr, default=None):
        if attr in self:
            return self[attr]
        else:
            return default

def attribify(context):
    # THIS IS TAKEN FROM JTOOLKIT
    """takes a set of nested dictionaries and converts them into AttrDict. Also searches through lists"""
    if isinstance(context, dict) and not isinstance(context, AttrDict):
        newcontext = AttrDict(context)
        for key, value in newcontext.items():
            if isinstance(value, (dict, list)):
                newcontext[key] = attribify(value)
        return newcontext
    elif isinstance(context, list):
        for n, item in enumerate(context):
            if isinstance(item, (dict, list)):
                context[n] = attribify(item)
        return context
    else:
        return context

def render_jtoolkit(obj):
    """Render old style Pootle display objects which are jToolkit objects
    containing all the necessary information to be rendered."""
    if hasattr(obj, "templatename") and hasattr(obj, "templatevars"):
        return render("%s.html" % obj.templatename, **attribify(obj.templatevars))
    else:
        if isinstance(obj, server.Redirect):
            if obj.ispermanent:
                return HttpResponsePermanentRedirect(obj.location)
            return HttpResponseRedirect(obj.location)
        if isinstance(obj, widgets.SendFile):
            content_type = hasattr(obj, 'content_type') and obj.content_type or 'text/plain'
            return HttpResponse(open(obj.sendfile_path).read(), content_type=content_type)
        return HttpResponse(obj.getcontents(), obj.content_type)

def render_to_kid(template, context):
    return render(template, **attribify(context))

class KidRequestContext(dict):
    def __init__(self, req, context):
        self.update(context)
        completetemplatevars(self, req)

