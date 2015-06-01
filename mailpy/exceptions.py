# -*- coding: utf-8 -*-
from .response import MailResponse, TextMailResponse, HtmlMailResponse

__all__ = (
    'MailPyError', 'MailViewAlreadyRegistered', 'MailMethodAlreadyRegistered',  # api and router errors
    'MailError', 'TextMailError', 'HtmlMailError'  # response errors
)


class MailPyError(Exception):
    """
    Base mailpy exception.
    """
    pass


class MailViewAlreadyRegistered(MailPyError):
    """
    Thrown by MailRouter.register_view().
    """
    pass


class MailMethodAlreadyRegistered(MailPyError):
    """
    Thrown by MailRouter.register_method().
    """
    pass


class MailError(MailResponse, Exception):
    """
    Mail error - response used as an exception.
    """
    status_code = 400


class TextMailError(TextMailResponse, MailError):
    """
    Text mail error.
    """
    pass


class HtmlMailError(HtmlMailResponse, MailError):
    """
    HTML mail error.
    """
    pass


class MailViewError(TextMailError):
    """
    Custom exception used by MailView methods.
    """
    message = ''

    def __init__(self, request, text='', **kwargs):
        text = text or self.message
        status_code = kwargs.get('status_code', self.status_code)
        super(MailViewError, self).__init__(request, 'ERROR [%s]: %s' % (status_code, text), **kwargs)
