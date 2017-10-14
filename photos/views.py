# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound

from photos.models import Photo, PUBLIC

def home(request):
	photos = Photo.objects.filter(visibility=PUBLIC).order_by('-created_at')

	photosView = []
	for photo in photos[:5]:
		photoData = {"id": photo.pk, "name": photo.name, "url": photo.url, "description": photo.description}
		photosView.append(photoData)

	return render(request, 'photos/home.html', {"photos": photosView})


def detail(request, id):
	"""
	Photo detail
	:param request:
	:param id:
	:return:
	"""
	"""
	try:
		photo = Photo.objects.get(pk=id)
	except Photo.DoesNotExist:
		photo = None
	except Photo.MultipleObjects:
		photo = photo[0]
	"""
	photos = Photo.objects.filter(pk=id)
	if len(photos) == 1:
		photo = photos[0]
	else:
		photo = None

	if photo is not None:
		return render(request, 'photos/detail.html', {"photo": photo})
	else:
		return HttpResponseNotFound("Photo {0} not found".format(id))
