from allauth.account.adapter import DefaultAccountAdapter
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
