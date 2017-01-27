Frequently Asked Questions (FAQ)
================================

Caught out by a problem installing or running Pootle? We hope you'll find some
answers here.  Ideal candidates are specific installation issues that we can't
integrate into the main docs.  Feel free to provide updates with your own
findings.

Installation
------------

Does Pootle run under Python 3?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pootle does not, yet, support Python 3 but it definitely is a goal.

Our first priority has been cleaning up the code and getting onto the latest
version of Django.  We've achieved that with Pootle 2.8.0.

We also want to be Django warning free, we've also achieved that in Pootle
2.8.0.

All of these where needed to ease to migration to Python 3.

Currently, we're trying to eliminate Python 2 specific changes and we're coding
pylint checks to prevent any regression.

If you want to help make this happen sooner, patches are welcome.


ModuleNotFoundError: No module named 'syspath_override'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: pytb

    File "/home/pootle/env/lib/python3.6/site-packages/pootle/runner.py", line 19, in <module>
       import syspath_override  # noqa
     ModuleNotFoundError: No module named 'syspath_override'

You are running Pootle using Python 3, change your virtual environment to
Python 2 and try again.

Something like this will be needed to setup your virtual environment.

.. code:: console

   $ mkvirtualenv --python=/path/to/python2 pootle
