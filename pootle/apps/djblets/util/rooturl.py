from django.conf import settings
from django.conf.urls.defaults import patterns, include, handler404, handler500
from django.core.exceptions import ImproperlyConfigured


# Ensures that we can run nose on this without needing to set SITE_ROOT.
# Also serves to let people know if they set one variable without the other.
if hasattr(settings, "SITE_ROOT"):
    if not hasattr(settings, "SITE_ROOT_URLCONF"):
        raise ImproperlyConfigured("SITE_ROOT_URLCONF must be set when "
                                   "using SITE_ROOT")

    urlpatterns = patterns('',
        (r'^%s' % settings.SITE_ROOT[1:], include(settings.SITE_ROOT_URLCONF)),
    )
