.. _customization:

Customizing the look
====================

In some cases it might be desirable to customize the styling of Pootle to fit
in with your other websites or other aspects of your identity. It might also be
required to add a common header or footer for proper visual integration.

It's highly recommended to put any custom changes separate from the distributed
files, so that upgrades are unlikely to affect your customizations.
For controlling where to put templates, you can check the
``TEMPLATE_DIRS`` setting; for static assets check the ``STATICFILES_DIRS``
setting.

.. note::

   In development, make sure all ``STATICFILES_DIRS`` directories are being
   served by your development web server. In nginx that would be something like:

   ..code-block::

      root /home/myuser/;

      location /static/ {
        try_files /pootle/pootle$uri /custom_dir/pootle$uri;
        access_log off;
      }


.. _customization#building:

Rebuilding assets after customization
-------------------------------------

.. warning::

   After doing any customization, please execute the following commands to
   collect and build static content such as images, CSS and JavaScript files
   that are served by the Pootle server. Make sure your virtualenv is enabled
   before running these.

   .. code-block:: bash

      (env) $ python manage.py collectstatic --noinput --clear
      (env) $ python manage.py assets build

Alternatively you can run the ``make assets`` command from the root of the
repository.


.. _customization#css:

Customizing CSS
---------------

Create any needed files under your custom ``STATICFILES_DIRS`` and reference
them from your custom templates using the ``{% static %}`` template tag. You
can also inline styles in your templates as usual.


.. _customization#images:

Customizing images
------------------

You should put your custom images in your custom ``STATICFILES_DIRS``. From CSS
you would just reference them using a relative path.

On the contrary, if you want to reference images from HTML code or inline CSS,
you should use the ``{% static %}`` template tag.


.. _customization#templates:

Customizing templates
---------------------

In case you need to change a template, copy it into your custom
``TEMPLATE_DIRS`` with the same path name as it had before.

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
