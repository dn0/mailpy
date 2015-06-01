# -*- coding: utf-8 -*-
from functools import partial
from email.parser import FeedParser
from email.header import decode_header as _decode_header
import smtplib


def send_mail(from_addr, to_addrs, msg, host='localhost', port=25):
    """Send mail via SMTP(localhost:25)"""
    server = smtplib.SMTP(host, port)
    ret = server.sendmail(from_addr, to_addrs, msg)
    server.quit()

    return ret


def parse_message(file_input, sender, recipient):
    """Parse message from file input and create MailRequest"""
    from .request import MailRequest  # circular imports
    parser = FeedParser(partial(MailRequest, sender, recipient))

    for line in file_input:
        parser.feed(line)

    return parser.close()


def decode(string, encoding):
    """Helper for decode_header (in case it would return bytes str)"""
    try:
        return string.decode(encoding)
    except AttributeError:
        return str(string)


def decode_header(header):
    """Return decoded message header"""
    return ''.join(decode(value, charset or 'ascii') for value, charset in _decode_header(header))
