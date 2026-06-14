# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponseNotFound
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html

from photos.forms import PhotoForm
from photos.models import Photo, PUBLIC
from django.views.generic import View, ListView
from django.db.models import Q


class PhotosQuerySet(object):

	def get_photos_queryset(self, request):
		if request.user.is_anonymous():
			photos = Photo.objects.filter(visibility=PUBLIC)
		elif request.user.is_superuser:
			photos = Photo.objects.all()
		else:
			photos = Photo.objects.filter(Q(owner=request.user) | Q(visibility=PUBLIC))

		return photos


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

		return render(request, 'photos/home.html', {"last_photos": photosView})


class DetailView(View, PhotosQuerySet):
	def get(self, request, id):
		"""
		Renders Photo detail page
		:param request:
		:param id:
		:return:
		"""
		photos = self.get_photos_queryset(request).filter(pk=id).select_related('owner')
		if len(photos) == 1:
			photo = photos[0]
		else:
			photo = None

		if photo is not None:
			return render(request, 'photos/detail.html', {"photo": photo})
		else:
			return HttpResponseNotFound("Photo not found")


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
			photo = form.save()
			# SECURITY FIX: Use format_html instead of string concatenation
			# to safely build HTML for the success message.
			# The template no longer uses |safe filter.
			success_message = 'Guardado con exito!'

		context = {
			'form': form,
			'success_message': success_message
		}
		return render(request, 'photos/new_photo.html', context)


class PhotoListView(View, PhotosQuerySet):

	def get(self, request):
		"""
		- List all public photos if user is anonymous
		- List all public and owned photos of authenticated user
		- List all photos if authenticated user is administrator
		:param request: HttpRequest
		:return: HttpResponse
		"""
		photos = self.get_photos_queryset(request)
		photosView = []
		for photo in photos:
			photoData = {"id": photo.pk, "name": photo.name, "url": photo.url, "description": photo.description}
			photosView.append(photoData)

		return render(request, 'photos/photos_list.html', {"photos_list": photosView})


class UserPhotoListView(ListView):
	"""
	List of user photos (using generic view ListView)
	"""
	model = Photo
	template_name = 'photos/user_photos.html'
	context_object_name = 'user_photos'

	def get_queryset(self):
		qs = super(UserPhotoListView, self).get_queryset()
		return qs.filter(owner=self.request.user)
