# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
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
	# write_only: the field mirrors User.password, so serialising it handed
	# out the stored hash on every read.
	password = serializers.CharField(write_only=True)

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
		# `.get(field)` returns None for anything absent, so a partial update
		# blanked every field the caller did not send - and `set_password(None)`
		# marks the password unusable, locking the account out for good. Only
		# the keys actually supplied are applied.
		for field in ('first_name', 'last_name', 'username', 'email'):
			if field in validated_data:
				setattr(instance, field, validated_data[field])

		if 'password' in validated_data:
			instance.set_password(validated_data['password'])

		instance.save()

		return instance

	def validate_password(self, data):
		"""
		Runs the project's AUTH_PASSWORD_VALIDATORS.

		settings.py configures four validators (length, common passwords,
		all-numeric, similarity to the user's own attributes), but Django only
		applies them from forms and the admin. This serializer called
		set_password() directly, so none of them ever ran and the API accepted
		"1" as a password - the configuration looked like protection that was
		not actually in place anywhere a user could reach.
		"""
		# UserAttributeSimilarityValidator compares the password against the
		# user's username and e-mail, so it needs the instance to do its job.
		user = self.instance if self.instance else User(
			username=self.initial_data.get('username', ''),
			email=self.initial_data.get('email', ''),
			first_name=self.initial_data.get('first_name', ''),
			last_name=self.initial_data.get('last_name', ''),
		)

		try:
			validate_password(data, user)
		except DjangoValidationError as e:
			# Django and DRF each have their own ValidationError; the one DRF
			# turns into a 400 is its own.
			raise serializers.ValidationError(list(e.messages))

		return data

	def validate_username(self, data):
		users = User.objects.filter(username=data)
		if not self.instance and len(users) != 0:
			raise serializers.ValidationError("Ya existe un usuario con este username")
		elif self.instance and self.instance.username != data and len(users) != 0:
			raise serializers.ValidationError("Ya existe un usuario con este username")
		else:
			return data
