"""frikr URL Configuration

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
from django.conf.urls import url
from django.contrib import admin
from photos import views as photos
from users import views as users
from django.contrib.auth.decorators import login_required
from users.api import UserListAPI, UserDetailAPI

urlpatterns = [
    # admin URLs
    url(r'^admin/', admin.site.urls),

    # photo URLs
    url(r'^$', photos.HomeView.as_view(), name='photos_home'),
    url(r'^photos/(?P<id>[0-9]+)$', photos.DetailView.as_view(), name='photo_detail'),
    url(r'^photos/new$', photos.CreateView.as_view(), name='photo_create'),
    url(r'^photos$', photos.PhotoListView.as_view(), name='photo_list'),
    url(r'^my-photos$', login_required(photos.UserPhotoListView.as_view()), name='user_photos'),

    # users URLs
    url(r'^login$', users.LoginView.as_view(), name='users_login'),
    url(r'^logout$', users.LogoutView.as_view(), name='users_logout'),

    # User API urls
    url(r'^api/1.0/users$', UserListAPI.as_view(), name='user_list_api'),
    url(r'^api/1.0/users/(?P<id>[0-9]+)$', UserDetailAPI.as_view(), name='user_detail_api'),
]
