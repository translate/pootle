.. _project_setup:

Create a Project
================

Now that you have the server running, you can setup a project to translate on
the server.


Our assumptions
---------------

To simplify the example we assume that:

- The project uses PO files.
- You can copy these files to the Pootle server.
- There is a template file in POT format containing the strings that need to be
  translated.
- The project follows the GNU layout (More information on this is provided
  below).
- Pootle is correctly set up and running.
- There is at least one **rqworker** thread running. This is important.
- You are logged into the Pootle server using your newly created administrator
  user.


.. _project_setup#add-new-project:

Adding a new project
--------------------


.. _project_setup#placing-translation-files:

Placing translation files
+++++++++++++++++++++++++

You need to place the translation files for your new project in a location
where Pootle can find, read and write them. Pootle uses the 
:setting:`POOTLE_TRANSLATION_DIRECTORY` setting to find out where translation
files are stored on the server.

.. note: By default this is the :file:`translations` directory within the
   Pootle codebase, which might be difficult for you to find depending on how
   you installed Pootle. So most likely you want to change this in your custom
   settings file.


Our example project uses a GNU layout.

A GNU layout means that our project contains translation files named using
language codes. Within the project there are no directories, just files. There
can only be a single translation file per language in a project using this
layout.

This is the simplest layout possible and the reason we are using it in our
example.

Below you can see an example with two projects using the GNU layout:

::

    `-- translations
        `-- project1
        |   |-- de.po
        |   |-- fr.po
        |   |-- gl.po
        |   |-- pt_BR.po
        |   `-- templates.pot
        `-- project2
            |-- af.po
            |-- eu.po
            |-- pt_BR.po
            |-- templates.pot
            `-- zu.po


Among the regular translation files there are two files named 
:file:`templates.pot`. These are the template (master or reference) files that
contain the original strings. Usually these files contain only English strings,
it is much less confusing to use the term ``templates`` than e.g. ``en`` or
``English``.

To get started, create a :file:`my-project` directory in the location pointed
to by :setting:`POOTLE_TRANSLATION_DIRECTORY` and place within it the 
translation files for your new project. Make sure you have a
:file:`templates.pot` among those project translation files.


.. _project_setup#creating-the-project:

Creating the project
++++++++++++++++++++

At the top of the user interface, you will see your newly created administrator
username. Click on it and the main top menu will be displayed, then click on
**Admin** (highlighted in red):

.. image:: ../_static/accessing_admin_interface.png


Now you are in the administration interface. Go to the **Projects** tab and you
will see a **New Project** button:

.. image:: ../_static/add_project_button.png


Click on that button and the **Add Project** form will be displayed. Enter the
new project's details. **Code** must match the name of the directory within
:setting:`POOTLE_TRANSLATION_DIRECTORY` that contains the project translation
files, in our example :file:`my-project`. You can also provide a **Full Name**
easily readable for humans. You don't need to change the rest of the fields
unless you need to further customize your project.

.. image:: ../_static/add_project_form.png


Once you are done click on the **Save** button below the form to create the
project. Creating the project doesn't actually import all the translations to
Pootle. To do that you need to run :djadmin:`update_stores` on the command line
of the Pootle server:

.. code-block:: console

    $ pootle update_stores --project=my-project


This will import all the translations from disk into Pootle, calculate the
translation statistics and calculate the quality check failures. This might
take a while for a large project.

Looking at your new project you will see that Pootle has imported all the
existing translations for the existing languages that you copied to the
:file:`my-project` directory within :setting:`POOTLE_TRANSLATION_DIRECTORY`.


.. _project_setup#initialize-new-tp:

Enable translation to a new language
------------------------------------

When you want to add a new language to the project, follow these steps.

Go to your project overview and select **Languages** in the navigation
dropdown:

.. image:: ../_static/languages_in_project_dropdown.png


.. note:: Alternatively you can get the same result by clicking on the
   **Languages** link that is displayed below your project form in the
   administration interface:

   .. image:: ../_static/project_form_bottom_links.png


The existing languages enabled for the project are listed. In our example we
are adding **Arabic** to the project:

.. image:: ../_static/enable_new_tp_through_admin_UI.png


When you click the **Save** button the new language will be added for
translation. In large projects it may take some time to create the new
translation files from the ``templates``.

.. note:: If you want to enable translation to a language that doesn't yet
   exist in your Pootle instance, then you will first have to add the language
   in the **Languages** tab in the administration interface, in a similar way
   to :ref:`creating a new project <project_setup#creating-the-project>`.

   Once the language is created you can enable translation to that new language
   in any project by following the instructions above.


.. _project_setup#updating-strings:

Updating strings for existing project
-------------------------------------

Whenever developers introduce new strings, deprecate older ones, or change some
of them this impacts Pootle and the languages being translated.

When any of these changes occur, you will need to generate a new
:file:`templates.pot` and use it to bring the translations in Pootle up-to-date
with the new templates.

Once you have created the new :file:`templates.pot` place it within your
project's directory in :setting:`POOTLE_TRANSLATION_DIRECTORY`, replacing the
file with the same name. After that, invoke the following command which will
update the template translations in the Pootle database.

.. code-block:: console

    $ pootle update_stores --project=my-project --language=templates


This command will ensure that new strings are added to the project and any
strings which have been removed are marked as deprecated, and thus will not be
available for translation.

Now each of the languages will need to be brought into sync with the template
language. The first step is to save all the Pootle translations to disk:

.. code-block:: console

    $ pootle sync_stores --project=my-project


Then update all those translations on disk against the newer templates. We
recommend you to update them on disk using the :ref:`pot2po <toolkit:pot2po>`
command line tool because it can handle other formats besides Gettext PO.

.. code-block:: console

    $ cd $POOTLE_TRANSLATION_DIRECTORY  # Use the actual path!
    $ cd my-project
    $ pot2po -t af.po templates.pot af.po  # Repeat for each language by changing the language code.


.. note:: To preserve the existing translations we pass the previous
   translation file to the ``-t`` option.


When all the languages in the project have been updated you can push them back
to Pootle:

.. code-block:: console

    $ pootle update_stores --project=my-project


.. note:: If your project languages contain many translations you might want to
   perform the update against newer templates on a language by language basis.
