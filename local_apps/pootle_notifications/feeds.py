
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from pootle_notifications.models import Notice
from pootle_app.models import Language, Project, TranslationProject
from django.core.exceptions import ObjectDoesNotExist
from pootle.i18n.gettext import tr_lang
from django.contrib.syndication import feeds
from django.http import HttpResponse, Http404
from django.utils.translation import ugettext as _

def NoticeFeeds(request, url):
    param = ''
    try:
        default_param = url.split('/')
        if len(default_param) == 1 :
            f = LanguageFeeds
            param = default_param[0]
        elif len(default_param) == 2 :
            f = TransProjectFeeds
            param = default_param[0] + "/" + default_param[1]

        else:
            f = ''
    except ValueError:
        slug, param = url, ''

    try:
        feedgen = f(None, request).get_feed(param)
    except feeds.FeedDoesNotExist:
        raise Http404, "Invalid feed parameters. Slug %r is valid, but other parameters, or lack thereof, are not." % slug

    response = HttpResponse(mimetype=feedgen.mime_type)
    feedgen.write(response, 'utf-8')
    return response

class LanguageFeeds(Feed):
    """
    Hard-coded link, description and title as this is a test app.
    """
    link = "/feeds/"
    description = "Feeds for language notices"
    #title = "Language Feeds"
    
    def get_object(self, bits):

        """
        Get object_id and content_type_id based on bits
        """
        lang = Language.objects.get(code=bits[0])
        content = Notice(content_object = lang)
        return content

    def title(self, obj):
        lang = Language.objects.get(id = obj.object_id)
        return _('Feeds for  %(language)s',{"language": tr_lang(lang.fullname)})
    def items(self, obj):
        return Notice.objects.get_notices(obj)

    

class TransProjectFeeds(Feed):
    """
    Hard-coded link, description and title as this is a test app.
    """
    link = "/feeds/"
    description = "Feeds for translation project  notices"
    title = "Translation project Feeds"
    
    def get_object(self, bits):

        """
        Get object_id and content_type_id based on bits
        """
        real_path = bits[1] + "/" + bits[0]
        trans_proj = TranslationProject.objects.get(real_path=real_path)
        content = Notice(content_object = trans_proj)
        return content

    def items(self, obj):
        return Notice.objects.get_notices(obj)
   

class ProjectFeeds(Feed):
    """
    Hard-coded link, description and title as this is a test app.
    """
    link = "/feeds/"
    description = "Feeds for project notices"
    title = "Project Feeds"
    
    def get_object(self, bits):

        """
        Get object_id and content_type_id based on bits
        """
        proj = Project.objects.get(code=bits[0])
        content = Notice(content_object = proj)
        return content

    def items(self, obj):
        return Notice.objects.get_notices(obj)

    def item_link(self, obj):
        return "/noticelink/"

