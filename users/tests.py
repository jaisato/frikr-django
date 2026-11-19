# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase
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


class UserSerializerFieldLimitsTestCase(TestCase):
	"""
	The serializer is a plain Serializer, so it does not inherit the User
	model's limits; it has to declare them or the database is the first thing
	to notice (a 500 on PostgreSQL/MySQL).
	"""

	def data(self, **overrides):
		data = {
			'first_name': 'Ana', 'last_name': 'Ruiz', 'username': 'anaruiz',
			'email': 'ana@example.com', 'password': valid_password(),
		}
		data.update(overrides)
		return data

	def test_rejects_values_longer_than_the_user_columns(self):
		for field in ('first_name', 'last_name', 'username'):
			serializer = UserSerializer(data=self.data(**{field: 'a' * 151}))
			self.assertFalse(serializer.is_valid(), field)
			self.assertIn(field, serializer.errors)

	def test_rejects_usernames_django_itself_would_reject(self):
		serializer = UserSerializer(data=self.data(username='ana <b>ruiz</b>'))
		self.assertFalse(serializer.is_valid())
		self.assertIn('username', serializer.errors)

	def test_accepts_the_usual_username_characters(self):
		serializer = UserSerializer(data=self.data(username='ana.ruiz+test@home_1-x'))
		self.assertTrue(serializer.is_valid(), serializer.errors)


class UsernameUniquenessTestCase(TestCase):
	"""
	Usernames that differ only in case let a newcomer pass for an existing
	account ("Admin" next to "admin"); Django's UserCreationForm rejects them.
	"""

	def data(self, username):
		return {
			'first_name': 'Ana', 'last_name': 'Ruiz', 'username': username,
			'email': 'ana@example.com', 'password': valid_password(),
		}

	def test_rejects_a_username_that_only_differs_in_case(self):
		User.objects.create_user('admin', 'admin@example.com', valid_password())

		serializer = UserSerializer(data=self.data('Admin'))

		self.assertFalse(serializer.is_valid())
		self.assertIn('username', serializer.errors)

	def test_rejects_renaming_onto_another_account_in_a_different_case(self):
		User.objects.create_user('admin', 'admin@example.com', valid_password())
		user = User.objects.create_user('anaruiz', 'ana@example.com', valid_password())

		serializer = UserSerializer(instance=user, data=self.data('ADMIN'))

		self.assertFalse(serializer.is_valid())
		self.assertIn('username', serializer.errors)

	def test_lets_a_user_change_the_case_of_their_own_username(self):
		user = User.objects.create_user('anaruiz', 'ana@example.com', valid_password())

		serializer = UserSerializer(instance=user, data=self.data('AnaRuiz'))

		self.assertTrue(serializer.is_valid(), serializer.errors)

	def test_an_account_with_a_pre_existing_case_duplicate_can_still_update_itself(self):
		# The database index is case-sensitive, so both rows may already exist.
		# The view always sends the full object, unchanged username included.
		User.objects.create_user('admin', 'admin@example.com', valid_password())
		user = User.objects.create_user('Admin', 'other@example.com', valid_password())

		serializer = UserSerializer(instance=user, data=self.data('Admin'))

		self.assertTrue(serializer.is_valid(), serializer.errors)

	def test_put_on_the_own_profile_succeeds_despite_a_case_duplicate(self):
		User.objects.create_user('admin', 'admin@example.com', valid_password())
		password = valid_password()
		user = User.objects.create_user('Admin', 'other@example.com', password)
		self.client.login(username='Admin', password=password)

		response = self.client.put(
			reverse('user_detail_api', args=[user.pk]), self.data('Admin'), content_type='application/json',
		)

		self.assertEqual(response.status_code, 200, response.content)


class ProfileUpdateKeepsTheSessionTestCase(TestCase):
	"""
	PUT /api/1.0/users/<id> demanded the password on every update and re-hashed
	it. Django signs each session with a hash of the password, so editing your
	own e-mail logged you out on the next request, and staff could not correct
	someone's name without resetting that person's password.
	"""

	def setUp(self):
		self.password = valid_password()
		self.user = User.objects.create_user(
			'anaruiz', 'ana@example.com', self.password, first_name='Ana', last_name='Ruiz')
		self.url = reverse('user_detail_api', args=[self.user.pk])
		self.client.login(username='anaruiz', password=self.password)

	def data(self, **changes):
		data = {'first_name': 'Ana', 'last_name': 'Ruiz', 'username': 'anaruiz', 'email': 'ana@example.com'}
		data.update(changes)
		return data

	def put(self, client=None, **changes):
		client = client or self.client
		return client.put(self.url, self.data(**changes), content_type='application/json')

	def assertLoggedIn(self, client, logged_in=True):
		status_code = client.get(reverse('user_photos')).status_code
		self.assertEqual(status_code, 200 if logged_in else 302)

	def test_an_update_without_a_password_keeps_it_and_the_session(self):
		response = self.put(email='nueva@example.com')

		self.assertEqual(response.status_code, 200, response.content)
		self.user.refresh_from_db()
		self.assertEqual(self.user.email, 'nueva@example.com')
		self.assertTrue(self.user.check_password(self.password))
		self.assertLoggedIn(self.client)

	def test_changing_the_own_password_keeps_the_session_that_changed_it(self):
		new_password = valid_password()

		response = self.put(password=new_password)

		self.assertEqual(response.status_code, 200, response.content)
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password(new_password))
		self.assertLoggedIn(self.client)

	def test_changing_the_password_still_ends_the_other_sessions(self):
		other_device = Client()
		other_device.login(username='anaruiz', password=self.password)

		self.put(password=valid_password())

		self.assertLoggedIn(other_device, logged_in=False)

	def test_a_basic_auth_password_change_does_not_open_a_session(self):
		client = Client()
		credentials = base64.b64encode(('anaruiz:' + self.password).encode()).decode()

		response = client.put(
			self.url, self.data(password=valid_password()), content_type='application/json',
			HTTP_AUTHORIZATION='Basic ' + credentials,
		)

		self.assertEqual(response.status_code, 200, response.content)
		self.assertNotIn(settings.SESSION_COOKIE_NAME, response.cookies)

	def test_staff_can_edit_an_account_without_resetting_its_password(self):
		staff_password = valid_password()
		User.objects.create_user('staffer', 'staff@example.com', staff_password, is_staff=True)
		staff = Client()
		staff.login(username='staffer', password=staff_password)

		response = self.put(client=staff, first_name='Ana Maria')

		self.assertEqual(response.status_code, 200, response.content)
		self.user.refresh_from_db()
		self.assertEqual(self.user.first_name, 'Ana Maria')
		self.assertTrue(self.user.check_password(self.password))
		self.assertLoggedIn(self.client)

	def test_staff_resetting_a_password_leaves_the_staff_session_untouched(self):
		staff_password = valid_password()
		User.objects.create_user('staffer', 'staff@example.com', staff_password, is_staff=True)
		staff = Client()
		staff.login(username='staffer', password=staff_password)
		session_key = staff.session.session_key

		response = self.put(client=staff, password=valid_password())

		self.assertEqual(response.status_code, 200, response.content)
		# The staff session is not re-keyed and no cookie is sent again: only
		# the sessions of the account whose password changed are affected.
		self.assertNotIn(settings.SESSION_COOKIE_NAME, response.cookies)
		self.assertEqual(staff.session.session_key, session_key)
		self.assertLoggedIn(staff)
		self.assertLoggedIn(self.client, logged_in=False)

	def test_signing_up_still_requires_a_password(self):
		response = Client().post(
			reverse('user_list_api'), self.data(username='nuevo', email='nuevo@example.com'),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn('password', response.json())
