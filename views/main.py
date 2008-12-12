from django.db import connection

from Pootle.pootle import PootleServer
from Pootle.views.util import render_jtoolkit
from Pootle import pan_app

def pass_to_pootle(request, path):
    pootle = PootleServer()
    return render_jtoolkit(pootle.getpage(request, path))
