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

from pootle_app.models             import Suggestion, Submission
from pootle_store.models       import Unit
from pootle_app.models.profile     import get_profile
from pootle_app.models.permissions import check_permission, PermissionError

def suggest_translation(pootle_file, item, trans, request):
    if not check_permission("suggest", request):
        raise PermissionError(_("You do not have rights to suggest changes here"))
    translation_project = request.translation_project
    unit_query = Unit.objects.filter(store  = pootle_file.store,
                                     index  = item,
                                     source = pootle_file.getitem(item).getsource(),
                                     target = trans,
                                     state  = 'pending')
    if unit_query.count() == 0:
        unit = Unit(store  = pootle_file.store,
                    index  = item,
                    source = pootle_file.getitem(item).getsource(),
                    target = trans,
                    state  = 'pending', 
                    )
        unit.save()
        s = Suggestion(
            creation_time       = datetime.datetime.utcnow(),
            translation_project = translation_project,
            suggester           = get_profile(request.user),
            unit                = unit)
        s.save()
        pootle_file.addsuggestion(item, trans, s.suggester.user.username)
    else:
        # TBD: If a Unit with the specified data already exists, an
        # exception will be thrown (this happens if the user makes a
        # suggestion that is identical to a previous
        # suggestion). Notify the user of this error somehow
        pass

def update_translation(pootle_file, item, newvalues, request, suggestion=None):
    """updates a translation with a new value..."""
    if not check_permission("translate", request):
        raise PermissionError(_("You do not have rights to change translations here"))
    pootle_file.pofreshen()
    translation_project = request.translation_project
    if suggestion is None:
        if (type(newvalues['target']) == dict):
            target = newvalues['target'][0]
        else:
            target = newvalues['target']
        unit = Unit(store  = pootle_file.store,
                    index  = item,
                    source = unicode(pootle_file.getitem(item).getsource()),
                    target = target)
        unit.save()
        
            
    else:
        unit       = suggestion.unit
        unit.state = 'accepted'
    s = Submission(
        creation_time       = datetime.datetime.utcnow(),
        translation_project = translation_project,
        submitter           = get_profile(request.user),
        from_suggestion     = suggestion,
        unit                = unit)
    s.save()
    pootle_file.updateunit(item, newvalues, request.user, translation_project.language)
    translation_project.update_index(translation_project.indexer, pootle_file, [item])

def filter_by_suggester(query, pootle_file, item, suggitem):
    """returns who suggested the given item's suggitem if recorded, else None"""
    username = pootle_file.getsuggester(item, suggitem)
    try:
        query.filter(PootleProfile.objects.get(user__username=username))
    except PootleProfile.DoesNotExist:
        return query

def get_suggestion(pootle_file, item, newtrans, request):
    """Marks the suggestion specified by the parameters with the given status,
    and returns that suggestion object"""
    translation_project = request.translation_project
    unit  = Unit.objects.get(store  = pootle_file.store,
                             index  = item,
                             source = pootle_file.getitem(item).getsource(),
                             target = newtrans,
                             state  = 'pending'
                             )
    return Suggestion.objects.get(translation_project = translation_project,
                                  unit                = unit)

def reject_suggestion(pootle_file, item, suggitem, newtrans, request):
    """rejects the suggestion and removes it from the pending file"""
    if not check_permission("review", request):
        raise PermissionError(_("You do not have rights to review suggestions here"))

    # Deletes the suggestion from the database
    suggestion = get_suggestion(pootle_file, item, newtrans, request)
    suggestion.delete()
    # Deletes the suggestion from the .pending file
    pootle_file.deletesuggestion(item, suggitem, newtrans)

def accept_suggestion(pootle_file, item, suggitem, newtrans, request):
    """accepts the suggestion into the main pofile"""
    if not check_permission("review", request):
        raise PermissionError(_("You do not have rights to review suggestions here"))

    suggestion = get_suggestion(pootle_file, item, newtrans, request)
    pootle_file.deletesuggestion(item, suggitem, newtrans)
    new_values = {"target": newtrans, "fuzzy": False}
    update_translation(pootle_file, item, new_values, request, suggestion)

