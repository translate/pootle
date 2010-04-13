#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import cStringIO
import os

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext as _N
from django.core.exceptions import PermissionDenied

from pootle_misc.baseurl           import redirect
from pootle_translationproject.models import TranslationProject
from pootle_store.models import Store, Unit
from pootle_store.views import translate_page
from pootle_app.models.permissions import get_matching_permissions, check_permission
from pootle_app.models import store_iteration
from pootle_profile.models import get_profile
from pootle_app.views.language     import dispatch
from pootle_app.convert            import convert_table
from pootle_app                    import unit_update

from pootle_app.views.language.translate_page import find_and_display

from pootle_app.views.language.translate_page import get_diff_codes
from pootle_app.views.language.translate_page import highlight_diffs
from pootle_app.views.language.translate_page import get_string_array

def get_stats_headings():
    """returns a dictionary of localised headings"""
    return {
        "name":                   _("Name"),
        "translated":             _("Translated"),
        "translatedpercentage":   _("Translated percentage"),
        "translatedwords":        _("Translated words"),
        "fuzzy":                  _("Fuzzy"),
        "fuzzypercentage":        _("Fuzzy percentage"),
        "fuzzywords":             _("Fuzzy words"),
        "untranslated":           _("Untranslated"),
        "untranslatedpercentage": _("Untranslated percentage"),
        "untranslatedwords":      _("Untranslated words"),
        "total":                  _("Total"),
        "totalwords":             _("Total Words"),
        # l10n: noun. The graphical representation of translation status
        "progress":               _("Progress"),
        "summary":                _("Summary")
        }

def get_translation_project(f):
    def decorated_f(request, language_code, project_code, *args, **kwargs):
        translation_project = get_object_or_404(TranslationProject, language__code=language_code, project__code=project_code)
        return f(request, translation_project, *args, **kwargs)
    return decorated_f

def set_request_context(f):
    def decorated_f(request, translation_project, *args, **kwargs):
        # For now, all permissions in a translation project are
        # relative to the root of that translation project.
        request.permissions = get_matching_permissions(
            get_profile(request.user), translation_project.directory)
        request.translation_project = translation_project
        return f(request, translation_project, *args, **kwargs)
    return decorated_f

################################################################################

@get_translation_project
@set_request_context
def translate(request, translation_project, dir_path):
    pootle_path = translation_project.pootle_path + dir_path
    units_query = Unit.objects.filter(store__pootle_path__startswith=pootle_path)
    return translate_page(request, units_query)
def translate_page(request, translation_project, dir_path):
    def next_store_item(search, store_name, item):
        return store_iteration.get_next_match(directory,
                                              store_name,
                                              item,
                                              search)

    def prev_store_item(search, store_name, item):
        return store_iteration.get_prev_match(directory,
                                              store_name,
                                              item,
                                              search)

    directory = translation_project.directory.get_relative(dir_path)
    return find_and_display(request, directory, next_store_item, prev_store_item)

def handle_translation_file(request, translation_project, file_path):
    pootle_path = translation_project.pootle_path + (file_path or '')
    store = get_object_or_404(Store, pootle_path=pootle_path)
    def get_item(itr, item):
        try:
            return itr.next()
        except StopIteration:
            return item

    def next_store_item(search, store_name, item):
        if 0 <= item < store.getquickstats()['total']:
            return store, get_item(search.next_matches(store, item), item - 1)
        else:
            return store, store.getquickstats()['total'] - 1

    def prev_store_item(search, store_name, item):
        if store.getquickstats()['total'] > item > 0:
            return store, get_item(search.prev_matches(store, item), item + 1)
        else:
            return store, 0

    return find_and_display(request, store.parent, next_store_item, prev_store_item)


@get_translation_project
@set_request_context
def commit_file(request, translation_project, file_path):
    if not check_permission("commit", request):
        raise PermissionDenied(_("You do not have rights to commit files here"))
    pootle_path = translation_project.directory.pootle_path + file_path
    store = get_object_or_404(Store, pootle_path=pootle_path)
    result = translation_project.commitpofile(request, store)
    return redirect(dispatch.show_directory(request, translation_project.directory.pootle_path))

@get_translation_project
@set_request_context
def update_file(request, translation_project, file_path):
    if not check_permission("commit", request):
        raise PermissionDenied(_("You do not have rights to update files here"))
    pootle_path = translation_project.directory.pootle_path + file_path
    store = get_object_or_404(Store, pootle_path=pootle_path)
    result = translation_project.update_file(request, store)
    return redirect(dispatch.show_directory(request, translation_project.directory.pootle_path))

MIME_TYPES = {
    "po":  "text/x-gettext-translation; charset=%(encoding)s",
    "csv": "text/csv; charset=%(encoding)s",
    "xlf": "application/x-xliff; charset=%(encoding)s",
    "ts":  "application/x-linguist; charset=%(encoding)s",
    "mo":  "application/x-gettext-translation" }

@get_translation_project
@set_request_context
def export(request, translation_project, file_path, format):
    store = get_object_or_404(Store, pootle_path=translation_project.directory.pootle_path + file_path)
    encoding = getattr(store.file.store, "encoding", "UTF-8")
    content_type = MIME_TYPES[format] % dict(encoding=encoding)
    if format == translation_project.project.localfiletype:
        response = HttpResponse(str(store.file.store), content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename=%s' % store.name
    else:
        convert_func = convert_table[translation_project.project.localfiletype, format]
        output_file = cStringIO.StringIO()
        input_file  = cStringIO.StringIO(str(store.file.store))
        convert_func(input_file, output_file, None)
        response = HttpResponse(output_file.getvalue(), content_type=content_type)
        filename, ext = os.path.splitext(store.name)
        filename += os.path.extsep + format
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response


@get_translation_project
@set_request_context
def handle_file(request, translation_project, file_path):
    return handle_translation_file(request, translation_project, file_path)

@get_translation_project
@set_request_context
def handle_suggestions(request, translation_project, file_path, item):
    """Handles accepts/rejects of suggestions selectively via AJAX, receiving
       and sending data in JSON format.

       Response attributes are described below:
        * "status": Indicates the status after trying the action.
                    Possible values: "error", "success".
        * "message": Status message of the transaction. Depending on the status
                    it will display an error message, or the number of
                    suggestions rejected/accepted.
        * "diffs": Updated diff for the current translation after performing
                   an action. If there are no suggestions pending, an empty
                   dict will be returned."""
    pootle_path = translation_project.pootle_path + file_path
    store = Store.objects.get(pootle_path=pootle_path)
    item = int(item)

    def get_pending_suggestions(item):
        """Gets pending suggestions for item in pofilename."""
        itemsuggestions = []
        suggestions = store.getsuggestions(item)
        for suggestion in suggestions:
            if suggestion.hasplural():
                itemsuggestions.append(suggestion.target.strings)
            else:
                itemsuggestions.append([suggestion.target])
        return itemsuggestions

    def get_updated_diffs(trans, suggestions):
        """Returns the diff between the current translation and the
           suggestions available after performing an accept/reject
           action.
           If no suggestions are available anymore, just return an
           empty list."""
        # No suggestions left, no output at all
        if len(suggs) == 0:
            return []
        else:
            diffcodes = {}
            forms = []
            for pluralitem, pluraltrans in enumerate(trans):
                pluraldiffcodes = [get_diff_codes(pluraltrans,
                                                  suggestion[pluralitem])
                                   for suggestion in suggestions]
                diffcodes[pluralitem] = pluraldiffcodes
                combineddiffs = reduce(list.__add__, pluraldiffcodes, [])
                transdiff = highlight_diffs(pluraltrans, combineddiffs,
                                            issrc=True)
                form = { "diff": transdiff }
                forms.append(form)
            return forms

    response = {}
    # Decode JSON data sent via POST
    data = simplejson.loads(request.POST.get("data", "{}"))
    if not data:
        response["status"] = "error"
        response["message"] = _("No suggestion data given.")
    else:
        response["del_ids"] = []
        rejects = data.get("rejects", [])
        reject_candidates = len(rejects)
        reject_count = 0
        accepts = data.get("accepts", [])
        accept_candidates = len(accepts)
        accept_count = 0

        for sugg in accepts:
            try:
                unit_update.accept_suggestion(store, item, int(sugg["id"]),
                                              sugg["newtrans"], request)
                response["del_ids"].append((item, sugg["id"]))
                response["accepted_id"] = (item, sugg["id"])
                accept_count += 1
            except ValueError, e:
                # Probably an issue with "item". The exception might tell us
                # everything we need, while no error will probably help the user
                response["message"] = e
            except PermissionDenied, e:
                response["message"] = e


        for sugg in reversed(rejects):
            try:
                unit_update.reject_suggestion(store, int(item), int(sugg["id"]),
                                              sugg["newtrans"], request)
                reject_count += 1
                response["del_ids"].append((int(item), sugg["id"]))
            except ValueError, e:
                # Probably an issue with "item". The exception might tell us
                # everything we need, while no error will probably help the user
                response["message"] = e
            except PermissionDenied, e:
                response["message"] = e

        response["status"] = (reject_candidates == reject_count and
                              accept_candidates == accept_count) and \
                              "success" or "error"

        if response["status"] == "success":
            amsg = ""
            rmsg = ""
            if accept_candidates != 0:
                amsg = _("Suggestion accepted.")
            if reject_candidates != 0:
                rmsg = _N("Suggestion rejected.",
                          "%d suggestions rejected.",
                          reject_count, reject_count)
            response["message"] = amsg + rmsg
            # Get updated diffs
            current_trans = get_string_array(store.getitem(item).target)
            suggs = get_pending_suggestions(item)
            response["diffs"] = get_updated_diffs(current_trans, suggs)

    response = simplejson.dumps(response, indent=4)
    return HttpResponse(response, mimetype="application/json")

