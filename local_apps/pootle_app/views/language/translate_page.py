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
import os

from django.utils.html import urlize
from django.utils.translation import ugettext as _
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext

from translate.storage import po
from translate.misc.multistring import multistring

from pootle_app.views import pagelayout
from pootle_app.models import TranslationProject, Directory
from pootle_store.models import Store
from pootle_app.models.profile import get_profile
from pootle_app import unit_update, url_manip
from pootle_app.models import permissions
from pootle_app.models.permissions import check_permission

from pootle.i18n.gettext import tr_lang, language_dir

import dispatch, navbar_dict, search_forms

xml_re = re.compile("&lt;.*?&gt;")

def oddoreven(polarity):
    if polarity % 2 == 0:
        return "even"
    elif polarity % 2 == 1:
        return "odd"

def get_alt_projects(request, store):
    # do we have enabled alternative source language?
    if settings.ENABLE_ALT_SRC:
        # try to get the project if the user has chosen an alternate source language
        return TranslationProject.objects.filter(language__in=get_profile(request.user).alt_src_langs.all(),
                                                 project=request.translation_project.project_id)
    else:
        return TranslationProject.objects.none()

def add_file_links(request, store):
    """adds a section on the current file, including any checks happening"""
    state = dispatch.TranslatePageState(request.GET)
    template_vars = {}
    if store is not None:
        if len(state.match_names) > 0:
            checknames = \
            ["<a href='http://translate.sourceforge.net/wiki/toolkit/pofilter_tests#%(checkname)s' \
            title='%(checkname)s' target='_blank'>%(checkname)s</a>" % \
            {"checkname": matchname.replace("check-", "", 1)} for matchname in state.match_names]
            # TODO: put the following parameter in quotes, since it will be foreign in all target languages
            # l10n: the parameter is the name of one of the quality checks, like "fuzzy"
            template_vars["checking_text"] = _("checking %s", ", ".join(checknames))
    return template_vars

def get_rows_and_icon(request, profile):
    state = dispatch.TranslatePageState(request.GET)
    if state.view_mode == 'view':
        return get_display_rows(profile), "file"
    else:
        return get_display_rows(profile), "edit"

def get_finished_text(request, stoppedby):
    """gets notice to display when the translation is finished"""
    # l10n: "batch" refers to the set of translations that were reviewed
    return {"title":        _("End of batch"),
            "stoppedby":    stoppedby,
            "finishedlink": dispatch.show_directory(request, url_manip.parent(request.path_info)),
            "returnlink":   _("Click here to return to the index")}

def get_page_links(request, store, pagesize, translations, item, first_item):
    """gets links to other pages of items, based on the given baselink"""

    pagelinks = []
    pofilelen = store.file.getitemslen()

    if pofilelen <= pagesize or item is None:
        return pagelinks

    lastitem = min(pofilelen - 1, first_item + pagesize - 1)
    if pofilelen > pagesize and not item == 0:
        # l10n: noun (the start)
        pagelinks.append({"href": dispatch.translate(request, request.path_info, item=0),
                          "text": _("Start")})
    if item > 0:
        linkitem = max(item - pagesize, 0)
        # l10n: the parameter refers to the number of messages
        pagelinks.append({"href": dispatch.translate(request, request.path_info, item=linkitem),
                          "text": _("Previous %d", (item - linkitem))})

    # l10n: the third parameter refers to the total number of messages in the file
    pagelinks.append({"text": _("Items %(first)d to %(last)d of %(total)d",
                                {"first": first_item + 1, "last": lastitem + 1, "total": pofilelen})
                      })

    if item + len(translations) < pofilelen:
        linkitem = item + pagesize
        itemcount = min(pofilelen - linkitem, pagesize)
        # l10n: the parameter refers to the number of messages
        pagelinks.append({"href": dispatch.translate(request, request.path_info, item=linkitem),
                          "text": _("Next %d", itemcount)})

    if pofilelen > pagesize and (item + pagesize) < pofilelen:
        # l10n: noun (the end)
        pagelinks.append({"href": dispatch.translate(request, request.path_info,
                                                     item=max(pofilelen - 1, 0)),
                          "text": _("End")})

    for n, pagelink in enumerate(pagelinks):
        if n < len(pagelinks)-1:
            pagelink["sep"] = " | "
        else:
            pagelink["sep"] = ""
    return pagelinks


def get_display_rows(profile):
    """get the number of rows to display"""
    rowsdesired = profile.unit_rows
    maximum = 30
    return min(rowsdesired, maximum)

def get_units(store, item_start, item_stop):
    return [store.file.store.units[index] for index in store.file.total[max(item_start,0):item_stop]]

def get_translations(request, profile, store, item):
    """gets the list of translations desired for the view, and sets editable and firstitem parameters"""
    state = dispatch.TranslatePageState(request.GET)
    if store is None:
        # editable, first item, items
        return -1, item, []
    elif state.view_mode == 'view':
        rows = get_display_rows(profile)
        return -1, item, get_units(store, item, item + rows)
    else:
        rows = get_display_rows(profile)
        before = rows / 2
        first_item = max(item - before, 0)
        last_item = first_item + rows
        pofilelen = store.file.getitemslen()
        if last_item > pofilelen:
            last_item = pofilelen
            first_item = max(last_item - rows, 0)
        items = get_units(store, first_item, last_item)
        return item, first_item, items

def get_header_plural(request, store):
    # get plural information from Language model
    nplurals = request.translation_project.language.nplurals
    plurals = request.translation_project.language.pluralequation

    try:
        # get plural information from Store
        snplurals, splurals = store.file.store.getheaderplural()
        if snplurals and snplurals.isdigit():
            # file has plural information
            #FIXME: should we check if file has correct language headers
            nplurals = int(snplurals)
            plurals = splurals
    except:
        # not a POHeader store
        pass

    return nplurals, plurals

def ensure_trans_plurals(request, store, orig, trans):
    nplurals, plurals = get_header_plural(request, store)
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
    if not text:
        return u""
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
    if not text:
        return u""
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

def get_terminology(request, store, item):
    try:
        term_matcher = request.translation_project.gettermmatcher()
        if term_matcher is not None:
            return term_matcher.matches(store.file.getitem(item).source)
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

def get_edit_link(request, store, item):
    """gets a link to edit the given item, if the user has permission"""
    if check_permission("translate", request) or check_permission("suggest", request):
        # l10n: verb
        return {"href": dispatch.translate(request, request.path_info,
                                           view_mode='translate', item=item, match_names=[]),
                "text": _("Edit"), "linkid": "editlink%d" % item}
    else:
        return {}

def get_trans_view(request, store, item, trans, textarea=False):
    """returns a widget for viewing the given item's translation"""
    if textarea:
        escapefunction = escape_for_textarea
    else:
        escapefunction = escape_text
    editlink = get_edit_link(request, store, item)
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
            form = {"title": _("Plural Form %d", pluralitem), "n": pluralitem, "text": escapefunction(pluraltext)}
            editclass = ""
            if cantrans or cansugg:
                # Some claim string concatenation is slow, so we rewrite the
                # commented line as a single string with formatting:
                #editclass = ables + "edittrans" + str(item) + "p" + str(pluralitem)
                editclass = "%sedittrans%sp%s" % (ables, str(item), str(pluralitem))
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

def get_trans_edit(request, store, item, trans):
    """returns a widget for editing the given item and translation"""
    transdict = { "rows": 5 }
    if check_permission("translate", request) or check_permission("suggest", request):
        profile = get_profile(request.user)
        transdict = { "rows": profile.input_height }
        focusbox = ""
        if len(trans) > 1:
            buttons = get_trans_buttons(request, request.translation_project, item, ["translate", "suggest", "copy", "skip", "back"])
            forms = []
            for pluralitem, pluraltext in enumerate(trans):
                pluralform = _("Plural Form %d", pluralitem)
                pluraltext = escape_for_textarea(pluraltext)
                textid = "trans%d-%d" % (item, pluralitem)
                forms.append({"title": pluralform, "name": textid, "text": pluraltext, "n": pluralitem})
                if not focusbox:
                    focusbox = textid
            transdict["forms"] = forms
        elif trans:
            buttons = get_trans_buttons(request, request.translation_project, item, ["translate", "suggest", "copy", "skip", "back"])
            transdict["text"] = escape_for_textarea(trans[0])
            textid = "trans%d" % item
            focusbox = textid
        else:
            # Perhaps there is no plural information available
            buttons = get_trans_buttons(request, request.translation_project, item, ["skip", "back"])
            # l10n: This is an error message that will display if the relevant problem occurs
            transdict["text"] = escape_for_textarea(_("Translation not possible because plural information for your language is not available. Please contact the site administrator."))
            textid = "trans%d" % item
            focusbox = textid

        transdict["buttons"] = buttons
        transdict["focusbox"] = focusbox
    else:
        # TODO: work out how to handle this (move it up?)
        transdict.update(get_trans_view(request, store, item, trans, textarea=True))
        buttons = get_trans_buttons(request, request.translation_project, item, ["skip", "back"])
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

def get_trans_review(request, store, item, trans, suggestions):
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
            pluralform = _("Plural Form %d", pluralitem)
            form["title"] = pluralform
        forms.append(form)
    transdict = {
        "current_title": _("Current Translation:"),
        "editlink":      get_edit_link(request, store, item),
        "forms":         forms,
        "isplural":      hasplurals or None,
        "itemid":        "trans%d" % item,
        }
    suggitems = []
    for suggid, msgstr in enumerate(suggestions):
        suggestedby = store.getsuggester(item, suggid)
        if len(suggestions) > 1:
            if suggestedby:
                # l10n: First parameter: number
                # l10n: Second parameter: name of translator
                suggtitle = _("Suggestion %(suggid)d by %(user)s:", {"suggid": (suggid+1), "user": suggestedby})
            else:
                suggtitle = _("Suggestion %d:", (suggid+1))
        else:
            if suggestedby:
                # l10n: parameter: name of translator
                suggtitle = _("Suggestion by %s:", suggestedby)
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
                form["title"] = _("Plural Form %d", pluralitem)
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

def get_translated_store(alt_project, store):
    """returns the file corresponding to store in the alternative TranslationProject"""
    try:
        translation_directory = get_translated_directory(alt_project.language.code,
                                                     Directory.objects.root,
                                                     store.parent)
        if alt_project.project.get_treestyle() == 'gnu':
            name = alt_project.language.code + os.extsep + alt_project.project.localfiletype
        else:
            name = store.name
        try:
            return translation_directory.child_stores.get(name=name)
        except Store.DoesNotExist:
            return None
    except Directory.DoesNotExist:
        return None

def get_alt_src_dict(request, store, unit, alt_project):
    alt_src_dict = {"available": False}
    # TODO: handle plurals !!
    if alt_project is not None:
        #FIXME: we should bail out if alternative language == target language
        language = alt_project.language
        alt_src_dict.update({
                "languagename": language.fullname,
                "languagecode": language.code,
                "dir":          language_dir(language.code),
                "title":        tr_lang(language.fullname),
                "available":    True })
        translated_store = get_translated_store(alt_project, store)
        if translated_store is not None:
            #FIXME: we should bundle the makeindex thing into a property
            if not hasattr(translated_store.file.store, "sourceindex"):
                translated_store.file.store.makeindex()

            translated_unit = translated_store.file.store.findunit(unit.source)
            if translated_unit is not None and translated_unit.istranslated():
                if unit.hasplural():
                    unit_dict = {
                        "forms":     [{"title": _("Plural Form %d", i),
                                       "n":     i,
                                       "text":  escape_text(text)}
                                      for i, text in enumerate(translated_unit.target.strings)],
                        "isplural":  True }
                else:
                    unit_dict = {
                        "text":      escape_text(translated_unit.target),
                        "isplural":  False }

                alt_src_dict.update(unit_dict)
            else:
                alt_src_dict["available"] = False
        else:
            alt_src_dict["available"] = False
    return alt_src_dict

def get_alt_src_list(request, store, unit):
    return [get_alt_src_dict(request, store, unit, alt_project)
            for alt_project in get_alt_projects(request, store)]

def make_table(request, profile, store, item):
    editable, first_item, translations = get_translations(request, profile, store, item)
    state = dispatch.TranslatePageState(request.GET)
    items = []
    suggestions = {}
    if (state.view_mode in ('review', 'translate')):
        suggestions = {state.item: store.getsuggestions(state.item)}
    for row, unit in enumerate(translations):
        tmsuggestions = []
        orig = get_string_array(unit.source)
        trans = ensure_trans_plurals(request, store, orig, get_string_array(unit.target))
        item = first_item + row
        origdict = getorigdict(item, orig, item == editable)
        transmerge = {}
        suggestions[item] = store.getsuggestions(item)

        message_context = ""
        if item == editable:
            translator_comments = unit.getnotes(origin="translator")
            developer_comments = urlize(escape_text(unit.getnotes(origin="developer"), stripescapes=True))
            locations = " ".join(unit.getlocations())
            if isinstance(unit, po.pounit):
                message_context = "".join(unit.getcontext())
            tmsuggestions = store.gettmsuggestions(item)
            tmsuggestions.extend(get_terminology(request, store, item))
            transmerge = get_trans_edit(request, store, item, trans)
        else:
            translator_comments = unit.getnotes(origin="translator")
            developer_comments = unit.getnotes(origin="developer")
            locations = ""
            transmerge = get_trans_view(request, store, item, trans)

        itemsuggestions = []
        for suggestion in suggestions[item]:
            if suggestion.hasplural():
                itemsuggestions.append(suggestion.target.strings)
            else:
                itemsuggestions.append([suggestion.target])
        transreview = get_trans_review(request, store, item, trans, itemsuggestions)
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
                itemdict["altsrcs"] = get_alt_src_list(request, store, unit)

        items.append(itemdict)
    return items, translations, first_item

keymatcher = re.compile("(\D+)([0-9\-]+)")

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

def handle_suggestions(last_item, request, store, submitsuggests, skips, translations):
    for item in submitsuggests:
        if item in skips or item not in translations:
            continue
        value = translations[item]
        unit_update.suggest_translation(store, item, value, request)
        last_item = item
    return last_item

def handle_submits(last_item, request, store, submits, skips, translations, comments, fuzzies):
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

        unit_update.update_translation(store, item, newvalues, request)
        last_item = item
    return last_item


def process_post(request, store):
    """receive any translations submitted by the user"""
    post_dict = request.POST.copy()
    backs = []
    skips = []
    submitsuggests = []
    submits = []
    translations = {}
    suggestions = {}
    comments = {}
    fuzzies = {}
    delkeys = []
    for key, value in post_dict.iteritems():
        keytype, item = parsekey(key)
        if keytype is None:
            continue
        try:
            item, dashitem, subdashitem = dashsplit(item)
        except:
            continue
        if keytype == "skip":
            skips.append(item)
        elif keytype == "back":
            backs.append(item)
        elif keytype == "submitsuggest":
            submitsuggests.append(item)
        elif keytype == "submit":
            submits.append(item)
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
    last_item = handle_suggestions(last_item, request, store, submitsuggests, skips, translations)
    last_item = handle_submits(last_item, request, store, submits, skips, translations, comments, fuzzies)
    return prev_last_item, last_item

def process_post_main(store_name, item, request, next_store_item, prev_store_item):
    store = Store.objects.get(pootle_path=store_name)
    request.translation_project.indexer # Force initialization of the indexer
    prev_item, next_item = process_post(request, store)

    search = search_forms.search_from_request(request)
    if next_item > -1:
        return next_store_item(search, store_name, next_item + 1)
    elif prev_item > -1:
        return prev_store_item(search, store_name, prev_item - 1)
    else:
        return store, item

def get_position(request, next_store_item, prev_store_item):
    state      = dispatch.TranslatePageState(request.GET)
    store_name = dispatch.get_store(request)
    item       = state.item
    if request.method == 'POST':
        if 'new_search' in request.POST:
            return next_store_item(search_forms.search_from_request(request), store_name, item)
        else:
            return process_post_main(store_name, item, request, next_store_item, prev_store_item)
    else:
        return next_store_item(search_forms.search_from_request(request), store_name, item)

def get_failure_message(request):
    if 'store' not in request.GET:
        return _("No file matched your query")
    else:
        return _("End of results")

def find_and_display(request, directory, next_store_item, prev_store_item):
    try:
        store, item = get_position(request, next_store_item, prev_store_item)
        return view(request, directory, store, item)
    except StopIteration:
        return view(request, directory, None, 0, get_failure_message(request))

def view(request, directory, store, item, stopped_by=None):
    """the page which lets people edit translations"""
    state = dispatch.TranslatePageState(request.GET)
    if not check_permission("view", request):
        # raise projects.Rights404Error(None)
        # TBD: Raise an exception similar to Rights404Error
        raise permissions.PermissionError('No view rights')

    if store is not None:
        formaction = dispatch.translate(request, request.path_info, store=store.pootle_path ,item=0)
        store_path = store.pootle_path
    else:
        formaction = ''
        store_path = ''
    if stopped_by is not None:
        notice = get_finished_text(request, stopped_by)
    else:
        notice = {}
    profile  = get_profile(request.user)
    translation_project = request.translation_project
    language = translation_project.language
    project  = translation_project.project
    if store is not None:
        items, translations, first_item = make_table(request, profile, store, item)
        navbar = navbar_dict.make_store_navbar_dict(request, store)
    else:
        items, translations, first_item = [], [], -1
        navbar = navbar_dict.make_directory_navbar_dict(request, directory, links_required='translate')
    # self.pofilename can change in search...
    mainstats = ""
    pagelinks = None
    rows, icon = get_rows_and_icon(request, profile)
    navbar["icon"] = icon
    if store is not None:
        postats = store.getquickstats()
        untranslated, fuzzy = postats["total"] - postats["translated"], postats["fuzzy"]
        translated, total = postats["translated"], postats["total"]
        mainstats = _("%(translated)d/%(total)d translated\n(%(untranslated)d untranslated, %(fuzzy)d fuzzy)",
                      {
                          "translated": translated,
                          "total": total,
                          "untranslated": untranslated,
                          "fuzzy": fuzzy,
                       }
        )
        pagelinks = get_page_links(request, store, rows, translations, item, first_item)

    # templatising
    templatename = "language/translatepage.html"
    instancetitle = _(settings.TITLE)
    # l10n: first parameter: name of the installation (like "Pootle")
    # l10n: second parameter: project name
    # l10n: third parameter: target language
    # l10n: fourth parameter: file name
    language_data = {"code": pagelayout.weblanguage(language.code),
                     "name": language.fullname,
                     "dir":  language_dir(language.code)}
    stats = {"summary": mainstats,
             "checks":  [],
             "tracks":  [],
             }
    templatevars = {
        "title_path":                store_path,
        "project":                   {"code": project.code,
                                      "name": project.fullname},
        "language":                  language_data,
        "store":                store_path,
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
        "reviewmode":                state.view_mode == 'review',
        "accept_title":              _("Accept suggestion"),
        "reject_title":              _("Reject suggestion"),
        "fuzzytext":                 _("Fuzzy"),
        # l10n: Ajax link for suggestions.    %s is the number of suggestions
        "viewsuggtext":              _("View Suggestions"),
        # l10n: Heading above the textarea for translator comments.
        "translator_comments_title": _("Translator Comments"),
        # l10n: Heading above the comments extracted from the programing source code
        "developer_comments_title":  _("Developer Comments"),
        # l10n: This heading refers to related translations and terminology
        "related_title":             _("Related"),
        # l10n: text next to search field
        'search':                    search_forms.get_search_form(request),
        # general vars
        "instancetitle":             instancetitle,
        "permissions":               request.permissions,
        # l10n: Text displayed when an AJAX petition is being made
        "canedit":                   check_permission("translate", request) or check_permission("suggest", request),
        "cantranslate":              check_permission("translate", request),
        "cansuggest":                check_permission("suggest", request),
        # l10n: Button label
        "accept_button":             _("Accept"),
        # l10n: Button label
        "reject_button":             _("Reject")
        }

    templatevars.update(add_file_links(request, store))
    return render_to_response("language/translatepage.html", templatevars, RequestContext(request))
