# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from users.serializers import UserSerializer


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
		users = User.objects.all()
		serializer = UserSerializer(users, many=True)

		return Response(serializer.data)


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
