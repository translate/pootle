.. _getting-started:

Getting started
===============

Pootle is a web portal that allows you to translate more easily. The name
stands for PO-based Online Translation / Localization Engine, but you may need
to read `this <http://www.thechestnut.com/flumps.htm>`_. Pootle is GPL licensed
Free Software, and you can download it and run your own copy if you like.

You can also help participate in the development in many ways (you don't have
to be able to program).

The Pootle project itself is hosted at http://pootle.translatehouse.org where
you can find details about source code, mailing lists, etc.


.. _getting-started#registration:

Registration
------------

While everybody can view the files, only registered users can edit them and
receive credit for their effort, so unless your server uses LDAP
authentication, the first thing you should do in order to translate, is to
register.

You can register in the register page (accessible by clicking *Register* in the
menubar) following two simple steps, providing you have a current e-mail
address.

#. Fill in your desired user name, a valid e-mail account, and enter your
   password twice for verification. Then choose *Register* and an you will receive a
   message with an activation link in the e-mail address you have provided.

#. When you receive the activation message by e-mail, just click on the
   activation link and your account will be activated.


.. _getting-started#login:

Login and user settings setup
-----------------------------

Now that you are a registered user, you can login to Pootle by following the
*Login* link on the top menubar and filling in your credentials.

Once you have logged in, your account's dashboard will be shown, which includes
links to your selected languages and projects.

The first time you log in, no links will be shown since you haven't chosen any
before. You can click on the link provided to change your settings and select
your preferred languages and projects. You can set more settings within the
same page as well.


.. _getting-started#browsing:

Browsing the files tree
-----------------------

Now that your dashboard is set up, you can reach the desired files for
translation directly through the links in it.

Another way to find the file you wish to translate is through the main page.
The main page displays two categories: languages and projects. Choosing a
language will give you the list of projects available for translation into this
language; choosing a project will give you the list of languages to which it
can be translated.

Once you have chosen both the project and the language, you'll be presented
with the files and directories available for translation.


.. _getting-started#heading-to-translating:

Heading to translating
----------------------

If you click on a filename it will start showing all the entries on the file,
independently whether the entries are translated or not. This is also known as
*Translate All*.

Alternatively, if the translation for a file is not complete, you can click on
the summary text (eg, *27 words need attention*), which will give you through all
the untranslated or fuzzy entries on the file. This mode is also named as *Quick
Translate*.

In both cases you'll be presented with a two-column table, with the strings to
be translated on the left, and the current translation on the right.

The current edited entry will appear as a text box with the options *Skip* and
*Suggest* or *Submit* below it. Naturally you can enter text in the text box
and submit it or skip to the next entry.

You can also directly access any of the other entries presented by clicking on
the numbers on the left-hand side.

.. _getting-started#other-aids:

Other aids from Pootle
----------------------

Pootle's editor also helps translators by displaying
:ref:`terminology` related to the entry currently being edited.

Another helpful feature is the :ref:`alternative_source_language`, which
displays how the current entry has been translated into other languages. In
order for this to work, you must select your desired alternative source
languages in you account's settings.

In addition to the above, you can also download the translation file,
:ref:`work offline <offline>` with your favourite editor and upload the file.
For multi-file projects, you can download a ZIP file with all the files for a
directory and upload the ZIP file with the translated files.
