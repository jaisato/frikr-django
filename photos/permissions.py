# -*- coding: utf-8 -*-
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
	"""
	Reading a visible photo is open; changing or deleting one is the owner's
	right alone.

	IsAuthenticatedOrReadOnly on its own only asks "are you logged in?", and the
	detail queryset also contains other people's public photos - so any
	authenticated user could edit or delete any public photo in the site.
	"""

	def has_object_permission(self, request, view, obj):
		if request.method in permissions.SAFE_METHODS:
			return True

		if request.user.is_superuser:
			return True

		return obj.owner_id == request.user.pk
