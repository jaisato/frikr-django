# -*- coding: utf-8 -*-
from rest_framework import serializers
from models import Photo


class PhotoSerializer(serializers.ModelSerializer):

	class Meta:
		model = Photo
		exclude = []
		read_only_fields = ('owner',)


class PhotoListSerializer(PhotoSerializer):

	class Meta(PhotoSerializer.Meta):
		fields = ('id', 'name', 'url', 'owner')
		read_only_fields = ('owner',)
