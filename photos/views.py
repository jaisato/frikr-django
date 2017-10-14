# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse

from photos.models import Photo


def home(request):
	photos = Photo.objects.all()

	photosView = []
	for photo in photos:
		photoData = {"name": photo.name, "url": photo.url, "description": photo.description}
		photosView.append(photoData)

	return render(request, 'photos/home.html', {"photos": photosView})


