from django.db import connection

from Pootle.pootle import PootleServer
from Pootle.views.util import render_jtoolkit
from Pootle import pan_app

_pootle = None

def pass_to_pootle(request, path):
    global _pootle
    
    if _pootle is None:
        _pootle = PootleServer()

    page = _pootle.getpage(request, path)
    return render_jtoolkit(page)
