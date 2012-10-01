.. _captchas:

Captcha support
===============

.. versionadded:: 2.0.5

With Pootle's flexible :doc:`permissions <permissions>` several ways of
interacting with your translation community are possible.  If you have a very
open Pootle server, you might want to ensure that spammers don't abuse it by
enabling `captchas <http://en.wikipedia.org/wiki/CAPTCHA>`_.


.. _captchas#configuration:

Configuration
-------------

.. versionchanged:: 2.1
   Captchas are now enabled by default.


If you have no need for captchas, e.g. at a translation sprint, you might
want to remove captcha support. To disable set :setting:`USE_CAPTCHA` in
*settings/90-local.conf* to ``False``.  Restart your server for the setting
to take effect.


.. _captchas#customization:

Customization
-------------

The captchas can be customized.  Look at the captcha template and code:

- *pootle/templates/captcha.html* and
- *pootle/middleware/captcha.py*

and make the changes you need.
