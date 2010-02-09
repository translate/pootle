#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import locale

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User, UserManager, AnonymousUser
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save

from pootle.i18n.override import lang_choices

from pootle_misc.baseurl import l

from pootle_language.models import Language
from pootle_project.models import Project


class PootleUserManager(UserManager):
    """A manager class which is meant to replace the manager class for the User model. This manager
    hides the 'nobody' and 'default' users for normal queries, since they are special users. Code
    that needs access to these users should use the methods get_default_user and get_nobody_user."""
    def get_default_user(self):
        return super(PootleUserManager, self).get_query_set().select_related(depth=1).get(username='default')

    def get_nobody_user(self):
        return super(PootleUserManager, self).get_query_set().select_related(depth=1).get(username='nobody')

    def hide_defaults(self):
        return super(PootleUserManager, self).get_query_set().exclude(username__in=('nobody', 'default'))

# Since PootleUserManager has no state, we can just replace the User manager's class with PootleUserManager
# to get the desired functionality.
User.objects.__class__ = PootleUserManager

class PootleProfileManager(models.Manager):
    def get_query_set(self):
        return super(PootleProfileManager, self).get_query_set().select_related(
            'languages', 'projects', 'alt_src_langs')

class PootleProfile(models.Model):
    objects = PootleProfileManager()
    class Meta:
        db_table = 'pootle_app_pootleprofile'

    # This is the only required field
    user = models.OneToOneField(User, unique=True, db_index=True)

    unit_rows       = models.SmallIntegerField(default=10)
    input_height    = models.SmallIntegerField(default=5)
    languages       = models.ManyToManyField(Language, blank=True, limit_choices_to=~Q(code='templates'), related_name="user_languages", db_index=True)
    projects        = models.ManyToManyField(Project, blank=True, db_index=True)
    ui_lang         = models.CharField(max_length=50, blank=True, null=True, choices=(choice for choice in lang_choices()), verbose_name=_('Interface Language'))
    alt_src_langs   = models.ManyToManyField(Language, blank=True, db_index=True, limit_choices_to=~Q(code='templates'), related_name="user_alt_src_langs")

    def __unicode__(self):
        return self.user.username
    def get_absolute_url(self):
        return l('/accounts/%s/' % self.user.username)
    
    def _get_status(self):
        #FIXME: what's this for?
        return "Foo"

    status = property(_get_status)
    isopen = property(lambda self: True)

    def _get_pootle_user(self):
        if self.user_id is not None:
            return self.user
        else:
            return AnonymousUser()

    def getuserstatistics(self):
        """ get user statistics for user statistics links"""
        from pootle_app.models.suggestion import _get_suggestions
        userstatistics = []
        userstatistics.append({'text': _('Suggestions Accepted'), 'count': _get_suggestions(self, "accepted").count()})
        userstatistics.append({'text': _('Suggestions Pending'), 'count': _get_suggestions(self, "pending").count()})
        userstatistics.append({'text': _('Suggestions Reviewed'), 'count': self.suggestions_reviewer_set.count()})
        userstatistics.append({'text': _('Submissions Made'), 'count': self.submission_set.count()})
        return userstatistics

    def getquicklinks(self):
        """gets a set of quick links to user's project-languages"""
        from pootle_translationproject.models import TranslationProject
        from pootle_app.models.permissions import check_profile_permission
        quicklinks = []
        # TODO: This can be done MUCH more efficiently with a bit of
        # query forethought.  Why don't we just select all the
        # TranslationProject objects from the database which match the
        # user's Languages and Projects? This should be efficient.
        #
        # But this will only work once we move TranslationProject
        # wholly to the DB (and away from its current brain damaged
        # half-non-db/half-db implementation).
        
        for language in Language.objects.filter(user_languages=self):
            langlinks = []
            for translation_project in TranslationProject.objects.filter(
                language=language, project__pootleprofile=self):
                isprojectadmin = check_profile_permission(self, 'administrate',
                                                          translation_project.directory)

                langlinks.append({
                    'code': translation_project.project.code,
                    'name': translation_project.project.fullname,
                    'isprojectadmin': isprojectadmin,
                    })

            islangadmin = check_profile_permission(self, 'administrate', language.directory)
            quicklinks.append({'code': language.code,
                               'name': language.localname(),
                               'islangadmin': islangadmin,
                               'projects': langlinks})
            quicklinks.sort(cmp=locale.strcoll, key=lambda dict: dict['name'])
        return quicklinks

    pootle_user = property(_get_pootle_user)


def create_pootle_profile(sender, instance, **kwargs):
    """A post-save hook for the User model which ensures that it gets an
    associated PootleProfile."""
    try:
        profile = instance.get_profile()
    except PootleProfile.DoesNotExist:
        profile = PootleProfile(user=instance)
        profile.save()

post_save.connect(create_pootle_profile, sender=User)

def get_profile(user):
    """Return the PootleProfile associated with a user.

    This function is only necessary if 'user' could be an anonymous
    user.  If you know for certain that a user is logged in, then use
    the .get_profile() method on a user instead."""
    if user.is_authenticated():
        # Return the PootleProfile associated with authenticated users
        return user.get_profile()
    else:
        # Anonymous users get the PootleProfile associated with the 'nobody' user
        return User.objects.get(username='nobody').get_profile()

