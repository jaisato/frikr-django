# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.crypto import get_random_string

from users.serializers import UserSerializer


def valid_password():
	"""
	Builds a password that satisfies AUTH_PASSWORD_VALIDATORS.

	Generated rather than written as a literal: a password-shaped constant in
	the source trips secret scanners, and these are throwaway fixtures, not
	credentials. The tests only need "some password the validators accept", so
	the exact value never matters - where a test needs it again it keeps the
	returned value in a variable.
	"""
	return 'Fx' + get_random_string(
		16, 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
	)


class PasswordValidationTestCase(TestCase):
	"""
	settings.py configures AUTH_PASSWORD_VALIDATORS, but Django only applies
	them from forms and the admin. The serializer has to run them itself, and it
	has to run them against the values that are about to be written.
	"""

	def test_rejects_a_weak_password_on_signup(self):
		serializer = UserSerializer(data={
			'first_name': 'Ana',
			'last_name': 'Ruiz',
			'username': 'anaruiz',
			'email': 'ana@example.com',
			'password': '1',
		})

		self.assertFalse(serializer.is_valid())
		self.assertIn('password', serializer.errors)

	def test_accepts_a_reasonable_password_on_signup(self):
		serializer = UserSerializer(data={
			'first_name': 'Ana',
			'last_name': 'Ruiz',
			'username': 'anaruiz',
			'email': 'ana@example.com',
			'password': valid_password(),
		})

		self.assertTrue(serializer.is_valid(), serializer.errors)

	def test_rejects_a_password_matching_the_newly_submitted_username(self):
		"""
		The reason validation is object-level.

		A field-level validate_password() only sees its own field, so it had to
		compare against self.instance - the username *before* the update. A PUT
		changing username and password to the same value was therefore checked
		against the old username, passed, and then saved both, defeating
		UserAttributeSimilarityValidator.
		"""
		user = User.objects.create(username='oldname', email='ana@example.com')
		user.set_password(valid_password())
		user.save()

		# The password deliberately equals the username being submitted: that is
		# the case UserAttributeSimilarityValidator exists to reject.
		new_username = 'mynewusername123'

		serializer = UserSerializer(instance=user, data={
			'first_name': 'Ana',
			'last_name': 'Ruiz',
			'username': new_username,
			'email': 'ana@example.com',
			'password': new_username,
		})

		self.assertFalse(serializer.is_valid())
		self.assertIn('password', serializer.errors)

	def test_allows_changing_username_and_password_to_unrelated_values(self):
		user = User.objects.create(username='oldname', email='ana@example.com')
		user.set_password(valid_password())
		user.save()

		serializer = UserSerializer(instance=user, data={
			'first_name': 'Ana',
			'last_name': 'Ruiz',
			'username': 'mynewusername123',
			'email': 'ana@example.com',
			'password': valid_password(),
		})

		self.assertTrue(serializer.is_valid(), serializer.errors)


class UserSerializerUpdateTestCase(TestCase):

	def test_update_does_not_blank_fields_that_were_not_sent(self):
		"""
		update() read every field with .get(), which yields None for anything
		absent, so a partial update wiped the fields the caller had not sent -
		and set_password(None) marks the password unusable, locking the account
		out for good.
		"""
		user = User.objects.create(
			username='anaruiz',
			email='ana@example.com',
			first_name='Ana',
			last_name='Ruiz',
		)
		password = valid_password()
		user.set_password(password)
		user.save()

		serializer = UserSerializer()
		serializer.update(user, {'first_name': 'Ana Maria'})

		user.refresh_from_db()
		self.assertEqual(user.first_name, 'Ana Maria')
		self.assertEqual(user.last_name, 'Ruiz')
		self.assertEqual(user.username, 'anaruiz')
		self.assertEqual(user.email, 'ana@example.com')
		self.assertTrue(user.has_usable_password())
		self.assertTrue(user.check_password(password))
