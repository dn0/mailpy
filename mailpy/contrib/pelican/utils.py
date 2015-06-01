# -*- coding: utf-8 -*-
from __future__ import absolute_import

import re
import unicodedata


def stringify(value):
    """Convert unicode to ascii"""
    try:
        value = unicodedata.normalize('NFKD', value)
    except TypeError:
        pass

    return value.encode('ascii', 'ignore').decode('ascii')


def slugify(value):
    """Return value suitable for filename (taken from django.utils.text.slugify)"""
    value = re.sub('[^\w\s-]', '', stringify(value)).strip().lower()

    return re.sub('[-\s]+', '-', value)
