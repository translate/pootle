#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
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

import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from lxml.html import rewrite_links


__all__ = (
    'get_markup_filter_name', 'get_markup_filter', 'apply_markup_filter',
)


logger = logging.getLogger('pootle.markup')


def rewrite_internal_link(link):
    """Converts `link` into an internal link.

    Any active static pages defined for a site can be linked by pointing
    to its virtual path by starting the anchors with the `#/` sequence
    (e.g. `#/the/virtual/path`).

    Links pointing to non-existent pages will return `#`.
    Links not starting with `#/` will be omitted.
    """
    if not link.startswith('#/'):
        return link

    from staticpages.models import AbstractPage

    virtual_path = link[2:]
    url = u'#'

    for page_model in AbstractPage.__subclasses__():
        try:
            page = page_model.live.get(
                    virtual_path=virtual_path,
                )
            url = page.get_absolute_url()
        except ObjectDoesNotExist:
            pass

    return url


def get_markup_filter_name():
    """Returns a nice version for the current markup filter's name."""
    name, args = get_markup_filter()
    return {
        'textile': u'Textile',
        'markdown': u'Markdown',
        'restructuredtext': u'reStructuredText',
    }.get(name, u'HTML')


def get_markup_filter():
    """Returns the configured filter as a tuple with name and args.

    In the following case this function returns (None, message) instead,
    where message tells the reason why not a markup filter is returned:

        * There is no markup filter set.

        * The MARKUP_FILTER option is improperly set.

        * The markup filter name set can't be used because the required
          package isn't installed.

        * The markup filter name set is not one of the acceptable markup
          filter names.
    """
    try:
        markup_filter, markup_kwargs = settings.MARKUP_FILTER
        if markup_filter is None:
            return (None, "unset")
        elif markup_filter == 'textile':
            import textile
        elif markup_filter == 'markdown':
            import markdown
        elif markup_filter == 'restructuredtext':
            import docutils
        else:
            raise ValueError()
    except AttributeError:
        logger.error("MARKUP_FILTER is missing. Falling back to HTML.")
        return (None, "missing")
    except IndexError:
        logger.error("MARKUP_FILTER is misconfigured. Falling back to HTML.")
        return (None, "misconfigured")
    except ImportError:
        logger.warning("Can't find the package which provides '%s' markup "
                        "support. Falling back to HTML.", markup_filter)
        return (None, "uninstalled")
    except ValueError:
        logger.error("Invalid value '%s' in MARKUP_FILTER. Falling back to "
                      "HTML." % markup_filter)
        return (None, "invalid")

    return (markup_filter, markup_kwargs)


def apply_markup_filter(text):
    """Applies a text-to-HTML conversion function to a piece of text and
    returns the generated HTML.

    The function to use is derived from the value of the setting
    ``MARKUP_FILTER``, which should be a 2-tuple:

        * The first element should be the name of a markup filter --
          e.g., "markdown" -- to apply. If no markup filter is desired,
          set this to None.

        * The second element should be a dictionary of keyword
          arguments which will be passed to the markup function. If no
          extra arguments are desired, set this to an empty
          dictionary; some arguments may still be inferred as needed,
          however.

    So, for example, to use Markdown with safe mode turned on (safe
    mode removes raw HTML), put this in your settings file::

        MARKUP_FILTER = ('markdown', { 'safe_mode': 'escape' })

    Currently supports Textile, Markdown and reStructuredText, using
    names identical to the template filters found in
    ``django.contrib.markup``.

    Borrowed from http://djangosnippets.org/snippets/104/
    """
    markup_filter_name, markup_kwargs = get_markup_filter()

    if not text.strip():
        return text

    html = text

    if markup_filter_name is not None:
        if markup_filter_name == 'textile':
            import textile
            if 'encoding' not in markup_kwargs:
                markup_kwargs.update(encoding=settings.DEFAULT_CHARSET)
            if 'output' not in markup_kwargs:
                markup_kwargs.update(output=settings.DEFAULT_CHARSET)

            html = textile.textile(text, **markup_kwargs)

        elif markup_filter_name == 'markdown':
            import markdown
            html = markdown.markdown(text, **markup_kwargs)

        elif markup_filter_name == 'restructuredtext':
            from docutils import core
            if 'settings_overrides' not in markup_kwargs:
                markup_kwargs.update(
                    settings_overrides=getattr(
                        settings,
                        "RESTRUCTUREDTEXT_FILTER_SETTINGS",
                        {},
                    )
                )
            if 'writer_name' not in markup_kwargs:
                markup_kwargs.update(writer_name='html4css1')

            parts = core.publish_parts(source=text, **markup_kwargs)
            html = parts['html_body']

    return rewrite_links(html, rewrite_internal_link)
