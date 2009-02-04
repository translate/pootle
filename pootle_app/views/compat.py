from django.conf import settings

### backwards compatiblity 
import kid
import os
OLD_TEMPLATEDIR = settings.TEMPLATE_DIRS[0]

# needed for 'buildpage'
from pootle_app.views.util import attribify
from Pootle.i18n import gettext

def loadurl(filename, context):
    "opens a template file and returns contents as string"
    filename = os.path.join(OLD_TEMPLATEDIR, filename+os.extsep+"html")
    if os.path.exists(filename):
        return open(filename, "r").read()
    return None
    
def buildpage(source, context, loadurl=loadurl, localize=None, innerid=None):
    #(self, source, context, loadurl=None, localize=None, innerid=None):
    context = attribify(context)
    t = kid.Template(source=source,**context)
    return t.serialize(output='xhtml')

# the most "important" method for rendering backwards compatible templates
def render_to_pootleresponse(pootlepage):
    templatename = pootlepage.templatename
    template = open(os.path.join(OLD_TEMPLATEDIR, templatename+os.extsep+"html"), "r").read()
    page = buildpage(template, pootlepage.templatevars or {})
    return HttpResponse(page)

def pootlesession(req):
    """Make a wrapper around Django session object to make it work
    with Pootle's page classes seamlessly."""
    print 'WARNING: This view uses pootlesession.'
    class wrapped_session(object):
        w = None
    
        def __init__(self, req):
            # helpers here.
            def is_admin(req):
                def _inner():
                    if not req.user.is_anonymous:
                        if req.user.is_authenticated and req.user.is_superuser:
                            return True
                    return False
                return _inner
            class foo:
                defaultlanguage = 'en'

            if not req.user.is_authenticated():
                status = 'not logged in'
            else:
                status = 'logged in as <b>%s</b>' % req.user

            object.__setattr__(self, 'w', req)
            object.__setattr__(self, 'map', {
                'isopen': req.user.is_authenticated(),
                'issiteadmin': is_admin(req),
                'language':  gettext.get_active(), #'en', # FIXME - currently static
                'server': foo(),
                'status': status,
                })
        

        def __getattr__(self, k):
            if self.map.has_key(k):
                print 'PootleSession accessed: %r' % k
            try:
                return self.map[k]
            except KeyError:
                return getattr(self.w, k)

        def __setattr__(self, k, v):
            print 'PootleSession set: %r=%r' % (k,v)
            print self.w, k, v
            object.__setattr__(self, k, v)

    session = wrapped_session(req)
    return session

def errorlist_from_errors(errors):
    # FIXME a rather ugly hack just to keep things jtoolkit-friendly
    error_list = []
    for e in errors:
        error_list.extend([ str(a) for a in errors[e]])
    return " ".join(error_list)

    

### end backwards compatibility
