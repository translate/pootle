.. _contributing:

Contributing
============

There are several ways you can contribute to improve Pootle, even if you don't
know programming! Want to know how? Please keep reading.

- You can give us feedback about things that annoy you or about areas you see
  for improvement. You can reach us in `our mailing list
  <https://lists.sourceforge.net/lists/listinfo/translate-pootle>`_ or in the
  `Pootle channel <https://gitter.im/translate/pootle>`_.

- Found a bug? Report it in our `Bugzilla tracker
  <https://github.com/translate/pootle/issues/>`_. You can also always contact
  us on IRC. Make sure to read more about :ref:`how to report bugs
  <contributing#reporting_bugs>`.

- Translate the User Interface into your own language. Pootle is translated
  into `nearly 50 languages <http://pootle.locamotion.org/projects/pootle/>`_.
  Is your language missing? Have you found any errors in the translation? Learn
  :ref:`how to contribute translating <contributing#translating>`.

- Suggest :ref:`documentation improvements <contributing#documentation>` by
  fixing mistakes and adding new sections.

- In case you have coding skills and are willing to contribute patches, fixes,
  or new features, read how you can :ref:`hack on Pootle <hacking>`.


.. _contributing#requesting_features:

Requesting features
-------------------

Sometimes Pootle doesn't quite meet your expectations or you have an idea for a
great new feature.

It might help to understand how Pootle developers evaluate new features:

1.  Is it generally useful? *i.e.* will it be useful for a large number
    of people?

2.  Does it follow the ethos of Pootle? *e.g.* does it keep the interface
    clean, is it intuitive and non-technical?

3.  How long would it take to implement?

    1. Does it require fundamental changes to how Pootle works? *i.e.* long, or
    2. Is this just a simple change of layout or a simple feature? *i.e.* short

4.  Is this something a developer is passionate about?  Does this meet their
    itch or are they convinced it is a winning feature?

How can I make a winning feature request?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you really do want your feature to succeed here are some options to help
you when reporting or requesting the feature.

1.  Have you thought about this and provided a clear use case?

    * Using a real use case would be good.
    * Make it clear why you think this feature is important, don't assume it is
      obvious.

2.  Have you made some mockups of the UI?

    * Isn't it a bit unfair that you expect a volunteer coder to create the
      mockup for your feature?

3.  Did you have some discussion on the mailing list or on the Pootle channel?

    * Drive-by feature requests usually don't get attention.  But if you have
      built a case and some links to developers, i.e. they know you, then they
      will listen. Proposing your idea in these forums could be helpful for
      your case.

4.  Can you code?

    * If you can code the feature yourself that will always win some
      acceptance.  But realise that someone does need to review your code and
      your code still needs to meet the acceptance criterion. So discuss early.

    * If you can't code, commission someone to write it for you.  Or spend a
      lot more time making sure that you use the volunteers' free time to your
      best advantage, *i.e.* you need to work hard to make the feature clear
      and easy to implement.


.. _contributing#reporting_bugs:

Reporting bugs
--------------

In order to best solve the problem we need good bug reports. Reports that do
not give a full picture or which coders are unable to reproduce, end up wasting
a lot of time. If you, the expert in your bug, spend a bit of time you can make
sure your bug gets fixed.


First **see if the bug is not already reported**. Perhaps someone already
reported it and you can provide some extra information in that bug report.  You
can also add yourself in the CC field so that you get notified of any changes
to the bug report.

If you could not find the bug, you should report it. Look through each of the
following sections and make sure you have given the information required.


Be verbose
^^^^^^^^^^

Tell us exactly how came to see this bug. Don't say::

    Suggesting doesn't work

Rather say::

    In a translation project with proper permissions when I try to suggest I
    get a 404 error.

So we need to know:

#. What procedure you followed
#. What you got, and
#. What you expected to get


Steps to reproduce
^^^^^^^^^^^^^^^^^^

Tell us exactly how to reproduce the error. Mention the steps if needed, or
give an example. Without being able to reproduce the error, it will not easily
get fixed.


Include tracebacks
^^^^^^^^^^^^^^^^^^

If you are a server administrator you can get this information from the web
server's error log. In case you're hacking on Pootle, the traceback will be
displayed both in the console and the browser.

A traceback will give a much better clue as to what the error might be and send
the coder on the right path. It may be a very simple fix, may relate to your
setup or might indicate a much more complex problem. Tracebacks help coders get
you information quicker.


Be available
^^^^^^^^^^^^

If you can be on `Pootle channel <https://gitter.im/translate/pootle>`_ or the
`mailing list <https://lists.sourceforge.net/lists/listinfo/translate-pootle>`_
to answer questions and test possible fixes then this will help to get your
problem fixed quickly.


.. _contributing#translating:

Translating
-----------

Pootle's User Interface translations are kept in the `official Pootle server
<http://pootle.locamotion.org/>`_. If you have a user in that server, you can
start translating right away. Otherwise, just create a new user and start
translating.

If your language already has a translation and you want to further improve or
complete it, you can contribute suggestions that will later be reviewed by the
language administrators.

If you can't find your language and want to have that added or have concerns of
any other means, contact us on our `mailing list
<https://lists.sourceforge.net/lists/listinfo/translate-pootle>`_ or on the
`Pootle channel <https://gitter.im/translate/pootle>`_.

Although desirable, it's not mandatory to use the official Pootle server to
translate Pootle itself. In case you feel more comfortable working with files
and offline tools, just head to the `code repository at GitHub
<https://github.com/translate/pootle/>`_, create your localization based on the
latest template and submit it to us by `opening a bug
<https://github.com/translate/pootle/issues/new>`_ or by sending us a pull
request.


.. _contributing#documentation:

Documentation
-------------

You can help us documenting Pootle by just mentioning typos, providing reworded
alternatives or by writing full sections.

`Pootle's documentation
<http://docs.translatehouse.org/projects/pootle/en/latest/>`_ is written using
`reStructuredText <http://docutils.sourceforge.net/rst.html>`_ and `Sphinx
<http://sphinx-doc.org/>`_.

If you intend to build the documentation yourself (it's converted from reST to
HTML using Sphinx), you may want to :ref:`setup a development environment
<hacking#setup>` for that.
