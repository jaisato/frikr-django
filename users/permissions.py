# -*- coding: utf-8 -*-
from rest_framework import permissions


def is_authenticated(user):
	"""
	User.is_authenticated is a method on Django < 1.10 and a property from 1.10
	on. Reading it as a property on an older release yields a bound method,
	which is always truthy - so a permission written only one way would silently
	let anonymous requests through. Normalise both shapes.
	"""
	if user is None:
		return False

	flag = user.is_authenticated

	return bool(flag() if callable(flag) else flag)


class IsSelfOrStaff(permissions.BasePermission):
	"""
	Only the owner of the account - or a staff member - may read or modify it.

	Without this the user endpoints inherit DRF's default AllowAny, which means
	anybody can PUT /users/<id>/ and the serializer calls set_password() on the
	way through: an unauthenticated account takeover.
	"""

	def has_permission(self, request, view):
		return is_authenticated(request.user)

	def has_object_permission(self, request, view, obj):
		if request.user.is_staff:
			return True

		return obj.pk == request.user.pk


class IsStaffOrCreateOnly(permissions.BasePermission):
	"""
	Anyone may register (POST); listing every account is staff-only.

	Leaving the list open let anyone enumerate usernames and e-mail addresses.
	"""

	def has_permission(self, request, view):
		if request.method == 'POST':
			return True

		return is_authenticated(request.user) and request.user.is_staff
