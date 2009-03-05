from django.test.client import Client

from django.contrib.auth.models import User
from pootle_app.translation_project import TranslationProject

import re

def test_frontpage():
    c = Client()
    response = c.get('/')
    assert response.status_code == 200
    


def test_login():
    c = Client()
    response = c.post('/login.html', {'username': 'admin', 'password': 'admin'})
    assert response.status_code == 302
    assert re.match('http://.*/home/$', response.get('Location', None))
