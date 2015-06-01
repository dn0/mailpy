# -*- coding: utf-8 -*-
from email.message import Message
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .utils import send_mail, decode_header
from .request import MailRequest

__all__ = ('MailResponse', 'TextMailResponse', 'HtmlMailResponse')


class MailResponse(object):
    """
    Mail response (message wrapper).
    """
    status_code = 200

    def __init__(self, request, message, sender=None, recipients=None, subject=None, status_code=None):
        assert isinstance(request, MailRequest), 'request must be an instance of %s' % MailRequest
        assert isinstance(message, Message), 'message must be an instance of %s' % Message

        if sender is None:
            sender = request.recipient

        if recipients is None:
            recipients = [request.sender]

        if subject is None:
            subject = 'Re: ' + request.get('Subject', '')  # Use original (encoded) header

        assert isinstance(recipients, (tuple, list)), 'recipients must a tuple or list'

        self._sent = False
        self._subject = subject
        self.request = request
        self.message = message
        self.status_code = status_code or self.status_code
        # SMTP envelope headers
        self.sender = sender
        self.recipients = recipients
        # Message headers
        self._add_message_headers()

    def _add_message_headers(self):
        """Add basic message headers and custom mailpy headers"""
        message = self.message

        # Message headers
        if 'Subject' not in message:
            message['Subject'] = self._subject

        if 'From' not in message:
            message['From'] = self.sender

        if 'To' not in message:
            message['To'] = ','.join(self.recipients)

        message['In-Reply-To'] = self.request.message_id
        message['X-mailpy-resource'] = self.request.resource
        message['X-mailpy-method'] = self.request.method
        message['X-mailpy-status-code'] = str(self.status_code)

    def __repr__(self):
        return '%s(status=%s, from="%s", to="%s", subject="%s")' % (self.__class__.__name__, self.status_code,
                                                                    self.sender, self.recipient,
                                                                    self.message.get('Subject', ''))

    def __str__(self):
        return '%s' % self.message

    @property
    def recipient(self):
        return ','.join(self.recipients)

    @property
    def subject(self):
        return decode_header(self.message.get('Subject', ''))

    def send(self, sendmail_fun=send_mail):
        self._sent = True
        return sendmail_fun(self.sender, self.recipients, self.message.as_string())


class TextMailResponse(MailResponse):
    """
    Text mail response.
    """
    def __init__(self, request, text, charset='utf-8', **kwargs):
        super(TextMailResponse, self).__init__(request, MIMEText(text, _charset=charset), **kwargs)


class HtmlMailResponse(MailResponse):
    """
    HTML mail response.
    """
    def __init__(self, request, html, text=None, charset='utf-8', **kwargs):
        msg = MIMEMultipart('alternative')

        if text is not None:
            msg.attach(MIMEText(text, 'text', _charset=charset))

        msg.attach(MIMEText(html, 'html', _charset=charset))

        super(HtmlMailResponse, self).__init__(request, msg, **kwargs)
