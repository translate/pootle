# myapp/siteconfig.py
# NOTE: Import this file in your urls.py or some place before
#       any code relying on settings is imported.
from django.contrib.sites.models import Site
 
from djblets.siteconfig.models import SiteConfiguration
from django.conf import settings
 
from djblets.siteconfig.django_settings import apply_django_settings, generate_defaults
 
defaults = {
    'DESCRIPTION' : """<div dir="ltr" lang="en">This is a demo installation of Pootle.<br /> You can also visit the official <a href="http://pootle.locamotion.org">Pootle server</a>. The server administrator has not provided contact information or a description of this server. If you are the administrator for this server, edit this description in your preference file or in the administration interface.</div>""",
    'TITLE' : "Pootle Demo",
}

settings_map = {
    # siteconfig key    settings.py key
    'DESCRIPTION':        'DESCRIPTION',
    'TITLE'      :        'TITLE',
}

defaults.update(generate_defaults(settings_map))
 
def load_site_config():
    """Sets up the SiteConfiguration, provides defaults and syncs settings."""
    try:
        siteconfig = SiteConfiguration.objects.get_current()
    except SiteConfiguration.DoesNotExist:
        # Either warn or just create the thing. Depends on your app
        siteconfig = SiteConfiguration(site=Site.objects.get_current(),
                                       version="1.0")
        siteconfig.save()
 
    # Code will go here for settings work in later examples.
    if not siteconfig.get_defaults():
        siteconfig.add_defaults(defaults)
    apply_django_settings(siteconfig, settings_map)
 
 
load_site_config()
