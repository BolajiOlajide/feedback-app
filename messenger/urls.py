from django.conf.urls import url
from views import (
    ConversationListView,
    ConversationView,
    ConversationStartView,
    ConversationSlackJoinView,
)


urlpatterns = [

    url(r'^conversations/$',
        ConversationListView.as_view(),
        name='conversations'
        ),
    url(r'^conversations/start/$',
        ConversationStartView.as_view(),
        name='conversation_start'
        ),
    url(r'^conversations/(?P<pk>\d+)/$',
        ConversationView.as_view(),
        name='conversation'
        ),
    url(r'^conversations/(?P<join_hash>[\w,\W]+)/slack_join/$',
        ConversationSlackJoinView.as_view(),
        name='conversation_slack_join'
        ),
]
