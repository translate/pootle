from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.http import JsonResponse


class PootleAccountAdapter(DefaultAccountAdapter):
    """
    Reimplementation of DefaultAccountAdapter from allauth to change ajax_response

    Differences:
      - the html key is removed for performance reasons
      - form_errors is renamed to errors
    """
    def ajax_response(self, request, response, redirect_to=None, form=None):
        data = {}
        if redirect_to:
            status = 200
            data["location"] = redirect_to

        if form:
            if form.is_valid():
                status = 200
            else:
                status = 400
                data["errors"] = form._errors

        return JsonResponse(data, status=status)

    def is_open_for_signup(self, request):
        """
        Controls whether signups are enabled on the site
        This can be changed by setting CAN_REGISTER = False
        in the settings. Defaults to True.
        """
        return getattr(settings, "CAN_REGISTER", True)
