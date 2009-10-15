#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

import datetime

from django.db.models import ObjectDoesNotExist
from django.utils.translation import ugettext as _

from pootle_app.models             import Suggestion, Submission
from pootle_app.models.profile     import get_profile, PootleProfile
from pootle_app.models.permissions import check_permission, PermissionError


def _suggestion_hash(store, item, trans):
    return hash((store.pootle_path, item, unicode(trans)))

def suggest_translation(store, item, trans, request):
    if not check_permission("suggest", request):
        raise PermissionError(_("You do not have rights to suggest changes here"))
    translation_project = request.translation_project
    s = Suggestion(
        creation_time       = datetime.datetime.utcnow(),
        translation_project = translation_project,
        suggester           = get_profile(request.user),
        unit                = _suggestion_hash(store, item, trans),
        state               = 'pending',
        )
    s.save()
    store.addsuggestion(item, trans, s.suggester.user.username)
    #FIXME: we don't handle identical suggestions


def update_translation(store, item, newvalues, request, suggestion=None):
    """updates a translation with a new value..."""

    if not check_permission("translate", request):
        raise PermissionError(_("You do not have rights to change translations here"))

    translation_project = request.translation_project

    s = Submission(
        creation_time       = datetime.datetime.utcnow(),
        translation_project = translation_project,
        submitter           = get_profile(request.user),
        from_suggestion     = suggestion,
        )
    s.save()
    store.file.updateunit(item, newvalues, request.user, translation_project.language)
    translation_project.update_index(translation_project.indexer, store, [item])


def get_suggestion(store, item, newtrans, request):
    """Marks the suggestion specified by the parameters with the given status,
    and returns that suggestion object"""
    translation_project = request.translation_project
    return Suggestion.objects.get(translation_project = translation_project, unit=_suggestion_hash(store, item, newtrans))

def reject_suggestion(store, item, suggitem, newtrans, request):
    """rejects the suggestion and removes it from the pending file"""
    if not check_permission("review", request):
        raise PermissionError(_("You do not have rights to review suggestions here"))

    try:
        # Deletes the suggestion from the database
        suggestion = get_suggestion(store, item, newtrans, request)
        suggestion.delete()
    except ObjectDoesNotExist:
        pass
    # Deletes the suggestion from the .pending file
    store.deletesuggestion(item, suggitem, newtrans)

def accept_suggestion(store, item, suggitem, newtrans, request):
    """accepts the suggestion into the main pofile"""
    if not check_permission("review", request):
        raise PermissionError(_("You do not have rights to review suggestions here"))

    new_values = {"target": newtrans, "fuzzy": False}

    suggestion = None
    try:
        suggestion = get_suggestion(store, item, newtrans, request)
        suggestion.state = 'accepted'
        suggestion.save()
    except ObjectDoesNotExist:
        pass
    
    update_translation(store, item, new_values, request, suggestion)
    
    store.deletesuggestion(item, suggitem, newtrans)
    
