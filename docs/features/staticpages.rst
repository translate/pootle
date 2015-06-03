.. _staticpages:

Static Pages
============

Pootle makes it easy to setup additional custom content without too much
effort.

There are three types of static pages:

#. Regular -- these work like normal web pages and are able to present
   additional content such as a "Getting Started" page.  You will want to add
   these into other :doc:`UI customisation </developers/customization>`.
#. Legal -- in addition to presenting content like a Regular page, Legal pages
   require that users agree to the content otherwise they are logged off the
   system.  Use these pages for presenting terms of service or changes in
   licensing terms that user must accept before they can use or continue to use
   Pootle.
#. Announcements -- these appear in the sidebar and can present special
   instructions about projects.  If you change these pages then they will be
   presented to users on their next visit.  Announcements can also make use of
   link rewriting to allow URLs to vary based on the language being browsed.


Use **Admin -- Static Pages** to create and manage static pages.

The static pages are by default formatted using HTML. But you can use Markdown
or RestructuredText by setting :setting:`POOTLE_MARKUP_FILTER` correctly.


Links in static pages
---------------------

When linking to a static page externally or in any customisations, your links
would be pointing to ``/pages/$slug``, such as ``/pages/gettting-started``.

For linking to another static page from within a static page use the
``#/$slug`` syntax.  Thus, if you created a *Getting Started* page as a static
page which pointed to your *Licence Statement* legal page we'd use this
``#/licence_statement`` in the URL.


Special features of announcement pages
--------------------------------------


Naming your slug
^^^^^^^^^^^^^^^^

When creating an announcement page use a slug ``projects/$project`` so that the
page will be used on the ``$project`` project.

Other slug names may be used:

- ``$lang`` - for an announcement page that will appear on every single project
  enabled for the ``$lang`` languages.
- ``$lang/$project`` - for an announcement page that is specific to the
  ``$project`` project in the ``$lang`` language.

The prefered model though is to use the ``projects/$project`` convention for a
single easy-to-maintian page.


Language link rewriting in Announcement pages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. pootle/apps/pootle_misc/templatetags/cleanhtml.py:rewrite_language_links()
   provide the functionality discussed here.

In many cases you have URLs in announcement pages that would be identical
except for variations in the language code.  Examples would include links to
team wiki pages, signoff pages, progress dashboards, live test versions, etc.

Any link within your announcement page that uses a fake language code of
``/xx/`` will be rewritten with the language code for this translation.  Thus
if you insert a link such as ``http://example.com/signoff/xx/`` then that will
be rewritten to ``http://example.com/signoff/af/`` for a user viewing this
announcement page for the Afrikaans language translation.
