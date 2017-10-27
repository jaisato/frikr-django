# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from users.pagination import UserPageNumberPagination
from users.serializers import UserSerializer
from rest_framework import status


class UserListAPI(APIView):
	"""
	API view of User list
	"""

	def get(self, request):
		"""
		Get all users
		:param request: Http Request
		:return: Response of users list
		"""
		users = User.objects.filter()
		# pagination
		paginator = UserPageNumberPagination()
		paginator.paginate_queryset(users, request)

		serializer = UserSerializer(users, many=True)

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
	def get(self, request, id):
		"""
		Gets user detail
		:param request: Http request
		:param id: User id
		:return: Response of user detail
		"""
		user = get_object_or_404(User, pk=id)
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
		serializer = UserSerializer(instance=user, data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_200_OK)
		else:
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, id):
		"""
		Deletes the given user
		:param request:
		:param id:
		:return:
		"""
		user = get_object_or_404(User, pk=id)
		user.delete()

		return Response(status=status.HTTP_204_NO_CONTENT)
