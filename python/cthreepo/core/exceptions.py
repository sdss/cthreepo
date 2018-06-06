# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-12-05 12:01:21
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-05-29 17:30:01

from __future__ import print_function, division, absolute_import


class CthreepoError(Exception):
    """A custom core Cthreepo exception"""

    def __init__(self, message=None):

        message = 'There has been an error' \
            if not message else message

        super(CthreepoError, self).__init__(message)


class CthreepoNotImplemented(CthreepoError):
    """A custom exception for not yet implemented features."""

    def __init__(self, message=None):

        message = 'This feature is not implemented yet.' \
            if not message else message

        super(CthreepoNotImplemented, self).__init__(message)


class CthreepoApiError(CthreepoError):
    """A custom exception for API errors"""

    def __init__(self, message=None):
        if not message:
            message = 'Error with Http Response from Cthreepo API'
        else:
            message = 'Http response error from Cthreepo API. {0}'.format(message)

        super(CthreepoApiError, self).__init__(message)


class CthreepoApiAuthError(CthreepoApiError):
    """A custom exception for API authentication errors"""
    pass


class CthreepoMissingDependency(CthreepoError):
    """A custom exception for missing dependencies."""
    pass


class CthreepoWarning(Warning):
    """Base warning for Cthreepo."""
    pass


class CthreepoUserWarning(UserWarning, CthreepoWarning):
    """The primary warning class."""
    pass


class CthreepoSkippedTestWarning(CthreepoUserWarning):
    """A warning for when a test is skipped."""
    pass


class CthreepoDeprecationWarning(CthreepoUserWarning):
    """A warning for deprecated features."""
    pass

