#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
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

"""Support for user (administrator)-provided extension actions.

These are used by placing in an extension actions directory Python modules
that define subclasses of the base class ExtensionAction and create instances
of those subclasses.  Depending on their place in the inheritance hierarchy,
these instances will show up as user-visible links in the Actions sections of
various pages; when those links are followed, the run() method of the class
will be invoked to perform the action.

There can be multiple instances of a subclass, for example a download action
subclass might generate different archive formats (zip, tar, etc.) based on
the last part of the title for each instance.  Note that multiple instances
of a subclass will share the same tooltip (since it is the class docstring).

Besides multiple instances of a subclass, any extension action may be invoked
at several points in the Pootle page hierarchy, so that if there is need to
store data associated with those invocations using instance properties or
attributes, they should be structured as dictionaries keyed on the path in
the Pootle page hierarchy (pootle_path or path_obj).

Here's an ASCII art diagram of the class inheritance hierarchy:

                              +---------------+
                              |ExtensionAction|
                              +---------------+
                               ^ ^ ^ ^     ^ ^
    Tracked instance classes   | | | |     | |  Functional mixin classes
                               | | | |     | |
           +-------------+     | | | |     | |     +--------------+
           |ProjectAction|-----+ | | |     | +-----|DownloadAction|
           +-------------+       | | |     |       +--------------+
                                 | | |     |
          +--------------+       | | |     |       +-------------+
          |LanguageAction|-------+ | |     +-------|CommandAction|
          +--------------+         | |             +-------------+
                                   | |
+------------------------+         | |
|TranslationProjectAction|---------+ |
+------------------------+           |
          ^                          |
          |  +-----------+           |
          |  |StoreAction|-----------+
          |  +-----------+
          |     ^
          |     |
          |     |
       +-----------+
       |HelloAction|
       +-----------+

http://www.asciiflow.com/#6089174316691145678/854915636

"""

import logging
import os
import pkgutil
import shutil
import sys
from urllib import unquote_plus, urlencode

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext as _

from pootle_app.models.permissions import check_permission
from pootle_app.project_tree import ensure_target_dir_exists
from pootle_misc.baseurl import l
from pootle_store.util import absolute_real_path, relative_real_path

logger = logging.getLogger(__name__)

#: Module separator (period); this constant used to improve code readability
DOT = '.'

#: Subdirectory to scan for extension actions
EXTDIR = 'ext_actions'

#: Full (possibly relative) path of directory to scan for extension actions
_EXTPATH = os.path.join(os.path.dirname(__file__), EXTDIR)


def _getmod():
    """Get module (package) name and directory path for extension actions

    Uses __name__ for module name if it is useful (not '__main__').  Otherwise,
    use __loader__ if defined, and if that fails, try path searching for
    __file__ to try to guess the module name.  Fallback is to use the directory
    name as the "module" with all '.' replaced with ',' to try to avoid
    RuntimeWarning about missing parent module.

    :returns: Extension package (module) name
    :rtype: str

    """

    if __name__ != '__main__':
        i = __name__.rfind(DOT)
        if i > 0:
            dirmod = __name__[:i + 1] + EXTDIR
        else:
            dirmod = EXTDIR
    else:
        try:
            dirmod = DOT.join([__loader__.fullname,  # pylint: disable=E0602
                              EXTDIR])
        except NameError:
            if not _EXTPATH.startswith(os.sep):
                dirmod = _EXTPATH.replace(os.sep, DOT)
            else:
                # Find where __file__ may be loaded from (longest prefix first)
                for path in sorted(sys.path, key=len, reverse=True):
                    if (_EXTPATH.find(path) == 0 and
                            path.rstrip(os.sep) != _EXTPATH.rstrip(os.sep)):
                        dirmod = DOT.join(_EXTPATH[len(path):]
                                          .split(os.sep)).lstrip(DOT)
                        break
                else:
                    # can't find module, return _EXTPATH without any dots
                    return _EXTPATH.replace(DOT, ',')

    # __import__(dirmod) may be needed to suppress "RuntimeWarning: Parent
    # module ... not found" if imp.load_module() given name containing dot
    if dirmod not in sys.modules:
        try:
            __import__(dirmod)
        except ImportError:
            # Fake it out so that we don't try again
            sys.modules[dirmod] = None

    return dirmod + DOT

_EXTMOD = _getmod()


class ExtensionAction(object):
    """User (administrator)-provided actions for execution in Pootle UI

    .. class:: ExtensionAction(category, title, **kwargs)

    This is an (abstract) base class for all extension actions; creating an
    instance of this class will not display any actions in the UI.  It exists
    to provide a place for common code shared by most subclasses, and to
    provide a common ancestor class that will always be the last one (before
    ``object``) in the linearized chain of superclasses (MRO = method
    resolution order).  Any class that inherits from ExtensionAction should
    *only* inherit from ExtensionAction or its subclasses, and not any other
    classes (this is necessary to ensure that ExtensionAction is immediately
    before object in the MRO).

    The initializer for any subclass of ExtensionAction must call __init__
    via ``super(MySubClass, self).__init__(**kwargs)`` to ensure that all other
    classes and mixins have their initializers called.  Do not use positional
    parameters for this, but always make calls using a keyword argument dict
    (**kwargs) or explicit keyword=value arguments.

    Any subclass that wishes to have its instances tracked should define a
    class attribute tracked and set it to True.

    The initializer requires two arguments that are used for the category
    (label on the left side of the "Actions" section) and title (link text).
    If the subclass has a docstring, it is used for the tooltip - unlike
    the category and title, the tooltip will be shared by all instances.

    Other arguments are presumed to be intended for subclasses and are ignored.

    :param category: Unlocalized category (label) text, e.g. "Manage"
    :type category: str
    :param title: Unlocalized text for display as link text
    :type title: str

    """

    #: Dictionary mapping ExtensionAction classes to lists of their instances
    _instances = {}

    @classmethod
    def instances(cls, rescan=False):
        """Return all instances of this class

        .. classmethod:: instances([rescan=False])

        This will attempt to load any classes the first time it is called
        (or any time that rescan=True).

        :param rescan: Whether to (re)try loading any extension action modules
        :type rescan: boolean
        :returns: All instances of the class
        :rtype: list(ExtensionAction)

        """
        if not ExtensionAction._instances or rescan:
            for importer, modname, _x in pkgutil.iter_modules([_EXTPATH]):
                full_modname = _EXTMOD + modname
                if full_modname not in sys.modules:
                    try:
                        importer.find_module(modname).load_module(full_modname)
                    except StandardError:
                        logger.exception("bad extension action module %s",
                                         modname)
                    else:
                        logger.info("loaded extension action module %s",
                                    full_modname)

        if cls not in ExtensionAction._instances:
            ExtensionAction._instances[cls] = []

        return cls._instances[cls]

    @classmethod
    def lookup(cls, title):
        """Find ExtensionAction (sub)class instance by title

        .. classmethod:: lookup(title)

        This will return the instance for the specified title or raise KeyError
        if it is not (any longer) in use.

        :param title: URL-encoded (quoted) title
        :type title: str
        :returns: The first instance matching the title
        :rtype: ExtensionAction
        :raises: KeyError if no instance with title is found

        """
        for ext in cls.instances():
            if ext.title == unquote_plus(title):
                return ext
        raise KeyError

    def __init__(self, category, title, **kwargs):  # pylint: disable=W0613
        """
        >>> setattr(ExtensionAction, 'tracked', True)
        >>> a = ExtensionAction('a', 'b')
        >>> tb = ExtensionAction(title='ta', category='tb')
        >>> assert a in a.instances()
        >>> assert tb in a.instances(rescan=True)
        """
        self._category = category
        self._title = title
        self._error = ''
        self._output = ''
        self.permission = 'view'
        logger.debug("%s.__init__ '%s'", type(self).__name__, title)
        for cls in type(self).__mro__:
            if getattr(cls, 'tracked', False):
                if cls not in self._instances:
                    ExtensionAction._instances[cls] = [self]
                else:
                    ExtensionAction._instances[cls].append(self)
                logger.debug("instances[%s] = %s",
                             cls.__name__, ExtensionAction._instances[cls])

    def __repr__(self):
        """
        >>> ExtensionAction('cat', 'dog')
        ExtensionAction(category="cat", title="dog")
        >>> ProjectAction(title="dog", category="cat")
        ProjectAction(category="cat", title="dog")
        >>> eval(repr(ProjectAction(category="cat", title="dog")))
        ProjectAction(category="cat", title="dog")
        >>> ExtensionAction('cat', 'dog').run(path="foo", root="/root", \
                                              language="foo")
        """
        return (type(self).__name__ + '(category="' + self.category +
                '", title="' + self.title + '")')

    def _query_url(self, pootle_path):
        """Return relative URL for this action

        This is the URL that will be used to perform the action (via GET) -
        it is the pootle_path for the language, project, translationproject,
        or store, with a query component like "?ext_actions=Say+hello" where
        the value is the form-encoded title of the extension action instance.

        >>> ExtensionAction(category='X', title='Do it')._query_url("foo/bar")
        'foo/bar?ext_actions=Do+it'
        """
        return ''.join([l(pootle_path), '?', urlencode({EXTDIR: self.title})])

    @property
    def category(self):
        """Heading for action grouping

        The (unlocalized) text of the category in which the action will be
        placed.  An example might be "Translate offline" if the action would
        be placed together with the "Download (.zip)" and "Upload" actions.

        """
        return self._category

    @property
    def title(self):
        """The (unlocalized) text for the action link."""
        return self._title

    @property
    def error(self):
        """Text from the last call to set_error()."""
        return self._error

    @property
    def output(self):
        """Text from the last call to set_output()."""
        return self._output

    def run(self, path, root,  # pylint: disable=R0913,W0613
            language='*', project='*', store='*', **kwargs):
        """Run an extension action: this class implementation just logs warning

        .. method:: run(path, root[,
                        language='*', project='*', store='*', kwargs])

        :param path: Pootle path from URL
        :type path: str
        :param root: Absolute path of translations root directory (PODIR)
        :type root: str
        :param language: Language code, e.g. 'af' (or '*')
        :type language: str
        :param project: Name of project, e.g. 'tutorial' (or '*')
        :type project: str
        :param store: Store name (filename) (or '*')
        :type store: str

        Always pass arguments as keyword arguments, ordering is not preserved
        for subclasses (and optional arguments may become required).
        """
        logger.warning("%s lacks run(): %s for lang %s proj %s store %s "
                       "(path %s)", type(self).__name__,
                       self.title, language, project, store, path)

    def set_error(self, text):
        """Set error output of action for display"""
        self._error = text

    def set_output(self, text):
        """Set output of action for display"""
        self._output = text

    def is_active(self, request):
        """Check if the action is active."""
        return check_permission(self.permission, request)


class ProjectAction(ExtensionAction):
    """Project-level action

    This is an extension action that operates on a project (across all
    languages).

    """

    tracked = True

    def __init__(self, **kwargs):
        """
        >>> ProjectAction(category="cat", title="dog")
        ProjectAction(category="cat", title="dog")
        """
        super(ProjectAction, self).__init__(**kwargs)


class LanguageAction(ExtensionAction):
    """Language global action

    This is an extension action that operates on a language (across all
    projects).

    """

    tracked = True

    def __init__(self, **kwargs):
        """
        >>> LanguageAction(category="cat", title="dog")
        LanguageAction(category="cat", title="dog")
        """
        super(LanguageAction, self).__init__(**kwargs)


class TranslationProjectAction(ExtensionAction):
    """Project + Language action

    This is an extension action that operates on a particular translation of
    a project for a particular language.

    """

    tracked = True

    def __init__(self, **kwargs):
        """
        >>> TranslationProjectAction(category="cat", title="dog")
        TranslationProjectAction(category="cat", title="dog")
        >>> TranslationProjectAction(category='cat', title='dog').run( \
                path="foo/bar", root="/root", tpdir="bar/foo", \
                language="foo", project="bar")
        """
        super(TranslationProjectAction, self).__init__(**kwargs)

    def run(self, path, root, tpdir,  # pylint: disable=R0913,W0613
            language, project, store='*', style='nongnu', **kwargs):
        """Run an extension action: this class implementation just logs warning

        .. method:: run(path, root, tpdir, language, project[,
                        store='*', style='nongnu', kwargs])

        :param path: Pootle path from URL
        :type path: str
        :param root: Absolute path of translations root directory (PODIR)
        :type root: str
        :param tpdir: Translation project directory path (relative to root)
        :type tpdir: str
        :param language: Language code, e.g. 'af'
        :type language: str
        :param project: Name of project, e.g. 'tutorial'
        :type project: str
        :param store: Store name (filename) (or '*') (relative to tpdir)
        :type store: str
        :param style: Project directory tree style, e.g. 'gnu' (or 'nongnu')
        :type style: str
        :param kwargs: Additional keyword arguments are allowed and ignored

        Always pass arguments as keyword arguments, ordering is not preserved
        for subclasses (and optional arguments may become required).
        """
        logger.warning("%s lacks run(): %s for lang %s proj %s store %s "
                       "(path %s, %s style)", type(self).__name__,
                       self.title, language, project, store, path, style)

    def get_link_func(self):
        """Return a link_func for use by pootle_translationproject.actions

        >>> s = TranslationProjectAction(category='a', title='boyo!')
        >>> setattr(s, 'pootle_path', '/pootle/')  # simulate path_obj
        >>> d = s.get_link_func()('GET', s)
        >>> assert d['text'] == u'boyo!'
        >>> assert s.lookup(d['href'][d['href'].find('=') + 1:]) == s
        >>> assert 'tooltip' in d
        >>> assert 'icon' in d
        """
        def link_func(_request, path_obj, **_kwargs):
            """Curried link function with self bound from instance method"""
            link = {'text': _(self.title),
                    'href': self._query_url(path_obj.pootle_path),
                    'icon': getattr(self, 'icon', 'icon-vote-inactive')}
            if type(self).__doc__:
                link['tooltip'] = ' '.join(type(self).__doc__.split())
            return link
        return link_func


class StoreAction(ExtensionAction):
    """Individual store (file) action

    This is an extension action that operates on a particular store
    (translation file) of a particular language for a particular project.

    """

    tracked = True

    def __init__(self, **kwargs):
        """
        >>> StoreAction(category="cat", title="dog")
        StoreAction(category="cat", title="dog")
        >>> StoreAction(category='cat', title='dog').run( \
                path="foo/bar/baz", root="/root", tpdir="bar/foo", \
                language="foo", project="bar", store="baz", style="gnu")
        """
        super(StoreAction, self).__init__(**kwargs)

    # These cannot be handled by making TranslationProjectAction a superclass,
    # as we need to allow user extension classes to have both StoreAction and
    # TranslationProjectAction (or just one of them) as superclasses to
    # indicate which contexts are appropriate for the action.

    # The __dict__ magic is not needed for Python 3.
    get_link_func = TranslationProjectAction.get_link_func
    run = TranslationProjectAction.run

    get_link_func = TranslationProjectAction.__dict__['get_link_func']
    run = TranslationProjectAction.__dict__['run']


class DownloadAction(ExtensionAction):
    """
    This is a class for extension actions that will return a file (stream)
    for downloading when the user clicks on the link.  It is intended to be
    used as a mixin for other extension actions, and *must* precede them in
    the superclass inheritance list.
    """

    def __init__(self, **kwargs):
        super(DownloadAction, self).__init__(**kwargs)
        self._dl_path = {}

    def set_download_file(self, path_obj, filepath):
        """Set file for download
        """
        filename = relative_real_path(filepath)
        export_path = os.path.join('POOTLE_EXPORT', filename)
        abs_export_path = absolute_real_path(export_path)
        try:
            ensure_target_dir_exists(abs_export_path)
            shutil.copyfile(filepath, abs_export_path)
        except (IOError, OSError, shutil.Error) as e:
            msg = (_("Failed to copy download file to export directory %s") %
                   abs_export_path)
            logger.exception('%s', msg)
            return ''.join([msg, ": ", str(e)])
        cache.set(self._cache_key(path_obj), path_obj.get_mtime(),
                  settings.OBJECT_CACHE_TIMEOUT)
        self._dl_path[path_obj.pootle_path] = export_path
        return ''

    def _cache_key(self, path_obj):
        """Return cache key for download data"""
        return iri_to_uri("%s:export_action" %
                          self._query_url(path_obj.pootle_path))

    def get_download(self, path_obj):
        """Return export path of generated (cached) download"""
        return self._dl_path.get(path_obj.pootle_path, None)

    def get_link_func(self):
        """Return a link_func for use by pootle_translationproject.actions

        >>> setattr(DownloadAction, 'tracked', True)
        >>> s = DownloadAction(category='c', title='d')
        >>> setattr(s, 'pootle_path', '/pootle/')  # simulate path_obj
        >>> d = s.get_link_func()('GET', s)
        >>> assert d['text'] == u'd'
        >>> assert s.lookup(d['href'][d['href'].find('=') + 1:]) == s
        >>> assert 'tooltip' in d
        >>> assert 'icon' in d
        """
        def link_func(_request, path_obj, **_kwargs):
            """Curried link function with self bound from instance method"""
            link = {'text': _(self.title),
                    'icon': getattr(self, 'icon', 'icon-download')}
            export_path = self.get_download(path_obj)
            if export_path:
                abs_export_path = absolute_real_path(export_path)
                last_export = cache.get(self._cache_key(path_obj))
                if last_export and (last_export == path_obj.get_mtime() and
                                    os.path.isfile(abs_export_path)):
                    # valid and up-to-date cache file - link to that
                    link['href'] = reverse('pootle-export', args=[export_path])
            if 'href' not in link:
                # no usable cache file, link to action query to generate it
                link['href'] = self._query_url(path_obj.pootle_path)
            if type(self).__doc__:
                # return docstring with normalized whitespace as tooltip
                link['tooltip'] = ' '.join(type(self).__doc__.split())
            return link
        return link_func


class CommandAction(ExtensionAction):
    """Command-line action mixin

    This is a class for extension actions that can be invoked from the command
    line; it is intended to be used as a mixin for other extension actions;
    since you can always write an standalone script for a command action that
    is not available within the Pootle UI.

    """

    tracked = True

    def __init__(self, **kwargs):
        super(CommandAction, self).__init__(**kwargs)

    def parseargs(self, *args):
        """Parse command line arguments"""
        # argparse handling?

    def runcmd(self):
        """run management command"""
        # print usage?

if __name__ == "__main__":
    import doctest

    logger.setLevel(logging.ERROR)
    logger.propagate = False
    logger.addHandler(logging.StreamHandler())

    doctest.testmod()
