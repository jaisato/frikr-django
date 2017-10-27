# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from photos.settings import BADWORDS


def badwords_detector(value):
	"""
	Validate whether there's any badword on value. Badwords defined in settings.BADWORDS
	:param value:
	:return: Boolean
	"""
	for badword in BADWORDS:
		if badword.lower() in value.lower():
			raise ValidationError('Word {0} is not allowed'.format(badword))

	return True
