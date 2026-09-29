# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
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


class LoginRedirectTestCase(TestCase):
	"""
	`?next=` used to be handed straight to redirect(), so
	https://this-site/login/?next=https://evil.example/ sent a user who had
	just logged in on the real domain - which is exactly what makes the trick
	work - onto an attacker-controlled page they now trust.
	"""

	def setUp(self):
		self.password = valid_password()
		self.user = User.objects.create(username='anaruiz', email='ana@example.com')
		self.user.set_password(self.password)
		self.user.save()

	def login(self, next_param):
		return self.client.post(
			reverse('users_login') + '?next=' + next_param,
			{'usr': 'anaruiz', 'pwd': self.password},
		)

	def test_refuses_to_redirect_to_another_host(self):
		response = self.login('https://evil.example/')

		self.assertEqual(response.status_code, 302)
		self.assertNotIn('evil.example', response['Location'])

	def test_refuses_a_protocol_relative_url(self):
		"""
		//evil.example has no scheme, so it reads like a path and slips past a
		naive "does it start with http" check, but a browser treats it as an
		absolute URL to another host.
		"""
		response = self.login('//evil.example/')

		self.assertEqual(response.status_code, 302)
		self.assertNotIn('evil.example', response['Location'])

	def test_still_honours_a_local_next(self):
		response = self.login('/photos/1')

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response['Location'], '/photos/1')


class StaffCannotTakeOverPrivilegedAccountsTestCase(TestCase):
	"""
	PUT on /api/1.0/users/<id> sets the password. Staff used to pass the object
	permission for *any* account, so a staff user could reset a superuser's
	password and log in as them.
	"""

	def setUp(self):
		self.staff_password = valid_password()
		self.staff = User.objects.create_user('staffer', 'staff@example.com', self.staff_password, is_staff=True)
		self.root = User.objects.create_superuser('root', 'root@example.com', valid_password())
		self.plain = User.objects.create_user('plain', 'plain@example.com', valid_password())
		self.client.login(username='staffer', password=self.staff_password)

	def payload(self, username):
		return {
			'first_name': 'X', 'last_name': 'Y', 'username': username,
			'email': username + '@example.com', 'password': valid_password(),
		}

	def test_staff_cannot_modify_or_delete_a_superuser(self):
		url = reverse('user_detail_api', args=[self.root.pk])
		self.assertEqual(self.client.put(url, self.payload('root'), content_type='application/json').status_code, 403)
		self.assertEqual(self.client.delete(url).status_code, 403)
		self.assertTrue(User.objects.filter(pk=self.root.pk).exists())

	def test_staff_can_still_read_and_manage_ordinary_accounts(self):
		self.assertEqual(self.client.get(reverse('user_detail_api', args=[self.root.pk])).status_code, 200)
		url = reverse('user_detail_api', args=[self.plain.pk])
		self.assertEqual(self.client.put(url, self.payload('plain'), content_type='application/json').status_code, 200)
