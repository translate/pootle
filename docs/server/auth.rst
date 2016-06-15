.. _auth:

User Authentication and Authorization
=====================================

Pootle's backend for authenticating and authorizing users is provided by
`django-allauth <https://django-allauth.readthedocs.io/>`_, and it comes
with a heavily-customized client-side user interface.

Note that while Allauth supports local and social sign-in flows, not all
of them have been equally-tested on Pootle, so your mileage might vary.

At the same time, Allauth also provides `tons of settings
<https://django-allauth.readthedocs.io/en/latest/configuration.html>`_
which deployments can configure to their needs, although some of them
clash directly with how our workflow has been designed. For instance,
leaving ``UNIQUE_EMAIL = True`` becomes a hard requirement.


Setting Up a Social Provider
----------------------------

Each third party social authentication provider has its own requirements,
although most of them implement similar protocols (OAuth, OAuth2, OpenID
etc.).

Usually providers require consumers to register their apps on the provider
website. On the Pootle side of things, your provider might need to be
registered as a social app against your host. In order to do this you will
need to insert a few records into your SQL database.

An example with GitHub follows.

GitHub
^^^^^^

1. `Register your app <https://github.com/settings/applications/new>`_
   against your host.

   Application name
      Some descriptive name
   Homepage URL
      URL to your Pootle server, e.g. ``http://foo.bar.tld``
   Application description
      Some descriptive text
   Authorization callback URL
      URL to the callback endpoint of your provider in the Pootle server, e.g.
      ``http://foo.bar.tld/accounts/github/login/callback/``

2. Let Allauth know about your social provider.

.. code-block:: sql

  UPDATE django_site SET DOMAIN = 'foo.bar.tld', name = 'Site name' WHERE id=1;
  INSERT INTO socialaccount_socialapp (provider, name, secret, client_id, 'key')
         VALUES ("github", "GitHub", "---Client-Secret-from-above---",
                 "---Client-ID-from-above---", "");
  INSERT INTO socialaccount_socialapp_sites (socialapp_id, site_id)
         VALUES (1,1);

Note the first line simply sets the domain name for the default site; you
can omit it if it's already up-to-date.

