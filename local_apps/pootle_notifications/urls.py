
from feeds import LanguageFeeds
from django.conf.urls.defaults import *

feeds = {
        'lang': LanguageFeeds
        }

urlpatterns = patterns('',
    (r'^language/$', 'language_notice'),
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
                {'feed_dict': feeds}),

)
