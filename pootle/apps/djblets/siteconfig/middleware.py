from djblets.siteconfig.models import SiteConfiguration


class SettingsMiddleware(object):
    """
    Middleware that performs necessary operations for siteconfig settings.

    Right now, the primary responsibility is to check on each request if
    the settings have expired, so that a web server worker process doesn't
    end up with a stale view of the site settings.
    """
    def process_request(self, request):
        SiteConfiguration.objects.check_expired()
