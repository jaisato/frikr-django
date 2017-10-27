# -*- coding: utf-8 -*-
from django import forms

from photos.models import Photo
from photos.settings import BADWORDS


class PhotoForm(forms.ModelForm):
	"""
	Form model for photos
	"""
	class Meta:
		model = Photo
		exclude = ['owner']

	# def clean(self):
	# 	"""
	# 	Validation of description. It checks description doesn't contain bad words.
	# 	:return:
	# 	"""
	# 	cleaned_data = super(PhotoForm, self).clean()
	#
	# 	description = self.cleaned_data.get('description', '')
	#
	# 	for bad_word in BADWORDS:
	# 		if bad_word.lower() in description.lower():
	# 			raise forms.ValidationError('The word {0} is not allowed'.format(bad_word))
	#
	# 	return cleaned_data
