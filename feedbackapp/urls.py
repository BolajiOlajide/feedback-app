"""feedbackapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from feedback import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.AuthenticationView.as_view(), name='homepage'),
    url(r'^feedback/', include('feedback.urls')),
    url(r'^messenger/', include('messenger.urls', namespace='messenger')),

]

handler404 = 'feedback.views.custom_404'
handler500 = 'feedback.views.custom_500'
