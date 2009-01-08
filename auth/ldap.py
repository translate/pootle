#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
# 
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import ldap

from django.conf import settings
from django.contrib.auth.models import User

from pootle_app.models import make_pootle_user

def bind_anonymous(ldo):
    """Bind to the server using the anonymous credentials"""
    ldo.simple_bind_s(settings.ANON_LDAP_USERNAME, self.ANON_LDAP_PASSWORD)

def mail_search(ldo, username):
    """Do a search on the given e-mail address; returns the standard
    result of search_s query.
    """    
    return ldo.search_s("dc=mozilla", ldap.SCOPE_SUBTREE, "mail=%s" % email)

def get_dn(ldo, username):
     """Private method to find the distinguished name for a given username"""

    sres = mail_search(ldo, username)
    if len(sres) > 1:
        raise AmbiguousAccount(email, len(sres))
    if len(sres) == 0:
        raise NoSuchAccount(username)
    
    # sres[0][0] is the distinguished name of the first result
    return sres[0][0]   

def connect(ldo, username, password):
    """ Retrieves the distinguished name associated with the given username,
    then binds to the server using that distinguished name and the given
    password.

    If the bind fails, the appropriate exception will be raised after the
    connection is rebound using the anonymous credentials, as per the
    invariant described in the class docstring that this object must be
    bound to the server after any public method exits.

    """
    # No try/except around getDn: anything it raises we want to pass on
    dn = get_dn(ldo, username)
    ldo.simple_bind_s(dn, password)

def get_user(username):
    """This should always return a user object. If the LDAP user has logged
    in before, then there will be a user object. If not, then we quickly
    create a user object and return it to the user."""
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        user = make_pootle_user(username=username)
        user.is_active = True
        user.save()
        return user

class MozillaLdapBackend(object):
    """
    This is a Django authentication module which implements LDAP
    authentication as required by Mozilla. 

    To use this module, simply add it to the tuple AUTHENTICATION_BACKENDS
    in settings.py.
    """
    def authenticate(self, username=None, password=None):
        ldo = ldap.initialize(self.LDAP_HOST)
        try:
            connect(ldo, username, password)
        except NoSuchAccount: # Bad e-mail, credentials are bad.
            return None
        except ldap.INVALID_CREDENTIALS: # Bad password, credentials are bad.
            return None
        except ldap.UNWILLING_TO_PERFORM: # Bad password, credentials are bad.
            return None
        except: # No other exceptions are normal, so we raise this.
            raise
        else: # No exceptions: the connection succeeded and the user exists!
            return get_user(username)

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
