"""
View which can render and send email from a contact form.

"""

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from contact_form_i18n.forms import ContactForm


def contact_form(request, form_class=ContactForm,
                 template_name='contact_form/contact_form.html',
                 success_url=None, extra_context=None,
                 fail_silently=False):
    """
    Render a contact form, validate its input and send an email
    from it.

    **Optional arguments:**

    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``fail_silently``
        If ``True``, errors when sending the email will be silently
        supressed (i.e., with no logging or reporting of any such
        errors. Default value is ``False``.

    ``form_class``
        The form to use. If not supplied, this will default to
        ``contact_form.forms.ContactForm``. If supplied, the form
        class must implement a method named ``save()`` which sends the
        email from the form; the form class must accept an
        ``HttpRequest`` as the keyword argument ``request`` to its
        constructor, and it must implement a method named ``save()``
        which sends the email and which accepts the keyword argument
        ``fail_silently``.

    ``success_url``
        The URL to redirect to after a successful submission. If not
        supplied, this will default to the URL pointed to by the named
        URL pattern ``contact_form_sent``.

    ``template_name``
        The template to use for rendering the contact form. If not
        supplied, defaults to
        :template:`contact_form/contact_form.html`.

    **Context:**

    ``form``
        The form instance.
    
    **Template:**

    The value of the ``template_name`` keyword argument, or
    :template:`contact_form/contact_form.html`.

    """
    #
    # We set up success_url here, rather than as the default value for
    # the argument. Trying to do it as the argument's default would
    # mean evaluating the call to reverse() at the time this module is
    # first imported, which introduces a circular dependency: to
    # perform the reverse lookup we need access to contact_form/urls.py,
    # but contact_form/urls.py in turn imports from this module.
    #
    
    if success_url is None:
        success_url = reverse('contact_form_sent')
    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES, request=request)
        if form.is_valid():
            form.save(fail_silently=fail_silently)
            return HttpResponseRedirect(success_url)
    else:
        form = form_class(request=request)

    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value
    
    return render_to_response(template_name,
                              { 'form': form },
                              context_instance=context)
