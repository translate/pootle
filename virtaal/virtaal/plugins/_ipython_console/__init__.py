#!/usr/bin/env python

import gobject
import gtk
import pango
from gtk import gdk

from virtaal.controllers import BasePlugin

from ipython_view import *


class IPythonWindow(gtk.Window):
    """The window that will contain the console widget."""

    FONT = "Luxi Mono 10"

    # INITIALIZERS #
    def __init__(self, namespace={}, destroy_cb=None):
        super(IPythonWindow, self).__init__()
        self._setup_console()
        self.console.updateNamespace(namespace)

    def _setup_console(self):
        self.scrolled_win = gtk.ScrolledWindow()
        self.scrolled_win.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        self.console = IPythonView()
        self.console.modify_font(pango.FontDescription(self.FONT))
        self.console.set_wrap_mode(gtk.WRAP_CHAR)

        self.scrolled_win.add(self.console)
        self.add(self.scrolled_win)


class Plugin(BasePlugin):
    description = _("Run-time access to Virtaal's internals (for developers).")
    display_name = _('IPython Console')
    version = 0.1

    # INITIALIZERS #
    def __init__(self, internal_name, main_controller):
        self.internal_name = internal_name
        self.main_controller = main_controller

        self._init_plugin()

    def _init_plugin(self):
        self.window = None

        self._setup_key_bindings()
        self._setup_menu_item()

    def _setup_key_bindings(self):
        """Setup Gtk+ key bindings (accelerators)."""

        gtk.accel_map_add_entry("<Virtaal>/View/IPython Console", gtk.keysyms.y, gdk.CONTROL_MASK)

        self.accel_group = gtk.AccelGroup()
        self.accel_group.connect_by_path("<Virtaal>/View/IPython Console", self._on_menuitem_activated)

        self.main_controller.view.add_accel_group(self.accel_group)

    def _setup_menu_item(self):
        self.menu = self.main_controller.view.gui.get_widget('menu_view')
        self.menuitem = gtk.MenuItem(label=_('_IPython Console'))
        self.menuitem.show()
        self.menu.append(self.menuitem)

        accel_group = self.menu.get_accel_group()
        if accel_group is None:
            accel_group = self.accel_group
            self.menu.set_accel_group(self.accel_group)
        self.menuitem.set_accel_path("<Virtaal>/View/IPython Console")
        self.menu.set_accel_group(accel_group)

        self.menuitem.connect('activate', self._on_menuitem_activated)


    # METHODS #
    def show_console(self, *args):
        if not self.window:
            ns = {
                '__builtins__' : __builtins__,
                'mc': self.main_controller,
                'mv': self.main_controller.view,
                'sc': self.main_controller.store_controller,
                'sv': self.main_controller.store_controller.view,
                'uc': self.main_controller.unit_controller,
                'uv': self.main_controller.unit_controller.view,
                'src': self.main_controller.unit_controller.view.sources[0],
                'tgt': self.main_controller.unit_controller.view.targets[0],
            }

            self.window = IPythonWindow(namespace=ns, destroy_cb=self._on_console_destroyed)
            self.window.set_size_request(600, 400)
            self.window.set_title('Virtaal IPython Console')
            self.window.set_transient_for(self.main_controller.view.main_window)
            self.window.connect('destroy', self._on_console_destroyed)
        self.window.show_all()
        self.window.grab_focus()


    # EVENT HANDLERS #
    def _on_console_destroyed(self, *args):
        self.window = None

    def _on_menuitem_activated(self, *args):
        self.show_console()
