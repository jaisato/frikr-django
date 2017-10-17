# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.Serializer):
	"""
	User serializer to create and update user instances from serialized data
	"""
	id = serializers.ReadOnlyField() # identifier read only
	first_name = serializers.CharField()
	last_name = serializers.CharField()
	username = serializers.CharField()
	email = serializers.EmailField()
	password = serializers.CharField()

	def create(self, validated_data):
		"""
		Create a user instance from validated data
		:param validated_data: Dictionary with user data
		:return: User object
		"""
		instance = User()

		return self.update(instance, validated_data)

	def update(self, instance, validated_data):
		"""
		Updates a user from validated data
		:param instance: User to be updated
		:param validated_data: Dictionary with user data
		:return:
		"""
		instance.first_name = validated_data.get('first_name')
		instance.last_name = validated_data.get('last_name')
		instance.username = validated_data.get('username')
		instance.email = validated_data.get('email')
		instance.set_password(validated_data.get('password'))

		instance.save()

		return instance
