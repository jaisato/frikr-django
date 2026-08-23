# -*- coding: utf-8 -*-
from rest_framework import serializers
from models import Photo


class PhotoSerializer(serializers.ModelSerializer):

	class Meta:
		model = Photo
		exclude = []
		read_only_fields = ('owner',)


class PhotoListSerializer(serializers.ModelSerializer):
	"""
	The trimmed shape used for listings.

	This used to subclass PhotoSerializer and its Meta. Inheriting the Meta
	brought `exclude = []` along with it, and ModelSerializer asserts that
	`fields` and `exclude` are never both set - so building this serializer
	raised AssertionError and GET /api/1.0/photos answered 500. Declaring the
	Meta independently is what keeps `fields` the only option in play.
	"""

	class Meta:
		model = Photo
		fields = ('id', 'name', 'url', 'owner')
		read_only_fields = ('owner',)
