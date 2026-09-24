"""frikr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import re_path
from django.contrib import admin
from photos import views as photos
from photos.api import PhotoListAPI, PhotoDetailAPI
from users import views as users
from django.contrib.auth.decorators import login_required
from users.api import UserListAPI, UserDetailAPI

urlpatterns = [
    # admin URLs
    re_path(r'^admin/', admin.site.urls),

    # photo URLs
    re_path(r'^$', photos.HomeView.as_view(), name='photos_home'),
    re_path(r'^photos/(?P<id>[0-9]+)$', photos.DetailView.as_view(), name='photo_detail'),
    re_path(r'^photos/new$', photos.CreateView.as_view(), name='photo_create'),
    re_path(r'^photos$', photos.PhotoListView.as_view(), name='photo_list'),
    re_path(r'^my-photos$', login_required(photos.UserPhotoListView.as_view()), name='user_photos'),

    # Photo API urls
    re_path(r'^api/1.0/photos$', PhotoListAPI.as_view(), name='photo_list_api'),
    re_path(r'^api/1.0/photos/(?P<pk>[0-9]+)$', PhotoDetailAPI.as_view(), name='photo_detail_api'),

    # users URLs
    re_path(r'^login$', users.LoginView.as_view(), name='users_login'),
    re_path(r'^logout$', users.LogoutView.as_view(), name='users_logout'),

    # User API urls
    re_path(r'^api/1.0/users$', UserListAPI.as_view(), name='user_list_api'),
    re_path(r'^api/1.0/users/(?P<id>[0-9]+)$', UserDetailAPI.as_view(), name='user_detail_api'),
]
