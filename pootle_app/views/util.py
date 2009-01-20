import os
from os import path
import mimetypes
import kid

from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.forms.util import ErrorList

from jToolkit.web import server
from jToolkit.widgets import widgets

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

def form_set_as_table(formset):
    """Create an HTML table from the formset. The first form in the
    formset is used to obtain a list of the fields that need to be
    displayed. All these fields not appearing in 'exclude' will be
    placed into consecutive columns.

    Errors, if there are any, appear in the row above the form which
    triggered any errors.

    If the forms are based on database models, the order of the
    columns is determined by the order of the fields in the model
    specification."""
    def add_header(result, fields, form):
        result.append('<tr>\n')
        for field in fields:
            result.append('<th>')
            result.append(unicode(form.fields[field].label))
            result.append('</th>\n')
        result.append('</tr>\n')

    def add_errors(result, fields, form):
        # If the form has errors, then we'll add a table row with the
        # errors.
        if len(form.errors) > 0:
            result.append('<tr>\n')
            for field in fields:
                result.append('<td>')
                result.append(form.errors.get(field, ErrorList()).as_ul())
                result.append('</td>\n')
            result.append('</tr>\n')

    def add_widgets(result, fields, form):
        result.append('<tr>\n')
        for i, field in enumerate(fields):
            result.append('<td>')
            # Include a hidden element containing the form's id to the
            # first column.
            if i == 0:
                result.append(form['id'].as_hidden())
            result.append(form[field].as_widget())
            result.append('</td>\n')
        result.append('</tr>\n')

    result = []
    first_form = formset.forms[0]
    # Get the fields of the form, but filter our the 'id' field,
    # since we don't want to print a table column for it.
    fields = [field for field in first_form.fields if field != 'id']
    add_header(result, fields, first_form)
    for form in formset.forms:
        add_errors(result, fields, form)
        add_widgets(result, fields, form)
    return u''.join(result)

################################################################################

def add_prefix(prefix, name, num=None):
    if num is None:
        return '%s-%s' % (prefix, name)
    else:
        return '%s-%s-%s' % (prefix, num, name)

class FakeQuery(list):
    """A list that appears to be a Django QuerySet. This is so that we can
    pass lists to where QuerySets are expected."""
    def all(self):
        return self

def get_formset_objects(query, prefix, model_class):
    """Find all id elements in the query which are prefixed with 'prefix'
    and use these as ids (that is, primary keys) in the Django method
    in_bulk to obtain a list of the objects in 'model_class' which
    have these ids.

    Wrap the final result in a FakeQuery to make the result usable
    where Django expects Querysets."""
    # Read the total number of forms. For this to work, a
    # ManagementForm has to be present. Perhaps we should rather try
    # to instantiate a ManagementForm and use that to get this value?
    length = int(query[add_prefix(prefix, 'TOTAL_FORMS')])
    # Enumerate the values [0, length), using the numbers as indices
    # to construct keys which are used to look up values in the HTTP
    # query dictionary.
    ids = [int(query[add_prefix(prefix, 'id', i)]) for i in xrange(length)]
    # model_class.objects.in_bulk(ids) returns a dictionary mapping
    # ids->objects.
    id_object_map = model_class.objects.in_bulk(ids)
    # We only care about the objects, but we want the retain the order
    # of the ids as they appear in 'ids'. Thus, we enumerate 'ids' and
    # pick out the corresponding objects in id_object_map; this gives
    # us our objects in the right sequence. Now Wrap everything in the
    # FakeQuery class to simluate a Django QuerySet.
    return FakeQuery(id_object_map[id] for id in ids)

def init_formset_from_data(formset_class, data):
    """Initialize a formset using the ids in 'data'. Now Django is
    supposed to be able to do this. What happens though, is that you
    pass a queryset to your formset class and Django matches the forms
    in your post data one for one, in sequence to the data in your
    QuerySet. So, imagine that your post data has ids [1, 6, 10, 20]
    and your queryset has ids [1, 2, 3, 4] (as might happen if you
    pass MyModel.objects.all()), then Django will erroneously
    instantiate the objects with ids [1, 2, 3, 4] and associate those
    instances with your form data.

    Not terribly good. What if the data has changed since we last
    looked?

    init_formset_from_data deals with this by first looking for all
    the ids, asking Django to instantiate these objects via in_bulk
    and passing the resulting (fake) QuerySet to the formset class."""

    # Note that Django's modelformset_factory doesn't allow you to set
    # the prefix to be used with a formset. The default, at least in
    # Django 1.0 is 'form'.
    queryset = get_formset_objects(data, 'form', formset_class.model)
    return formset_class(data, queryset=queryset)

################################################################################

def choices_from_models(seq):
    return [(-1, '')] + [(item.id, unicode(item)) for item in seq]

def selected_model(model_class, field):
    try:
        return model_class.objects.get(pk=field.data)
    except model_class.DoesNotExist:
        return None

