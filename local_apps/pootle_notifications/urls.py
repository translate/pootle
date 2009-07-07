
from feeds import LanguageFeeds
from django.conf.urls.defaults import *
from pootle_notifications.views import lang_notice, proj_notice, transproj_notices, index
feeds = {
        'lang': LanguageFeeds
        }

urlpatterns = patterns('',
    (r'^notice/$', index),
    (r'^notice/lang/$', lang_notice),
    (r'^notice/proj/$', proj_notice),
    (r'^notice/transproj/$', transproj_notices),
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
                {'feed_dict': feeds}),

)
