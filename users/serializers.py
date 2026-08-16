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

	def validate(self, attrs):
		"""
		Runs the project's AUTH_PASSWORD_VALIDATORS.

		settings.py configures four validators (length, common passwords,
		all-numeric, similarity to the user's own attributes), but Django only
		applies them from forms and the admin. This serializer called
		set_password() directly, so none of them ever ran and the API accepted
		"1" as a password - the configuration looked like protection that was
		not actually in place anywhere a user could reach.

		This is an object-level validator rather than validate_password() on
		purpose. UserAttributeSimilarityValidator compares the password against
		the user's own username, e-mail and name; a field-level validator only
		receives its own field, so it had to read those from self.instance -
		the values as they are *before* the update. A PUT that changed the
		username and the password together was therefore checked against the
		old username and then saved both, so submitting the same value for
		username and password passed a rule that exists to reject exactly that.

		By the time validate() runs, every field has been collected, so the
		comparison uses the values that are actually about to be written.
		"""
		password = attrs.get('password')

		if password is None:
			return attrs

		# What the user will look like once this request is applied: the
		# submitted values, falling back to what the instance already holds for
		# anything the request did not send.
		def field(name):
			if name in attrs:
				return attrs[name]
			return getattr(self.instance, name, '') if self.instance else ''

		prospective = User(
			username=field('username'),
			email=field('email'),
			first_name=field('first_name'),
			last_name=field('last_name'),
		)

		try:
			validate_password(password, prospective)
		except DjangoValidationError as e:
			# Django and DRF each have their own ValidationError; the one DRF
			# turns into a 400 is its own. Keying it to `password` puts the
			# messages on the field they belong to.
			raise serializers.ValidationError({'password': list(e.messages)})

		return attrs

	def validate_username(self, data):
		users = User.objects.filter(username=data)
		if not self.instance and len(users) != 0:
			raise serializers.ValidationError("Ya existe un usuario con este username")
		elif self.instance and self.instance.username != data and len(users) != 0:
			raise serializers.ValidationError("Ya existe un usuario con este username")
		else:
			return data
