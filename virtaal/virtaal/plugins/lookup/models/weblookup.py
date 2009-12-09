#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
#
# This file is part of Virtaal.
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

import gtk
import pango
import urllib
from os import path

from virtaal.common import pan_app
from virtaal.views import BaseView

try:
    from virtaal.plugins.lookup.models.baselookupmodel import BaseLookupModel
except ImportError:
    from virtaal_plugins.lookup.models.baselookupmodel import BaseLookupModel


class LookupModel(BaseLookupModel):
    """Look-up the selected string on the web."""

    __gtype_name__ = 'WebLookupModel'
    #l10n: plugin name
    display_name = _('Web Look-up')
    description = _('Look-up the selected text on a web site')

    URLDATA = [
        {
            'display_name': _('Google'),
            'url': 'http://www.google.com/search?q=%(query)s',
            'quoted': True,
        },
        {
            'display_name': _('Wikipedia'),
            'url': 'http://%(querylang)s.wikipedia.org/wiki/%(query)s',
            'quoted': False,
        },
        {
            'display_name': _('Open-Tran.eu'),
            'url': 'http://%(querylang)s.%(nonquerylang)s.open-tran.eu/suggest/%(query)s',
            'quoted': True,
        },
    ]
    """A list of dictionaries containing data about each URL:
    * C{display_name}: The name that will be shown in the context menu
    * C{url}: The actual URL that will be queried. See below for template
        variables.
    * C{quoted}: Whether or not the query string should be put in quotes (").

    Valid template variables in 'url' fields are:
    * C{%(query)s}: The selected text that makes up the look-up query.
    * C{%(querylang)s}: The language of the query string (one of C{%(srclang)s}
        or C{%(tgtlang)s}).
    * C{%(nonquerylang)s}: The source- or target language which is B{not} the
        language that the query (selected text) is in.
    * C{%(srclang)s}: The currently selected source language.
    * C{%(tgtlang)s}: The currently selected target language.
    """

    # INITIALIZERS #
    def __init__(self, internal_name, controller):
        self.controller = controller
        self.internal_name = internal_name

        self.configure_func = self.configure
        self.urldata_file = path.join(pan_app.get_config_dir(), "weblookup.ini")

        self._load_urldata()

    def _load_urldata(self):
        urls = pan_app.load_config(self.urldata_file).values()
        if urls:
            for u in urls:
                if 'quoted' in u:
                    u['quoted'] = u['quoted'] == 'True'
            self.URLDATA = urls


    # METHODS #
    def configure(self, parent):
        configure_dialog = WebLookupConfigDialog(parent.get_toplevel())
        configure_dialog.urldata = self.URLDATA
        configure_dialog.run()
        self.URLDATA = configure_dialog.urldata
        #logging.debug('New URL data: %s' % (self.URLDATA))

    def create_menu_items(self, query, role, srclang, tgtlang):
        querylang = role == 'source' and srclang or tgtlang
        nonquerylang = role != 'source' and srclang or tgtlang
        query = urllib.quote(query)
        items = []
        for urlinfo in self.URLDATA:
            uquery = query
            if 'quoted' in urlinfo and urlinfo['quoted']:
                uquery = '"' + uquery + '"'

            i = gtk.MenuItem(urlinfo['display_name'])
            lookup_str = urlinfo['url'] % {
                'query':        uquery,
                'querylang':    querylang,
                'nonquerylang': nonquerylang,
                'srclang':      srclang,
                'tgtlang':      tgtlang
            }
            i.connect('activate', self._on_lookup, lookup_str)
            items.append(i)
        return items

    def destroy(self):
        config = dict([ (u['display_name'], u) for u in self.URLDATA ])
        pan_app.save_config(self.urldata_file, config)


    # SIGNAL HANDLERS #
    def _on_lookup(self, menuitem, url):
        from virtaal.support.openmailto import open
        open(url)


class WebLookupConfigDialog(object):
    """Dialog manages the URLs used by the web look-up plug-in."""

    COL_NAME, COL_URL, COL_QUOTE, COL_DATA = range(4)

    # INITIALIZERS #
    def __init__(self, parent):
        self.gladefilename, self.gui = BaseView.load_glade_file(
            ["virtaal", "virtaal.glade"],
            root='WebLookupManager',
            domain='virtaal'
        )

        self._get_widgets()
        if isinstance(parent, gtk.Widget):
            self.dialog.set_transient_for(parent)
            self.dialog.set_icon(parent.get_toplevel().get_icon())

        self._init_widgets()
        self._init_treeview()

    def _get_widgets(self):
        widget_names = ('btn_url_add', 'btn_url_remove', 'tvw_urls')

        for name in widget_names:
            setattr(self, name, self.gui.get_widget(name))

        self.dialog = self.gui.get_widget('WebLookupManager')
        self.add_dialog = WebLookupAddDialog(self.dialog)

    def _init_treeview(self):
        self.lst_urls = gtk.ListStore(str, str, bool, object)
        self.tvw_urls.set_model(self.lst_urls)

        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_('Name'))
        col.pack_start(cell)
        col.add_attribute(cell, 'text', self.COL_NAME)
        col.props.resizable = True
        col.set_sort_column_id(0)
        self.tvw_urls.append_column(col)

        cell = gtk.CellRendererText()
        cell.props.ellipsize = pango.ELLIPSIZE_MIDDLE
        col = gtk.TreeViewColumn(_('URL'))
        col.pack_start(cell)
        col.add_attribute(cell, 'text', self.COL_URL)
        col.props.resizable = True
        col.set_expand(True)
        col.set_sort_column_id(1)
        self.tvw_urls.append_column(col)

        cell = gtk.CellRendererToggle()
        cell.set_radio(False)
        #l10n: Whether the selected text should be surrounded by "quotes"
        col = gtk.TreeViewColumn(_('Quote Query'))
        col.pack_start(cell)
        col.add_attribute(cell, 'active', self.COL_QUOTE)
        self.tvw_urls.append_column(col)

    def _init_widgets(self):
        self.btn_url_add.connect('clicked', self._on_add_clicked)
        self.btn_url_remove.connect('clicked', self._on_remove_clicked)


    # ACCESSORS #
    def _get_urldata(self):
        return [row[self.COL_DATA] for row in self.lst_urls]
    def _set_urldata(self, value):
        self.lst_urls.clear()
        for url in value:
            self.lst_urls.append((url['display_name'], url['url'], url['quoted'], url))
    urldata = property(_get_urldata, _set_urldata)


    # METHODS #
    def run(self, parent=None):
        if isinstance(parent, gtk.Widget):
            self.dialog.set_transient_for(parent)

        self.dialog.show()
        self.dialog.run()
        self.dialog.hide()


    # SIGNAL HANDLERS #
    def _on_add_clicked(self, button):
        url = self.add_dialog.run()
        if url is None:
            return
        self.lst_urls.append((url['display_name'], url['url'], url['quoted'], url))

    def _on_remove_clicked(self, button):
        selected = self.tvw_urls.get_selection().get_selected()
        if not selected or not selected[1]:
            return
        selected[0].remove(selected[1])


class WebLookupAddDialog(object):
    """The dialog used to add URLs for the web look-up plug-in."""

    # INITIALIZERS #
    def __init__(self, parent):
        self.gladefilename, self.gui = BaseView.load_glade_file(
            ["virtaal", "virtaal.glade"],
            root='WebLookupAdd',
            domain='virtaal'
        )
        self._get_widgets()

        if isinstance(parent, gtk.Window):
            self.dialog.set_transient_for(parent)
            self.dialog.set_icon(parent.get_toplevel().get_icon())

    def _get_widgets(self):
        widget_names = ('btn_url_cancel', 'btn_url_ok', 'cbtn_url_quote', 'ent_url_name', 'ent_url')

        for name in widget_names:
            setattr(self, name, self.gui.get_widget(name))

        self.dialog = self.gui.get_widget('WebLookupAdd')


    # METHODS #
    def run(self):
        self.ent_url.set_text('')
        self.ent_url_name.set_text('')
        self.cbtn_url_quote.set_active(False)

        self.dialog.show()
        response = self.dialog.run()
        self.dialog.hide()

        if response != gtk.RESPONSE_OK:
            return None

        self.url = {
            'display_name':   self.ent_url_name.get_text(),
            'url':            self.ent_url.get_text(),
            'quoted':         self.cbtn_url_quote.get_active(),
        }
        return self.url
