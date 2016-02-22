.. _styleguide:

Styleguide
==========

Pootle developers try to stick to some development standards that are
gathered in this document.

Python and documentation
------------------------

For Python code and documentation Pootle follows the
:ref:`Translate Styleguide <toolkit:styleguide>` adding extra
clarifications listed below.

- :ref:`Python style conventions <toolkit:styleguide-general>`

- :ref:`Documentation style conventions <toolkit:styleguide-docs>`


Pootle-specific Python guidelines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pootle has specific conventions for Python coding style.


Imports
~~~~~~~

Like in :ref:`Python import conventions <toolkit:styleguide-imports>` in
Translate styleguide, but imports should be grouped in the following
order:

1) __future__ library imports
2) Python standard library imports
3) Third party libraries imports (Including Translate Toolkit ones)
4) Django imports
5) Django external apps imports
6) Other Pootle apps imports
7) Current package (or app) imports, using explicit relative imports (See `PEP
   328 <https://www.python.org/dev/peps/pep-0328/#guido-s-decision>`_)

Check :ref:`Python import conventions <toolkit:styleguide-imports>` in
Translate styleguide for other conventions that the imports must follow.

.. code-block:: python

    import re
    import sys.path as sys_path
    import time
    from datetime import timedelta
    from os import path

    from lxml.html import fromstring
    from translate.storage import versioncontrol

    from django.contrib.sites.models import Site
    from django.db import models
    from django.db.models import Q
    from django.db.models.signals import post_save

    from tastypie.models import ApiKey

    from pootle_language.models import Language
    from pootle_translationproject.models import TranslationProject

    from .forms import GoalForm
    from .models import Tag


Order in models
~~~~~~~~~~~~~~~

Model's inner classes and methods should keep the following order:

- Database fields
- Non database fields
- Default ``objects`` manager
- Custom manager attributes (i.e. other managers)
- ``class Meta``
- ``def natural_key()`` (Because it is tightly related to model fields)
- Properties
- Any method decorated with ``@classmethod``
- ``def __unicode__()``
- ``def __str__()``
- Any other method starting with ``__`` (for example ``__init__()``)
- ``def save()``
- ``def delete()``
- ``def get_absolute_url()``
- ``def get_translate_url()``
- Any custom methods


Fields in models and forms
~~~~~~~~~~~~~~~~~~~~~~~~~~

- If the field declaration fits in one line:

  - Put all the options on that line,
  - Don't put a comma after the last option,
  - The parenthesis that closes the field declaration goes just after the last
    option.

- If the field declaration spans to several lines:

  - Each option goes on its own line (including the first one),
  - The options are indented 4 spaces,
  - The last option must have a comma after it,
  - The closing parenthesis in the field declaration goes on its own line,
    aligned with the first line in the field declaration.

.. code-block:: python

    class SampleForm(forms.Form):
        # Field declaration that spans to several lines.
        language = forms.ChoiceField(
            label=_('Interface Language'),
            initial="",
            required=False,
            widget=forms.Select(attrs={
                'class': 'js-select2 select2-language',
            }),
            help_text=_('Default language for using on the user interface.'),
        )
        # One line field declaration.
        project = forms.ModelChoiceField(Project, required=True)


URL patterns
~~~~~~~~~~~~

When writing the URL patterns:

- URL patterns can be grouped by putting a blank line between the groups.
- On each URL pattern:

  - Specify the URL pattern using the ``url()`` function, not a tuple.
  - Each parameter must go on its own line in all cases, indenting them one
    level to allow easily seeing the different URL patterns.
  - In URLs:

    - Use hyphens, never underscores.
    - To split long URLs use implicit string continuation. Note that URLs are
      raw strings.

- URL pattern names must be named like ``pootle-{app}-{view}`` (except in some
  specific cases):

  - ``{app}`` is the app name, which sometimes can be shortened, e.g. using
    **tp** to avoid the longish **translationproject**. The chosen app name
    must be used consistently across all the URL patterns for the app.
  - ``{view}`` is a unique string which might consist on several words,
    separated with hyphens, that might not match the name of the view that is
    handled by the URL pattern.
  - The exceptions to this naming convention are:

    - URL patterns for AJAX views must be named like ``pootle-xhr-{view}``.
    - URL patterns in *pootle_app* app must be named like:

      - *pootle_app* admin URLs must be named like ``pootle-admin-{view}``
      - Other *pootle_app* URLs must be named like ``pootle-{view}``.

.. code-block:: python

    urlpatterns = patterns('pootle_project.views',
        # Listing of all projects.
        url(r'^$',
            'projects_index'),

        # Whatever URLs.
        url(r'^incredibly-stupid/randomly-long-url-with-hyphens-that-is-split-'
            r'and-continued-on-next-line.html$',
            'whatever',
            name='pootle-project-whatever'),

        # Admin URLs.
        url(r'^(?P<project_code>[^/]*)/admin.html$',
            'project_admin'),
        url(r'^(?P<project_code>[^/]*)/permissions.html$',
            'project_admin_permissions',
            name='pootle-project-admin-permissions'),
    )


Variables naming
~~~~~~~~~~~~~~~~

In order to have a more consistent code the use of specific names for some
heavily used variables is encouraged:

- ``ctx``: Name for the dictionary with the context passed to a template for
  rendering. Also known as *context*, *template variables* or *template vars*.

  .. code-block:: python

    # Good.
    ctx = {
        'language': language,
    }


    # Bad.
    context = {
      ...

    templatevars = {
      ...

    template_vars = {
      ...


Settings naming
~~~~~~~~~~~~~~~

Pootle specific settings must be named like ``POOTLE_*``, for example:
``POOTLE_ENABLE_API``, ``POOTLE_VCS_DIRECTORY`` or ``POOTLE_MARKUP_FILTER``


Pootle-specific documentation guidelines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For documenting several things, Pootle defines custom Sphinx roles.

- Settings::

    .. setting:: POOTLE_TITLE

  To link to a setting, use ``:setting:`POOTLE_TITLE```.

- Icons::

    Some reference to |icon:some-icon| in the text.

  This allows you to easily add inline images of icons used in Pootle.
  The icons are all files from :file:`pootle/static/images/sprite`.  If you
  were referring to an icon :file:`icon-edit.png` then you would use the syntax
  ``|icon:icon-edit|``.  The icon reference is always prefixed by ``icon:``
  and the name of the icon is used without the extension.

  E.g. ``|icon:icon-google-translate|`` will insert this
  |icon:icon-google-translate| icon.

- Pootle manage.py commands::

    .. django-admin:: sync_stores

  To link to a command, use ``:djadmin:`sync_stores``


JavaScript
----------

Follow the great `Airbnb JavaScript Style Guide
<https://github.com/airbnb/javascript/blob/master/README.md>`_. Go check it out
for all the details.

As a summary, that includes:

* 2-space indent.
* Single quotes.
* ``pascalCase`` variable naming.

In addition to that:

* Try to be in the 80 (+4) soft character limit, but be wise to know when to
  make exceptions.
* `Use ES2015 <http://babeljs.io/docs/learn-es2015/>`_.
* `Avoid jQuery <http://youmightnotneedjquery.com/>`_.

When dealing with existing or legacy code, also keep in mind to:

* Prefix with ``$`` Variables holding jQuery objects.
* Use ``js-`` to prefix selectors for elements queried via JavaScript.


React + JSX
^^^^^^^^^^^

For React + JSX code also follow the `Airbnb React/JSX Style Guide
<https://github.com/airbnb/javascript/blob/master/react/README.md>`_, with the
following exceptions:

* Naming extensions: Use ``.js`` extension for React components (not ``.jsx``).
* Use ``React.createClass({})`` over extending ``React.Component``.

Also bear in mind the following:

* Event handler naming: ``handle*()`` for methods, ``on*()`` for props.
* ``propTypes``: sort them alphabetically, but also group them to place
  ``isRequired`` types first.


HTML
----

Indenting
  - Indent using 2 spaces. Don't use tabs.

  - Although it's desirable to avoid lines longer than 80 characters, most of
    the time the templating library doesn't easily allow this. So try not to
    extend too much the line length.

Template naming
  - If a template name consists on several words they must be joined using
    underscores (never hyphens), e.g. *my_precious_template.html*

  - If a template is being used in AJAX views, even if it is also used for
    including it on other templates, the first word on its name must be `xhr`,
    e.g. *xhr_tag_form.html*.

  - If a template is intended to be included by other templates, and it is not
    going to be used directly, start its name with an underscore, e.g.
    *_included_template.html*.

Quoting
  - Always use double quotes for HTML attribute values.
  - Always use single quotes for Django template tags and template filters
    located inside HTML attribute values.

    .. code-block:: html

        <!-- Good -->
        <a href="{% url 'whatever' %}" class="highlight">


.. The following are in their own code-block as two of them don't render
   correctly

    .. code-block:: text

        <!-- Bad -->
        <a href='{% url "whatever" %}' class='highlight'>
        <a href="{% url "whatever" %}" class="highlight">
        <a href='{% url 'whatever' %}' class='highlight'>


CSS
---

Indenting
  - Indent using 4 spaces. Don't use tabs.

  - Put selectors and braces on their own lines.

  Good:

  .. code-block:: css

    .foo-bar,
    .foo-bar:hover
    {
        background-color: #eee;
    }

  Bad:

  .. code-block:: css

    .foo-bar, .foo-bar:hover {
      background-color: #eee;
    }

Naming
  - Selectors should all be in lowercase and consequent words should be
    separated using dashes. As an example, rather use ``.tm-results`` and not
    ``.TM_results``.
