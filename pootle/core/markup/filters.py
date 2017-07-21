# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from ..utils.html import rewrite_links


__all__ = (
    'get_markup_filter_name', 'get_markup_filter_display_name',
    'get_markup_filter', 'apply_markup_filter',
)


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
            page = page_model.objects.live().get(virtual_path=virtual_path,)
            url = page.get_absolute_url()
        except ObjectDoesNotExist:
            pass

    return url


def get_markup_filter_name():
    """Returns the current markup filter's name."""
    name = get_markup_filter()[0]
    return 'html' if name is None else name


def get_markup_filter_display_name():
    """Returns a nice version for the current markup filter's name."""
    name = get_markup_filter_name()
    return {
        'textile': u'Textile',
        'markdown': u'Markdown',
        'restructuredtext': u'reStructuredText',
        'html': u'HTML',
    }.get(name)


def get_markup_filter():
    """Returns the configured filter as a tuple with name and args.

    If there is any problem it returns (None, '').
    """
    try:
        markup_filter, markup_kwargs = settings.POOTLE_MARKUP_FILTER
        if markup_filter is None:
            return (None, "unset")
        elif markup_filter == 'textile':
            import textile  # noqa
        elif markup_filter == 'markdown':
            import markdown  # noqa
        elif markup_filter == 'restructuredtext':
            import docutils  # noqa
        elif markup_filter == 'html':
            pass
        else:
            return (None, '')
    except Exception:
        return (None, '')

    return (markup_filter, markup_kwargs)


def apply_markup_filter(text):
    """Applies a text-to-HTML conversion function to a piece of text and
    returns the generated HTML.

    The function to use is derived from the value of the setting
    ``POOTLE_MARKUP_FILTER``, which should be a 2-tuple:

        * The first element should be the name of a markup filter --
          e.g., "markdown" -- to apply. If no markup filter is desired,
          set this to None.

        * The second element should be a dictionary of keyword
          arguments which will be passed to the markup function. If no
          extra arguments are desired, set this to an empty
          dictionary; some arguments may still be inferred as needed,
          however.

    So, for example, to use Markdown with bleach cleaning turned on (cleaning
    removes non-whitelisted HTML), put this in your settings file::

        POOTLE_MARKUP_FILTER = ('markdown', {})

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
            import bleach
            import markdown

            # See ALLOWED_TAGS, ALLOWED_ATTRIBUTES and ALLOWED_STYLES
            # https://github.com/mozilla/bleach/blob/master/bleach/sanitizer.py
            tags = bleach.ALLOWED_TAGS + [
                u'h1', u'h2', u'h3', u'h4', u'h5',
                u'p', u'pre',
                u'img',
                u'hr',
                u'span',
            ]
            attrs = bleach.ALLOWED_ATTRIBUTES.copy()
            attrs.update({
                'img': ['alt', 'src'],
            })
            styles = bleach.ALLOWED_STYLES

            tags_provided = ('clean' in markup_kwargs
                             and 'extra_tags' in markup_kwargs['clean'])
            if tags_provided:
                tags += markup_kwargs['clean']['extra_tags']

            attrs_provided = ('clean' in markup_kwargs
                              and 'extra_attrs' in markup_kwargs['clean'])
            if attrs_provided:
                attrs.update(markup_kwargs['clean']['extra_attrs'])

            styles_provided = ('clean' in markup_kwargs
                               and 'extra_styles' in markup_kwargs['clean'])
            if styles_provided:
                styles += markup_kwargs['clean']['extra_styles']

            html = bleach.clean(markdown.markdown(text, **markup_kwargs),
                                tags=tags, attributes=attrs, styles=styles)

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
