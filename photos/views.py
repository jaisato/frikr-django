# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse

from photos.models import Photo, PUBLIC


def home(request):
	photos = Photo.objects.filter(visibility=PUBLIC).order_by('-created_at')

	photosView = []
	for photo in photos[:5]:
		photoData = {"name": photo.name, "url": photo.url, "description": photo.description}
		photosView.append(photoData)

	return render(request, 'photos/home.html', {"photos": photosView})


