# -*- coding: utf-8 -*-
from django.conf import settings

COPYRIGHT = 'RIG'
COPYLEFT = 'LEF'
CREATIVE_COMMONS = 'CC'

DEFAULT_LICENSES = (
	(COPYRIGHT, 'Copyright'),
	(COPYLEFT, 'Copyleft'),
	(CREATIVE_COMMONS, 'Creative Commons')
)

LICENSES = DEFAULT_LICENSES + getattr(settings, 'LICENSES', ())

BADWORDS = getattr(settings, 'PROJECT_BADWORDS', [])
