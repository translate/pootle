

from django.views.generic import FormView, TemplateView

from pootle.core.views.mixins import SuperuserRequiredMixin


class PootleAdminView(SuperuserRequiredMixin, TemplateView):
    pass


class PootleAdminFormView(SuperuserRequiredMixin, FormView):
    pass
