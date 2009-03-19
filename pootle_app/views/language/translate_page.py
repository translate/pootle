#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This file is somewhat based on the older Pootle/translatepage.py
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

import re
import difflib
import operator
import copy

from django.contrib.auth.models import User
from django.utils.html import urlize
from django.utils.translation import ugettext as _
from django.conf import settings
N_ = _

from translate.storage import po
from translate.misc.multistring import multistring

from pootle_app.views.util import render_to_kid, KidRequestContext
from pootle_app.translation_project import TranslationProject
from pootle_app.fs_models import Directory, Store
from pootle_app.profile import get_profile
from pootle_app.views.common import navbar_dict, search_forms
from pootle_app.url_manip import URL, read_all_state
from pootle_app import unit_update
from pootle_app import permissions
from pootle_app.permissions import check_permission

from Pootle import pagelayout
from Pootle import projects
from Pootle import pootlefile
from Pootle.i18n.jtoolkit_i18n import tr_lang

xml_re = re.compile("&lt;.*?&gt;")

def oddoreven(polarity):
    if polarity % 2 == 0:
        return "even"
    elif polarity % 2 == 1:
        return "odd"

def get_alt_projects(request, pootle_file):
    # do we have enabled alternative source language?
    if settings.ENABLE_ALT_SRC:
        # try to get the project if the user has chosen an alternate source language
        return TranslationProject.objects.filter(language__in=get_profile(request.user).alt_src_langs.all(),
                                                 project=request.translation_project.project_id)
    else:
        return TranslationProject.objects.none()

def get_assign_box():
    """gets strings if the user can assign strings"""
    return {
        "title":        _("Assign Strings"),
        "user_title":   _("Assign to User"),
        "action_title": _("Assign Action"),
        "submit_text":  _("Assign Strings"),
        "users":        User.objects.order_by('username')
    }

def add_file_links(request, url_state, pootle_file):
    """adds a section on the current file, including any checks happening"""
    template_vars = {}
    if url_state['translate_display'].show_assigns and check_permission("assign", request):
        template_vars["assigns"] = get_assign_box()
    if pootle_file is not None:
        if len(url_state['search'].match_names) > 0:
            checknames = \
            ["<a href='http://translate.sourceforge.net/wiki/toolkit/pofilter_tests#%(checkname)s' \
            title='%(checkname)s' target='_blank'>%(checkname)s</a>" % \
            {"checkname": matchname.replace("check-", "", 1)} for matchname in url_state['search'].match_names]
            # TODO: put the following parameter in quotes, since it will be foreign in all target languages
            # l10n: the parameter is the name of one of the quality checks, like "fuzzy"
            template_vars["checking_text"] = _("checking %s") % ", ".join(checknames)
    return template_vars

def get_rows_and_icon(profile, url_state):
    if url_state['translate_display'].view_mode == 'view':
        return get_display_rows(profile, "view"), "file"
    else:
        return get_display_rows(profile, "translate"), "edit"

def get_finished_text(request, stoppedby, url_state):
    """gets notice to display when the translation is finished"""
    # l10n: "batch" refers to the set of translations that were reviewed
    title = _("End of batch")
    link_state = read_all_state({})
    for attr in ('show_assigns', 'show_checks', 'editing'):
        setattr(link_state['translate_display'], attr, getattr(url_state['translate_display'], attr, False))
    link = URL(request.path_info, link_state).parent
    finishedlink = link.as_relative_to_path_info(request)
    returnlink = _("Click here to return to the index")
    stoppedbytext = stoppedby
    return {"title":        title,
            "stoppedby":    stoppedbytext,
            "finishedlink": finishedlink,
            "returnlink":   returnlink}

def get_page_links(request, pootle_file, pagesize, translations, first_item):
    """gets links to other pages of items, based on the given baselink"""
    url = URL(pootle_file.store.pootle_path, read_all_state({}))
    url.state['translate_display'].view_mode = 'translate'
    pagelinks = []
    pofilelen = len(pootle_file.total)
    if pofilelen <= pagesize or first_item is None:
        return pagelinks
    lastitem = min(pofilelen-1, first_item + pagesize - 1)
    if pofilelen > pagesize and not first_item == 0:
        # l10n: noun (the start)
        pagelinks.append({"href": url.as_relative_to_path_info(request), "text": _("Start")})
    else:
        # l10n: noun (the start)
        pagelinks.append({"text": _("Start")})
    if first_item > 0:
        linkitem = max(first_item - pagesize, 0)
        # l10n: the parameter refers to the number of messages
        new_url = copy.deepcopy(url)
        new_url.state['position'].item = linkitem
        pagelinks.append({"href": new_url.as_relative_to_path_info(request),
                          "text": _("Previous %d") % (first_item - linkitem)})
    else:
        # l10n: the parameter refers to the number of messages
        pagelinks.append({"text": _("Previous %d" % pagesize)})
        # l10n: the third parameter refers to the total number of messages in the file
    pagelinks.append({"text": _("Items %d to %d of %d") % (first_item + 1, lastitem + 1, pofilelen)})
    if first_item + len(translations) < len(pootle_file.total):
        linkitem = first_item + pagesize
        itemcount = min(pofilelen - linkitem, pagesize)
        # l10n: the parameter refers to the number of messages
        new_url = copy.deepcopy(url)
        new_url.state['position'].item = linkitem
        pagelinks.append({"href": new_url.as_relative_to_path_info(request),
                          "text": _("Next %d") % itemcount})
    else:
        # l10n: the parameter refers to the number of messages
        pagelinks.append({"text": _("Next %d") %  pagesize})
    if pofilelen > pagesize and (url.state['position'].item + pagesize) < pofilelen:
        # l10n: noun (the end)
        new_url = copy.deepcopy(url)
        new_url.state['position'].item = max(pofilelen - pagesize, 0)
        pagelinks.append({"href": new_url.as_relative_to_path_info(request),
                          "text": _("End")})
    else:
        # l10n: noun (the end)
        pagelinks.append({"text": _("End")})
    for n, pagelink in enumerate(pagelinks):
        if n < len(pagelinks)-1:
            pagelink["sep"] = " | "
        else:
            pagelink["sep"] = ""
    return pagelinks

def get_display_rows(profile, mode):
    """get the number of rows to display for the given mode"""
    if mode == "view":
        rowsdesired = profile.view_rows
        default = 10
        maximum = 100
    elif mode == "translate":
        rowsdesired = profile.translate_rows
        default = 7
        maximum = 20
    else:
        raise ValueError("getdisplayrows has no mode '%s'" % mode)
    return min(rowsdesired, maximum)

def get_units(pootle_file, item_start, item_stop):
    return [pootle_file.units[index] for index in pootle_file.total[max(item_start,0):item_stop]]

def get_translations(profile, pootle_file, url_state):
    """gets the list of translations desired for the view, and sets editable and firstitem parameters"""
    item = url_state['position'].item
    if pootle_file is None:
        # editable, first item, items
        return -1, item, []
    elif url_state['translate_display'].view_mode == 'view':
        rows = get_display_rows(profile, "view")
        return -1, item, get_units(pootle_file, item, item + rows)
    else:
        rows = get_display_rows(profile, "translate")
        before = rows / 2
        fromitem = item - before
        first_item = max(item - before, 0)
        toitem = first_item + rows
        items = get_units(pootle_file, fromitem, toitem)
        return item, first_item, items

def get_header_plural(pootle_file):
    nplurals, plurals = pootle_file.getheaderplural()
    if not (nplurals and nplurals.isdigit()):
        # The file doesn't have plural information declared. Let's get it from
        # the language
        nplurals = pootle_file.translation_project.language.nplurals
    else:
        nplurals = int(nplurals)
    return nplurals, plurals

def ensure_trans_plurals(pootle_file, orig, trans):
    nplurals, plurals = get_header_plural(pootle_file)
    if len(orig) > 1:
        if len(trans) != nplurals:
            # Chop if in case it is too long
            trans = trans[:nplurals]
            trans.extend([u""] * (nplurals-len(trans)))
    return trans

def get_string_array(string):
    if isinstance(string, multistring):
        return string.strings
    else:
        return [string]

def fancy_spaces(string):
    """Returns the fancy spaces that are easily visible."""
    spaces = string.group()
    while spaces[0] in "\t\n\r":
        spaces = spaces[1:]
    return '<span class="translation-space"> </span>\n' * len(spaces)

def add_fancy_spaces(text):
    """Insert fancy spaces"""
    #More than two consecutive:
    text = re.sub("[ ]{2,}", fancy_spaces, text)
    #At start of string
    text = re.sub("^[ ]+", fancy_spaces, text)
    #After newline
    text = re.sub("\\n([ ]+)", fancy_spaces, text)
    #At end of string
    text = re.sub("[ ]+$", fancy_spaces, text)
    return text

def replace_in_seq(text, *replacements):
    for original, replacement in replacements:
        text = text.replace(original, replacement)
    return text

def escape_text(text, fancy_spaces=True, stripescapes=False):
    """Replace special characters &, <, >, add and handle escapes if asked."""
    text = replace_in_seq(text,
                          ("&", "&amp;"), # Must be done first!
                          ("<", "&lt;"),
                          (">", "&gt;"))

    if stripescapes:
        text = replace_in_seq(text,
                              ("\n", '<br />'),
                              ("\r", '<br />'))
    else:
        fancyescape = lambda escape: \
            '<span class="translation-highlight-escape">%s</span>' % escape
        fancy_xml = lambda escape: \
            '<span class="translation-highlight-html">%s</span>' % escape.group()
        text = xml_re.sub(fancy_xml, text)
        text = replace_in_seq(text,
                              ("\r\n", fancyescape('\\r\\n') + '<br />'),
                              ("\n",   fancyescape('\\n') + '<br />'),
                              ("\r",   fancyescape('\\r') + '<br />'),
                              ("\t",   fancyescape('\\t')))
    text = replace_in_seq(text, ("<br />", '<br />\n'))
    # we don't need it at the end of the string

    if text.endswith("<br />\n"):
        text = text[:-len("<br />\n")]

    if fancy_spaces:
        text = add_fancy_spaces(text)
    return text

def getorigdict(item, orig, editable):
    if editable:
        focus_class = "translate-original-focus"
    else:
        focus_class = ""
    purefields = []
    for pluralid, pluraltext in enumerate(orig):
        pureid = "orig-pure%d-%d" % (item, pluralid)
        purefields.append({"pureid": pureid, "name": pureid, "value": pluraltext})
    origdict = {
        "focus_class":    focus_class,
        "itemid":         "orig%d" % item,
        "pure":           purefields,
        "isplural":       len(orig) > 1 or None,
        "singular_title": _("Singular"),
        "plural_title":   _("Plural"),
        }
    if len(orig) > 1:
        origdict["singular_text"] = escape_text(orig[0])
        origdict["plural_text"] = escape_text(orig[1])
    else:
        origdict["text"] = escape_text(orig[0])
    return origdict

def get_terminology(pootle_file, item):
    try:
        term_matcher = pootle_file.translation_project.gettermmatcher()
        if term_matcher is not None:
            return term_matcher.matches(pootle_file.getitem(item).source)
        else:
            return []
    except:
        import logging
        import traceback
        logging.log(logging.ERROR, traceback.format_exc())
        return []

def remove_button_if_no_permission(label, buttons, request):
    if label in buttons and not check_permission(label, request):
        buttons.remove(label)

def get_trans_buttons(request, translation_project, item, desiredbuttons):
    """gets buttons for actions on translation"""
    remove_button_if_no_permission("suggest",   desiredbuttons, request)
    remove_button_if_no_permission("translate", desiredbuttons, request)
    specialchars = translation_project.language.specialchars
    return {
        "desired":      desiredbuttons,
        "item":         item,
        # l10n: verb
        "copy_text":    _("Copy"),
        "skip":         _("Skip"),
        # l10n: verb
        "back":         _("Back"),
        "suggest":      _("Suggest"),
        "submit":       _("Submit"),
        "specialchars": specialchars,
        }

def escape_for_textarea(text):
    return replace_in_seq(text, 
                          ("&", "&amp;"), # Must be done first!
                          ("<", "&lt;"),
                          (">", "&gt;"),
                          ("\r\n", '\\r\\n'),
                          ("\n", '\\n'),
                          ("\\n", '\\n\n'),
                          ("\t", '\\t'))

def unescape_submition(text):
    return replace_in_seq(text, 
                          ("\t", ""),
                          ("\n", ""),
                          ("\r", ""),
                          ("\\t", "\t"),
                          ("\\n", "\n"),
                          ("\\r", "\r"))

def get_edit_link(request, pootle_file, item):
    """gets a link to edit the given item, if the user has permission"""
    if check_permission("translate", request) or check_permission("suggest", request):
        url = URL('/'+request.path_info[1:], read_all_state({}))
        url.state['translate_display'].view_mode = 'translate'
        url.state['position'].item  = item
        # l10n: verb
        return {"href": url.as_relative_to_path_info(request),
                "text": _("Edit"), "linkid": "editlink%d" % item}
    else:
        return {}

def get_trans_view(request, pootle_file, item, trans, textarea=False):
    """returns a widget for viewing the given item's translation"""
    if textarea:
        escapefunction = escape_for_textarea
    else:
        escapefunction = escape_text
    editlink = get_edit_link(request, pootle_file, item)
    transdict = {"editlink": editlink}

    cansugg  = check_permission("suggest",  request)
    cantrans = check_permission("translate", request)
    ables = ""
    if cansugg: 
        ables = "suggestable " + ables
    if cantrans: 
        ables = "submitable "  + ables

    if len(trans) > 1:
        forms = []
        for pluralitem, pluraltext in enumerate(trans):
            form = {"title": _("Plural Form %d" % pluralitem), "n": pluralitem, "text": escapefunction(pluraltext)}
            editclass = ""
            if cantrans or cansugg: 
                editclass = ables+"edittrans"+str(item)+"p"+str(pluralitem)
            form["editclass"] = editclass

            forms.append(form)
        transdict["forms"] = forms
    elif trans:
        transdict["text"] = escapefunction(trans[0])
        editclass = ""
        if cantrans or cansugg: 
            editclass = ables+"edittrans"+str(item)
        transdict["editclass"] = editclass

    else:
        # Error, problem with plurals perhaps?
        transdict["text"] = ""
    return transdict

def get_trans_edit(request, pootle_file, item, trans):
    """returns a widget for editing the given item and translation"""
    transdict = {
        "rows": 5,
        "cols": 40,
        }
    if check_permission("translate", request) or check_permission("suggest", request):
        profile = get_profile(request.user)
        transdict = {
            "rows": profile.input_height,
            "cols": profile.input_width
            }
        focusbox = ""
        spellargs = {"standby_url": "spellingstandby.html", "js_url": "/js/spellui.js", "target_url": "spellcheck.html"}
        if len(trans) > 1:
            buttons = get_trans_buttons(request, pootle_file.translation_project, item, ["back", "skip", "copy", "suggest", "translate"])
            forms = []
            for pluralitem, pluraltext in enumerate(trans):
                pluralform = _("Plural Form %d" % pluralitem)
                pluraltext = escape_for_textarea(pluraltext)
                textid = "trans%d-%d" % (item, pluralitem)
                forms.append({"title": pluralform, "name": textid, "text": pluraltext, "n": pluralitem})
                if not focusbox:
                    focusbox = textid
            transdict["forms"] = forms
        elif trans:
            buttons = get_trans_buttons(request, pootle_file.translation_project, item, ["back", "skip", "copy", "suggest", "translate"])
            transdict["text"] = escape_for_textarea(trans[0])
            textid = "trans%d" % item
            focusbox = textid
        else:
            # Perhaps there is no plural information available
            buttons = get_trans_buttons(request, pootle_file.translation_project, item, ["back", "skip"])
            # l10n: This is an error message that will display if the relevant problem occurs
            transdict["text"] = escape_for_textarea(_("Translation not possible because plural information for your language is not available. Please contact the site administrator."))
            textid = "trans%d" % item
            focusbox = textid

        transdict["can_spell"] = False
        transdict["spell_args"] = spellargs
        transdict["buttons"] = buttons
        transdict["focusbox"] = focusbox
    else:
        # TODO: work out how to handle this (move it up?)
        transdict.update(get_trans_view(request, pootle_file, item, trans, textarea=True))
        buttons = get_trans_buttons(request, pootle_file.translation_project, item, ["back", "skip"])
    transdict["buttons"] = buttons
    return transdict

def highlight_diffs(text, diffs, issrc=True):
    """highlights the differences in diffs in the text.
    diffs should be list of diff opcodes
    issrc specifies whether to use the src or destination positions in reconstructing the text
    this escapes the text on the fly to prevent confusion in escaping the highlighting"""
    if issrc:
        diffstart = [(i1, 'start', tag) for (tag, i1, i2, j1, j2) in diffs if tag != 'equal']
        diffstop  = [(i2, 'stop', tag) for (tag, i1, i2, j1, j2) in diffs if tag != 'equal']
    else:
        diffstart = [(j1, 'start', tag) for (tag, i1, i2, j1, j2) in diffs if tag != 'equal']
        diffstop  = [(j2, 'stop', tag) for (tag, i1, i2, j1, j2) in diffs if tag != 'equal']
    diffswitches = diffstart + diffstop
    diffswitches.sort()
    textdiff = ""
    textnest = 0
    textpos = 0
    spanempty = False
    for i, switch, tag in diffswitches:
        textsection = escape_text(text[textpos:i])
        textdiff += textsection
        if textsection:
            spanempty = False
        if switch == 'start':
            textnest += 1
        elif switch == 'stop':
            textnest -= 1
        if switch == 'start' and textnest == 1:
            # start of a textition
            textdiff += "<span class='translate-diff-%s'>" % tag
            spanempty = True
        elif switch == 'stop' and textnest == 0:
            # start of an equals block
            if spanempty:
                # FIXME: work out why kid swallows empty spans, and browsers display them horribly, then remove this
                textdiff += "()"
            textdiff += "</span>"
        textpos = i
    textdiff += escape_text(text[textpos:])
    return textdiff

def get_diff_codes(cmp1, cmp2):
    """compares the two strings and returns opcodes"""
    return difflib.SequenceMatcher(None, cmp1, cmp2).get_opcodes()

def get_trans_review(request, pootle_file, item, trans, suggestions):
    """returns a widget for reviewing the given item's suggestions"""
    hasplurals = len(trans) > 1
    diffcodes = {}
    for pluralitem, pluraltrans in enumerate(trans):
        if isinstance(pluraltrans, str):
            trans[pluralitem] = pluraltrans.decode("utf-8")
    for suggestion in suggestions:
        for pluralitem, pluralsugg in enumerate(suggestion):
            if isinstance(pluralsugg, str):
                suggestion[pluralitem] = pluralsugg.decode("utf-8")
    forms = []
    for pluralitem, pluraltrans in enumerate(trans):
        pluraldiffcodes = [get_diff_codes(pluraltrans, suggestion[pluralitem]) for suggestion in suggestions]
        diffcodes[pluralitem] = pluraldiffcodes
        combineddiffs = reduce(list.__add__, pluraldiffcodes, [])
        transdiff = highlight_diffs(pluraltrans, combineddiffs, issrc=True)
        form = {"n": pluralitem, "diff": transdiff, "title": None}
        if hasplurals:
            pluralform = _("Plural Form %d" % pluralitem)
            form["title"] = pluralform
        forms.append(form)
    transdict = {
        "current_title": _("Current Translation:"),
        "editlink":      get_edit_link(request, pootle_file, item),
        "forms":         forms,
        "isplural":      hasplurals or None,
        "itemid":        "trans%d" % item,
        }
    suggitems = []
    for suggid, msgstr in enumerate(suggestions):
        suggestedby = pootle_file.getsuggester(item, suggid)
        if len(suggestions) > 1:
            if suggestedby:
                # l10n: First parameter: number
                # l10n: Second parameter: name of translator
                suggtitle = _("Suggestion %d by %s:" % ((suggid+1), suggestedby))
            else:
                suggtitle = _("Suggestion %d:" % (suggid+1))
        else:
            if suggestedby:
                # l10n: parameter: name of translator
                suggtitle = _("Suggestion by %s:" % suggestedby)
            else:
                suggtitle = _("Suggestion:")
        forms = []
        for pluralitem, pluraltrans in enumerate(trans):
            pluralsuggestion = msgstr[pluralitem]
            suggdiffcodes = diffcodes[pluralitem][suggid]
            suggdiff = highlight_diffs(pluralsuggestion, suggdiffcodes, issrc=False)
            if isinstance(pluralsuggestion, str):
                pluralsuggestion = pluralsuggestion.decode("utf8")
            form = {"diff": suggdiff}
            form["suggid"] = "suggest%d-%d-%d" % (item, suggid, pluralitem)
            form["value"] = pluralsuggestion
            if hasplurals:
                form["title"] = _("Plural Form %d" % pluralitem)
            forms.append(form)
        suggdict = {
            "title":     suggtitle,
            "author":    suggestedby,
            "forms":     forms,
            "suggid":    "%d-%d" % (item, suggid),
            "canreview": check_permission("review", request),
            "back":      None,
            "skip":      None,
            }
        suggitems.append(suggdict)
    # l10n: verb
    backbutton = {"item": item, "text": _("Back")}
    skipbutton = {"item": item, "text": _("Skip")}
    if suggitems:
        suggitems[-1]["back"] = backbutton
        suggitems[-1]["skip"] = skipbutton
    else:
        transdict["back"] = backbutton
        transdict["skip"] = skipbutton
    transdict["suggestions"] = suggitems
    return transdict

def get_translated_directory(target_language_code, root_directory, directory):
    if directory.parent != root_directory:
        translated_directory = get_translated_directory(target_language_code,
                                                        root_directory,
                                                        directory.parent)
        return translated_directory.child_dirs.get(name=directory.name)
    else:
        return root_directory.child_dirs.get(name=target_language_code)

def get_translated_store(target_language, pootle_file):
    try:
        translation_directory = get_translated_directory(target_language.code,
                                                     Directory.objects.root,
                                                     pootle_file.store.parent)
        try:
            return translation_directory.child_stores.get(name=pootle_file.store.name)
        except Store.DoesNotExist:
            return None
    except Directory.DoesNotExist:
        return None

def get_alt_src_dict(request, pootle_file, unit, url_state, alt_project):
    def translate_unit(translated_pootle_file):
        translated_unit = translated_pootle_file.id_index[unit.getid()]
        if unit.hasplural():
            return {
                "forms":     [{"title": _("Plural Form %d") % i,
                               "n":     i,
                               "text":  escape_text(text)}
                              for i, text in enumerate(translated_unit.target.strings)],
                "isplural":  True }
        else:
            return {
                "text":      escape_text(translated_unit.target),
                "isplural":  False }

    alt_src_dict = {"available": False}
    # TODO: handle plurals !!
    if alt_project is not None:
        language = alt_project.language
        alt_src_dict.update({
                "languagename": language.fullname,
                "languagecode": language.code,
                "dir":          pagelayout.languagedir(language.code),
                "title":        tr_lang(language.fullname),
                "available":    True })
        translated_store = get_translated_store(language, pootle_file)
        if translated_store is not None:
            alt_src_dict.update(
                pootlefile.with_store(request.translation_project,
                                      translated_store,
                                      translate_unit))
        else:
            alt_src_dict["available"] = False
    return alt_src_dict

def get_alt_src_list(request, pootle_file, unit, url_state):
    return [get_alt_src_dict(request, pootle_file, unit, url_state, alt_project)
            for alt_project in get_alt_projects(request, pootle_file)]

def make_table(request, profile, pootle_file, url_state):
    editable, first_item, translations = get_translations(profile, pootle_file, url_state)
    item = url_state['position'].item
    items = []
    suggestions = {}
    if (url_state['translate_display'].view_mode in ('review', 'translate')):
        suggestions = {item: pootle_file.getsuggestions(item)}
    for row, unit in enumerate(translations):
        tmsuggestions = []
        orig = get_string_array(unit.source)
        trans = ensure_trans_plurals(pootle_file, orig, get_string_array(unit.target))
        item = first_item + row
        origdict = getorigdict(item, orig, item == editable)
        transmerge = {}
        suggestions[item] = pootle_file.getsuggestions(item)

        message_context = ""
        if item == editable:
            translator_comments = unit.getnotes(origin="translator")
            developer_comments = urlize(escape_text(unit.getnotes(origin="developer"), stripescapes=True))
            locations = " ".join(unit.getlocations())
            if isinstance(unit, po.pounit):
                message_context = "".join(unit.getcontext())
            tmsuggestions = pootle_file.gettmsuggestions(item)
            tmsuggestions.extend(get_terminology(pootle_file, item))
            transmerge = get_trans_edit(request, pootle_file, item, trans)
        else:
            translator_comments = unit.getnotes(origin="translator")
            developer_comments = unit.getnotes(origin="developer")
            locations = ""
            transmerge = get_trans_view(request, pootle_file, item, trans)

        itemsuggestions = []
        for suggestion in suggestions[item]:
            if suggestion.hasplural():
                itemsuggestions.append(suggestion.target.strings)
            else:
                itemsuggestions.append([suggestion.target])
        transreview = get_trans_review(request, pootle_file, item, trans, itemsuggestions)
        if 'forms' in transmerge.keys():
            for fnum in range(len(transmerge['forms'])):
                transreview['forms'][fnum].update(transmerge['forms'][fnum])
        elif 'text' in transmerge.keys():
            transreview['forms'][0]['text'] = transmerge['text']

        transmerge.update(transreview)

        transdict = {
            "itemid":      "trans%d" % item,
            "focus_class": origdict["focus_class"],
            "isplural":    len(trans) > 1,
            }
        transdict.update(transmerge)
        polarity = oddoreven(item)
        if item == editable:
            focus_class = "translate-focus"
        else:
            focus_class = ""

        state_class = ""
        fuzzy = None
        if unit.isfuzzy():
            state_class += "translate-translation-fuzzy"
            fuzzy = "checked"

        hassuggestion = len(transdict.get("suggestions", {})) > 0

        itemdict = {
            "itemid":              item,
            "orig":                origdict,
            "trans":               transdict,
            "polarity":            polarity,
            "focus_class":         focus_class,
            "editable":            item == editable,
            "state_class":         state_class,
            "fuzzy":               fuzzy,
            "translator_comments": translator_comments,
            "developer_comments":  developer_comments,
            "locations":           locations,
            "message_context":     message_context,
            "tm":                  tmsuggestions,
            "hassuggestion":       hassuggestion
            }

        itemdict["altsrcs"] = []
        # do we have enabled alternative source language?
        if settings.ENABLE_ALT_SRC:
            # get alternate source project information in a dictionary
            if item == editable:
                itemdict["altsrcs"] = get_alt_src_list(request, pootle_file, unit, url_state)

        items.append(itemdict)
    return items, translations, first_item

keymatcher = re.compile("(\D+)([0-9.]+)")

def parsekey(key):
    match = keymatcher.match(key)
    if match:
        keytype, itemcode = match.groups()
        return keytype, itemcode
    return None, None

def dashsplit(item):
    dashcount = item.count("-")
    if dashcount == 2:
        item, dashitem, subdashitem = item.split("-", 2)
        return int(item), int(dashitem), int(subdashitem)
    elif dashcount == 1:
        item, dashitem = item.split("-", 1)
        return int(item), int(dashitem), None
    else:
        return int(item), None, None

def handle_skips(last_item, skips):
    for item in skips:
        last_item = item
    return last_item

def handle_backs(last_item, backs):
    for item in backs:
        last_item = item
    return last_item

def handle_suggestions(last_item, request, pootle_file, submitsuggests, skips, translations):
    for item in submitsuggests:
        if item in skips or item not in translations:
            continue
        value = translations[item]
        unit_update.suggest_translation(pootle_file, item, value, request)
        last_item = item
    return last_item

def handle_submits(last_item, request, pootle_file, submits, skips, translations, comments, fuzzies):
    for item in submits:
        if item in skips or item not in translations:
            continue

        newvalues = {}
        newvalues["target"] = translations[item]
        if isinstance(newvalues["target"], dict) and len(newvalues["target"]) == 1 and 0 in newvalues["target"]:
            newvalues["target"] = newvalues["target"][0]

        newvalues["fuzzy"] = False
        if (fuzzies.get(item) == u'on'):
            newvalues["fuzzy"] = True

        translator_comments = comments.get(item)
        if translator_comments:
            newvalues["translator_comments"] = translator_comments

        unit_update.update_translation(pootle_file, item, newvalues, request)
        last_item = item
    return last_item

def handle_rejects(last_item, pootle_file, rejects, skips, translations, suggestions):
    # Make sure we have rejects list properly sorted
    rejects.sort(key=operator.itemgetter(1))
    # It's necessary to loop the list reversed in order to selectively remove items
    for item, suggid in reversed(rejects):
        value = suggestions[item, suggid]
        if isinstance(value, dict) and len(value) == 1 and 0 in value:
            value = value[0]
        unit_update.reject_suggestion(pootle_file, item, suggitem, newtrans, request)
        last_item = item
    return last_item

def handle_accepts(last_item, pootle_file, accepts, skips, translations, suggestions):
    for item, suggid in accepts:
        if (item, suggid) in rejects or (item, suggid) not in suggestions:
            continue
        value = suggestions[item, suggid]
        if isinstance(value, dict) and len(value) == 1 and 0 in value:
            value = value[0]
        unit_update.acceptsuggestion(pootle_file, item, suggitem, newtrans, request)
        last_item = item
    return last_item

def process_post(request, pootle_file):
    """receive any translations submitted by the user"""
    post_dict = request.POST.copy()
    backs = []
    skips = []
    submitsuggests = []
    submits = []
    accepts = []
    rejects = []
    translations = {}
    suggestions = {}
    comments = {}
    fuzzies = {}
    delkeys = []
    for key, value in post_dict.iteritems():
        keytype, item = parsekey(key)
        if keytype is None:
            continue
        item, dashitem, subdashitem = dashsplit(item)
        if keytype == "skip":
            skips.append(item)
        elif keytype == "back":
            backs.append(item)
        elif keytype == "submitsuggest":
            submitsuggests.append(item)
        elif keytype == "submit":
            submits.append(item)
        elif keytype == "accept":
            accepts.append((item, dashitem))
        elif keytype == "reject":
            rejects.append((item, dashitem))
        elif keytype == "translator_comments":
            # We need to remove carriage returns from the input.
            value = value.replace("\r", "")
            comments[item] = value
        elif keytype == "fuzzy":
            fuzzies[item] = value
        elif keytype == "trans":
            value = unescape_submition(value)
            if dashitem is not None:
                translations.setdefault(item, {})[dashitem] = value
            else:
                translations[item] = value
        elif keytype == "suggest":
            suggestions.setdefault((item, dashitem), {})[subdashitem] = value
        elif keytype == "orig-pure":
            # this is just to remove the hidden fields from the argdict
            pass
        else:
            continue
        delkeys.append(key)

    for key in delkeys:
        del post_dict[key]

    prev_last_item = handle_backs(-1, backs)
    last_item = handle_skips(-1, skips)
    last_item = handle_suggestions(last_item, request, pootle_file, submitsuggests, skips, translations)
    last_item = handle_submits(last_item, request, pootle_file, submits, skips, translations, comments, fuzzies)
    last_item = handle_rejects(last_item, pootle_file, rejects, skips, translations, suggestions)
    last_item = handle_accepts(last_item, pootle_file, accepts, skips, translations, suggestions)
    return prev_last_item, last_item

def process_post_main(store_name, item, request, next_store_item, prev_store_item):
    store = Store.objects.get(pootle_path=store_name)
    request.translation_project.indexer # Force initialization of the indexer
    prev_item, next_item = pootlefile.with_store(request.translation_project, store,
                                                 lambda pootle_file: process_post(request, pootle_file))
    if next_item > -1:
        return next_store_item(store_name, next_item + 1)
    elif prev_item > -1:
        return prev_store_item(store_name, prev_item - 1)
    else:
        return store, item

def get_position(store_name, item, request, next_store_item, prev_store_item):
    if request.method == 'POST':
        return process_post_main(store_name, item, request, next_store_item, prev_store_item)
    else:
        return next_store_item(store_name, item)

def get_failure_message(url_state):
    if url_state['position'].store is None:
        return _("No file matched your query")
    else:
        return _("End of results")

def find_and_display(request, directory, next_store_item, prev_store_item):
    url_state = read_all_state(request.GET)
    try:
        store, item = get_position(url_state['position'].store, url_state['position'].item,
                                   request, next_store_item, prev_store_item)
        url_state['position'].store = store.pootle_path
        url_state['position'].item  = item
        return pootlefile.with_store(request.translation_project, store,
                                     lambda pootle_file: view(request, directory, pootle_file, url_state))
    except StopIteration:
        return view(request, directory, None, url_state, get_failure_message(url_state))

def view(request, directory, pootle_file, url_state, stopped_by=None):
    """the page which lets people edit translations"""
    if not check_permission("view", request):
        # raise projects.Rights404Error(None)
        # TBD: Raise an exception similar to Rights404Error
        raise permissions.PermissionError('No view rights')

    if pootle_file is not None:
        form_url_state = copy.deepcopy(url_state)
        del form_url_state['position'].item
        formaction = URL(request.path_info, form_url_state).as_relative(request.path_info)
        store_path = pootle_file.store.pootle_path
    else:
        formaction = ''
        store_path = ''
    if stopped_by is not None:
        notice = get_finished_text(request, stopped_by, url_state)
    else:
        notice = {}
    profile  = get_profile(request.user)
    translation_project = request.translation_project
    language = translation_project.language
    project  = translation_project.project
    if pootle_file is not None:
        items, translations, first_item = make_table(request, profile, pootle_file, url_state)
        navbar = navbar_dict.make_store_navbar_dict(request, pootle_file.store, url_state)
    else:
        items, translations, first_item = [], [], -1
        navbar = navbar_dict.make_store_navbar_dict(request, directory, url_state)
    # self.pofilename can change in search...
    mainstats = ""
    pagelinks = None
    rows, icon = get_rows_and_icon(profile, url_state)
    if pootle_file is not None:
        postats = pootle_file.store.get_quick_stats(translation_project.checker)
        untranslated, fuzzy = postats["total"] - postats["translated"], postats["fuzzy"]
        translated, total = postats["translated"], postats["total"]
        mainstats = _("%d/%d translated\n(%d untranslated, %d fuzzy)" % (translated, total, untranslated, fuzzy))
        pagelinks = get_page_links(request, pootle_file, rows, translations, first_item)

    # templatising
    templatename = "translatepage"
    instancetitle = N_(settings.TITLE)
    # l10n: first parameter: name of the installation (like "Pootle")
    # l10n: second parameter: project name
    # l10n: third parameter: target language
    # l10n: fourth parameter: file name
    language_data = {"code": pagelayout.weblanguage(language.code),
                     "name": language.fullname,
                     "dir":  pagelayout.languagedir(language.code)}
    stats = {"summary": mainstats,
             "checks":  [],
             "tracks":  [],
             "assigns": []}
    templatevars = {
        "pagetitle":                 _("%s: translating %s into %s: %s") % \
            (instancetitle, project.fullname, language.fullname, store_path),
        "project":                   {"code": project.code,
                                      "name": project.fullname},
        "language":                  language_data,
        "pofilename":                store_path,
        # navigation bar
        "navitems":                  [navbar],
        "pagelinks":                 pagelinks,
        # translation form
        "actionurl":                 formaction,
        "notice":                    notice,
        # l10n: Heading above the table column with the source language
        "original_title":            _("Original"),
        # l10n: Heading above the table column with the target language
        "translation_title":         _("Translation"),
        # l10n: Heading above the table column with the action for the current
        # translation unit
        "action_title":              _("Action"),
        "items":                     items,
        "reviewmode":                url_state['translate_display'].view_mode == 'review',
        "accept_title":              _("Accept suggestion"),
        "reject_title":              _("Reject suggestion"),
        "fuzzytext":                 _("Fuzzy"),
        # l10n: Ajax link for suggestions.    %s is the number of suggestions
        "viewsuggtext":              _("View Suggestions (%s)"),
        # l10n: Heading above the textarea for translator comments.
        "translator_comments_title": _("Translator comments"),
        # l10n: Heading above the comments extracted from the programing source code
        "developer_comments_title":  _("Developer comments"),
        # l10n: This heading refers to related translations and terminology
        "related_title":             _("Related"),
        # optional sections, will appear if these values are replaced
        "assign":                    None,
        # l10n: text next to search field
        'search':                    search_forms.get_search_form(request, url_state['search'].search_text),
        # general vars
        "instancetitle":             instancetitle,
        "permissions":               request.permissions,
        # l10n: Text displayed when an AJAX petition is being made
        "canedit":                   check_permission("suggest", request) or check_permission("translate", request),
        "ajax_status_text":          _("Working..."),
        # l10n: Text displayed in an alert box when an AJAX petition has failed
        "ajax_error":                _("Error: Something went wrong."),
        # l10n: Button label
        "accept_button":             _("Accept"),
        # l10n: Button label
        "reject_button":             _("Reject")
        }

    if url_state['translate_display'].show_assigns and check_permission("assign", request):
        templatevars["assign"] = get_assign_box()
    templatevars.update(add_file_links(request, url_state, pootle_file))
    return render_to_kid("translatepage.html", KidRequestContext(request, templatevars, bannerheight=81))
