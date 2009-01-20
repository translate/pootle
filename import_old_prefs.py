#!/usr/bin/env python
# coding: utf-8

'''Author: Asheesh Laroia <asheesh@creativecommons.org>
Copyright: (C) 2008 Creative Commons
Permission is granted to redistribute this file under the GPLv2 or later, 
 at your option.   See COPYING for details.'''

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'Pootle.settings'

from django.db import transaction

from django.contrib.auth.models import User
from Pootle.pootle_app.models import Project, Language, PootleProfile, make_pootle_user, get_profile

import sys
from jToolkit import prefs
import types

def main():
    '''Read sys.argv for cofiguration, and perform the imports.'''
    if len(sys.argv) != 3:
        print "Usage: %s old_pootle.prefs users.prefs" % (
                sys.argv[0])
        return

    oldprefsfile = sys.argv[1]
    parsed_oldprefs = prefs.PrefsParser(oldprefsfile)
    usersfile = sys.argv[2]
    parsed_users = prefs.PrefsParser(usersfile)
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
        assert type(value) == int
        return bool(value)
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
        db_proj = Project(code=proj)

        # fullname
        db_proj.fullname = _get_attribute(data, proj, 'fullname')

        # description
        db_proj.description = _get_attribute(data, proj, 'description')

        # checkstyle
        db_proj.checkstyle = _get_attribute(data, proj, 'checkstyle',
                             unicode_me = False)

        # localfiletype
        db_proj.localfiletype = _get_attribute(data, proj, 'localfiletype')

        # createmofiles?
        db_proj.createmofiles = try_type(bool,
                                 _get_attribute(data, proj, 'createmofiles',
                                 unicode_me=False, default=0))

        # treestyle
        db_proj.treestyle = _get_attribute(data, proj, 'treestyle',
                            unicode_me = False)

        # ignoredfiles
        db_proj.ignoredfiles = _get_attribute(data, proj, 'ignoredfiles',
                               default=u'')

        db_proj.save()

def _get_user_attribute(data, user_name, attribute, unicode_me = True,
                        default = ''):
    return _get_attribute(data, user_name, attribute, unicode_me, default,
                          prefix='')

def import_users(parsed_users):
    data = parsed_users.__root__._assignments # Is this really the
                                              # right way?

    # Groan - figure out the usernames
    user_names = set([key.split('.')[0] for key in data])
    
    for user_name in user_names:
        must_add_user_object = True

        if type(user_name) == unicode:
            pass
        else:
            user_name = unicode(user_name, 'utf-8')
        # id for free, obviously.

        # Check if we already exist:
        possible_us = User.objects.filter(username=user_name).all()
        if possible_us:
            print >> sys.stderr, 'Already found a user for named', user_name
            print >> sys.stderr, 'Going to skip importing his data, but will',
            print >> sys.stderr, 'import his language and project preferences.'
            assert len(possible_us) == 1
            user = possible_us[0]
            must_add_user_object = False
        else:
            # username
            user = make_pootle_user(user_name)

            # name
            user.name = _get_user_attribute(data, user_name, 'name')

            # email
            user.email = _get_user_attribute(data, user_name, 'email')

            # activated
            user.activated = try_type(bool,
                             _get_user_attribute(data, user_name, 'activated',
                             unicode_me=False, default=0))

            # activationcode
            user.activationcode = _get_user_attribute(data, user_name,
                                  'activationcode', unicode_me = False,
                                  default=0)

            # passwdhash
            user.passwdhash = _get_user_attribute(data, user_name,
                              'passwdhash', unicode_me = False)

            # logintype
            # "hash" is the login type that indicates "hash" the user's
            # submitted password into MD5 and check against a local file/DB.
            user.logintype = _get_user_attribute(data, user_name, 'logintype',
                             unicode_me = False, default = 'hash')

            # siteadmin
            user.siteadmin = try_type(bool,
                             _get_user_attribute(data, user_name, 'siteadmin',
                             unicode_me=False, default=0))

            # viewrows
            user.viewrows = try_type(int,
                            _get_user_attribute(data, user_name, 'viewrows',
                            unicode_me=False, default=10))

            # translaterows
            user.translaterows = try_type(int,
                                 _get_user_attribute(data, user_name,
                                 'translaterows', unicode_me=False, default=10))

            # uilanguage
            raw_uilanguage = _get_user_attribute(data, user_name, 'uilanguages')
            assert ',' not in raw_uilanguage # just one value here
            if raw_uilanguage:
                db_uilanguage = alchemysession.query(Language).filter_by(
                                               code=raw_uilanguage).all()[0]
                user.uilanguage = db_uilanguage
            else:
                pass # leave it NULL

            # altsrclanguage
            raw_altsrclanguage = _get_user_attribute(data, user_name,
                                                     'altsrclanguage')
            assert ',' not in raw_altsrclanguage # just one value here
            if raw_altsrclanguage:
                db_altsrclanguage = alchemysession.query(Language).filter_by(
                                    code=raw_altsrclanguage).all()[0]
                user.altsrclanguage = db_altsrclanguage
            else:
                pass # leave it NULL
            user.save()

        # ASSUMPTION: Someone has already created all the necessary projects
        # and languages in the web UI or through the earlier importer
    
        # Fill in the user_projects table
        # (projects in the users.prefs file)
        raw_projects = _get_user_attribute(data, user_name, 'projects')
        projects_list = raw_projects.split(',')
        # remove the empty string from our list of "projects"
        projects_list = filter(lambda thing: thing, projects_list)
        for project_name in projects_list:
            try:
                db_project = Project.objects.filter(code=project_name).all()[0]
            except NoResultFound: # wrong exception name
                print >> sys.stderr, "Failed to add", user, "to project ID", 
                print >> sys.stderr, project_name, 
                print >> sys.stderr, "; you probably need to create it."
            if db_project not in user.projects:
                user.projects.append(db_project)

        # Fill in the user_languages table
        # (languages in users.prefs)
        raw_languages = _get_user_attribute(data, user_name, 'languages')
        languages_list = raw_languages.split(',')
        # remove the empty string from our list of "languages"
        languages_list = filter(lambda thing: thing, languages_list)
        for language_name in languages_list:
            try:
                db_language = Language.objects.filter(code=language_name).all()[0]
            except IndexError:
                print >> sys.stderr, "Failed to add", user, "to language ID",
                print >> sys.stderr, language_name,
                print >> sys.stderr,  "; you probably need to create it."
            profile = get_profile(user)
            if db_language not in profile.languages:
                profile.languages.append(db_language)
                profile.save()

        if must_add_user_object:
            # Commit the user.
            user.save()
        else:
            print 'YOW?' # should save() or something
			

if __name__ == '__main__':
    main()
