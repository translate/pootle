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

from django.utils.translation import ugettext as _
from django.core.exceptions import PermissionDenied

from pootle_app.models             import Suggestion
from pootle_statistics.models import Submission
from pootle_profile.models import get_profile
from pootle_app.models.permissions import check_permission

def _suggestion_hash(store, item, trans):
    # since django's IntegerField is always 32 bit on mysql we cast to
    # make sure we don't pass larger hashes
    return int(hash((store.pootle_path, item, unicode(trans))) & 0xfffffff)

def suggest_translation(store, item, trans, request):
    if not check_permission("suggest", request):
        raise PermissionDenied(_("You do not have rights to suggest changes here"))
    translation_project = request.translation_project
    unit = store.getitem(item)
    profile = get_profile(request.user)
    unit.add_suggestion(trans, profile)
    s = Suggestion(
        creation_time       = datetime.datetime.utcnow(),
        translation_project = translation_project,
        suggester           = profile,
        unit                = _suggestion_hash(store, item, trans),
        state               = 'pending',
        )
    s.save()

def update_translation(store, item, newvalues, request, suggestion=None):
    """updates a translation with a new value..."""

    if not check_permission("translate", request):
        raise PermissionDenied(_("You do not have rights to change translations here"))

    translation_project = request.translation_project

    s = Submission(
        creation_time       = datetime.datetime.utcnow(),
        translation_project = translation_project,
        submitter           = get_profile(request.user),
        from_suggestion     = suggestion,
        )
    try:
        s.save()
    except:
        # FIXME: making from_suggestion OneToOne was a mistake since
        # we can't distinguish between identical suggestions.
        pass

    store.updateunit(item, newvalues, translation_project.checker,
                          user=request.user, language=translation_project.language)
    translation_project.update_index(translation_project.indexer, store, item)


def update_suggestion(state, store, item, newtrans, request):
    """Marks the suggestion specified by the parameters with the given status,
    and returns that suggestion object"""
    translation_project = request.translation_project
    suggestion, created  = Suggestion.objects.get_or_create(translation_project=translation_project,
                                                            unit=_suggestion_hash(store, item, newtrans))
    suggestion.state = state
    suggestion.reviewer = get_profile(request.user)
    suggestion.review_time = datetime.datetime.utcnow()
    suggestion.save()
    return suggestion


def reject_suggestion(store, item, suggitem, newtrans, request):
    """rejects the suggestion and removes it from the pending file"""
    if not check_permission("review", request):
        raise PermissionDenied(_("You do not have rights to review suggestions here"))

    update_suggestion('rejected', store, item, newtrans, request)
    # Deletes the suggestion from the .pending file
    unit = store.getitem(item)
    unit.reject_suggestion(suggitem, newtrans)

def accept_suggestion(store, item, suggitem, newtrans, request):
    """accepts the suggestion into the main pofile"""
    if not check_permission("review", request):
        raise PermissionDenied(_("You do not have rights to review suggestions here"))

    suggestion = update_suggestion('accepted', store, item, newtrans, request)

    new_values = {"target": newtrans, "fuzzy": False}
    unit = store.getitem(item)
    unit.accept_suggestion(suggitem, newtrans)
