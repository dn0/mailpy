# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import errno as err

__all__ = ('PelicanAPIError', 'FileNotFound', 'FileAlreadyExists', 'UnknownFileFormat')


class PelicanAPIError(Exception):
    """
    Pelican API base exception.
    """
    pass


class FileNotFound(PelicanAPIError, OSError):
    """
    File does not exist on FS.
    """
    errno = err.ENOENT
    strerror = os.strerror(err.ENOENT)


class FileAlreadyExists(PelicanAPIError, OSError):
    """
    File already exists on FS.
    """
    errno = err.EEXIST
    strerror = os.strerror(err.EEXIST)


class UnknownFileFormat(PelicanAPIError):
    """
    Invalid pelican content file.
    """
    pass
