from django.db import connection

from Pootle.pootle import PootleServer
from pootle_app.views.util import render_jtoolkit
from Pootle import pan_app

def pass_to_pootle(request, path):
    page = pan_app.pootle_server.getpage(request, path)
    return render_jtoolkit(page)
