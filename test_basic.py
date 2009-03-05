from django.test.client import Client

from django.contrib.auth.models import User
from pootle_app.translation_project import TranslationProject



def test_frontpage():
    """test that a front page exists
    only useful for testing the testing environment really"""
    
    c = Client()
    import pdb
    response = c.get('/')
    assert response.status_code == 200
    

