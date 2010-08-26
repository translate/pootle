
from django.forms.util import ValidationError
from django.utils.safestring import mark_safe


class FormError(ValidationError):
    pass
class SubmitError(FormError):
    pass
class HandlerError(FormError):
    pass


class View(object):
    def find_post_handler_action(self, request):
        action_names = [action_name for action_name in self.handlers
                        if action_name in set(request.POST)]
        if len(action_names) == 1:
            return action_names[0]
        else:
            raise SubmitError('Only one submit action may be handled per POST')

    def find_handlers(self, forms):
        handlers = {}
        for form in forms.itervalues():
            for action_name, _action_label in form.actions:
                if action_name not in handlers:
                    handlers[action_name] = form
                else:
                    raise HandlerError('More than one form defines the handler %s' % action_name)
        return handlers

    def __init__(self, forms):
        self.handlers = self.find_handlers(forms)
        self.forms = forms

    def __call__(self, request, *args, **kwargs):
        template_vars = {}
        for form_name, form_class in self.forms.iteritems():
            if form_class.must_display(request, *args, **kwargs):
                template_vars[form_name] = form_class(request)
            else:
                template_vars[form_name] = None
        if request.method == 'POST':
            action = self.find_post_handler_action(request)
            form = self.handlers[action](request, data=request.POST, files=request.FILES)
            template_vars.update(form.dispatch(action, request, *args, **kwargs))
        return self.GET(template_vars, request, *args, **kwargs)

    def GET(self, template_vars, request, *args, **kwargs):
        raise NotImplementedError()


class Handler(object):
    Form = None # This should be implemented as an inner class

    actions = [] # This should be all

    @classmethod
    def must_display(cls, request, *args, **kwargs):
        return True

    def __init__(self, request, data=None, files=None):
        self.form = self.Form(data=data, files=files)

    def dispatch(self, action, request, *args, **kwargs):
        handler = getattr(self, action)
        return handler(request, *args, **kwargs)

    def render_submits(self):
        output = u""
        for action in self.actions:
            output += u'<input type="submit" name="%(action_name)s" value="%(action_value)s" />' % {
                'action_name': action[0], 'action_value': unicode(action[1]) }
        return mark_safe(output)

    def as_p(self):
        return mark_safe("""
        %(inner_form)s
        <p class="common-buttons-block">%(submits)s</p>""" % {
            'inner_form': self.form.as_p(),
            'submits': self.render_submits(),
            })
