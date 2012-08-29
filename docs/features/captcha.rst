.. _captchas:

Captcha support
===============

.. versionadded:: 2.0.5

With Pootle's flexible :doc:`permissions <permissions>` several ways of
interacting with your translation community are possible.  If you have a very
open Pootle server, you might want to ensure that spammers don't abuse it.

Read more about `captchas on Wikipedia
<http://en.wikipedia.org/wiki/CAPTCHA>`_.


.. _captchas#configuration:

Configuration
-------------

.. versionchanged:: 2.1
   Captchas are now enabled by default.


Enable the setting ``USE_CAPTCHA`` in your *localsettings.py*, and restart your
server.


.. _captchas#customization:

Customization
-------------

To customize the captchas have a look at the template and the code using it:

- *templates/captcha.html* and
- *pootle/middleware/captcha.py*
