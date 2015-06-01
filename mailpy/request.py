# -*- coding: utf-8 -*-
from email.message import Message

from .utils import decode_header

__all__ = ('MailRequest',)


class MailRequest(Message):
    """
    Mail request.
    """
    def __init__(self, sender, recipient):
        Message.__init__(self)
        self.sender = sender
        self.recipient = recipient
        method, resource = recipient.split('@', 1)
        self.method = method.replace('-', '_').lower()
        self.resource = '.'.join(reversed(resource.replace('-', '_').lower().split('.')))

    def __repr__(self):
        return '%s(from="%s", to="%s", subject="%s")' % (self.__class__.__name__, self.sender,
                                                         self.recipient, self.get('Subject', ''))

    @property
    def subject(self):
        return decode_header(self.get('Subject', ''))

    @property
    def message_id(self):
        return self.get('Message-Id', '')
