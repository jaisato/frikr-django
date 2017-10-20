# -*- coding: utf-8 -*-
from rest_framework.generics import ListCreateAPIView
from models import Photo
from photos.serializers import PhotoSerializer


class PhotoListAPI(ListCreateAPIView):
	queryset = Photo.objects.all()
	serializer_class = PhotoSerializer
