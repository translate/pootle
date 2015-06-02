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
   licensing terms.
#. Announcements -- these appear in the sidebar and can present special
   instructions about projects.  Use the project code to ensure that this pages
   appears as a sidebar for that project.  If you change these pages then they
   will be presented to users when next they visit the project.

The static pages are by default formatted using HTML. But you can use Markdown
or RestructuredText by setting :setting:`MARKUP_FILTER` correctly.
