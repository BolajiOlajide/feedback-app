from django.conf.urls import url
from feedback import views


urlpatterns = [

    url(r'^user/authenticate/$',
        views.GoogleAuthenticateView.as_view(),
        name='verify'
        ),

    url(r'^user/home/$',
        views.UserHomeView.as_view(),
        name='dashboard'
        ),

]
