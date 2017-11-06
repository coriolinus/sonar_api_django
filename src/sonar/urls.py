"""sonar URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
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
from user.views import UserViewSet

from django.conf.urls import url
from hashtags.views import HashtagViewSet
from mentions.views import MentionsViewSet
from ping.views import PingViewSet
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token
from timeline.views import TimelineViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'pings', PingViewSet)
router.register(r'timeline', TimelineViewSet, 'timeline')
router.register(r'mentions', MentionsViewSet, 'mentions')
router.register(r'hashtags', HashtagViewSet, 'hashtag')

urlpatterns = router.urls
urlpatterns += [
    url(r'^get-token/', obtain_auth_token)
]
