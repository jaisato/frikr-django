# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponseNotFound
from django.urls import reverse
from django.utils.decorators import method_decorator

from photos.forms import PhotoForm
from photos.models import Photo, PUBLIC
from django.views.generic import View


class HomeView(View):
	def get(self, request):
		"""
		Shows the photo homepage
		:param request:
		:return:
		"""
		photos = Photo.objects.filter(visibility=PUBLIC).order_by('-created_at')

		photosView = []
		for photo in photos[:5]:
			photoData = {"id": photo.pk, "name": photo.name, "url": photo.url, "description": photo.description}
			photosView.append(photoData)

		return render(request, 'photos/home.html', {"photos": photosView})


class DetailView(View):
	def get(self, request, id):
		"""
		Renders Photo detail page
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
		photos = Photo.objects.filter(pk=id).select_related('owner')
		if len(photos) == 1:
			photo = photos[0]
		else:
			photo = None

		if photo is not None:
			return render(request, 'photos/detail.html', {"photo": photo})
		else:
			return HttpResponseNotFound("Photo {0} not found".format(id))


class CreateView(View):

	@method_decorator(login_required())
	def get(self, request):
		"""
		Renders a form to create a new photo
		:param request:
		:return:
		"""
		context = {
			'form': PhotoForm()
		}
		return render(request, 'photos/new_photo.html', context)

	@method_decorator(login_required())
	def post(self, request):
		"""
		Creates new photo from form model
		:param request:
		:return:
		"""
		success_message = ''
		photo_with_owner = Photo()
		photo_with_owner.owner = request.user
		form = PhotoForm(request.POST, instance=photo_with_owner)

		if form.is_valid():
			photo = form.save() # genera el objeto del formulario, lo guarda en BD y lo devuelve
			success_message = 'Guardado con éxito! '
			success_message += '<a href="{0}"'.format(reverse('photo_detail', args=[photo.pk])) + '>'
			success_message += 'Ver Foto'
			success_message += '</a>'

		context = {
			'form': form,
			'success_message': success_message
		}
		return render(request, 'photos/new_photo.html', context)
