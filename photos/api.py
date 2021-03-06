# -*- coding: utf-8 -*-
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from models import Photo
from photos.serializers import PhotoSerializer, PhotoListSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from photos.views import PhotosQuerySet


class PhotoListAPI(PhotosQuerySet, ListCreateAPIView):
	queryset = Photo.objects.all()
	serializer_class = PhotoListSerializer
	permission_classes = (IsAuthenticatedOrReadOnly,)

	def get_serializer_class(self):
		return PhotoSerializer if self.request.method == "POST" else PhotoListSerializer

	def get_queryset(self):
		return self.get_photos_queryset(self.request)

	def perform_create(self, serializer):
		serializer.save(owner=self.request.user)


class PhotoDetailAPI(PhotosQuerySet, RetrieveUpdateDestroyAPIView):
	queryset = Photo.objects.all()
	serializer_class = PhotoSerializer
	permission_classes = (IsAuthenticatedOrReadOnly,)

	def get_queryset(self):
		return self.get_photos_queryset(self.request)
