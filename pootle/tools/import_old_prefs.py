#!/usr/bin/env python
# coding: utf-8

'''Author: Asheesh Laroia <asheesh@creativecommons.org>
Copyright: (C) 2008 Creative Commons
Permission is granted to redistribute this file under the GPLv2 or later, 
 at your option.   See COPYING for details.'''

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.db import transaction

from django.contrib.auth.models import User
from pootle_app.models.project import Project
from pootle_app.models.language import Language
from pootle.legacy.jToolkit import prefs

import sys
import types
import logging

def main():
    '''Read sys.argv for configuration, and perform the imports.'''
    if len(sys.argv) != 3:
        print "Usage: %s old_pootle.prefs users.prefs" % (
                sys.argv[0])
        return

    oldprefsfile = sys.argv[1]
    parsed_oldprefs = prefs.PrefsParser(oldprefsfile)
    usersfile = sys.argv[2]
    parsed_users = prefs.PrefsParser(usersfile)
    try:
        try:
            transaction.enter_transaction_management()
            transaction.managed(True)

            set_up_db_then_import_languages_then_users(parsed_oldprefs,
                                                       parsed_users)
        except:
            if transaction.is_dirty():
                transaction.rollback()
            if transaction.is_managed():
                transaction.leave_transaction_management()
            raise
    finally:
        if transaction.is_managed():
            if transaction.is_dirty():
                transaction.commit()
        if transaction.is_managed():
            transaction.leave_transaction_management()

def set_up_db_then_import_languages_then_users(oldprefs, parsed_users):
    '''oldprefs and parsed_users are jToolkit prefs.PrefsParser
    objects.'''
    import_languages(oldprefs)
    import_projects(oldprefs)
    import_users(parsed_users)

def _get_attribute(data, name, attribute, unicode_me = True, 
                   default = '', prefix='Pootle.languages.'):
    raw_value = data.get(prefix + name + '.' + attribute, default)
    if unicode_me:
        assert type(raw_value) in types.StringTypes
        if type(raw_value) == unicode:
            value = raw_value
        else:
            value = unicode(raw_value, 'utf-8')
    else:
        if raw_value == '':
            value = default
        else:
            value = raw_value
    return value

def try_type(try_me, value):
    '''This gentle type-converter should work fine for int and bool.
    It would not work for unicode, though.'''
    assert try_me is not unicode
    if try_me == bool:
        if isinstance(value, int):
            return bool(value)
        return value
    if try_me == int:
        if type(value) == int:
            return value
        if value.isdigit():
            return int(value)
    assert type(value) == try_me
    return value

def import_languages(parsed_data):
    data = parsed_data.__root__._assignments # Is this really the right way?
    prefix = 'Pootle.languages.'

    # Filter out unrelated keys
    keys = [key for key in data if key.startswith(prefix)]

    # Clean up 'sv_SE.pluralequation' into 'sv_SE'
    langs = set([key[len(prefix):].split('.')[0] for key in keys])

    for lang in map(lambda s: unicode(s, 'utf-8'), langs):
        # id, for free
        # code:
        try:
            db_lang = Language.objects.get(code=lang)
            logging.log(logging.INFO,
                        'Already found a language named %s.\n'\
                        'Data for this language are not imported.',
                        lang)
            continue
        except Language.DoesNotExist:
            db_lang = Language(code=lang)

        # fullname
        db_lang.fullname = _get_attribute(data, lang, 'fullname')

        # nplurals
        db_lang.nplurals = try_type(int,
                                    _get_attribute(data, lang, 'nplurals',
                                    unicode_me = False, default=1))

        # pluralequation
        db_lang.pluralequation = _get_attribute(data, 
                                 lang, 'pluralequation', unicode_me = False)

        # specialchars
        db_lang.specialchars = _get_attribute(data, lang, 'specialchars')

        db_lang.save()

def import_projects(parsed_data):
    # This could prompt the user, asking:
    # "Want us to import projects? Say no if you have already 
    # added the projects to the new Pootle DB in the web UI."

    data = parsed_data.__root__._assignments # Is this really the right way?
    prefix = 'Pootle.projects.'

    # Filter out unrelated keys
    keys = [key for key in data if key.startswith(prefix)]

    # Clean up 'pootle.fullname' into 'pootle'
    projs = set([key[len(prefix):].split('.')[0] for key in keys]) 

    for proj in map(lambda s: unicode(s, 'utf-8'), projs):
        # id, for free
        # code:
        try:
            db_proj = Project.objects.get(code=proj)
            logging.log(logging.INFO,
                        'Already found a project named %s.\n'\
                        'Data for this project are not imported.',
                        proj)
            continue
        except Project.DoesNotExist:
            db_proj = Project(code=proj)

        # fullname
        db_proj.fullname = _get_attribute(data, proj, 'fullname', prefix=prefix)

        # description
        db_proj.description = _get_attribute(data, proj, 'description',
                                             prefix=prefix)

        # checkstyle
        db_proj.checkstyle = _get_attribute(data, proj, 'checkstyle',
                                            unicode_me = False, prefix=prefix)

        # localfiletype
        db_proj.localfiletype = _get_attribute(data, proj, 'localfiletype',
                                               default='po', prefix=prefix)

        # treestyle
        db_proj.treestyle = _get_attribute(data, proj, 'treestyle',
                            unicode_me = False, default='auto', prefix=prefix)

        # ignoredfiles
        db_proj.ignoredfiles = _get_attribute(data, proj, 'ignoredfiles',
                               default=u'', prefix=prefix)

        db_proj.save()

def _get_user_attribute(data, user_name, attribute, unicode_me = True,
                        default = ''):
    return _get_attribute(data, user_name, attribute, unicode_me, default,
                          prefix='')

def create_database_user(data, user_name):
    # Create basic user information
    user = User(username       = user_name,
                first_name     = _get_user_attribute(data, user_name, 'name'),
                email          = _get_user_attribute(data, user_name, 'email'),
                is_active      = try_type(bool, _get_user_attribute(data, user_name, 'activated',
                                                                    unicode_me=False, default=0)),
                password       = _get_user_attribute(data, user_name, 'passwdhash',
                                                     unicode_me = False),
                # "hash" is the login type that indicates "hash" the user's
                # submitted password into MD5 and check against a local file/DB.
#                logintype      = _get_user_attribute(data, user_name, 'logintype',
#                                                     unicode_me = False,
#                                                     default = 'hash'),
                is_superuser   = try_type(bool, _get_user_attribute(data, user_name, 'rights.siteadmin',
                                                                    unicode_me=False, default=0)))
    # We have to save the user to ensure that an associated PootleProfile is created...
    user.save()
    logging.log(logging.INFO, 'Created a user object for %s', user_name)

    # Profile information
    profile = user.get_profile()
    profile.unit_rows      = try_type(int, _get_user_attribute(data, user_name, 'viewrows',
                                                               unicode_me=False, default=10))
    # uilanguage
    raw_uilanguage = _get_user_attribute(data, user_name, 'uilanguages')
    assert ',' not in raw_uilanguage # just one value here
    if raw_uilanguage:
        try:
            profile.ui_lang = Language.objects.get(code=raw_uilanguage)
        except Language.DoesNotExist:
            logging.log(logging.ERROR, "The user %(username)s has %(lang_code)s as his/her "\
                            "UI language, but %(lang_code)s is not available in Pootle's "\
                            "language database", dict(username=user.username, lang_code=raw_uilanguage))
    else:
        pass # leave it NULL

    # altsrclanguage
    raw_altsrclanguage = _get_user_attribute(data, user_name,
                                             'altsrclanguage')
    assert ',' not in raw_altsrclanguage # just one value here
    if raw_altsrclanguage:
        try:
            profile.alt_src_lang = Language.objects.get(code=raw_altsrclanguage)
        except Language.DoesNotExist:
            logging.log(logging.ERROR, "The user %(username)s has %(lang_code)s as his/her "\
                            "alternative source language, but %(lang_code)s is not "\
                            "available in Pootle's language database", 
                        dict(username=user.username, lang_code=raw_uilanguage))
    else:
        pass # leave it NULL
    profile.save()
    logging.log(logging.INFO, 'Created a profile object for %s', user_name)

    return user, profile

def augment_list(profile, data, model, user_property, property_name):
    """Enumerate the list of codes (language or project codes, for
    example) in property named 'user_property' in the jToolkit prefs
    node 'data'. Filter the list removing all empty entries. Then, for
    each code, check whether the property named 'user_property' in
    'profile' (which is a PootleProfile instance) contains an element
    with the code 'code'. If not, add it.
    """
    # Get the property named 'user_property' from the prefs node
    # 'data' for the username given by profile.user.username
    jtoolkit_property = _get_user_attribute(data, profile.user.username, user_property)
    # Split jtoolkit_property by ',', filtering out all strings which
    # contain only spaces and enumerate using the variable 'code'.
    for code in (code for code in jtoolkit_property.split(',') if code.strip()):
        # Arguments to be passed to logging.log calls below
        log_args = dict(property_name=property_name,
                        username=profile.user.username,
                        code=code)
        try:
            # Get the Django object from 'model' which has the code 'code'
            db_object = model.objects.get(code=code)
            # See if 'db_object' is profile.user_property
            if db_object not in getattr(profile, user_property).all():
                # If not, then add it
                getattr(profile, user_property).add(db_object)
                logging.log(logging.INFO,
                            "Adding %(property_name)s %(code)s for user %(username)s",
                            log_args)
        except model.DoesNotExist:
            # Oops. No Django object in 'model' has the code
            # 'code'. Tell the user that the necessary object should
            # be created.
            logging.log(logging.ERROR, 
                        "Failed to add %(username)s to %(property_name)s ID "\
                            "%(code)s; you probably need to create it", log_args)

def as_unicode(string):
    if isinstance(string, unicode):
        return string
    elif isinstance(string, str):
        return string.decode('utf-8')
    else:
        raise Exception('You must pass a string type')

def import_users(parsed_users):
    data = parsed_users.__root__._assignments # Is this really the
                                              # right way?

    # Groan - figure out the usernames
    usernames = (key.split('.')[0] for key in data)
    for username in (as_unicode(username) for username in usernames):
        must_add_user_object = True

        # Check if we already exist:
        try:
            user = User.objects.get(username=username)
            profile = user.get_profile()
            logging.log(logging.INFO, 'Already found a user named %s\n'\
                            'Going to skip importing his data, but will '\
                            'import his language and project preferences.',
                        username)
        except User.DoesNotExist:
            user, profile = create_database_user(data, username)

        # ASSUMPTION: Someone has already created all the necessary projects
        # and languages in the web UI or through the earlier importer
        augment_list(profile, data, Project,  'projects',  'project')
        augment_list(profile, data, Language, 'languages', 'language')
        # We might have modified the profile, so save it in case.
        profile.save()

if __name__ == '__main__':
    main()
