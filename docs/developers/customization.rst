.. _customization:

Customizing Pootle
==================

In some cases it might be desirable to customize the styling of Pootle to fit
in with your other websites or other aspects of your identity. It might also be
required to add a common header or footer for proper visual integration
and even adjust and enhance existing functionality.

It's highly recommended to put any custom changes separate from the distributed
files, so that upgrades are unlikely to affect your customizations.


.. _customization#templates:

Customizing templates
---------------------

In case you need to change a template, copy it into your custom
:setting:`TEMPLATE_DIRS` with the same path name as it had before.

.. warning::

   If you edit any templates, keep in mind that changes to the text could
   result in untranslated text for users of the non-English user
   interface.

You can customize specific blocks of templates by indicating which template the
current template is customizing. Use the ``{% overextends %}`` template tag for
that (requires to install the `django-overextends package
<https://pypi.python.org/pypi/django-overextends>`_). This must be the first
tag in the template.

.. code-block:: django

   {% overextends 'browser/overview.html' %}

   {% block pre_content %}
   {{ block.super }}
   <h1>My custom content</h1>
   {% endblock %}

Check the original templates in order to know which blocks can be
customized.

On upgrades, you will want to check if the templates and the contained
blocks differ.


.. _customization#javascript:

Customizing JavaScript
----------------------

You can place any custom scripts in your custom :setting:`STATICFILES_DIRS`
directory and make them part of the default Pootle bundles by adding a very
simple *manifest.json* file under the *js/* directory of your custom
:setting:`STATICFILES_DIRS`.

This file must contain an object of key-values where the keys correspond
to the entry points defined by Pootle and the values are arrays of module
names to include in the output bundle. Check out the
*pootle/static/js/webpack.config.js* file to see the existing entry
points.

Example:

.. code-block:: javascript

  {
    "common": ["login.js", "extra_module.js"]
  }

In the example above, the *login.js* and the *extra_module.js* JavaScript
modules will be added as part of the *common* bundle. If *common* didn't
exist as an entry point before, a new bundle will be output.

Note that the *manifest.json* file has to be valid JSON, otherwise it will
be omitted.

Custom scripts can ``require()`` Pootle modules that are part of the core
bundles by prefixing paths with ``pootle/``. For instance the
``require('pootle/models')`` call will make Pootle's own ``models`` module
available in the scope of a 3rd party script.

Needless to say, you can refer to your custom scripts the same way as you
would refer to any other static asset, i.e. by using the ``{% static %}``
template tag.


.. _customization#css:

Customizing CSS
---------------

Create any needed files under your custom :setting:`STATICFILES_DIRS` and
reference them from your custom templates using the ``{% static %}`` template
tag. You can also inline styles in your templates as usual.


.. _customization#images:

Customizing images
------------------

You should put your custom images in your custom :setting:`STATICFILES_DIRS`.
From CSS you would just reference them using a relative path.

On the contrary, if you want to reference images from HTML code or inline CSS,
you should use the ``{% static %}`` template tag.


.. _customization#install-node-libs:

Installing JS build libraries
-----------------------------

Before you can rebuild your static assets with any CSS or JavaScript
customisations, you will need to install some Node.js libraries.

Before proceeding please make sure you have :ref:`Node.js and npm installed in
your system <requirements#customize-static>`.

.. code-block:: console

   (env) $ cd $pootle_dir
   (env) $ cd pootle/static/js/
   (env) $ npm install

``$pootle_dir`` is the directory where Pootle is installed.


.. _customization#assets:

Rebuilding assets after customization
-------------------------------------

Before rebuilding your assets for the first time you must :ref:`install the
JavaScript build libraries <customization#install-node-libs>`.

After doing any customizations, you will need to regenerate any modified
bundles and gather all the static assets in a single place for public
consumption.

You will need to activate your virtual environment before running these
commands.

.. code-block:: console

   (env) $ pootle webpack
   (env) $ pootle collectstatic --noinput --clear -i node_modules
   (env) $ pootle assets build
