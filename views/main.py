from django.db import connection

from Pootle.pootle import PootleServer
from Pootle.views.util import render_jtoolkit
from Pootle import pan_app

def view_old_style(request, path):
    pootle = PootleServer(pan_app.prefs, pan_app.get_po_tree())
    return render_jtoolkit(pootle.getpage(request, path))
