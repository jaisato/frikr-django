# -*- coding: utf-8 -*-
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from photos.models import Photo
from photos.serializers import PhotoSerializer, PhotoListSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly, BasePermission, SAFE_METHODS
from photos.views import PhotosQuerySet


class IsOwnerOrReadOnly(BasePermission):
	"""
	Allows read-only access to anyone permitted by the queryset, but restricts
	write/update/delete operations to the photo's owner.
	"""

	def has_object_permission(self, request, view, obj):
		if request.method in SAFE_METHODS:
			return True

		return obj.owner_id == request.user.id


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
	permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)

	def get_queryset(self):
		return self.get_photos_queryset(self.request)
