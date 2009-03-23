#!/usr/bin/env python
# coding: utf-8

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'Pootle.settings'

from django.db import transaction
import sys
import md5

from django.core.management.base import NoArgsCommand
from django.core.management.color import no_style
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

from pootle_app.models.permissions import PermissionSet, get_pootle_permissions
from pootle_app.models import Directory, PootleProfile

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        modify_default_permissions()

def modify_default_permissions():
    root = Directory.objects.root
    all_permissions = get_pootle_permissions().values()
    for username in ('default', 'nobody'):
        profile = PootleProfile.objects.select_related(depth=1).get(user__username=username)
        permission_set = PermissionSet.objects.get(profile=profile, directory=root)
        permission_set.positive_permissions = all_permissions
        permission_set.save()

if __name__ == "__main__":
    main()
