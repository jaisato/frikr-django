# -*- coding: utf-8 -*-
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from users.pagination import UserPageNumberPagination
from users.permissions import IsSelfOrStaff, IsStaffOrCreateOnly
from users.serializers import UserSerializer
from rest_framework import status


class UserListAPI(APIView):
	"""
	API view of User list
	"""
	permission_classes = (IsStaffOrCreateOnly,)

	def get(self, request):
		"""
		Get all users
		:param request: Http Request
		:return: Response of users list
		"""
		users = User.objects.all().order_by('pk')
		# pagination
		paginator = UserPageNumberPagination()
		# The return value of paginate_queryset() *is* the page. It was being
		# discarded and the full queryset serialised instead, so every page of
		# the response contained every user in the database - the paging
		# metadata said "page 2 of 7" while the body held all seven pages.
		page = paginator.paginate_queryset(users, request)

		serializer = UserSerializer(page, many=True)

		return paginator.get_paginated_response(serializer.data)

	def post(self, request):
		"""
		Creates new user
		:param request:
		:return:
		"""
		serializer = UserSerializer(data=request.data)
		if serializer.is_valid():
			user = serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		else:
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailAPI(APIView):
	"""
	API view of user detail
	"""
	permission_classes = (IsSelfOrStaff,)
	def get(self, request, id):
		"""
		Gets user detail
		:param request: Http request
		:param id: User id
		:return: Response of user detail
		"""
		user = get_object_or_404(User, pk=id)
		self.check_object_permissions(request, user)
		serializer = UserSerializer(user)

		return Response(serializer.data)

	def put(self, request, id):
		"""
		Updates a given user
		:param request:
		:param id:
		:return:
		"""
		user = get_object_or_404(User, pk=id)
		self.check_object_permissions(request, user)
		serializer = UserSerializer(instance=user, data=request.data)
		if serializer.is_valid():
			serializer.save()
			self.keep_session_after_own_password_change(request, user, serializer.validated_data)
			return Response(serializer.data, status=status.HTTP_200_OK)
		else:
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	@staticmethod
	def keep_session_after_own_password_change(request, user, validated_data):
		"""
		Django signs each session with a hash of the password, so a new password
		ends every session opened with the old one. That is the point for the
		other devices, but the session that made the change was dropped on its
		next request too. update_session_auth_hash() is what Django's own
		PasswordChangeView calls to keep it.

		Only for a session-authenticated user changing their own password: a
		staff member's session has nothing to do with someone else's password,
		and a Basic-auth client has no session - writing the hash would open one
		and send it a cookie it never asked for.
		"""
		if 'password' not in validated_data or user.pk != request.user.pk:
			return

		if isinstance(request.successful_authenticator, SessionAuthentication):
			update_session_auth_hash(request, user)

	def delete(self, request, id):
		"""
		Deletes the given user
		:param request:
		:param id:
		:return:
		"""
		user = get_object_or_404(User, pk=id)
		self.check_object_permissions(request, user)
		user.delete()

		return Response(status=status.HTTP_204_NO_CONTENT)
