.. _captchas:

Captcha Support
===============

With Pootle's flexible :doc:`permissions <permissions>` several ways of
interacting with your translation community are possible.  If you have a very
open Pootle server, you might want to ensure that spammers don't abuse it by
enabling :wp:`captchas <CAPTCHA>`.


.. _captchas#configuration:

Configuration
-------------

If you have no need for captchas, e.g. at a translation sprint, you might want
to remove captcha support. To disable it, set :setting:`POOTLE_CAPTCHA_ENABLED`
in your configuration file to ``False``.  Restart your server for the setting
to take effect.


.. _captchas#customization:

Customization
-------------

The captchas can be customized.  Look at the captcha template and code:

- *pootle/templates/captcha.html* and
- *pootle/middleware/captcha.py*

and make the changes you need.
